"""Heuristic scoring helpers used by the search service."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from gateway.search.filtering import parse_iso_datetime
from gateway.search.models import CoverageInfo, SearchWeights


class HeuristicScorer:
    """Apply hybrid heuristic signals and aggregate scoring metadata."""

    def __init__(
        self,
        *,
        weights: SearchWeights,
        vector_weight: float,
        lexical_weight: float,
    ) -> None:
        self.weight_subsystem = weights.subsystem
        self.weight_relationship = weights.relationship
        self.weight_support = weights.support
        self.weight_coverage_penalty = weights.coverage_penalty
        self.weight_criticality = weights.criticality
        self.vector_weight = vector_weight
        self.lexical_weight = lexical_weight

    def build_chunk(self, payload: dict[str, Any], score: float) -> dict[str, Any]:
        return {
            "chunk_id": payload.get("chunk_id"),
            "artifact_path": payload.get("path"),
            "artifact_type": payload.get("artifact_type"),
            "subsystem": payload.get("subsystem"),
            "namespace": payload.get("namespace"),
            "tags": payload.get("tags"),
            "text": payload.get("text"),
            "coverage_missing": bool(payload.get("coverage_missing")),
            "score": score,
            "subsystem_criticality": payload.get("subsystem_criticality"),
            "coverage_ratio": payload.get("coverage_ratio"),
            "git_timestamp": payload.get("git_timestamp"),
        }

    def lexical_score(self, query: str, chunk: dict[str, Any]) -> float:
        text = str(chunk.get("text") or "")
        if not text:
            return 0.0
        tokens = re.split(r"\W+", text.lower())
        query_tokens = re.split(r"\W+", query.lower())
        matches = sum(1 for token in tokens if token and token in query_tokens)
        total = len(tokens) or 1
        return matches / total

    def base_scoring(self, *, vector_score: float, lexical_score: float) -> dict[str, Any]:
        weighted_vector = vector_score * self.vector_weight
        weighted_lexical = lexical_score * self.lexical_weight
        adjusted_score = weighted_vector + weighted_lexical
        return {
            "vector_score": vector_score,
            "lexical_score": lexical_score,
            "weighted_vector_score": weighted_vector,
            "weighted_lexical_score": weighted_lexical,
            "adjusted_score": adjusted_score,
        }

    def apply_graph_scoring(
        self,
        *,
        base_scoring: dict[str, Any],
        vector_score: float,
        lexical_score: float,
        query_tokens: set[str],
        chunk: dict[str, Any],
        graph_context: dict[str, Any],
    ) -> dict[str, Any]:
        subsystem_affinity = self._calculate_subsystem_affinity(chunk.get("subsystem") or "", query_tokens)
        related = graph_context.get("related_artifacts") or []
        supporting_bonus = self._calculate_supporting_bonus(related)
        coverage_info = self._calculate_coverage_info(chunk)
        criticality_score = self._calculate_criticality_score(chunk, graph_context)

        adjusted_score = base_scoring["weighted_vector_score"] + base_scoring.get("weighted_lexical_score", 0.0)
        adjusted_score += subsystem_affinity * self.weight_subsystem
        adjusted_score += len(related) * self.weight_relationship * 0.1
        adjusted_score += supporting_bonus * self.weight_support
        adjusted_score -= coverage_info.penalty
        adjusted_score += criticality_score * self.weight_criticality

        scoring = dict(base_scoring)
        scoring.update(
            {
                "adjusted_score": adjusted_score,
                "signals": {
                    "subsystem_affinity": subsystem_affinity,
                    "relationship_count": len(related),
                    "supporting_bonus": supporting_bonus,
                    "coverage_missing": coverage_info.missing_flag,
                    "coverage_ratio": coverage_info.ratio,
                    "criticality_score": criticality_score,
                    "coverage_penalty": coverage_info.penalty,
                },
            }
        )
        return scoring

    def populate_additional_signals(
        self,
        *,
        scoring: dict[str, Any],
        chunk: dict[str, Any],
        graph_context: dict[str, Any] | None,
        path_depth: float | None,
        freshness_days: float | None,
    ) -> dict[str, Any]:
        signals = scoring.setdefault("signals", {})

        path_value = path_depth if path_depth is not None else self._estimate_path_depth(graph_context)
        signals["path_depth"] = float(path_value) if path_value is not None else None

        criticality = chunk.get("subsystem_criticality")
        if criticality is None:
            criticality = self._extract_subsystem_criticality(graph_context)
        signals.setdefault("criticality_score", self._normalise_criticality(criticality))

        if freshness_days is None:
            freshness_days = self.compute_freshness_days(chunk, graph_context)
        signals.setdefault("freshness_days", freshness_days)

        signals.setdefault("coverage_ratio", chunk.get("coverage_ratio"))
        return scoring

    def compute_freshness_days(
        self,
        chunk: dict[str, Any],
        graph_context: dict[str, Any] | None,
    ) -> float | None:
        candidates = [
            chunk.get("git_timestamp"),
            chunk.get("last_modified"),
            chunk.get("last_modified_at"),
            chunk.get("updated_at"),
        ]
        if graph_context:
            primary = graph_context.get("primary_node", {})
            props = primary.get("properties") or {}
            candidates.extend(
                [
                    props.get("git_timestamp"),
                    props.get("last_modified"),
                    props.get("updated_at"),
                ]
            )
        for value in candidates:
            parsed = parse_iso_datetime(value)
            if parsed is not None:
                delta = datetime.now(UTC) - parsed
                return max(delta.total_seconds() / 86400.0, 0.0)
        return None

    @staticmethod
    def _calculate_subsystem_affinity(subsystem: str, query_tokens: set[str]) -> float:
        if not subsystem:
            return 0.0
        if subsystem in query_tokens:
            return 1.0
        if any(subsystem in token or token in subsystem for token in query_tokens):
            return 0.5
        return 0.0

    @staticmethod
    def _calculate_supporting_bonus(related_artifacts: list[dict[str, Any]]) -> float:
        design_docs = 0
        test_cases = 0
        for item in related_artifacts:
            identifier = item.get("id", "")
            if isinstance(identifier, str) and identifier.startswith("DesignDoc:"):
                design_docs += 1
            elif isinstance(identifier, str) and identifier.startswith("TestCase:"):
                test_cases += 1
        return min(design_docs, 2) * 0.2 + min(test_cases, 2) * 0.1

    def _calculate_coverage_info(self, chunk: dict[str, Any]) -> CoverageInfo:
        coverage_missing_flag = 1.0 if chunk.get("coverage_missing") else 0.0
        coverage_ratio_raw = chunk.get("coverage_ratio")
        coverage_ratio = self._coerce_ratio_value(coverage_ratio_raw)
        if coverage_ratio is None:
            coverage_ratio = 0.0 if coverage_missing_flag else 1.0
        penalty = self.weight_coverage_penalty * (1.0 - coverage_ratio)
        return CoverageInfo(ratio=coverage_ratio, penalty=penalty, missing_flag=coverage_missing_flag)

    @staticmethod
    def _coerce_ratio_value(value: object) -> float | None:
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float)):
            return max(0.0, min(1.0, float(value)))
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                numeric = float(text)
            except ValueError:
                return None
            return max(0.0, min(1.0, numeric))
        return None

    @staticmethod
    def _calculate_criticality_score(
        chunk: dict[str, Any],
        graph_context: dict[str, Any] | None,
    ) -> float:
        criticality_value = chunk.get("subsystem_criticality")
        if criticality_value is None:
            criticality_value = HeuristicScorer._extract_subsystem_criticality(graph_context)
        return HeuristicScorer._normalise_criticality(criticality_value)

    @staticmethod
    def _extract_subsystem_criticality(graph_context: dict[str, Any] | None) -> str | None:
        if not graph_context:
            return None
        primary = graph_context.get("primary_node", {})
        props = primary.get("properties") or {}
        if props.get("criticality"):
            return props.get("criticality")
        relationships = graph_context.get("relationships") or []
        for rel in relationships:
            target_props = rel.get("target", {}).get("properties") or {}
            if target_props.get("criticality"):
                return target_props.get("criticality")
        return None

    @staticmethod
    def _normalise_criticality(value: str | float | None) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        lookup = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0,
        }
        return lookup.get(str(value).lower(), 0.0)

    @staticmethod
    def _estimate_path_depth(graph_context: dict[str, Any] | None) -> float:
        if not graph_context:
            return 0.0
        relationships = graph_context.get("relationships") or []
        if any(rel.get("type") == "BELONGS_TO" for rel in relationships):
            return 1.0
        return 0.0


__all__ = ["HeuristicScorer"]

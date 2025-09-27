"""Search service exposing vector search with graph context."""

from .feedback import SearchFeedbackStore
from .exporter import ExportOptions, ExportStats, export_training_dataset
from .maintenance import (
    PruneOptions,
    PruneStats,
    RedactOptions,
    RedactStats,
    prune_feedback_log,
    redact_dataset,
)
from .evaluation import EvaluationMetrics, evaluate_model
from .dataset import DatasetLoadError, load_dataset_records, build_feature_matrix
from .service import SearchResult, SearchResponse, SearchService

__all__ = [
    "SearchService",
    "SearchResult",
    "SearchResponse",
    "SearchFeedbackStore",
    "DatasetLoadError",
    "load_dataset_records",
    "build_feature_matrix",
    "ExportOptions",
    "ExportStats",
    "export_training_dataset",
    "PruneOptions",
    "PruneStats",
    "RedactOptions",
    "RedactStats",
    "prune_feedback_log",
    "redact_dataset",
    "EvaluationMetrics",
    "evaluate_model",
]

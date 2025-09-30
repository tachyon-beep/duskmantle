"""Search service exposing vector search with graph context."""

from .dataset import DatasetLoadError, build_feature_matrix, load_dataset_records
from .evaluation import EvaluationMetrics, evaluate_model
from .exporter import ExportOptions, ExportStats, export_training_dataset
from .feedback import SearchFeedbackStore
from .maintenance import PruneOptions, PruneStats, RedactOptions, RedactStats, prune_feedback_log, redact_dataset
from .service import SearchResponse, SearchResult, SearchService

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

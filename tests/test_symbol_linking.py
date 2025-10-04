from pathlib import Path

from gateway.ingest.artifacts import Artifact
from gateway.ingest.pipeline import _annotate_test_symbol_links


def make_artifact(path: str, artifact_type: str, content: str, extra: dict | None = None) -> Artifact:
    return Artifact(
        path=Path(path),
        artifact_type=artifact_type,
        subsystem=None,
        content=content,
        git_commit=None,
        git_timestamp=None,
        extra_metadata=extra or {},
    )


def test_annotate_links_matches_method_reference() -> None:
    symbols = [
        {
            "id": "src/project/module.py::Example.method",
            "qualified_name": "Example.method",
            "name": "method",
            "kind": "method",
            "language": "python",
        }
    ]
    source = make_artifact(
        "src/project/module.py",
        "code",
        "class Example:\n    def method(self):\n        return True\n",
        extra={"symbols": symbols},
    )
    test_content = "from project.module import Example\n\n\ndef test_calls_method():\n    Example.method()\n"
    test_artifact = make_artifact("tests/project/test_module.py", "test", test_content)

    _annotate_test_symbol_links([source, test_artifact])

    assert test_artifact.extra_metadata["exercises_symbols"] == ["src/project/module.py::Example.method"]
    details = test_artifact.extra_metadata["exercises_symbol_details"]
    assert details[0]["qualified_name"] == "Example.method"


def test_annotate_links_ignores_unrelated_tokens() -> None:
    symbols = [
        {
            "id": "src/project/module.py::serialize_payload",
            "qualified_name": "serialize_payload",
            "name": "serialize_payload",
            "kind": "function",
            "language": "python",
        }
    ]
    source = make_artifact(
        "src/project/module.py",
        "code",
        "def serialize_payload(data):\n    return data\n",
        extra={"symbols": symbols},
    )
    unrelated = make_artifact(
        "tests/other/test_unrelated.py",
        "test",
        "def test_placeholder():\n    assert 'serialize_payload' == 'serialize_payload'\n",
    )

    _annotate_test_symbol_links([source, unrelated])

    assert "exercises_symbols" not in unrelated.extra_metadata

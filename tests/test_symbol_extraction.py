from pathlib import Path

import pytest

from gateway.ingest.symbols import extract_symbols

pytest.importorskip("tree_sitter_languages")


def test_extract_python_symbols_simple() -> None:
    content = """
class Example:
    def method(self) -> None:
        pass

def helper():
    return 1
""".strip()

    symbols = extract_symbols(Path("src/example.py"), content)
    names = {symbol.qualified_name: symbol for symbol in symbols}

    assert set(names) >= {"Example", "Example.method", "helper"}
    assert names["Example"].kind == "class"
    assert names["Example.method"].kind == "method"
    assert names["helper"].kind == "function"
    assert names["helper"].language == "python"

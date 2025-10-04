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



def test_extract_typescript_symbols() -> None:
    content = """
export class Example {
  method(): void {}
}

export function helper(): void {}
""".strip()

    symbols = extract_symbols(Path("src/example.ts"), content)
    names = {symbol.qualified_name: symbol for symbol in symbols}

    assert set(names) >= {"Example", "Example.method", "helper"}
    assert names["Example"].kind == "class"
    assert names["Example.method"].kind == "method"
    assert names["Example"].language == "typescript"
    assert names["helper"].kind == "function"


def test_extract_go_symbols() -> None:
    content = """
package example

type Example struct {}

func (e *Example) Method() {}

func helper() {}
""".strip()

    symbols = extract_symbols(Path("src/example.go"), content)
    names = {symbol.qualified_name: symbol for symbol in symbols}

    assert names["helper"].kind == "function"
    assert names["helper"].language == "go"
    assert any(symbol.kind == "method" and symbol.name == "Method" for symbol in symbols)

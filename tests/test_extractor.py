"""Tests for mermaid diagram extraction from markdown files."""

import pytest
from pathlib import Path


@pytest.fixture
def simple_mermaid_content():
    """Single mermaid block in markdown."""
    return """# My Document

Some introduction text.

```mermaid
flowchart TD
    A[Start] --> B[End]
```

Some closing text.
"""


@pytest.fixture
def multiple_mermaid_content():
    """Multiple mermaid blocks in markdown."""
    return """# Architecture

## Flow

```mermaid
flowchart LR
    A --> B
    B --> C
```

## Sequence

```mermaid
sequenceDiagram
    Alice->>Bob: Hello
    Bob-->>Alice: Hi
```

## Gantt

```mermaid
gantt
    title Project Timeline
    section Phase 1
    Task 1: 2024-01-01, 30d
```
"""


@pytest.fixture
def empty_mermaid_content():
    """Markdown with empty mermaid block."""
    return """# Document

```mermaid
```

More text.
"""


@pytest.fixture
def no_mermaid_content():
    """Markdown without any mermaid blocks."""
    return """# Regular Document

This is just normal markdown.

```python
print("Not a mermaid diagram")
```

Some more text.
"""


@pytest.fixture
def malformed_fence_content():
    """Markdown with malformed code fences."""
    return """# Document

```mermaid
flowchart TD
    A --> B

No closing fence here.

```python
print("test")
```
"""


@pytest.fixture
def mixed_code_blocks_content():
    """Markdown with mixed code blocks."""
    return """# Document

```javascript
console.log("JS code");
```

```mermaid
pie title Pets
    "Dogs" : 386
    "Cats" : 85
```

```python
print("Python code")
```

```mermaid
graph TD
    A[Node A]
```
"""


@pytest.fixture
def temp_markdown_file(tmp_path):
    """Create a temporary markdown file."""

    def _create_file(content, filename="test.md"):
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path

    return _create_file


class TestMermaidExtractor:
    """Test suite for mermaid diagram extraction."""

    def test_extract_single_block(self, simple_mermaid_content):
        """Test extraction of a single mermaid block."""
        from src.extractor import extract_mermaid_blocks

        blocks = extract_mermaid_blocks(simple_mermaid_content)

        assert len(blocks) == 1
        assert "flowchart TD" in blocks[0]["content"]
        assert "A[Start] --> B[End]" in blocks[0]["content"]

    def test_extract_multiple_blocks(self, multiple_mermaid_content):
        """Test extraction of multiple mermaid blocks."""
        from src.extractor import extract_mermaid_blocks

        blocks = extract_mermaid_blocks(multiple_mermaid_content)

        assert len(blocks) == 3
        assert "flowchart" in blocks[0]["content"]
        assert "sequenceDiagram" in blocks[1]["content"]
        assert "gantt" in blocks[2]["content"]

    def test_extract_empty_block(self, empty_mermaid_content):
        """Test extraction of empty mermaid block."""
        from src.extractor import extract_mermaid_blocks

        blocks = extract_mermaid_blocks(empty_mermaid_content)

        # Empty blocks should be extracted but may be filtered
        assert isinstance(blocks, list)

    def test_extract_no_mermaid(self, no_mermaid_content):
        """Test extraction when no mermaid blocks exist."""
        from src.extractor import extract_mermaid_blocks

        blocks = extract_mermaid_blocks(no_mermaid_content)

        assert len(blocks) == 0

    def test_detect_flowchart_type(self, simple_mermaid_content):
        """Test detection of flowchart diagram type."""
        from src.extractor import extract_mermaid_blocks, detect_diagram_type

        blocks = extract_mermaid_blocks(simple_mermaid_content)
        diagram_type = detect_diagram_type(blocks[0]["content"])

        assert diagram_type == "flowchart"

    def test_detect_sequence_type(self):
        """Test detection of sequence diagram type."""
        from src.extractor import detect_diagram_type

        content = """sequenceDiagram
    participant A
    A->>B: Message"""

        diagram_type = detect_diagram_type(content)

        assert diagram_type == "sequence"

    def test_detect_gantt_type(self):
        """Test detection of gantt diagram type."""
        from src.extractor import detect_diagram_type

        content = """gantt
    title Timeline
    section Work
    Task: 2024-01-01, 5d"""

        diagram_type = detect_diagram_type(content)

        assert diagram_type == "gantt"

    def test_detect_class_type(self):
        """Test detection of class diagram type."""
        from src.extractor import detect_diagram_type

        content = """classDiagram
    class Animal {
        +name: string
    }"""

        diagram_type = detect_diagram_type(content)

        assert diagram_type == "class"

    def test_detect_state_type(self):
        """Test detection of state diagram type."""
        from src.extractor import detect_diagram_type

        content = """stateDiagram-v2
    [*] --> Active
    Active --> [*]"""

        diagram_type = detect_diagram_type(content)

        assert diagram_type == "state"

    def test_detect_er_type(self):
        """Test detection of entity relationship diagram type."""
        from src.extractor import detect_diagram_type

        content = """erDiagram
    CUSTOMER ||--o{ ORDER : places"""

        diagram_type = detect_diagram_type(content)

        assert diagram_type == "er"

    def test_detect_pie_type(self):
        """Test detection of pie chart type."""
        from src.extractor import detect_diagram_type

        content = """pie title Distribution
    "A" : 45
    "B" : 55"""

        diagram_type = detect_diagram_type(content)

        assert diagram_type == "pie"

    def test_detect_journey_type(self):
        """Test detection of user journey diagram type."""
        from src.extractor import detect_diagram_type

        content = """journey
    title User Journey
    section Shopping
      Browse: 5: User"""

        diagram_type = detect_diagram_type(content)

        assert diagram_type == "journey"

    def test_detect_git_type(self):
        """Test detection of git graph type."""
        from src.extractor import detect_diagram_type

        content = """gitGraph
    commit
    branch develop
    checkout develop"""

        diagram_type = detect_diagram_type(content)

        assert diagram_type == "git"

    def test_detect_graph_lr_type(self):
        """Test detection of graph LR as flowchart."""
        from src.extractor import detect_diagram_type

        content = """graph LR
    A --> B"""

        diagram_type = detect_diagram_type(content)

        assert diagram_type == "flowchart"

    def test_detect_unknown_type(self):
        """Test detection of unknown diagram type."""
        from src.extractor import detect_diagram_type

        content = """unknown diagram type
    some content"""

        diagram_type = detect_diagram_type(content)

        assert diagram_type == "unknown"

    def test_line_number_tracking(self, simple_mermaid_content):
        """Test that line numbers are tracked correctly."""
        from src.extractor import extract_mermaid_blocks

        blocks = extract_mermaid_blocks(simple_mermaid_content, track_lines=True)

        assert len(blocks) == 1
        assert "start_line" in blocks[0]
        assert "end_line" in blocks[0]
        assert blocks[0]["start_line"] > 0
        assert blocks[0]["end_line"] > blocks[0]["start_line"]

    def test_source_file_metadata(self, temp_markdown_file, simple_mermaid_content):
        """Test that source file is tracked in metadata."""
        from src.extractor import extract_mermaid_from_file

        file_path = temp_markdown_file(simple_mermaid_content, "source.md")
        blocks = extract_mermaid_from_file(file_path)

        assert len(blocks) == 1
        assert blocks[0]["source_file"] == str(file_path)

    def test_mixed_code_blocks(self, mixed_code_blocks_content):
        """Test extraction ignores non-mermaid code blocks."""
        from src.extractor import extract_mermaid_blocks

        blocks = extract_mermaid_blocks(mixed_code_blocks_content)

        assert len(blocks) == 2
        assert all(
            "mermaid" in block["content"].lower()
            or "pie" in block["content"].lower()
            or "graph" in block["content"].lower()
            for block in blocks
        )
        assert not any(
            "console.log" in block["content"] or "print(" in block["content"]
            for block in blocks
        )

    def test_whitespace_preservation(self):
        """Test that whitespace in diagrams is preserved."""
        from src.extractor import extract_mermaid_blocks

        content = """# Doc

```mermaid
flowchart TD
    A[Node A]
    B[Node B]
    A --> B
```
"""
        blocks = extract_mermaid_blocks(content)

        assert len(blocks) == 1
        # Check that indentation is preserved
        assert "    A[Node A]" in blocks[0]["content"]

    def test_special_characters_in_diagram(self):
        """Test handling of special characters in diagrams."""
        from src.extractor import extract_mermaid_blocks

        content = """# Doc

```mermaid
flowchart TD
    A["Node with 'quotes' & special chars!"]
    B[Node (with) [brackets]]
    A --> B
```
"""
        blocks = extract_mermaid_blocks(content)

        assert len(blocks) == 1
        assert "quotes" in blocks[0]["content"]
        assert "&" in blocks[0]["content"]
        assert "brackets" in blocks[0]["content"]

    def test_unicode_in_diagram(self):
        """Test handling of unicode characters in diagrams."""
        from src.extractor import extract_mermaid_blocks

        content = """# Doc

```mermaid
flowchart TD
    A[用户] --> B[系统]
    C[Émile] --> D[José]
```
"""
        blocks = extract_mermaid_blocks(content)

        assert len(blocks) == 1
        assert "用户" in blocks[0]["content"]
        assert "Émile" in blocks[0]["content"]

    def test_diagram_with_comments(self):
        """Test extraction of diagrams with mermaid comments."""
        from src.extractor import extract_mermaid_blocks

        content = """# Doc

```mermaid
flowchart TD
    %% This is a comment
    A[Start] --> B[End]
    %% Another comment
```
"""
        blocks = extract_mermaid_blocks(content)

        assert len(blocks) == 1
        assert "%% This is a comment" in blocks[0]["content"]

    def test_malformed_fence(self, malformed_fence_content):
        """Test handling of malformed code fences."""
        from src.extractor import extract_mermaid_blocks

        # Should handle gracefully without raising exception
        blocks = extract_mermaid_blocks(malformed_fence_content)

        assert isinstance(blocks, list)

    def test_extract_from_file_not_found(self, tmp_path):
        """Test extraction from non-existent file."""
        from src.extractor import extract_mermaid_from_file

        non_existent = tmp_path / "does_not_exist.md"

        with pytest.raises(FileNotFoundError):
            extract_mermaid_from_file(non_existent)

    def test_extract_from_empty_file(self, temp_markdown_file):
        """Test extraction from empty file."""
        from src.extractor import extract_mermaid_from_file

        file_path = temp_markdown_file("", "empty.md")
        blocks = extract_mermaid_from_file(file_path)

        assert len(blocks) == 0

    def test_block_index_metadata(self, multiple_mermaid_content):
        """Test that block index is tracked."""
        from src.extractor import extract_mermaid_blocks

        blocks = extract_mermaid_blocks(multiple_mermaid_content, track_index=True)

        assert len(blocks) == 3
        assert blocks[0]["index"] == 0
        assert blocks[1]["index"] == 1
        assert blocks[2]["index"] == 2

    def test_diagram_content_trimmed(self):
        """Test that extracted content is trimmed of excess whitespace."""
        from src.extractor import extract_mermaid_blocks

        content = """# Doc

```mermaid

flowchart TD
    A --> B

```
"""
        blocks = extract_mermaid_blocks(content)

        assert len(blocks) == 1
        # Content should not start or end with blank lines
        assert not blocks[0]["content"].startswith("\n\n")
        assert not blocks[0]["content"].endswith("\n\n")

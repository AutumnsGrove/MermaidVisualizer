"""
Refactored tests for extractor.py - matching actual implementation.

These tests work with the actual function signatures and return types,
using temp files instead of strings, and accessing dataclass attributes
instead of dictionary keys.
"""

import pytest
from pathlib import Path
from src.extractor import extract_mermaid_blocks, extract_from_multiple_files, MermaidDiagram


class TestMermaidExtractor:
    """Refactored test suite for mermaid extraction."""

    def test_extract_single_diagram(self, tmp_path):
        """Test extraction of a single mermaid block."""
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Document

```mermaid
flowchart TD
    A --> B
```
""")

        # Extract
        diagrams = extract_mermaid_blocks(test_file)

        # Verify
        assert len(diagrams) == 1
        assert isinstance(diagrams[0], MermaidDiagram)
        assert diagrams[0].diagram_type == "flowchart"
        assert "A --> B" in diagrams[0].content
        assert diagrams[0].index == 0
        assert diagrams[0].start_line > 0
        assert diagrams[0].end_line > diagrams[0].start_line
        assert diagrams[0].source_file == test_file.resolve()

    def test_extract_multiple_diagrams(self, tmp_path):
        """Test extraction of multiple diagrams from one file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Doc

```mermaid
flowchart TD
    A --> B
```

```mermaid
sequenceDiagram
    Alice->>Bob: Hi
```

```mermaid
gantt
    title Timeline
    Task 1: 2024-01-01, 30d
```
""")

        diagrams = extract_mermaid_blocks(test_file)

        assert len(diagrams) == 3
        assert diagrams[0].diagram_type == "flowchart"
        assert diagrams[1].diagram_type == "sequenceDiagram"
        assert diagrams[2].diagram_type == "gantt"
        assert diagrams[0].index == 0
        assert diagrams[1].index == 1
        assert diagrams[2].index == 2

    def test_no_diagrams_found(self, tmp_path):
        """Test file with no mermaid diagrams."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Just markdown\n\nNo diagrams here.")

        diagrams = extract_mermaid_blocks(test_file)

        assert len(diagrams) == 0
        assert diagrams == []

    def test_file_not_found(self, tmp_path):
        """Test error handling for missing file."""
        nonexistent = tmp_path / "missing.md"

        with pytest.raises(FileNotFoundError):
            extract_mermaid_blocks(nonexistent)

    def test_empty_mermaid_block(self, tmp_path):
        """Test that empty mermaid blocks are ignored."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Doc

```mermaid
```

```mermaid
flowchart TD
    A --> B
```
""")

        diagrams = extract_mermaid_blocks(test_file)

        # Empty blocks should be filtered out
        assert len(diagrams) == 1
        assert diagrams[0].diagram_type == "flowchart"

    def test_line_number_tracking(self, tmp_path):
        """Test that line numbers are tracked correctly."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Header
Line 2
Line 3
```mermaid
flowchart TD
    A --> B
```
""")

        diagrams = extract_mermaid_blocks(test_file)

        assert len(diagrams) == 1
        # Line numbers are 1-indexed, content starts after the fence marker
        assert diagrams[0].start_line == 4  # Content starts on line 4 (after ```mermaid)
        assert diagrams[0].end_line == 7    # Closing fence on line 7

    def test_different_diagram_types(self, tmp_path):
        """Test detection of various diagram types."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""
```mermaid
graph LR
    A --> B
```

```mermaid
classDiagram
    Class01 <|-- Class02
```

```mermaid
stateDiagram
    [*] --> State1
```

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
```

```mermaid
pie title Pets
    "Dogs" : 386
    "Cats" : 85
```
""")

        diagrams = extract_mermaid_blocks(test_file)

        assert len(diagrams) == 5
        assert diagrams[0].diagram_type == "graph"
        assert diagrams[1].diagram_type == "classDiagram"
        assert diagrams[2].diagram_type == "stateDiagram"
        assert diagrams[3].diagram_type == "erDiagram"
        assert diagrams[4].diagram_type == "pie"

    def test_unicode_content(self, tmp_path):
        """Test extraction of diagrams with unicode characters."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""# 文档

```mermaid
flowchart TD
    A[开始] --> B[结束]
```
""", encoding="utf-8")

        diagrams = extract_mermaid_blocks(test_file)

        assert len(diagrams) == 1
        assert "开始" in diagrams[0].content
        assert "结束" in diagrams[0].content

    def test_tilde_fence_support(self, tmp_path):
        """Test that ~~~ style fences work in addition to ```."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Doc

~~~mermaid
flowchart TD
    A --> B
~~~
""")

        diagrams = extract_mermaid_blocks(test_file)

        assert len(diagrams) == 1
        assert diagrams[0].diagram_type == "flowchart"

    def test_case_insensitive_fence(self, tmp_path):
        """Test that mermaid fence is case-insensitive."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Doc

```MERMAID
flowchart TD
    A --> B
```

```Mermaid
sequenceDiagram
    A->>B: Hi
```
""")

        diagrams = extract_mermaid_blocks(test_file)

        assert len(diagrams) == 2

    def test_extract_from_multiple_files(self, tmp_path):
        """Test extracting from multiple files at once."""
        # Create multiple test files
        file1 = tmp_path / "test1.md"
        file1.write_text("""
```mermaid
flowchart TD
    A --> B
```
""")

        file2 = tmp_path / "test2.md"
        file2.write_text("""
```mermaid
sequenceDiagram
    A->>B: Hi
```

```mermaid
gantt
    title Timeline
```
""")

        file3 = tmp_path / "test3.md"
        file3.write_text("No diagrams here")

        # Extract from all files
        diagrams = extract_from_multiple_files([file1, file2, file3])

        assert len(diagrams) == 3
        assert diagrams[0].source_file == file1.resolve()
        assert diagrams[1].source_file == file2.resolve()
        assert diagrams[2].source_file == file2.resolve()

    def test_extract_from_multiple_files_with_errors(self, tmp_path):
        """Test that extract_from_multiple_files continues despite errors."""
        # Create one valid file
        valid_file = tmp_path / "valid.md"
        valid_file.write_text("""
```mermaid
flowchart TD
    A --> B
```
""")

        # Reference a non-existent file
        invalid_file = tmp_path / "nonexistent.md"

        # Should not raise exception, just skip the invalid file
        diagrams = extract_from_multiple_files([valid_file, invalid_file])

        assert len(diagrams) == 1
        assert diagrams[0].source_file == valid_file.resolve()

    def test_unclosed_fence(self, tmp_path):
        """Test handling of unclosed code fence."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Doc

```mermaid
flowchart TD
    A --> B
""")

        diagrams = extract_mermaid_blocks(test_file)

        # Should still extract the content even without closing fence
        assert len(diagrams) == 1
        assert "flowchart" in diagrams[0].content

    def test_source_file_is_absolute_path(self, tmp_path):
        """Test that source_file is stored as absolute path."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""
```mermaid
flowchart TD
    A --> B
```
""")

        diagrams = extract_mermaid_blocks(test_file)

        assert len(diagrams) == 1
        assert diagrams[0].source_file.is_absolute()
        assert diagrams[0].source_file == test_file.resolve()

    def test_whitespace_only_block_ignored(self, tmp_path):
        """Test that blocks with only whitespace are ignored."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Doc

```mermaid


```

```mermaid
flowchart TD
    A --> B
```
""")

        diagrams = extract_mermaid_blocks(test_file)

        # Only the non-empty block should be extracted
        assert len(diagrams) == 1
        assert diagrams[0].diagram_type == "flowchart"

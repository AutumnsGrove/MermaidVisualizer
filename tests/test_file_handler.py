"""Tests for file system operations and file handling."""

import pytest
from pathlib import Path
import shutil


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project directory structure."""
    # Create directory structure
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "architecture").mkdir()
    (tmp_path / "docs" / "api").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    # Create markdown files with mermaid diagrams
    (tmp_path / "docs" / "README.md").write_text(
        """# Documentation

```mermaid
flowchart TD
    A --> B
```
"""
    )

    (tmp_path / "docs" / "architecture" / "system.md").write_text(
        """# System

```mermaid
sequenceDiagram
    A->>B: Message
```

```mermaid
flowchart LR
    X --> Y
```
"""
    )

    (tmp_path / "docs" / "api" / "endpoints.md").write_text(
        """# API

No diagrams here.
"""
    )

    # Create non-markdown files
    (tmp_path / "docs" / "image.png").write_text("fake image")
    (tmp_path / "src" / "code.py").write_text("print('hello')")

    # Create markdown in subdirectory
    (tmp_path / "tests" / "test.md").write_text(
        """# Test

```mermaid
gantt
    title Timeline
```
"""
    )

    return tmp_path


@pytest.fixture
def output_dir(tmp_path):
    """Create temporary output directory."""
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    return out_dir


@pytest.fixture
def single_file(tmp_path):
    """Create a single markdown file."""
    file_path = tmp_path / "single.md"
    file_path.write_text(
        """# Single

```mermaid
flowchart TD
    Start --> End
```

```mermaid
pie title Data
    "A" : 30
    "B" : 70
```
"""
    )
    return file_path


class TestFileDiscovery:
    """Test suite for file discovery operations."""

    def test_find_markdown_files_recursive(self, sample_project):
        """Test recursive discovery of markdown files."""
        from src.file_handler import find_markdown_files

        files = find_markdown_files(sample_project, recursive=True)

        assert len(files) >= 3
        assert any("README.md" in str(f) for f in files)
        assert any("system.md" in str(f) for f in files)
        assert any("test.md" in str(f) for f in files)

    def test_find_markdown_files_non_recursive(self, sample_project):
        """Test non-recursive discovery (only top level)."""
        from src.file_handler import find_markdown_files

        files = find_markdown_files(sample_project / "docs", recursive=False)

        assert len(files) == 1
        assert "README.md" in str(files[0])

    def test_find_markdown_files_excludes_non_markdown(self, sample_project):
        """Test that non-markdown files are excluded."""
        from src.file_handler import find_markdown_files

        files = find_markdown_files(sample_project, recursive=True)

        assert not any(str(f).endswith(".png") for f in files)
        assert not any(str(f).endswith(".py") for f in files)

    def test_find_markdown_files_empty_directory(self, tmp_path):
        """Test discovery in empty directory."""
        from src.file_handler import find_markdown_files

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        files = find_markdown_files(empty_dir)

        assert len(files) == 0

    def test_find_markdown_files_nonexistent_directory(self, tmp_path):
        """Test discovery in non-existent directory."""
        from src.file_handler import find_markdown_files

        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(FileNotFoundError):
            find_markdown_files(nonexistent)

    def test_find_markdown_files_with_pattern(self, sample_project):
        """Test discovery with filename pattern."""
        from src.file_handler import find_markdown_files

        files = find_markdown_files(
            sample_project, pattern="**/system.md", recursive=True
        )

        assert len(files) == 1
        assert "system.md" in str(files[0])

    def test_find_markdown_files_exclude_patterns(self, sample_project):
        """Test discovery with exclude patterns."""
        from src.file_handler import find_markdown_files

        files = find_markdown_files(
            sample_project, recursive=True, exclude_patterns=["**/tests/**"]
        )

        assert not any("tests" in str(f) for f in files)

    def test_find_markdown_files_single_file(self, single_file):
        """Test handling when path is a file, not directory."""
        from src.file_handler import find_markdown_files

        # Should return the file itself if it's a markdown file
        files = find_markdown_files(single_file.parent, recursive=False)

        assert len(files) == 1
        assert files[0] == single_file


class TestOutputFilenameGeneration:
    """Test suite for output filename generation."""

    def test_generate_output_filename_basic(self):
        """Test basic output filename generation."""
        from src.file_handler import generate_output_filename

        filename = generate_output_filename(
            source_file="document.md",
            block_index=0,
            diagram_type="flowchart",
            format="png",
        )

        assert filename == "document_0_flowchart.png"

    def test_generate_output_filename_with_path(self):
        """Test output filename generation with full path."""
        from src.file_handler import generate_output_filename

        filename = generate_output_filename(
            source_file="/path/to/document.md",
            block_index=2,
            diagram_type="sequence",
            format="svg",
        )

        assert filename == "document_2_sequence.svg"
        assert "/" not in filename

    def test_generate_output_filename_multiple_blocks(self):
        """Test filename generation for multiple blocks from same file."""
        from src.file_handler import generate_output_filename

        filenames = [
            generate_output_filename("doc.md", i, "flowchart", "png") for i in range(3)
        ]

        assert filenames[0] == "doc_0_flowchart.png"
        assert filenames[1] == "doc_1_flowchart.png"
        assert filenames[2] == "doc_2_flowchart.png"

    def test_generate_output_filename_unknown_type(self):
        """Test filename generation with unknown diagram type."""
        from src.file_handler import generate_output_filename

        filename = generate_output_filename(
            source_file="document.md",
            block_index=0,
            diagram_type="unknown",
            format="png",
        )

        assert filename == "document_0_unknown.png"

    def test_generate_output_filename_special_chars(self):
        """Test filename generation with special characters."""
        from src.file_handler import generate_output_filename

        filename = generate_output_filename(
            source_file="my document (v2).md",
            block_index=0,
            diagram_type="flowchart",
            format="png",
        )

        # Special characters should be sanitized
        assert " " not in filename or filename == "my_document_v2_0_flowchart.png"

    def test_generate_output_filename_with_prefix(self):
        """Test filename generation with custom prefix."""
        from src.file_handler import generate_output_filename

        filename = generate_output_filename(
            source_file="document.md",
            block_index=0,
            diagram_type="flowchart",
            format="png",
            prefix="diagram_",
        )

        assert filename.startswith("diagram_")

    def test_generate_output_filename_nested_path(self):
        """Test filename generation from nested path."""
        from src.file_handler import generate_output_filename

        filename = generate_output_filename(
            source_file="docs/architecture/system.md",
            block_index=0,
            diagram_type="sequence",
            format="png",
            preserve_path=True,
        )

        # Should preserve directory structure
        assert "architecture" in filename or "docs" in filename


class TestMappingCreation:
    """Test suite for diagram mapping creation."""

    def test_create_diagram_mapping(self, single_file):
        """Test creation of diagram mapping."""
        from src.file_handler import create_diagram_mapping

        diagrams = [
            {
                "source_file": str(single_file),
                "index": 0,
                "type": "flowchart",
                "output_file": "single_0_flowchart.png",
            },
            {
                "source_file": str(single_file),
                "index": 1,
                "type": "pie",
                "output_file": "single_1_pie.png",
            },
        ]

        mapping = create_diagram_mapping(diagrams)

        assert str(single_file) in mapping
        assert len(mapping[str(single_file)]) == 2

    def test_create_diagram_mapping_multiple_files(self, sample_project):
        """Test mapping creation with multiple source files."""
        from src.file_handler import create_diagram_mapping

        diagrams = [
            {
                "source_file": str(sample_project / "docs" / "README.md"),
                "index": 0,
                "type": "flowchart",
                "output_file": "README_0_flowchart.png",
            },
            {
                "source_file": str(
                    sample_project / "docs" / "architecture" / "system.md"
                ),
                "index": 0,
                "type": "sequence",
                "output_file": "system_0_sequence.png",
            },
        ]

        mapping = create_diagram_mapping(diagrams)

        assert len(mapping) == 2

    def test_create_diagram_mapping_empty(self):
        """Test mapping creation with no diagrams."""
        from src.file_handler import create_diagram_mapping

        mapping = create_diagram_mapping([])

        assert mapping == {}


class TestIndexGeneration:
    """Test suite for index.html generation."""

    def test_generate_index_html(self, output_dir):
        """Test generation of index.html."""
        from src.file_handler import generate_index_html

        diagrams = [
            {
                "source_file": "docs/README.md",
                "index": 0,
                "type": "flowchart",
                "output_file": "README_0_flowchart.png",
                "title": "System Overview",
            },
            {
                "source_file": "docs/api.md",
                "index": 0,
                "type": "sequence",
                "output_file": "api_0_sequence.png",
                "title": "API Flow",
            },
        ]

        index_path = generate_index_html(diagrams, output_dir)

        assert index_path.exists()
        assert index_path.name == "index.html"

        content = index_path.read_text()
        assert "README_0_flowchart.png" in content
        assert "api_0_sequence.png" in content

    def test_generate_index_html_empty(self, output_dir):
        """Test index generation with no diagrams."""
        from src.file_handler import generate_index_html

        index_path = generate_index_html([], output_dir)

        assert index_path.exists()
        content = index_path.read_text()
        assert "no diagrams" in content.lower() or len(content) > 0

    def test_generate_index_html_with_metadata(self, output_dir):
        """Test index generation with diagram metadata."""
        from src.file_handler import generate_index_html

        diagrams = [
            {
                "source_file": "docs/README.md",
                "index": 0,
                "type": "flowchart",
                "output_file": "README_0_flowchart.png",
                "title": "Architecture",
                "start_line": 10,
                "end_line": 15,
            }
        ]

        index_path = generate_index_html(diagrams, output_dir)

        content = index_path.read_text()
        assert "Architecture" in content
        assert "line" in content.lower() or "10" in content

    def test_generate_index_html_grouped_by_file(self, output_dir):
        """Test that index groups diagrams by source file."""
        from src.file_handler import generate_index_html

        diagrams = [
            {
                "source_file": "docs/README.md",
                "index": 0,
                "type": "flowchart",
                "output_file": "README_0_flowchart.png",
            },
            {
                "source_file": "docs/README.md",
                "index": 1,
                "type": "sequence",
                "output_file": "README_1_sequence.png",
            },
        ]

        index_path = generate_index_html(diagrams, output_dir)

        content = index_path.read_text()
        # Should show source file header
        assert "README.md" in content


class TestFileOperations:
    """Test suite for file operations."""

    def test_copy_file(self, tmp_path):
        """Test file copy operation."""
        from src.file_handler import copy_file

        source = tmp_path / "source.txt"
        source.write_text("test content")
        dest = tmp_path / "dest.txt"

        copy_file(source, dest)

        assert dest.exists()
        assert dest.read_text() == "test content"

    def test_ensure_directory_exists(self, tmp_path):
        """Test directory creation."""
        from src.file_handler import ensure_directory

        new_dir = tmp_path / "new" / "nested" / "dir"

        ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_already_exists(self, tmp_path):
        """Test directory creation when already exists."""
        from src.file_handler import ensure_directory

        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        ensure_directory(existing_dir)

        assert existing_dir.exists()

    def test_clean_output_directory(self, output_dir):
        """Test cleaning output directory."""
        from src.file_handler import clean_output_directory

        # Create some files
        (output_dir / "diagram1.png").write_text("test")
        (output_dir / "diagram2.svg").write_text("test")
        (output_dir / "index.html").write_text("test")

        clean_output_directory(output_dir)

        # Directory should be empty or only contain .gitkeep
        files = list(output_dir.iterdir())
        assert len(files) == 0 or all(f.name == ".gitkeep" for f in files)

    def test_get_relative_path(self, tmp_path):
        """Test getting relative path."""
        from src.file_handler import get_relative_path

        base = tmp_path / "project"
        file = tmp_path / "project" / "docs" / "file.md"

        rel_path = get_relative_path(file, base)

        assert str(rel_path) == "docs/file.md" or str(rel_path) == "docs\\file.md"

    def test_is_markdown_file(self):
        """Test markdown file detection."""
        from src.file_handler import is_markdown_file

        assert is_markdown_file(Path("document.md")) is True
        assert is_markdown_file(Path("document.MD")) is True
        assert is_markdown_file(Path("document.markdown")) is True
        assert is_markdown_file(Path("document.txt")) is False
        assert is_markdown_file(Path("document.py")) is False

    def test_get_file_stats(self, single_file):
        """Test getting file statistics."""
        from src.file_handler import get_file_stats

        stats = get_file_stats(single_file)

        assert "size" in stats
        assert "modified" in stats
        assert stats["size"] > 0

    def test_create_backup(self, tmp_path):
        """Test file backup creation."""
        from src.file_handler import create_backup

        original = tmp_path / "file.txt"
        original.write_text("original content")

        backup_path = create_backup(original)

        assert backup_path.exists()
        assert backup_path.read_text() == "original content"
        assert ".bak" in backup_path.name or "backup" in backup_path.name.lower()


class TestDiagramCaching:
    """Test suite for diagram caching functionality."""

    def test_should_regenerate_diagram_not_exists(self, tmp_path):
        """Test regeneration decision when output doesn't exist."""
        from src.file_handler import should_regenerate_diagram

        source = tmp_path / "source.md"
        source.write_text("content")
        output = tmp_path / "output.png"

        assert should_regenerate_diagram(source, output) is True

    def test_should_regenerate_diagram_source_newer(self, tmp_path):
        """Test regeneration when source is newer than output."""
        from src.file_handler import should_regenerate_diagram
        import time

        source = tmp_path / "source.md"
        output = tmp_path / "output.png"

        output.write_text("old")
        time.sleep(0.1)
        source.write_text("new")

        assert should_regenerate_diagram(source, output) is True

    def test_should_regenerate_diagram_output_newer(self, tmp_path):
        """Test no regeneration when output is newer than source."""
        from src.file_handler import should_regenerate_diagram
        import time

        source = tmp_path / "source.md"
        output = tmp_path / "output.png"

        source.write_text("old")
        time.sleep(0.1)
        output.write_text("new")

        assert should_regenerate_diagram(source, output) is False

    def test_force_regenerate(self, tmp_path):
        """Test forced regeneration."""
        from src.file_handler import should_regenerate_diagram

        source = tmp_path / "source.md"
        output = tmp_path / "output.png"

        source.write_text("content")
        output.write_text("content")

        assert should_regenerate_diagram(source, output, force=True) is True

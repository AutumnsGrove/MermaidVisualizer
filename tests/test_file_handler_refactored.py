"""
Refactored tests for file_handler.py - matching actual implementation.

These tests work with actual function names and signatures, create
DiagramMapping objects directly, and test the focused functionality
that actually exists.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from src.file_handler import (
    find_markdown_files,
    create_output_filename,
    get_project_name,
    ensure_output_dir,
    save_mapping,
    load_mapping,
    generate_index_html,
    create_linked_markdown,
    DiagramMapping
)


class TestFileDiscovery:
    """Test markdown file discovery functionality."""

    def test_find_markdown_files_recursive(self, tmp_path):
        """Test recursive markdown file discovery."""
        # Create directory structure
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "nested").mkdir()

        # Create markdown files
        (tmp_path / "README.md").write_text("# Root")
        (tmp_path / "docs" / "guide.md").write_text("# Guide")
        (tmp_path / "docs" / "nested" / "deep.markdown").write_text("# Deep")
        (tmp_path / "other.txt").write_text("Not markdown")

        files = find_markdown_files(tmp_path, recursive=True)

        # Should find all markdown files recursively
        assert len(files) == 3
        file_names = [f.name for f in files]
        assert "README.md" in file_names
        assert "guide.md" in file_names
        assert "deep.markdown" in file_names
        assert "other.txt" not in file_names

    def test_find_markdown_files_non_recursive(self, tmp_path):
        """Test non-recursive markdown file discovery."""
        # Create directory structure
        (tmp_path / "docs").mkdir()

        # Create markdown files
        (tmp_path / "README.md").write_text("# Root")
        (tmp_path / "docs" / "guide.md").write_text("# Guide")

        files = find_markdown_files(tmp_path, recursive=False)

        # Should only find files in root directory
        assert len(files) == 1
        assert files[0].name == "README.md"

    def test_find_markdown_files_empty_directory(self, tmp_path):
        """Test finding files in empty directory."""
        files = find_markdown_files(tmp_path, recursive=True)

        assert len(files) == 0
        assert files == []

    def test_find_markdown_files_directory_not_found(self, tmp_path):
        """Test error when directory doesn't exist."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            find_markdown_files(nonexistent)

    def test_find_markdown_files_not_a_directory(self, tmp_path):
        """Test error when path is not a directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        with pytest.raises(NotADirectoryError):
            find_markdown_files(file_path)

    def test_find_markdown_files_sorted_output(self, tmp_path):
        """Test that output is sorted consistently."""
        # Create files in non-alphabetical order
        (tmp_path / "zebra.md").write_text("# Z")
        (tmp_path / "alpha.md").write_text("# A")
        (tmp_path / "beta.md").write_text("# B")

        files = find_markdown_files(tmp_path)

        file_names = [f.name for f in files]
        assert file_names == sorted(file_names)


class TestFilenameGeneration:
    """Test output filename generation."""

    def test_create_output_filename_basic(self):
        """Test basic filename generation."""
        source = Path("architecture.md")
        filename = create_output_filename(source, 0, "flowchart", "png")

        assert filename == "architecture_0_flowchart.png"

    def test_create_output_filename_multiple_indices(self):
        """Test filename generation with different indices."""
        source = Path("design.md")

        filename1 = create_output_filename(source, 0, "flowchart", "png")
        filename2 = create_output_filename(source, 1, "sequence", "svg")
        filename3 = create_output_filename(source, 2, "gantt", "png")

        assert filename1 == "design_0_flowchart.png"
        assert filename2 == "design_1_sequence.svg"
        assert filename3 == "design_2_gantt.png"

    def test_create_output_filename_with_path(self):
        """Test that filename uses only basename, not full path."""
        source = Path("/some/long/path/document.md")
        filename = create_output_filename(source, 0, "flowchart", "png")

        assert filename == "document_0_flowchart.png"
        assert "/" not in filename

    def test_get_project_name_default(self):
        """Test project name extraction."""
        source = Path("/Users/name/Projects/MyProject/docs/file.md")
        project = get_project_name(source, levels_up=2)

        assert project == "MyProject"

    def test_get_project_name_different_levels(self):
        """Test project name with different levels."""
        source = Path("/Users/name/Projects/MyProject/docs/file.md")

        # Go up 1 level: docs
        project1 = get_project_name(source, levels_up=1)
        assert project1 == "docs"

        # Go up 3 levels: Projects
        project3 = get_project_name(source, levels_up=3)
        assert project3 == "Projects"


class TestDirectoryManagement:
    """Test directory creation and management."""

    def test_ensure_output_dir_creates_directory(self, tmp_path):
        """Test that output directory is created."""
        output_dir = tmp_path / "output"

        assert not output_dir.exists()

        ensure_output_dir(output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_ensure_output_dir_nested_directories(self, tmp_path):
        """Test creating nested directories."""
        nested_dir = tmp_path / "a" / "b" / "c"

        ensure_output_dir(nested_dir)

        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_ensure_output_dir_already_exists(self, tmp_path):
        """Test that existing directory doesn't cause error."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Should not raise error
        ensure_output_dir(output_dir)

        assert output_dir.exists()


class TestMappingPersistence:
    """Test diagram mapping save/load functionality."""

    def test_save_and_load_mapping(self, tmp_path):
        """Test saving and loading diagram mappings."""
        output_dir = tmp_path / "output"

        mappings = [
            DiagramMapping(
                source_file="/path/to/doc1.md",
                diagram_files=["diagram1.png", "diagram2.png"],
                timestamp="2024-01-01T12:00:00"
            ),
            DiagramMapping(
                source_file="/path/to/doc2.md",
                diagram_files=["diagram3.svg"],
                timestamp="2024-01-01T13:00:00"
            )
        ]

        # Save mappings
        save_mapping(mappings, output_dir)

        # Verify file was created
        mapping_file = output_dir / "diagram_mappings.json"
        assert mapping_file.exists()

        # Load mappings
        loaded_mappings = load_mapping(output_dir)

        assert len(loaded_mappings) == 2
        assert loaded_mappings[0].source_file == "/path/to/doc1.md"
        assert loaded_mappings[0].diagram_files == ["diagram1.png", "diagram2.png"]
        assert loaded_mappings[1].source_file == "/path/to/doc2.md"

    def test_load_mapping_file_not_found(self, tmp_path):
        """Test error when mapping file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_mapping(tmp_path)

    def test_save_mapping_creates_directory(self, tmp_path):
        """Test that save_mapping creates output directory."""
        output_dir = tmp_path / "nonexistent"

        mappings = [
            DiagramMapping(
                source_file="/path/to/doc.md",
                diagram_files=["diagram.png"],
                timestamp="2024-01-01T12:00:00"
            )
        ]

        save_mapping(mappings, output_dir)

        assert output_dir.exists()
        assert (output_dir / "diagram_mappings.json").exists()

    def test_mapping_json_format(self, tmp_path):
        """Test that saved JSON has correct format."""
        output_dir = tmp_path / "output"

        mappings = [
            DiagramMapping(
                source_file="/path/to/doc.md",
                diagram_files=["diagram.png"],
                timestamp="2024-01-01T12:00:00"
            )
        ]

        save_mapping(mappings, output_dir)

        # Read raw JSON
        with open(output_dir / "diagram_mappings.json") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["source_file"] == "/path/to/doc.md"
        assert data[0]["diagram_files"] == ["diagram.png"]
        assert data[0]["timestamp"] == "2024-01-01T12:00:00"


class TestHTMLGeneration:
    """Test HTML index generation."""

    def test_generate_index_html_basic(self, tmp_path):
        """Test basic HTML index generation."""
        output_dir = tmp_path / "output"

        mappings = [
            DiagramMapping(
                source_file="/path/to/doc.md",
                diagram_files=["diagram.png"],
                timestamp="2024-01-01T12:00:00"
            )
        ]

        generate_index_html(mappings, output_dir)

        index_file = output_dir / "index.html"
        assert index_file.exists()

        html_content = index_file.read_text()
        assert "<!DOCTYPE html>" in html_content
        assert "Mermaid Diagram Index" in html_content
        assert "doc.md" in html_content
        assert "diagram.png" in html_content

    def test_generate_index_html_empty_mappings(self, tmp_path):
        """Test HTML generation with no mappings."""
        output_dir = tmp_path / "output"

        generate_index_html([], output_dir)

        index_file = output_dir / "index.html"
        assert index_file.exists()

        html_content = index_file.read_text()
        assert "No diagrams generated yet" in html_content

    def test_generate_index_html_multiple_sources(self, tmp_path):
        """Test HTML with multiple source files."""
        output_dir = tmp_path / "output"

        mappings = [
            DiagramMapping(
                source_file="/path/to/doc1.md",
                diagram_files=["diagram1.png", "diagram2.png"],
                timestamp="2024-01-01T12:00:00"
            ),
            DiagramMapping(
                source_file="/path/to/doc2.md",
                diagram_files=["diagram3.svg"],
                timestamp="2024-01-01T13:00:00"
            )
        ]

        generate_index_html(mappings, output_dir)

        html_content = (output_dir / "index.html").read_text()
        assert "doc1.md" in html_content
        assert "doc2.md" in html_content
        assert "diagram1.png" in html_content
        assert "diagram2.png" in html_content
        assert "diagram3.svg" in html_content


class TestLinkedMarkdown:
    """Test linked markdown generation."""

    def test_create_linked_markdown_basic(self, tmp_path):
        """Test creating markdown with diagram links."""
        source_file = tmp_path / "doc.md"
        source_file.write_text("""# Document

```mermaid
flowchart TD
    A --> B
```

Some text.

```mermaid
sequenceDiagram
    A->>B: Hi
```
""")

        diagram_files = [
            str(tmp_path / "diagram1.png"),
            str(tmp_path / "diagram2.png")
        ]

        # Create dummy diagram files
        for df in diagram_files:
            Path(df).write_bytes(b"fake data")

        linked_file = create_linked_markdown(source_file, diagram_files, output_in_source_dir=True)

        assert linked_file is not None
        assert linked_file.exists()
        assert linked_file.name == "doc_linked.md"

        content = linked_file.read_text()
        assert "![[diagram1.png]]" in content
        assert "![[diagram2.png]]" in content
        assert "```mermaid" not in content

    def test_create_linked_markdown_source_not_found(self, tmp_path):
        """Test error when source file doesn't exist."""
        source_file = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            create_linked_markdown(source_file, [])

    def test_create_linked_markdown_preserves_other_content(self, tmp_path):
        """Test that non-mermaid content is preserved."""
        source_file = tmp_path / "doc.md"
        source_file.write_text("""# Title

This is regular text.

```python
def hello():
    print("world")
```

```mermaid
flowchart TD
    A --> B
```

More text.
""")

        diagram_files = [str(tmp_path / "diagram.png")]
        Path(diagram_files[0]).write_bytes(b"fake")

        linked_file = create_linked_markdown(source_file, diagram_files)
        content = linked_file.read_text()

        # Non-mermaid content should be preserved
        assert "# Title" in content
        assert "This is regular text" in content
        assert "```python" in content
        assert 'print("world")' in content
        assert "More text" in content

        # Mermaid should be replaced
        assert "![[diagram.png]]" in content
        assert "flowchart TD" not in content

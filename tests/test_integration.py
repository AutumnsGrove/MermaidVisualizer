"""
Integration tests for MermaidVisualizer.

These tests verify that the core modules work together correctly.
"""

import pytest
from pathlib import Path
from src import extractor, file_handler


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_extractor_with_real_file(self, tmp_path):
        """Test extractor with a real markdown file."""
        # Create a test markdown file
        test_file = tmp_path / "test.md"
        test_file.write_text(
            """# Test Document

```mermaid
flowchart TD
    A[Start] --> B[End]
```

## Another Section

```mermaid
sequenceDiagram
    Alice->>Bob: Hello
    Bob->>Alice: Hi
```
"""
        )

        # Extract diagrams
        diagrams = extractor.extract_mermaid_blocks(test_file)

        # Verify results
        assert len(diagrams) == 2
        assert diagrams[0].diagram_type == "flowchart"
        assert diagrams[1].diagram_type == "sequenceDiagram"
        assert diagrams[0].index == 0
        assert diagrams[1].index == 1
        assert "Start" in diagrams[0].content
        assert "Alice" in diagrams[1].content

    def test_file_handler_discover_files(self, tmp_path):
        """Test file handler can discover markdown files."""
        # Create test structure
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "test1.md").write_text("# Test 1")
        (tmp_path / "docs" / "test2.md").write_text("# Test 2")
        (tmp_path / "other.txt").write_text("Not markdown")

        # Discover files
        files = file_handler.find_markdown_files(tmp_path, recursive=True)

        # Verify
        assert len(files) == 2
        assert all(f.suffix == ".md" for f in files)

    def test_output_filename_generation(self, tmp_path):
        """Test output filename generation."""
        source_file = tmp_path / "document.md"

        filename = file_handler.create_output_filename(
            source_file, index=0, diagram_type="flowchart", format="png"
        )

        assert filename == "document_0_flowchart.png"

    def test_ensure_output_directory(self, tmp_path):
        """Test output directory creation."""
        output_dir = tmp_path / "diagrams"

        file_handler.ensure_output_dir(output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_end_to_end_workflow(self, tmp_path):
        """Test complete workflow without actual diagram generation."""
        # Setup
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        output_dir = tmp_path / "output"

        # Create test markdown file
        test_file = docs_dir / "architecture.md"
        test_file.write_text(
            """# System Architecture

```mermaid
flowchart LR
    Frontend --> Backend
    Backend --> Database
```

## Database Schema

```mermaid
erDiagram
    USER ||--o{ ORDER : places
```
"""
        )

        # 1. Discover markdown files
        md_files = file_handler.find_markdown_files(docs_dir, recursive=True)
        assert len(md_files) == 1

        # 2. Extract diagrams
        diagrams = extractor.extract_mermaid_blocks(md_files[0])
        assert len(diagrams) == 2

        # 3. Generate output filenames
        file_handler.ensure_output_dir(output_dir)

        filenames = [
            file_handler.create_output_filename(
                diagram.source_file, diagram.index, diagram.diagram_type, "png"
            )
            for diagram in diagrams
        ]

        assert len(filenames) == 2
        assert "architecture_0_flowchart.png" in filenames
        assert "architecture_1_erDiagram.png" in filenames

        # 4. Create mappings
        mapping = file_handler.DiagramMapping(
            source_file=str(test_file),
            diagram_files=[str(output_dir / f) for f in filenames],
            timestamp="2024-01-01 00:00:00",
        )

        # 5. Save mapping
        file_handler.save_mapping([mapping], output_dir)
        mapping_file = output_dir / "diagram_mappings.json"
        assert mapping_file.exists()

        # 6. Load mapping
        loaded_mappings = file_handler.load_mapping(output_dir)
        assert len(loaded_mappings) == 1
        assert loaded_mappings[0].source_file == str(test_file)

    def test_multiple_files_workflow(self, tmp_path):
        """Test workflow with multiple markdown files."""
        # Create directory structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create multiple files
        for i in range(3):
            file = docs_dir / f"doc{i}.md"
            file.write_text(
                f"""# Document {i}

```mermaid
flowchart TD
    A{i} --> B{i}
```
"""
            )

        # Discover all files
        md_files = file_handler.find_markdown_files(docs_dir, recursive=True)
        assert len(md_files) == 3

        # Extract from all files
        all_diagrams = []
        for md_file in md_files:
            diagrams = extractor.extract_mermaid_blocks(md_file)
            all_diagrams.extend(diagrams)

        assert len(all_diagrams) == 3

    def test_nested_directory_structure(self, tmp_path):
        """Test with nested directory structure."""
        # Create nested structure
        (tmp_path / "docs" / "api").mkdir(parents=True)
        (tmp_path / "docs" / "guides").mkdir(parents=True)

        (tmp_path / "docs" / "api" / "endpoints.md").write_text("# API")
        (tmp_path / "docs" / "guides" / "tutorial.md").write_text("# Tutorial")

        # Recursive discovery
        md_files = file_handler.find_markdown_files(tmp_path, recursive=True)
        assert len(md_files) == 2

        # Non-recursive discovery
        md_files_non_recursive = file_handler.find_markdown_files(
            tmp_path, recursive=False
        )
        assert len(md_files_non_recursive) == 0  # No files at root level

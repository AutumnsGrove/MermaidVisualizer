"""
Refactored tests for generator.py - matching actual implementation.

These tests work with the actual function signatures, properly mock
subprocess calls, and focus on core functionality without testing
non-existent features.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.generator import generate_diagram, validate_mermaid_syntax


class TestMermaidGenerator:
    """Refactored test suite for diagram generation."""

    @pytest.fixture
    def valid_mermaid_content(self):
        """Valid mermaid diagram content."""
        return """flowchart TD
    A[Start] --> B[End]
"""

    @pytest.fixture
    def mock_subprocess_success(self, tmp_path):
        """Mock successful subprocess execution."""
        with patch("src.generator.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            yield mock_run

    @pytest.fixture
    def mock_subprocess_failure(self):
        """Mock failed subprocess execution."""
        with patch("src.generator.subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Syntax error in mermaid diagram"
            )
            yield mock_run

    def test_generate_png_diagram(self, tmp_path, valid_mermaid_content, mock_subprocess_success):
        """Test successful PNG diagram generation."""
        output_path = tmp_path / "diagram.png"

        # Mock file creation by subprocess
        def create_output(*args, **kwargs):
            output_path.write_bytes(b"fake png data")
            return Mock(returncode=0, stdout="", stderr="")

        mock_subprocess_success.side_effect = create_output

        result = generate_diagram(valid_mermaid_content, output_path, format="png")

        assert result is True
        assert mock_subprocess_success.called
        # Verify the command includes expected arguments
        call_args = mock_subprocess_success.call_args[0][0]
        assert "/opt/homebrew/bin/npx" in call_args
        assert "@mermaid-js/mermaid-cli" in call_args
        assert "-i" in call_args
        assert "-o" in call_args
        assert str(output_path) in call_args

    def test_generate_svg_diagram(self, tmp_path, valid_mermaid_content, mock_subprocess_success):
        """Test successful SVG diagram generation."""
        output_path = tmp_path / "diagram.svg"

        def create_output(*args, **kwargs):
            output_path.write_text("<svg>fake svg</svg>")
            return Mock(returncode=0, stdout="", stderr="")

        mock_subprocess_success.side_effect = create_output

        result = generate_diagram(valid_mermaid_content, output_path, format="svg")

        assert result is True
        assert mock_subprocess_success.called

    def test_generate_with_custom_scale(self, tmp_path, valid_mermaid_content, mock_subprocess_success):
        """Test diagram generation with custom scale parameter."""
        output_path = tmp_path / "diagram.png"

        def create_output(*args, **kwargs):
            output_path.write_bytes(b"fake png data")
            return Mock(returncode=0, stdout="", stderr="")

        mock_subprocess_success.side_effect = create_output

        result = generate_diagram(valid_mermaid_content, output_path, format="png", scale=5)

        assert result is True
        # Verify scale parameter is passed
        call_args = mock_subprocess_success.call_args[0][0]
        assert "-s" in call_args
        assert "5" in call_args

    def test_generate_with_custom_width(self, tmp_path, valid_mermaid_content, mock_subprocess_success):
        """Test diagram generation with custom width parameter."""
        output_path = tmp_path / "diagram.png"

        def create_output(*args, **kwargs):
            output_path.write_bytes(b"fake png data")
            return Mock(returncode=0, stdout="", stderr="")

        mock_subprocess_success.side_effect = create_output

        result = generate_diagram(valid_mermaid_content, output_path, format="png", width=3000)

        assert result is True
        # Verify width parameter is passed
        call_args = mock_subprocess_success.call_args[0][0]
        assert "-w" in call_args
        assert "3000" in call_args

    def test_generate_diagram_empty_content(self, tmp_path):
        """Test that empty content returns False."""
        output_path = tmp_path / "diagram.png"

        result = generate_diagram("", output_path, format="png")

        assert result is False

    def test_generate_diagram_invalid_format(self, tmp_path, valid_mermaid_content):
        """Test that invalid format returns False."""
        output_path = tmp_path / "diagram.jpg"

        result = generate_diagram(valid_mermaid_content, output_path, format="jpg")

        assert result is False

    def test_generate_diagram_subprocess_failure(self, tmp_path, valid_mermaid_content, mock_subprocess_failure):
        """Test handling of subprocess failure."""
        output_path = tmp_path / "diagram.png"

        result = generate_diagram(valid_mermaid_content, output_path, format="png")

        assert result is False

    def test_generate_diagram_creates_output_directory(self, tmp_path, valid_mermaid_content, mock_subprocess_success):
        """Test that output directory is created if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "dir"
        output_path = nested_dir / "diagram.png"

        def create_output(*args, **kwargs):
            output_path.write_bytes(b"fake png data")
            return Mock(returncode=0, stdout="", stderr="")

        mock_subprocess_success.side_effect = create_output

        result = generate_diagram(valid_mermaid_content, output_path, format="png")

        assert result is True
        assert nested_dir.exists()

    def test_generate_diagram_timeout(self, tmp_path, valid_mermaid_content):
        """Test handling of subprocess timeout."""
        output_path = tmp_path / "diagram.png"

        with patch("src.generator.subprocess.run") as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 60)

            result = generate_diagram(valid_mermaid_content, output_path, format="png")

        assert result is False

    def test_generate_diagram_cli_not_found(self, tmp_path, valid_mermaid_content):
        """Test handling when mermaid-cli is not installed."""
        output_path = tmp_path / "diagram.png"

        with patch("src.generator.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("npx not found")

            result = generate_diagram(valid_mermaid_content, output_path, format="png")

        assert result is False

    def test_validate_mermaid_syntax_valid(self, mock_subprocess_success):
        """Test validation of valid mermaid syntax."""
        valid_content = """flowchart TD
    A --> B
"""

        def create_temp_output(*args, **kwargs):
            # Mock successful validation
            return Mock(returncode=0, stdout="", stderr="")

        mock_subprocess_success.side_effect = create_temp_output

        is_valid, error = validate_mermaid_syntax(valid_content)

        assert is_valid is True
        assert error == ""

    def test_validate_mermaid_syntax_invalid(self, mock_subprocess_failure):
        """Test validation of invalid mermaid syntax."""
        invalid_content = """flowchart TD
    A ---> B [invalid syntax]
"""

        is_valid, error = validate_mermaid_syntax(invalid_content)

        assert is_valid is False
        assert len(error) > 0

    def test_validate_mermaid_syntax_empty(self):
        """Test validation of empty content."""
        is_valid, error = validate_mermaid_syntax("")

        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_mermaid_syntax_no_diagram_type(self):
        """Test validation of content without valid diagram type."""
        invalid_content = "Just some text without a diagram type"

        is_valid, error = validate_mermaid_syntax(invalid_content)

        assert is_valid is False
        assert "diagram type" in error.lower()

    def test_validate_mermaid_syntax_timeout(self):
        """Test validation timeout handling."""
        valid_content = "flowchart TD\n    A --> B"

        with patch("src.generator.subprocess.run") as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)

            is_valid, error = validate_mermaid_syntax(valid_content)

        assert is_valid is False
        assert "timed out" in error.lower()

    def test_generate_diagram_output_file_empty(self, tmp_path, valid_mermaid_content, mock_subprocess_success):
        """Test that empty output files are detected and removed."""
        output_path = tmp_path / "diagram.png"

        def create_empty_output(*args, **kwargs):
            # Create an empty file
            output_path.write_bytes(b"")
            return Mock(returncode=0, stdout="", stderr="")

        mock_subprocess_success.side_effect = create_empty_output

        result = generate_diagram(valid_mermaid_content, output_path, format="png")

        assert result is False
        # Empty file should be removed
        assert not output_path.exists()

    def test_generate_diagram_output_not_created(self, tmp_path, valid_mermaid_content, mock_subprocess_success):
        """Test detection when subprocess succeeds but doesn't create output."""
        output_path = tmp_path / "diagram.png"

        # Mock doesn't create the file
        result = generate_diagram(valid_mermaid_content, output_path, format="png")

        assert result is False

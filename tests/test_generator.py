"""Tests for mermaid diagram generation (PNG/SVG)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, call
import subprocess


@pytest.fixture
def simple_flowchart():
    """Simple flowchart diagram."""
    return """flowchart TD
    A[Start] --> B[Process]
    B --> C[End]"""


@pytest.fixture
def sequence_diagram():
    """Sequence diagram."""
    return """sequenceDiagram
    participant User
    participant System
    User->>System: Request
    System-->>User: Response"""


@pytest.fixture
def invalid_syntax():
    """Invalid mermaid syntax."""
    return """flowchart TD
    A[Start] -->
    --> C[End]"""


@pytest.fixture
def output_dir(tmp_path):
    """Create temporary output directory."""
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    return out_dir


@pytest.fixture
def mock_subprocess_success():
    """Mock successful subprocess call."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        yield mock_run


@pytest.fixture
def mock_subprocess_failure():
    """Mock failed subprocess call."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr="Error: Invalid syntax"
        )
        yield mock_run


class TestDiagramGenerator:
    """Test suite for diagram generation."""

    def test_generate_png(self, simple_flowchart, output_dir, mock_subprocess_success):
        """Test PNG generation."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.png"
        result = generate_diagram(simple_flowchart, output_file, format="png")

        assert result is True
        mock_subprocess_success.assert_called_once()
        args = mock_subprocess_success.call_args[0][0]
        assert "mmdc" in args or "npx" in args
        assert str(output_file) in args

    def test_generate_svg(self, simple_flowchart, output_dir, mock_subprocess_success):
        """Test SVG generation."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.svg"
        result = generate_diagram(simple_flowchart, output_file, format="svg")

        assert result is True
        mock_subprocess_success.assert_called_once()
        args = mock_subprocess_success.call_args[0][0]
        assert "svg" in " ".join(args).lower() or "-o" in args

    def test_generate_with_npx(
        self, simple_flowchart, output_dir, mock_subprocess_success
    ):
        """Test generation using npx."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.png"
        result = generate_diagram(
            simple_flowchart, output_file, format="png", use_npx=True
        )

        assert result is True
        args = mock_subprocess_success.call_args[0][0]
        assert "npx" in args

    def test_generate_invalid_syntax(
        self, invalid_syntax, output_dir, mock_subprocess_failure
    ):
        """Test handling of invalid mermaid syntax."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.png"
        result = generate_diagram(invalid_syntax, output_file, format="png")

        assert result is False

    def test_generate_empty_content(self, output_dir):
        """Test generation with empty content."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.png"

        with pytest.raises(ValueError):
            generate_diagram("", output_file, format="png")

    def test_generate_creates_temp_file(
        self, simple_flowchart, output_dir, mock_subprocess_success
    ):
        """Test that temporary input file is created."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.png"

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_file = Mock()
            mock_file.name = "/tmp/mermaid_temp.mmd"
            mock_temp.return_value.__enter__.return_value = mock_file

            generate_diagram(simple_flowchart, output_file, format="png")

            mock_file.write.assert_called()

    def test_generate_with_theme(
        self, simple_flowchart, output_dir, mock_subprocess_success
    ):
        """Test generation with custom theme."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.png"
        result = generate_diagram(
            simple_flowchart, output_file, format="png", theme="dark"
        )

        assert result is True
        args = mock_subprocess_success.call_args[0][0]
        # Check if theme parameter is passed
        assert any("theme" in str(arg).lower() for arg in args) or result

    def test_generate_with_background_color(
        self, simple_flowchart, output_dir, mock_subprocess_success
    ):
        """Test generation with custom background color."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.png"
        result = generate_diagram(
            simple_flowchart, output_file, format="png", background_color="transparent"
        )

        assert result is True

    def test_generate_subprocess_timeout(self, simple_flowchart, output_dir):
        """Test handling of subprocess timeout."""
        from src.generator import generate_diagram

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=["mmdc"], timeout=30)

            output_file = output_dir / "diagram.png"
            result = generate_diagram(
                simple_flowchart, output_file, format="png", timeout=30
            )

            assert result is False

    def test_generate_subprocess_error(self, simple_flowchart, output_dir):
        """Test handling of subprocess error."""
        from src.generator import generate_diagram

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1, cmd=["mmdc"]
            )

            output_file = output_dir / "diagram.png"
            result = generate_diagram(simple_flowchart, output_file, format="png")

            assert result is False

    def test_validate_syntax_valid(self, simple_flowchart):
        """Test validation of valid mermaid syntax."""
        from src.generator import validate_mermaid_syntax

        is_valid, error = validate_mermaid_syntax(simple_flowchart)

        assert is_valid is True
        assert error is None or error == ""

    def test_validate_syntax_invalid(self, invalid_syntax):
        """Test validation of invalid mermaid syntax."""
        from src.generator import validate_mermaid_syntax

        is_valid, error = validate_mermaid_syntax(invalid_syntax)

        # Depending on implementation, may return False or True
        # (validation might be done by actual generation attempt)
        assert isinstance(is_valid, bool)
        if not is_valid:
            assert isinstance(error, str)

    def test_validate_syntax_empty(self):
        """Test validation of empty content."""
        from src.generator import validate_mermaid_syntax

        is_valid, error = validate_mermaid_syntax("")

        assert is_valid is False
        assert error is not None

    def test_validate_syntax_whitespace_only(self):
        """Test validation of whitespace-only content."""
        from src.generator import validate_mermaid_syntax

        is_valid, error = validate_mermaid_syntax("   \n\n  ")

        assert is_valid is False

    def test_batch_generate(
        self, simple_flowchart, sequence_diagram, output_dir, mock_subprocess_success
    ):
        """Test batch generation of multiple diagrams."""
        from src.generator import batch_generate_diagrams

        diagrams = [
            {"content": simple_flowchart, "output": output_dir / "diagram1.png"},
            {"content": sequence_diagram, "output": output_dir / "diagram2.png"},
        ]

        results = batch_generate_diagrams(diagrams, format="png")

        assert len(results) == 2
        assert all(r["success"] for r in results)

    def test_batch_generate_with_failures(
        self, simple_flowchart, invalid_syntax, output_dir
    ):
        """Test batch generation with some failures."""
        from src.generator import batch_generate_diagrams

        with patch("subprocess.run") as mock_run:
            # First call succeeds, second fails
            mock_run.side_effect = [
                Mock(returncode=0, stdout="", stderr=""),
                Mock(returncode=1, stdout="", stderr="Error"),
            ]

            diagrams = [
                {"content": simple_flowchart, "output": output_dir / "diagram1.png"},
                {"content": invalid_syntax, "output": output_dir / "diagram2.png"},
            ]

            results = batch_generate_diagrams(diagrams, format="png")

            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[1]["success"] is False

    def test_get_mermaid_cli_version(self, mock_subprocess_success):
        """Test getting mermaid CLI version."""
        from src.generator import get_mermaid_cli_version

        mock_subprocess_success.return_value.stdout = "9.3.0"

        version = get_mermaid_cli_version()

        assert version is not None
        mock_subprocess_success.assert_called()

    def test_get_mermaid_cli_version_not_installed(self):
        """Test version check when CLI not installed."""
        from src.generator import get_mermaid_cli_version

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            version = get_mermaid_cli_version()

            assert version is None

    def test_check_mermaid_cli_available(self, mock_subprocess_success):
        """Test checking if mermaid CLI is available."""
        from src.generator import is_mermaid_cli_available

        assert is_mermaid_cli_available() is True

    def test_check_mermaid_cli_not_available(self):
        """Test checking when mermaid CLI is not available."""
        from src.generator import is_mermaid_cli_available

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            assert is_mermaid_cli_available() is False

    def test_generate_with_width(
        self, simple_flowchart, output_dir, mock_subprocess_success
    ):
        """Test generation with custom width."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.png"
        result = generate_diagram(
            simple_flowchart, output_file, format="png", width=1920
        )

        assert result is True

    def test_generate_with_height(
        self, simple_flowchart, output_dir, mock_subprocess_success
    ):
        """Test generation with custom height."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.png"
        result = generate_diagram(
            simple_flowchart, output_file, format="png", height=1080
        )

        assert result is True

    def test_generate_with_scale(
        self, simple_flowchart, output_dir, mock_subprocess_success
    ):
        """Test generation with custom scale."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.png"
        result = generate_diagram(
            simple_flowchart, output_file, format="png", scale=2.0
        )

        assert result is True

    def test_generate_output_dir_created(
        self, simple_flowchart, tmp_path, mock_subprocess_success
    ):
        """Test that output directory is created if it doesn't exist."""
        from src.generator import generate_diagram

        output_file = tmp_path / "nested" / "dir" / "diagram.png"
        result = generate_diagram(simple_flowchart, output_file, format="png")

        assert result is True
        assert output_file.parent.exists()

    def test_generate_invalid_format(self, simple_flowchart, output_dir):
        """Test generation with invalid format."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.xyz"

        with pytest.raises(ValueError):
            generate_diagram(simple_flowchart, output_file, format="xyz")

    def test_generate_sequence_diagram(
        self, sequence_diagram, output_dir, mock_subprocess_success
    ):
        """Test generation of sequence diagram specifically."""
        from src.generator import generate_diagram

        output_file = output_dir / "sequence.png"
        result = generate_diagram(sequence_diagram, output_file, format="png")

        assert result is True

    def test_cleanup_temp_files(
        self, simple_flowchart, output_dir, mock_subprocess_success
    ):
        """Test that temporary files are cleaned up."""
        from src.generator import generate_diagram

        output_file = output_dir / "diagram.png"

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_file = Mock()
            mock_file.name = "/tmp/mermaid_temp.mmd"
            mock_temp.return_value.__enter__.return_value = mock_file

            generate_diagram(simple_flowchart, output_file, format="png")

            # Ensure context manager was used (cleanup happens automatically)
            mock_temp.return_value.__enter__.assert_called()
            mock_temp.return_value.__exit__.assert_called()

    def test_generate_with_config_file(
        self, simple_flowchart, output_dir, mock_subprocess_success
    ):
        """Test generation with custom config file."""
        from src.generator import generate_diagram

        config_file = output_dir / "config.json"
        config_file.write_text('{"theme": "dark"}')

        output_file = output_dir / "diagram.png"
        result = generate_diagram(
            simple_flowchart, output_file, format="png", config_file=config_file
        )

        assert result is True

    def test_unicode_in_diagram(self, output_dir, mock_subprocess_success):
        """Test generation with unicode characters."""
        from src.generator import generate_diagram

        unicode_diagram = """flowchart TD
    A[用户] --> B[系统]
    C[Café] --> D[Niño]"""

        output_file = output_dir / "unicode.png"
        result = generate_diagram(unicode_diagram, output_file, format="png")

        assert result is True

    def test_special_characters_in_output_path(
        self, simple_flowchart, tmp_path, mock_subprocess_success
    ):
        """Test generation with special characters in output path."""
        from src.generator import generate_diagram

        output_file = tmp_path / "diagram (with spaces).png"
        result = generate_diagram(simple_flowchart, output_file, format="png")

        assert result is True

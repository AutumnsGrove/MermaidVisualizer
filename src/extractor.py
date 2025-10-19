"""
Extract Mermaid diagrams from Markdown files.

This module provides functionality to parse Markdown files and extract
Mermaid diagram code blocks along with their metadata (source file,
line numbers, diagram type, etc.).
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class MermaidDiagram:
    """
    Represents a single Mermaid diagram extracted from a Markdown file.

    Attributes:
        content: The raw Mermaid diagram code
        source_file: Path to the source Markdown file
        start_line: Line number where the diagram starts (1-indexed)
        end_line: Line number where the diagram ends (1-indexed)
        diagram_type: Type of Mermaid diagram (flowchart, sequenceDiagram, etc.)
        index: Zero-based index of this diagram within the source file
        preceding_header: The markdown header immediately before the diagram (None if not found)
        diagram_title: Title/description extracted from within the diagram content (None if not found)
    """

    content: str
    source_file: Path
    start_line: int
    end_line: int
    diagram_type: str
    index: int
    preceding_header: Optional[str] = None
    diagram_title: Optional[str] = None


def _detect_diagram_type(content: str) -> str:
    """
    Detect the type of Mermaid diagram from its content.

    Analyzes the first non-empty line of the diagram to determine its type.
    Common types include: flowchart, sequenceDiagram, gantt, classDiagram,
    stateDiagram, erDiagram, journey, pie, gitGraph, etc.

    Args:
        content: The Mermaid diagram code

    Returns:
        The detected diagram type, or "unknown" if type cannot be determined
    """
    lines = content.strip().split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for common diagram types
        if stripped.startswith("flowchart"):
            return "flowchart"
        elif stripped.startswith("graph"):
            return "graph"
        elif stripped.startswith("sequenceDiagram"):
            return "sequenceDiagram"
        elif stripped.startswith("gantt"):
            return "gantt"
        elif stripped.startswith("classDiagram"):
            return "classDiagram"
        elif stripped.startswith("stateDiagram"):
            return "stateDiagram"
        elif stripped.startswith("erDiagram"):
            return "erDiagram"
        elif stripped.startswith("journey"):
            return "journey"
        elif stripped.startswith("pie"):
            return "pie"
        elif stripped.startswith("gitGraph"):
            return "gitGraph"
        elif stripped.startswith("mindmap"):
            return "mindmap"
        elif stripped.startswith("timeline"):
            return "timeline"
        elif stripped.startswith("quadrantChart"):
            return "quadrantChart"
        elif stripped.startswith("requirementDiagram"):
            return "requirementDiagram"
        elif stripped.startswith("C4Context"):
            return "c4Diagram"
        else:
            # Return the first word as a potential diagram type
            first_word = stripped.split()[0] if stripped else ""
            if first_word:
                return first_word

    return "unknown"


def _extract_preceding_header(lines: List[str], block_start_index: int, max_lookback: int = 10) -> Optional[str]:
    """
    Extract the markdown header that precedes a mermaid diagram block.

    Searches backwards from the block start position to find the nearest markdown
    header (lines starting with #). Ignores empty lines when searching.

    Args:
        lines: List of lines from the markdown file
        block_start_index: Zero-based index where the mermaid block fence starts
        max_lookback: Maximum number of lines to search backwards (default: 10)

    Returns:
        The header text without # symbols and leading/trailing whitespace,
        or None if no header is found within the lookback range.

    Example:
        >>> lines = ["# My Header", "", "```mermaid", "flowchart TD", "```"]
        >>> _extract_preceding_header(lines, 2)
        'My Header'
    """
    # Search backwards from the block start
    for i in range(block_start_index - 1, max(block_start_index - max_lookback - 1, -1), -1):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            continue

        # Check if this is a markdown header
        if line.startswith("#"):
            # Remove # symbols and whitespace
            header_text = line.lstrip("#").strip()
            return header_text if header_text else None

        # If we hit non-empty, non-header content, stop searching
        # (we don't want to skip over other content)
        break

    return None


def _extract_diagram_title(content: str, diagram_type: str) -> Optional[str]:
    """
    Extract a meaningful title from the mermaid diagram content itself.

    Attempts to find descriptive text within the diagram based on its type.
    Different diagram types store titles in different ways.

    Args:
        content: The mermaid diagram code
        diagram_type: The type of diagram (flowchart, sequenceDiagram, etc.)

    Returns:
        The extracted title text, or None if no title can be determined.

    Example:
        >>> content = "flowchart TD\\n    A[Start Process] --> B"
        >>> _extract_diagram_title(content, "flowchart")
        'Start Process'
    """
    lines = content.strip().split("\n")

    # Skip empty lines and the diagram type declaration
    content_lines = [line.strip() for line in lines if line.strip()]
    if not content_lines:
        return None

    # Remove the first line if it's the diagram type declaration
    if content_lines and any(
        content_lines[0].startswith(dt)
        for dt in [
            "flowchart",
            "graph",
            "sequenceDiagram",
            "gantt",
            "classDiagram",
            "stateDiagram",
            "erDiagram",
        ]
    ):
        content_lines = content_lines[1:]

    if not content_lines:
        return None

    # Try type-specific extraction
    if diagram_type in ["flowchart", "graph"]:
        # Look for text in square brackets in first node definition
        # Format: A[Some Text] or Start[Some Text]
        for line in content_lines:
            match = re.search(r"\[([^\]]+)\]", line)
            if match:
                return match.group(1).strip()

    elif diagram_type == "sequenceDiagram":
        # Look for title directive
        for line in content_lines:
            if line.startswith("title") or line.startswith("title:"):
                title = line.replace("title", "").replace(":", "").strip()
                if title:
                    return title

        # Fallback: extract first participant name
        for line in content_lines:
            if "participant" in line.lower():
                # Format: participant Alice or participant Alice as A
                match = re.search(r"participant\s+(\w+)", line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

    elif diagram_type == "gantt":
        # Look for title directive
        for line in content_lines:
            if line.startswith("title") or line.startswith("title:"):
                title = line.replace("title", "").replace(":", "").strip()
                if title:
                    return title

    elif diagram_type == "pie":
        # Look for title in pie chart
        # Format: pie title Some Title
        for line in content_lines:
            if "title" in line.lower():
                match = re.search(r"title\s+(.+)$", line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

    elif diagram_type == "classDiagram":
        # Extract first class name
        for line in content_lines:
            # Format: class ClassName or ClassName : attribute
            match = re.search(r"class\s+(\w+)|^(\w+)\s*[:{]", line)
            if match:
                class_name = match.group(1) or match.group(2)
                if class_name:
                    return class_name.strip()

    elif diagram_type == "erDiagram":
        # Extract first entity name
        for line in content_lines:
            # Format: ENTITY ||--o{ OTHER : relationship
            match = re.search(r"^([A-Z_]+)\s+[\|\}]", line)
            if match:
                return match.group(1).strip()

    # Generic fallback: try to find any text in square brackets or quotes
    for line in content_lines:
        # Try square brackets first
        match = re.search(r"\[([^\]]+)\]", line)
        if match:
            return match.group(1).strip()

        # Try quotes
        match = re.search(r'"([^"]+)"', line)
        if match:
            return match.group(1).strip()

    return None


def _extract_code_blocks(content: str) -> List[tuple]:
    """
    Extract all Mermaid code blocks from Markdown content.

    Supports both ``` and ~~~ style code fences. Handles edge cases like
    empty blocks, malformed fences, and nested structures.

    Args:
        content: The full Markdown file content

    Returns:
        List of tuples containing (mermaid_content, start_line, end_line, block_start_index)
        where block_start_index is the zero-based line index where the fence starts
    """
    blocks = []
    lines = content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for start of a mermaid code block
        # Match ```mermaid or ~~~mermaid (case-insensitive)
        match = re.match(r"^(`{3,}|~{3,})\s*mermaid\s*$", line, re.IGNORECASE)

        if match:
            fence_chars = match.group(1)
            fence_pattern = (
                re.escape(fence_chars[0]) + "{" + str(len(fence_chars)) + ",}"
            )
            block_start_index = i  # Zero-based index where fence starts
            start_line = i + 1  # 1-indexed
            block_lines = []
            i += 1

            # Collect lines until we find the closing fence
            while i < len(lines):
                current_line = lines[i]

                # Check if this is the closing fence
                if re.match(f"^{fence_pattern}\\s*$", current_line):
                    end_line = i + 1  # 1-indexed
                    mermaid_content = "\n".join(block_lines)

                    # Only add non-empty blocks
                    if mermaid_content.strip():
                        blocks.append((mermaid_content, start_line, end_line, block_start_index))
                    break

                block_lines.append(current_line)
                i += 1
            else:
                # Reached end of file without closing fence
                # Still add the block if it has content
                if block_lines and "\n".join(block_lines).strip():
                    end_line = len(lines)
                    blocks.append(("\n".join(block_lines), start_line, end_line, block_start_index))

        i += 1

    return blocks


def extract_mermaid_blocks(file_path: Path) -> List[MermaidDiagram]:
    """
    Extract all Mermaid diagrams from a Markdown file.

    Parses the specified Markdown file and extracts all Mermaid code blocks,
    returning them as structured MermaidDiagram objects with metadata.

    Args:
        file_path: Path to the Markdown file to parse

    Returns:
        List of MermaidDiagram objects, one for each diagram found.
        Returns an empty list if no diagrams are found.

    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If the file cannot be read due to permissions
        UnicodeDecodeError: If the file cannot be decoded as UTF-8

    Example:
        >>> from pathlib import Path
        >>> diagrams = extract_mermaid_blocks(Path("example.md"))
        >>> for diagram in diagrams:
        ...     print(f"Found {diagram.diagram_type} at line {diagram.start_line}")
    """
    # Validate that file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Read file content
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            e.encoding,
            e.object,
            e.start,
            e.end,
            f"Unable to decode file {file_path} as UTF-8",
        )

    # Extract code blocks
    code_blocks = _extract_code_blocks(content)

    # Split content into lines for header extraction
    lines = content.split("\n")

    # Convert to MermaidDiagram objects
    diagrams = []
    for index, (block_content, start_line, end_line, block_start_index) in enumerate(code_blocks):
        diagram_type = _detect_diagram_type(block_content)

        # Extract preceding header
        preceding_header = _extract_preceding_header(lines, block_start_index)

        # Extract diagram title from content
        diagram_title = _extract_diagram_title(block_content, diagram_type)

        diagram = MermaidDiagram(
            content=block_content,
            source_file=file_path.resolve(),  # Use absolute path
            start_line=start_line,
            end_line=end_line,
            diagram_type=diagram_type,
            index=index,
            preceding_header=preceding_header,
            diagram_title=diagram_title,
        )
        diagrams.append(diagram)

    return diagrams


def extract_from_multiple_files(file_paths: List[Path]) -> List[MermaidDiagram]:
    """
    Extract Mermaid diagrams from multiple Markdown files.

    Convenience function to process multiple files at once. Continues
    processing even if individual files fail, collecting errors.

    Args:
        file_paths: List of Paths to Markdown files

    Returns:
        List of all MermaidDiagram objects found across all files

    Note:
        Files that cannot be read are skipped silently. Use the single-file
        function if you need explicit error handling.
    """
    all_diagrams = []

    for file_path in file_paths:
        try:
            diagrams = extract_mermaid_blocks(file_path)
            all_diagrams.extend(diagrams)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError, ValueError):
            # Skip files that cannot be processed
            continue

    return all_diagrams

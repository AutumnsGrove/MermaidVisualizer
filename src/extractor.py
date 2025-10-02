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
    """

    content: str
    source_file: Path
    start_line: int
    end_line: int
    diagram_type: str
    index: int


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


def _extract_code_blocks(content: str) -> List[tuple]:
    """
    Extract all Mermaid code blocks from Markdown content.

    Supports both ``` and ~~~ style code fences. Handles edge cases like
    empty blocks, malformed fences, and nested structures.

    Args:
        content: The full Markdown file content

    Returns:
        List of tuples containing (mermaid_content, start_line, end_line)
    """
    blocks = []
    lines = content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for start of a mermaid code block
        # Match ```mermaid or ~~~mermaid (case-insensitive)
        match = re.match(r'^(`{3,}|~{3,})\s*mermaid\s*$', line, re.IGNORECASE)

        if match:
            fence_chars = match.group(1)
            fence_pattern = re.escape(fence_chars[0]) + "{" + str(len(fence_chars)) + ",}"
            start_line = i + 1  # 1-indexed
            block_lines = []
            i += 1

            # Collect lines until we find the closing fence
            while i < len(lines):
                current_line = lines[i]

                # Check if this is the closing fence
                if re.match(f'^{fence_pattern}\\s*$', current_line):
                    end_line = i + 1  # 1-indexed
                    mermaid_content = "\n".join(block_lines)

                    # Only add non-empty blocks
                    if mermaid_content.strip():
                        blocks.append((mermaid_content, start_line, end_line))
                    break

                block_lines.append(current_line)
                i += 1
            else:
                # Reached end of file without closing fence
                # Still add the block if it has content
                if block_lines and "\n".join(block_lines).strip():
                    end_line = len(lines)
                    blocks.append(("\n".join(block_lines), start_line, end_line))

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
            f"Unable to decode file {file_path} as UTF-8"
        )

    # Extract code blocks
    code_blocks = _extract_code_blocks(content)

    # Convert to MermaidDiagram objects
    diagrams = []
    for index, (block_content, start_line, end_line) in enumerate(code_blocks):
        diagram_type = _detect_diagram_type(block_content)

        diagram = MermaidDiagram(
            content=block_content,
            source_file=file_path.resolve(),  # Use absolute path
            start_line=start_line,
            end_line=end_line,
            diagram_type=diagram_type,
            index=index
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

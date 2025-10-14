"""
File handling module for MermaidVisualizer.

This module provides functions for discovering markdown files, managing output directories,
creating output filenames, and tracking diagram mappings.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class DiagramMapping:
    """
    Represents the mapping between a source file and its generated diagrams.

    Attributes:
        source_file: Path to the source markdown file
        diagram_files: List of paths to generated diagram files
        timestamp: When the diagrams were generated
    """

    source_file: str
    diagram_files: List[str]
    timestamp: str


def find_markdown_files(directory: Path, recursive: bool = True) -> List[Path]:
    """
    Discover markdown files in the specified directory.

    Args:
        directory: The directory to search for markdown files
        recursive: If True, search subdirectories recursively

    Returns:
        List of Path objects pointing to markdown files

    Raises:
        FileNotFoundError: If the directory does not exist
        PermissionError: If the directory cannot be accessed
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    markdown_files = []

    try:
        if recursive:
            # Use rglob for recursive search
            for pattern in ["*.md", "*.markdown"]:
                markdown_files.extend(directory.rglob(pattern))
        else:
            # Use glob for non-recursive search
            for pattern in ["*.md", "*.markdown"]:
                markdown_files.extend(directory.glob(pattern))
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied accessing directory: {directory}"
        ) from e

    # Sort for consistent ordering
    return sorted(set(markdown_files))


def get_markdown_files_from_path(path: Path, recursive: bool = True) -> List[Path]:
    """
    Get markdown files from a path (file or directory).

    Args:
        path: Path to a markdown file or directory containing markdown files
        recursive: If True and path is a directory, search subdirectories recursively

    Returns:
        List of Path objects pointing to markdown files

    Raises:
        FileNotFoundError: If the path does not exist
        ValueError: If the path is a file but not a markdown file
        PermissionError: If the path cannot be accessed
    """
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    if path.is_file():
        # Check if it's a markdown file
        if path.suffix.lower() in [".md", ".markdown"]:
            return [path]
        else:
            raise ValueError(f"File is not a markdown file: {path}")
    elif path.is_dir():
        # Use existing function for directories
        return find_markdown_files(path, recursive=recursive)
    else:
        raise ValueError(f"Path is neither a file nor a directory: {path}")


def create_output_filename(
    source_file: Path, index: int, diagram_type: str, format: str
) -> str:
    """
    Generate a standardized output filename for a diagram.

    Args:
        source_file: The source markdown file
        index: The index of the diagram within the source file
        diagram_type: The type of Mermaid diagram (e.g., 'flowchart', 'sequence')
        format: The output format (e.g., 'png', 'svg')

    Returns:
        Formatted filename string

    Example:
        >>> create_output_filename(Path('architecture.md'), 0, 'flowchart', 'png')
        'architecture_0_flowchart.png'
    """
    source_name = source_file.stem  # Get filename without extension
    return f"{source_name}_{index}_{diagram_type}.{format}"


def get_project_name(source_file: Path, levels_up: int = 2) -> str:
    """
    Extract project name from a source file path by going up N levels.

    Args:
        source_file: Path to the source markdown file
        levels_up: How many directory levels to go up (default: 2)

    Returns:
        Project name string

    Example:
        >>> get_project_name(Path('/Users/name/Projects/MyProject/docs/file.md'), 2)
        'MyProject'
    """
    try:
        # Go up the specified number of levels
        parent = source_file.resolve()
        for _ in range(levels_up):
            parent = parent.parent
        return parent.name
    except Exception:
        # Fallback to immediate parent if we can't go up enough levels
        return source_file.parent.name


def ensure_output_dir(output_dir: Path) -> None:
    """
    Ensure the output directory exists, creating it if necessary.

    Args:
        output_dir: Path to the output directory

    Raises:
        PermissionError: If the directory cannot be created due to permissions
        OSError: If directory creation fails for other reasons
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied creating directory: {output_dir}"
        ) from e
    except OSError as e:
        raise OSError(f"Failed to create directory: {output_dir}") from e


def save_mapping(mappings: List[DiagramMapping], output_dir: Path) -> None:
    """
    Save diagram mappings to a JSON file.

    Args:
        mappings: List of DiagramMapping objects to save
        output_dir: Directory where the mapping file will be saved

    Raises:
        PermissionError: If the mapping file cannot be written
        OSError: If file writing fails
    """
    ensure_output_dir(output_dir)

    mapping_file = output_dir / "diagram_mappings.json"

    # Convert dataclasses to dictionaries
    mappings_data = [asdict(mapping) for mapping in mappings]

    try:
        with mapping_file.open("w", encoding="utf-8") as f:
            json.dump(mappings_data, f, indent=2, ensure_ascii=False)
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied writing mapping file: {mapping_file}"
        ) from e
    except OSError as e:
        raise OSError(f"Failed to write mapping file: {mapping_file}") from e


def load_mapping(output_dir: Path) -> List[DiagramMapping]:
    """
    Load diagram mappings from a JSON file.

    Args:
        output_dir: Directory containing the mapping file

    Returns:
        List of DiagramMapping objects

    Raises:
        FileNotFoundError: If the mapping file does not exist
        json.JSONDecodeError: If the mapping file is invalid JSON
    """
    mapping_file = output_dir / "diagram_mappings.json"

    if not mapping_file.exists():
        raise FileNotFoundError(f"Mapping file not found: {mapping_file}")

    try:
        with mapping_file.open("r", encoding="utf-8") as f:
            mappings_data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in mapping file: {mapping_file}", e.doc, e.pos
        ) from e

    # Convert dictionaries back to dataclasses
    return [DiagramMapping(**data) for data in mappings_data]


def create_linked_markdown(
    source_file: Path, diagram_files: List[str], output_in_source_dir: bool = True
) -> Optional[Path]:
    """
    Create a modified markdown file with mermaid blocks replaced by wiki-style image links.

    Args:
        source_file: Path to the original markdown file
        diagram_files: List of paths to generated diagram files (in order)
        output_in_source_dir: If True, output diagrams to source file directory

    Returns:
        Path to the created linked markdown file, or None if creation failed

    Raises:
        FileNotFoundError: If source file doesn't exist
        PermissionError: If files cannot be read/written
    """
    if not source_file.exists():
        raise FileNotFoundError(f"Source file not found: {source_file}")

    # Read the original content
    try:
        content = source_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            e.encoding,
            e.object,
            e.start,
            e.end,
            f"Unable to decode file {source_file} as UTF-8",
        )

    # Find and replace mermaid blocks with image links
    lines = content.split("\n")
    result_lines = []
    diagram_index = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for start of a mermaid code block
        import re

        match = re.match(r"^(`{3,}|~{3,})\s*mermaid\s*$", line, re.IGNORECASE)

        if match and diagram_index < len(diagram_files):
            fence_chars = match.group(1)
            fence_pattern = (
                re.escape(fence_chars[0]) + "{" + str(len(fence_chars)) + ",}"
            )

            # Skip until we find the closing fence
            i += 1
            while i < len(lines):
                if re.match(f"^{fence_pattern}\\s*$", lines[i]):
                    break
                i += 1

            # Replace the entire block with image link
            diagram_path = Path(diagram_files[diagram_index])

            if output_in_source_dir:
                # Use just the filename for wiki-style link in same directory
                image_link = f"![[{diagram_path.name}]]"
            else:
                # Use relative path if in different directory
                try:
                    rel_path = diagram_path.relative_to(source_file.parent)
                    image_link = f"![[{rel_path}]]"
                except ValueError:
                    # If can't make relative, use absolute
                    image_link = f"![[{diagram_path}]]"

            result_lines.append(image_link)
            diagram_index += 1
        else:
            result_lines.append(line)

        i += 1

    # Create output filename
    output_file = source_file.parent / f"{source_file.stem}_linked{source_file.suffix}"

    # Write the modified content
    try:
        with output_file.open("w", encoding="utf-8") as f:
            f.write("\n".join(result_lines))
        return output_file
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied writing linked markdown: {output_file}"
        ) from e
    except OSError as e:
        raise OSError(f"Failed to write linked markdown: {output_file}") from e


def generate_index_html(mappings: List[DiagramMapping], output_dir: Path) -> None:
    """
    Generate an index.html file showing all diagrams with source links.

    Args:
        mappings: List of DiagramMapping objects
        output_dir: Directory where the index.html will be saved

    Raises:
        PermissionError: If the HTML file cannot be written
        OSError: If file writing fails
    """
    ensure_output_dir(output_dir)

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mermaid Diagram Index</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007acc;
            padding-bottom: 10px;
        }
        .source-section {
            background: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .source-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .source-file {
            font-size: 1.2em;
            font-weight: bold;
            color: #007acc;
        }
        .timestamp {
            color: #666;
            font-size: 0.9em;
        }
        .diagrams-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }
        .diagram-card {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background: #fafafa;
        }
        .diagram-card img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }
        .diagram-filename {
            margin-top: 8px;
            font-size: 0.9em;
            color: #555;
            word-break: break-all;
        }
        .no-diagrams {
            color: #999;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>Mermaid Diagram Index</h1>
"""

    if not mappings:
        html_content += '    <p class="no-diagrams">No diagrams generated yet.</p>\n'
    else:
        for mapping in mappings:
            source_path = Path(mapping.source_file)
            timestamp = mapping.timestamp

            html_content += f"""
    <div class="source-section">
        <div class="source-header">
            <div class="source-file">{source_path.name}</div>
            <div class="timestamp">{timestamp}</div>
        </div>
        <div><strong>Source:</strong> <code>{mapping.source_file}</code></div>
"""

            if mapping.diagram_files:
                html_content += '        <div class="diagrams-grid">\n'
                for diagram_file in mapping.diagram_files:
                    diagram_path = Path(diagram_file)
                    # Use relative path for HTML links
                    relative_path = diagram_path.name

                    html_content += f"""
            <div class="diagram-card">
                <img src="{relative_path}" alt="{relative_path}">
                <div class="diagram-filename">{relative_path}</div>
            </div>
"""
                html_content += "        </div>\n"
            else:
                html_content += (
                    '        <p class="no-diagrams">No diagrams found.</p>\n'
                )

            html_content += "    </div>\n"

    html_content += """
</body>
</html>
"""

    index_file = output_dir / "index.html"

    try:
        with index_file.open("w", encoding="utf-8") as f:
            f.write(html_content)
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied writing index file: {index_file}"
        ) from e
    except OSError as e:
        raise OSError(f"Failed to write index file: {index_file}") from e

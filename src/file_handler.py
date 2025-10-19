"""
File handling module for MermaidVisualizer.

This module provides functions for discovering markdown files, managing output directories,
creating output filenames, and tracking diagram mappings.
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Import MermaidDiagram for type hints
from .extractor import MermaidDiagram


# Diagram type prefix mappings for intelligent filename generation
DIAGRAM_TYPE_PREFIXES = {
    "sequenceDiagram": "seq",
    "flowchart": "graph",
    "graph": "graph",
    "classDiagram": "class",
    "stateDiagram": "state",
    "erDiagram": "er",
    "gantt": "gantt",
    "pie": "pie",
    "gitGraph": "git",
    "journey": "journey",
    "mindmap": "mind",
    "timeline": "time",
    "quadrantChart": "quad",
    "requirementDiagram": "req",
    "c4Diagram": "c4",
    "unknown": "diagram",
}


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


def sanitize_filename(text: str, max_length: int = 50) -> str:
    """
    Convert a string into a safe, filesystem-compatible filename.

    Args:
        text: The text to sanitize
        max_length: Maximum length of the resulting filename (default: 50)

    Returns:
        A sanitized filename string with safe characters only

    Example:
        >>> sanitize_filename("User Authentication Flow")
        'user_authentication_flow'
        >>> sanitize_filename("Class: User/Admin (v2.0)")
        'class_user_admin_v2_0'
        >>> sanitize_filename("")
        'untitled'
    """
    if not text or not text.strip():
        return "untitled"

    # Convert to lowercase
    sanitized = text.lower()

    # Replace spaces with underscores
    sanitized = sanitized.replace(" ", "_")

    # Remove or replace special characters (keep only alphanumeric, underscores, hyphens)
    # Allow unicode letters and digits
    sanitized = re.sub(r"[^\w\-]", "_", sanitized)

    # Replace multiple consecutive underscores/hyphens with a single underscore
    sanitized = re.sub(r"[_\-]+", "_", sanitized)

    # Remove leading/trailing underscores or hyphens
    sanitized = sanitized.strip("_-")

    # If still empty after sanitization, use fallback
    if not sanitized:
        return "untitled"

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip("_-")

    return sanitized


def generate_descriptive_filename(
    diagram: MermaidDiagram, format: str = "png", use_prefixes: bool = True
) -> str:
    """
    Generate an intelligent, descriptive filename for a diagram based on its metadata.

    The function prioritizes diagram metadata in the following order:
    1. preceding_header (markdown header before the diagram)
    2. diagram_title (title extracted from diagram content)
    3. Fallback to diagram type prefix + index

    Args:
        diagram: MermaidDiagram object containing metadata
        format: Output file format extension (default: "png")
        use_prefixes: If True, prepend diagram type prefix to all filenames (default: True)

    Returns:
        A descriptive filename string with the specified format extension

    Example:
        >>> diagram = MermaidDiagram(
        ...     content="flowchart TD\\n    A[Start]",
        ...     source_file=Path("doc.md"),
        ...     start_line=1,
        ...     end_line=5,
        ...     diagram_type="flowchart",
        ...     index=0,
        ...     preceding_header="User Authentication",
        ...     diagram_title=None
        ... )
        >>> generate_descriptive_filename(diagram, "png", True)
        'graph_user_authentication.png'
    """
    # Get the diagram type prefix
    diagram_prefix = DIAGRAM_TYPE_PREFIXES.get(diagram.diagram_type, "diagram")

    # Determine base name from metadata (in priority order)
    base_name = None

    if diagram.preceding_header:
        # Use the preceding header as the primary source
        base_name = sanitize_filename(diagram.preceding_header)
    elif diagram.diagram_title:
        # Fall back to diagram title
        base_name = sanitize_filename(diagram.diagram_title)

    # If we have a base name from metadata
    if base_name and base_name != "untitled":
        if use_prefixes:
            filename = f"{diagram_prefix}_{base_name}"
        else:
            filename = base_name
    else:
        # Fallback to type + index
        filename = f"{diagram_prefix}_{diagram.index}"

    # Append format extension
    return f"{filename}.{format}"


def resolve_filename_conflicts(filenames: List[str]) -> List[str]:
    """
    Resolve duplicate filenames by appending numeric suffixes.

    Detects duplicate filenames in the list and appends _2, _3, etc.
    to make them unique. The suffix is added before the file extension.

    Args:
        filenames: List of filenames (potentially with duplicates)

    Returns:
        List of unique filenames in the same order, with conflicts resolved

    Example:
        >>> resolve_filename_conflicts([
        ...     "seq_auth.png",
        ...     "seq_auth.png",
        ...     "graph_flow.svg",
        ...     "seq_auth.png"
        ... ])
        ['seq_auth.png', 'seq_auth_2.png', 'graph_flow.svg', 'seq_auth_3.png']
    """
    if not filenames:
        return []

    # Track how many times we've seen each base filename
    seen_counts = {}
    result = []

    for filename in filenames:
        # Split filename into base and extension
        path = Path(filename)
        base = path.stem  # filename without extension
        ext = path.suffix  # extension with dot

        # Track occurrences
        if filename not in seen_counts:
            seen_counts[filename] = 0

        seen_counts[filename] += 1
        count = seen_counts[filename]

        if count == 1:
            # First occurrence - use original name
            result.append(filename)
        else:
            # Duplicate - append numeric suffix before extension
            new_filename = f"{base}_{count}{ext}"
            result.append(new_filename)

    return result


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
    source_file: Path,
    index: int,
    diagram_type: str,
    format: str,
    use_intelligent_naming: bool = False,
    diagram: Optional[MermaidDiagram] = None,
) -> str:
    """
    Generate a standardized output filename for a diagram.

    This function supports both legacy filename generation (source_index_type.format)
    and new intelligent naming based on diagram metadata.

    Args:
        source_file: The source markdown file
        index: The index of the diagram within the source file
        diagram_type: The type of Mermaid diagram (e.g., 'flowchart', 'sequence')
        format: The output format (e.g., 'png', 'svg')
        use_intelligent_naming: If True, use metadata-based naming (requires diagram parameter)
        diagram: MermaidDiagram object (required if use_intelligent_naming is True)

    Returns:
        Formatted filename string

    Example:
        >>> # Legacy naming
        >>> create_output_filename(Path('architecture.md'), 0, 'flowchart', 'png')
        'architecture_0_flowchart.png'
        >>> # Intelligent naming
        >>> diagram = MermaidDiagram(...)  # with preceding_header="User Auth"
        >>> create_output_filename(
        ...     Path('architecture.md'), 0, 'flowchart', 'png',
        ...     use_intelligent_naming=True, diagram=diagram
        ... )
        'graph_user_auth.png'

    Note:
        When use_intelligent_naming=False (default), this function maintains
        backward compatibility with existing code. For new intelligent naming,
        consider using generate_descriptive_filename() directly.
    """
    if use_intelligent_naming:
        if diagram is None:
            raise ValueError(
                "diagram parameter is required when use_intelligent_naming=True"
            )
        return generate_descriptive_filename(diagram, format=format, use_prefixes=True)

    # Legacy naming: source_index_type.format
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
    Generate an interactive index.html file with lightbox gallery for viewing diagrams.

    Creates a beautiful, mobile-friendly gallery with zoom capabilities using GLightbox.
    Features include click-to-zoom, touch gestures, keyboard navigation, and responsive design.

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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    <meta name="description" content="Interactive gallery of Mermaid diagrams with zoom and mobile support">
    <title>Mermaid Diagram Gallery</title>

    <!-- GLightbox CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/glightbox@3.2.0/dist/css/glightbox.min.css">

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            text-align: center;
            padding: 40px 20px;
            color: white;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 2.5em;
            margin: 0 0 10px 0;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
            font-weight: 300;
        }

        .source-section {
            background: white;
            margin: 30px 0;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .source-section:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.25);
        }

        .source-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
            flex-wrap: wrap;
            gap: 10px;
        }

        .source-file {
            font-size: 1.4em;
            font-weight: 600;
            color: #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .source-file::before {
            content: "📄";
            font-size: 1.2em;
        }

        .timestamp {
            color: #888;
            font-size: 0.9em;
            font-weight: 400;
        }

        .source-path {
            margin-bottom: 20px;
            padding: 12px 16px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 4px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            color: #555;
            overflow-x: auto;
        }

        .diagrams-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 25px;
            margin-top: 20px;
        }

        .diagram-card {
            background: #fafafa;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }

        .diagram-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }

        .diagram-card::after {
            content: "🔍";
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255,255,255,0.95);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }

        .diagram-card:hover::after {
            opacity: 1;
        }

        .diagram-image-wrapper {
            background: white;
            padding: 15px;
            min-height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .diagram-card img {
            max-width: 100%;
            height: auto;
            display: block;
            border-radius: 4px;
        }

        .diagram-filename {
            padding: 15px;
            font-size: 0.85em;
            color: #666;
            background: white;
            border-top: 1px solid #eee;
            font-weight: 500;
            word-break: break-word;
        }

        .no-diagrams {
            color: #999;
            font-style: italic;
            text-align: center;
            padding: 40px;
            font-size: 1.1em;
        }

        .stats {
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 15px 25px;
            border-radius: 50px;
            display: inline-block;
            margin-top: 15px;
            font-size: 0.95em;
            backdrop-filter: blur(10px);
        }

        footer {
            text-align: center;
            padding: 40px 20px 20px;
            color: rgba(255,255,255,0.8);
            font-size: 0.9em;
        }

        /* Mobile optimizations */
        @media (max-width: 768px) {
            h1 {
                font-size: 2em;
            }

            .subtitle {
                font-size: 1em;
            }

            .source-section {
                padding: 20px;
                margin: 20px 0;
            }

            .source-header {
                flex-direction: column;
                align-items: flex-start;
            }

            .source-file {
                font-size: 1.2em;
            }

            .diagrams-grid {
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 15px;
            }

            .container {
                padding: 10px;
            }
        }

        /* Small mobile devices */
        @media (max-width: 480px) {
            .diagrams-grid {
                grid-template-columns: 1fr;
            }

            header {
                padding: 30px 15px;
            }
        }

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .diagram-image-wrapper {
                background: #2a2a2a;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Mermaid Diagram Gallery</h1>
            <div class="subtitle">Interactive diagrams with zoom and navigation</div>
"""

    # Count total diagrams
    total_diagrams = sum(len(mapping.diagram_files) for mapping in mappings)
    total_sources = len(mappings)

    if total_diagrams > 0:
        html_content += f"""            <div class="stats">
                📊 {total_diagrams} diagram{'' if total_diagrams == 1 else 's'} from {total_sources} source{'' if total_sources == 1 else 's'}
            </div>
"""

    html_content += """        </header>
"""

    if not mappings:
        html_content += '        <div class="no-diagrams">No diagrams generated yet. Run the generator to create some!</div>\n'
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
            <div class="source-path">{mapping.source_file}</div>
"""

            if mapping.diagram_files:
                html_content += '            <div class="diagrams-grid">\n'
                for idx, diagram_file in enumerate(mapping.diagram_files):
                    diagram_path = Path(diagram_file)
                    relative_path = diagram_path.name

                    # Create a description for the lightbox
                    description = f"{source_path.name} - Diagram {idx + 1}"

                    html_content += f"""                <a href="{relative_path}" class="glightbox diagram-card"
                   data-gallery="gallery-{source_path.stem}"
                   data-title="{relative_path}"
                   data-description="{description}">
                    <div class="diagram-image-wrapper">
                        <img src="{relative_path}" alt="{relative_path}" loading="lazy">
                    </div>
                    <div class="diagram-filename">{relative_path}</div>
                </a>
"""
                html_content += "            </div>\n"
            else:
                html_content += (
                    '            <div class="no-diagrams">No diagrams found in this file.</div>\n'
                )

            html_content += "        </div>\n"

    html_content += """
        <footer>
            <p>Generated by MermaidVisualizer • Click any diagram to zoom • Use arrow keys to navigate</p>
            <p style="font-size: 0.85em; margin-top: 10px;">💡 Tip: Pinch to zoom on mobile devices</p>
        </footer>
    </div>

    <!-- GLightbox JS -->
    <script src="https://cdn.jsdelivr.net/npm/glightbox@3.2.0/dist/js/glightbox.min.js"></script>

    <script>
        // Initialize GLightbox with custom settings
        const lightbox = GLightbox({
            touchNavigation: true,
            loop: true,
            autoplayVideos: false,
            zoomable: true,
            draggable: true,
            closeButton: true,
            slideEffect: 'slide',
            moreLength: 0,
            skin: 'modern',
            svg: {
                // Enable SVG zoom
                inline: true,
            }
        });

        // Add keyboard shortcuts info
        console.log('Keyboard shortcuts:');
        console.log('  - Arrow keys: Navigate between diagrams');
        console.log('  - ESC: Close lightbox');
        console.log('  - Mouse wheel: Zoom in/out');

        // Log initialization
        console.log('Gallery initialized with ' + document.querySelectorAll('.glightbox').length + ' diagrams');
    </script>
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

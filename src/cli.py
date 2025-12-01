"""
Command-line interface for MermaidVisualizer.

This module provides a CLI using Click framework for extracting Mermaid diagrams
from markdown files and generating visualizations. Uses Rich for beautiful
terminal output with progress bars, tables, and styled text.
"""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# Import core modules
from . import extractor
from . import file_handler
from . import generator

# Optional gist handler (requires requests)
try:
    from . import gist_handler

    GIST_AVAILABLE = True
except ImportError:
    gist_handler = None
    GIST_AVAILABLE = False

# Custom theme for consistent styling
custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "highlight": "bold cyan",
        "muted": "dim",
        "header": "bold magenta",
    }
)

# Global console instance with custom theme
console = Console(theme=custom_theme)


@dataclass
class ProcessingResult:
    """Result of processing files."""

    files_processed: int = 0
    diagrams_generated: int = 0
    diagrams_failed: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging with Rich handler for beautiful output.

    Args:
        verbose: If True, set logging level to DEBUG; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                tracebacks_show_locals=verbose,
                show_time=verbose,
                show_path=verbose,
            )
        ],
    )


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """Print a styled header panel."""
    content = Text()
    content.append(title, style="bold cyan")
    if subtitle:
        content.append(f"\n{subtitle}", style="dim")

    console.print(
        Panel(
            content,
            border_style="cyan",
            padding=(1, 2),
        )
    )


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[success]{message}[/success]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[error]{message}[/error]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[warning]{message}[/warning]")


def print_info(label: str, value: str) -> None:
    """Print an info line with label and value."""
    console.print(f"[info]{label}:[/info] {value}")


def validate_input_path(ctx, param, value):
    """Validate that input path (file or directory) exists, or is a valid gist URL."""
    # Check if it's a gist URL - if so, skip path validation
    if GIST_AVAILABLE and gist_handler.is_gist_url(str(value)):
        return value  # Return the URL string, we'll handle it later

    # Otherwise, validate as a path
    path = Path(value).resolve()
    if not path.exists():
        raise click.BadParameter(f"Path does not exist: {value}")
    if path.is_file() and path.suffix.lower() not in [".md", ".markdown"]:
        raise click.BadParameter(
            f"File must be a markdown file (.md or .markdown): {value}"
        )
    if not path.is_file() and not path.is_dir():
        raise click.BadParameter(f"Path must be a file or directory: {value}")
    return path


def validate_output_format(ctx, param, value):
    """Validate output format."""
    valid_formats = ["png", "svg"]
    if value.lower() not in valid_formats:
        raise click.BadParameter(
            f"Invalid format '{value}'. Must be one of: {', '.join(valid_formats)}"
        )
    return value.lower()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.1.0")
def cli(ctx):
    """
    \b
    MermaidVisualizer - Automated Mermaid Diagram Extraction & Generation

    Extract Mermaid diagrams from markdown files and generate visual diagrams
    in PNG or SVG format. Supports recursive directory scanning, multiple
    diagram types, and automated wiki-style markdown linking.

    \b
    QUICK START:
      $ mermaid generate                    # Generate from current directory
      $ mermaid generate -i ./docs          # Generate from a directory
      $ mermaid generate -i ./doc.md        # Generate from a single file
      $ mermaid scan                        # Preview diagrams (dry run)
      $ mermaid clean                       # Remove generated diagrams

    \b
    EXAMPLES:
      # Generate from a single file
      $ mermaid generate -i ./docs/architecture.md

      # Generate high-resolution PNG diagrams from a directory
      $ mermaid generate -i ./docs -o ./diagrams -s 3 -w 2400

      # Generate SVG diagrams with linked markdown files
      $ mermaid generate -f svg -l

      # Scan a file or directory without generating
      $ mermaid scan -i ./docs --recursive

      # Clean up generated files
      $ mermaid clean -o ./diagrams --yes

    \b
    SUPPORTED DIAGRAM TYPES:
      Flowcharts (graph, flowchart), Sequence Diagrams, Class Diagrams,
      State Diagrams, Entity Relationship Diagrams, Gantt Charts,
      Pie Charts, User Journey Diagrams, Git Graphs, Mindmaps, Timelines

    Use 'mermaid COMMAND --help' for detailed information on each command.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option(
    "--input-dir",
    "-i",
    default=".",
    callback=validate_input_path,
    help="Input file or directory to process (default: current directory)",
    show_default=True,
)
@click.option(
    "--output-dir",
    "-o",
    default="./diagrams",
    type=click.Path(),
    help="Output directory for generated diagrams",
    show_default=True,
)
@click.option(
    "--format",
    "-f",
    default="png",
    callback=validate_output_format,
    help="Output format: 'png' or 'svg'",
    show_default=True,
)
@click.option(
    "--scale",
    "-s",
    default=3,
    type=int,
    help="Scale factor for PNG output (higher = better quality, larger file)",
    show_default=True,
)
@click.option(
    "--width",
    "-w",
    default=2400,
    type=int,
    help="Width of output image in pixels",
    show_default=True,
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Recursively scan subdirectories for markdown files",
    show_default=True,
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging with detailed progress information",
)
@click.option(
    "-l",
    "--linked-file",
    is_flag=True,
    help="Create modified markdown files with wiki-style image links [[image.png]]",
    show_default=True,
)
@click.option(
    "--intelligent-names/--simple-names",
    default=True,
    help="Use intelligent, descriptive filenames based on diagram context (headers, titles)",
    show_default=True,
)
@click.option(
    "--gist",
    "-g",
    type=str,
    default=None,
    help="GitHub Gist URL to fetch markdown files from",
)
@click.option(
    "--github-token",
    type=str,
    default=None,
    envvar="GITHUB_TOKEN",
    help="GitHub personal access token for private gists and higher rate limits (can also set GITHUB_TOKEN env var)",
)
@click.option(
    "--api",
    is_flag=True,
    help="Use mermaid.ink API for rendering (no Node.js/Chrome needed - slim install)",
)
def generate(
    input_dir: Path,
    output_dir: str,
    format: str,
    scale: int,
    width: int,
    recursive: bool,
    verbose: bool,
    linked_file: bool,
    intelligent_names: bool,
    gist: Optional[str],
    github_token: Optional[str],
    api: bool,
) -> None:
    """
    Extract Mermaid diagrams from markdown files and generate visual diagrams.

    \b
    This command processes either a single markdown file, a directory
    containing markdown files, or a GitHub Gist with markdown files.
    It extracts ```mermaid code blocks and generates visual diagrams
    using the Mermaid CLI tool.

    \b
    INPUT SOURCES:
      Local files/directories:
        - Single markdown file: -i ./docs/architecture.md
        - Directory: -i ./docs
        - Current directory (default): mermaid generate

      GitHub Gists (public or private):
        - Auto-detect: -i https://gist.github.com/user/abc123
        - Explicit flag: --gist https://gist.github.com/user/abc123
        - Private gists: Add --github-token or set GITHUB_TOKEN env var

    \b
    OUTPUT STRUCTURE:
      When -l/--linked-file is used:
        - Diagrams are saved next to source markdown files
        - Creates *_linked.md files with embedded image references

      When not used (default):
        - Diagrams are saved to --output-dir in project subdirectories
        - Generates index.html for easy browsing

    \b
    FILENAME GENERATION:
      --intelligent-names (default):
        - Uses markdown headers and diagram titles for descriptive names
        - Examples: graph_user_authentication.png, seq_login_flow.png
        - Automatically resolves duplicate names with numeric suffixes

      --simple-names:
        - Uses traditional source_index_type.format naming
        - Example: architecture_0_flowchart.png

    \b
    EXAMPLES:
      # Basic usage (current directory)
      $ mermaid generate

      # Process a single markdown file
      $ mermaid generate -i ./docs/architecture.md

      # Process an entire directory
      $ mermaid generate -i ./docs

      # Fetch from a public GitHub Gist (auto-detect)
      $ mermaid generate -i https://gist.github.com/user/abc123

      # Fetch from a Gist with explicit flag
      $ mermaid generate --gist https://gist.github.com/user/abc123

      # Fetch from a private Gist
      $ mermaid generate -g https://gist.github.com/user/abc123 --github-token ghp_xxx
      $ export GITHUB_TOKEN=ghp_xxx && mermaid generate -i https://gist.github.com/user/abc123

      # Use simple filenames instead of intelligent names
      $ mermaid generate --simple-names

      # High-resolution PNG with custom scale
      $ mermaid generate -s 5 -w 3200

      # Generate SVG diagrams with intelligent naming
      $ mermaid generate -f svg --intelligent-names

      # Non-recursive directory scan
      $ mermaid generate --no-recursive

      # Create linked markdown files
      $ mermaid generate -l
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    # Enable API mode if requested
    if api:
        generator.set_api_mode(True)

    output_path = Path(output_dir).resolve()

    # Print header
    print_header(
        "MermaidVisualizer - Generate Diagrams",
        "Extracting and rendering Mermaid diagrams from markdown",
    )

    # Show mode
    console.print()
    if api:
        print_info("Mode", "API rendering (mermaid.ink)")
    else:
        print_info("Mode", "Local rendering (mermaid-cli)")

    try:
        # Ensure output directory exists
        file_handler.ensure_output_dir(output_path)
        logger.info(f"Output directory: {output_path}")

        # Handle GitHub Gist input
        gist_url = None

        # Check if --gist flag was used
        if gist:
            if not GIST_AVAILABLE:
                print_error("Gist support requires 'requests' package.")
                console.print("Install with: [cyan]pip install mermaid-visualizer[api][/cyan]")
                sys.exit(1)
            gist_url = gist
            logger.info(f"Using gist from --gist flag: {gist_url}")
        # Auto-detect if input_dir string looks like a gist URL
        elif GIST_AVAILABLE and gist_handler.is_gist_url(str(input_dir)):
            gist_url = str(input_dir)
            logger.info(f"Auto-detected gist URL: {gist_url}")

        # If we have a gist URL, fetch it
        if gist_url:
            try:
                console.print()
                print_info("Fetching from GitHub Gist", gist_url)

                with console.status("[cyan]Fetching gist files...[/cyan]", spinner="dots"):
                    md_files = gist_handler.fetch_gist_files(gist_url, github_token)

                if not md_files:
                    print_warning("No markdown files found in gist.")
                    return

                print_success(f"Fetched {len(md_files)} markdown file(s) from gist")

            except ValueError as e:
                print_error(f"Invalid gist: {e}")
                sys.exit(1)
            except ConnectionError as e:
                print_error(f"Connection error: {e}")
                sys.exit(1)
            except PermissionError as e:
                print_error(f"Permission denied: {e}")
                console.print("[muted]Tip: Use --github-token for private gists[/muted]")
                sys.exit(1)
        else:
            # Original logic: find markdown files from input_dir
            input_type = "file" if input_dir.is_file() else "directory"
            console.print()
            print_info("Input", f"{input_dir} ({input_type})")
            if input_dir.is_dir():
                print_info("Recursive", "Yes" if recursive else "No")

            md_files = file_handler.get_markdown_files_from_path(
                input_dir, recursive=recursive
            )

        if not md_files:
            print_warning("No markdown files found.")
            return

        print_info("Found", f"{len(md_files)} markdown file(s)")
        console.print()

        # Process files and generate diagrams
        result = ProcessingResult()
        mappings = []

        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="cyan", finished_style="green"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            expand=True,
        ) as progress:
            task = progress.add_task("[cyan]Processing files...", total=len(md_files))

            for md_file in md_files:
                try:
                    # Update progress description
                    progress.update(task, description=f"[cyan]Processing {md_file.name}...")

                    # Extract mermaid diagrams
                    diagrams = extractor.extract_mermaid_blocks(md_file)

                    if not diagrams:
                        logger.debug(f"No diagrams in {md_file.name}")
                        result.files_processed += 1
                        progress.advance(task)
                        continue

                    # Generate each diagram
                    diagram_files = []

                    # Determine output directory based on linked_file option
                    if linked_file:
                        # Output diagrams to the source file's directory
                        diagram_output_dir = md_file.parent
                    else:
                        # Get project name and create project-specific subdirectory
                        project_name = file_handler.get_project_name(
                            md_file, levels_up=3
                        )
                        diagram_output_dir = output_path / project_name

                    file_handler.ensure_output_dir(diagram_output_dir)

                    # Generate all filenames first, then resolve conflicts
                    if intelligent_names:
                        # Use intelligent naming with context from headers/titles
                        output_filenames = [
                            file_handler.create_output_filename(
                                diagram.source_file,
                                diagram.index,
                                diagram.diagram_type,
                                format,
                                use_intelligent_naming=True,
                                diagram=diagram,
                            )
                            for diagram in diagrams
                        ]
                        # Resolve any duplicate filenames
                        output_filenames = file_handler.resolve_filename_conflicts(
                            output_filenames
                        )
                    else:
                        # Use simple naming (source_index_type.format)
                        # No conflict resolution needed as index makes them unique
                        output_filenames = [
                            file_handler.create_output_filename(
                                diagram.source_file,
                                diagram.index,
                                diagram.diagram_type,
                                format,
                                use_intelligent_naming=False,
                            )
                            for diagram in diagrams
                        ]

                    # Generate diagrams with resolved filenames
                    for diagram, output_filename in zip(diagrams, output_filenames):
                        output_file = diagram_output_dir / output_filename

                        success = generator.generate(
                            diagram.content, output_file, format, scale, width
                        )

                        if success:
                            result.diagrams_generated += 1
                            diagram_files.append(str(output_file))
                            logger.debug(f"Generated: {output_filename}")
                        else:
                            result.diagrams_failed += 1
                            error_msg = f"Failed to generate diagram from {md_file.name} (index {diagram.index})"
                            result.errors.append(error_msg)
                            logger.error(error_msg)

                    # Save mapping if any diagrams were generated
                    if diagram_files:
                        mapping = file_handler.DiagramMapping(
                            source_file=str(md_file),
                            diagram_files=diagram_files,
                            timestamp=str(__import__("datetime").datetime.now()),
                        )
                        mappings.append(mapping)

                        # Create linked markdown if requested
                        if linked_file:
                            try:
                                linked_md = file_handler.create_linked_markdown(
                                    md_file, diagram_files, output_in_source_dir=True
                                )
                                if linked_md:
                                    logger.debug(
                                        f"Created linked markdown: {linked_md.name}"
                                    )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to create linked markdown for {md_file.name}: {str(e)}"
                                )

                    result.files_processed += 1

                except Exception as e:
                    result.diagrams_failed += 1
                    error_msg = f"Error processing {md_file.name}: {str(e)}"
                    result.errors.append(error_msg)
                    logger.exception(error_msg)

                progress.advance(task)

        # Save mappings and generate index per project
        if mappings:
            # Group mappings by project
            projects_map = {}
            for mapping in mappings:
                src_path = Path(mapping.source_file)
                proj_name = file_handler.get_project_name(src_path, levels_up=3)
                if proj_name not in projects_map:
                    projects_map[proj_name] = []
                projects_map[proj_name].append(mapping)

            # Save per project
            for proj_name, proj_mappings in projects_map.items():
                proj_dir = output_path / proj_name
                file_handler.save_mapping(proj_mappings, proj_dir)
                file_handler.generate_index_html(proj_mappings, proj_dir)
                logger.info(f"Generated index.html for {proj_name}")

        # Display summary
        console.print()
        console.print(Rule("[bold cyan]Summary[/bold cyan]", style="cyan"))
        console.print()

        # Create summary table
        summary_table = Table(show_header=False, box=None, padding=(0, 2))
        summary_table.add_column("Metric", style="dim")
        summary_table.add_column("Value")

        summary_table.add_row("Files processed", str(result.files_processed))
        summary_table.add_row(
            "Diagrams generated",
            f"[green]{result.diagrams_generated}[/green]",
        )
        if result.diagrams_failed > 0:
            summary_table.add_row(
                "Diagrams failed",
                f"[red]{result.diagrams_failed}[/red]",
            )

        console.print(summary_table)

        if result.errors and verbose:
            console.print()
            console.print("[bold red]Errors:[/bold red]")
            for error in result.errors:
                console.print(f"  [red]>[/red] {error}")

        if result.diagrams_generated > 0:
            console.print()
            print_success("Generation complete!")
            if not linked_file:
                console.print(f"[muted]View diagrams at: {output_path}[/muted]")

        if result.diagrams_failed > 0:
            sys.exit(1)

    except Exception as e:
        logger.exception("Error during generation")
        print_error(str(e))
        sys.exit(1)


@cli.command()
@click.option(
    "--input-dir",
    "-i",
    default=".",
    callback=validate_input_path,
    help="Input file or directory to scan for Mermaid diagrams",
    show_default=True,
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Recursively scan subdirectories for markdown files",
    show_default=True,
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging with detailed information",
)
def scan(
    input_dir: Path,
    recursive: bool,
    verbose: bool,
) -> None:
    """
    Scan for Mermaid diagrams without generating files (dry run).

    \b
    This command performs a dry run, scanning a single markdown file or
    directory for Mermaid diagrams and displaying what would be generated
    without actually creating any diagram files. Useful for previewing
    results before running 'generate'.

    \b
    OUTPUT:
      Displays a table showing:
        - Source markdown file name
        - Diagram type (flowchart, sequence, etc.)
        - Line range in the source file

    \b
    EXAMPLES:
      # Scan current directory
      $ mermaid scan

      # Scan a single file
      $ mermaid scan -i ./docs/architecture.md

      # Scan a specific directory
      $ mermaid scan -i ./docs

      # Scan directory without recursion
      $ mermaid scan --no-recursive

      # Verbose output with detailed logging
      $ mermaid scan -v
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    # Print header
    print_header(
        "MermaidVisualizer - Scan Diagrams",
        "Preview diagrams without generating files",
    )

    try:
        # Find markdown files
        input_type = "file" if input_dir.is_file() else "directory"
        console.print()
        print_info("Input", f"{input_dir} ({input_type})")
        if input_dir.is_dir():
            print_info("Recursive", "Yes" if recursive else "No")
        console.print()

        md_files = file_handler.get_markdown_files_from_path(
            input_dir, recursive=recursive
        )

        if not md_files:
            print_warning("No markdown files found.")
            return

        # Collect all diagrams with progress
        all_diagrams = []

        with console.status("[cyan]Scanning files...[/cyan]", spinner="dots") as status:
            for md_file in md_files:
                status.update(f"[cyan]Scanning {md_file.name}...[/cyan]")
                try:
                    diagrams = extractor.extract_mermaid_blocks(md_file)
                    all_diagrams.extend(diagrams)
                except Exception as e:
                    logger.error(f"Error scanning {md_file.name}: {str(e)}")

        total_diagrams = len(all_diagrams)

        if total_diagrams > 0:
            # Create rich table
            table = Table(
                title="Mermaid Diagrams Found",
                title_style="bold cyan",
                header_style="bold",
                border_style="cyan",
                show_lines=True,
            )
            table.add_column("#", style="dim", justify="right", width=4)
            table.add_column("Source File", style="cyan")
            table.add_column("Diagram Type", style="green")
            table.add_column("Lines", style="yellow", justify="center")
            table.add_column("Context", style="dim", max_width=30)

            for idx, diagram in enumerate(all_diagrams, 1):
                # Get context (header or title if available)
                context = diagram.preceding_header or diagram.diagram_title or "-"
                if len(context) > 30:
                    context = context[:27] + "..."

                table.add_row(
                    str(idx),
                    diagram.source_file.name,
                    diagram.diagram_type,
                    f"{diagram.start_line}-{diagram.end_line}",
                    context,
                )

            console.print(table)
            console.print()

            # Summary
            summary_text = Text()
            summary_text.append("Total: ", style="bold")
            summary_text.append(f"{total_diagrams}", style="bold cyan")
            summary_text.append(" diagram(s) in ", style="bold")
            summary_text.append(f"{len(md_files)}", style="bold cyan")
            summary_text.append(" file(s)", style="bold")

            console.print(Panel(summary_text, border_style="cyan"))
        else:
            print_warning("No Mermaid diagrams found.")

    except Exception as e:
        logger.exception("Error during scan")
        print_error(str(e))
        sys.exit(1)


@cli.command()
@click.option(
    "--output-dir",
    "-o",
    default="./diagrams",
    type=click.Path(),
    help="Output directory to clean",
    show_default=True,
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt and delete immediately",
)
def clean(output_dir: str, yes: bool) -> None:
    """
    Remove all generated diagrams from the output directory.

    \b
    WARNING: This command will delete all files in the specified output
    directory. By default, you will be prompted for confirmation before
    deletion. Use --yes to skip the confirmation.

    \b
    SAFETY:
      - Only deletes files, not subdirectories
      - Prompts for confirmation unless --yes is used
      - Shows count of files before deletion
      - Safe to run if directory doesn't exist

    \b
    EXAMPLES:
      # Clean default output directory (with confirmation)
      $ mermaid clean

      # Clean specific directory
      $ mermaid clean -o ./my-diagrams

      # Clean without confirmation prompt
      $ mermaid clean --yes

      # Clean and skip prompt
      $ mermaid clean -o ./diagrams -y
    """
    output_path = Path(output_dir).resolve()

    # Print header
    print_header(
        "MermaidVisualizer - Clean Diagrams",
        "Remove generated diagram files",
    )

    if not output_path.exists():
        console.print()
        print_warning(f"Directory does not exist: {output_path}")
        return

    # Count files
    files = list(output_path.glob("*"))
    file_count = len([f for f in files if f.is_file()])

    if file_count == 0:
        console.print()
        print_warning(f"No files to clean in: {output_path}")
        return

    console.print()
    console.print(f"[warning]This will delete {file_count} file(s) from:[/warning]")
    console.print(f"  [dim]{output_path}[/dim]")
    console.print()

    if not yes:
        if not click.confirm("Continue?"):
            print_warning("Cancelled.")
            return

    try:
        deleted = 0
        with console.status("[cyan]Deleting files...[/cyan]", spinner="dots"):
            for file in files:
                if file.is_file():
                    file.unlink()
                    deleted += 1

        console.print()
        print_success(f"Deleted {deleted} file(s)")

    except Exception as e:
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    cli()

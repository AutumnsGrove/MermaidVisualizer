"""
Command-line interface for MermaidVisualizer.

This module provides a CLI using Click framework for extracting Mermaid diagrams
from markdown files and generating visualizations.

Supports two installation modes:
- Slim: Only click required, API rendering, plain text output
- Full: All features including rich output, local rendering, gist support
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

import click

# Optional rich imports (for full install)
try:
    from rich.console import Console
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        TimeElapsedColumn,
    )
    from rich.table import Table
    from rich.panel import Panel
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    RichHandler = None

# Import core modules
from . import extractor
from . import generator
from . import file_handler

# Optional gist handler (requires requests)
try:
    from . import gist_handler
    GIST_AVAILABLE = True
except ImportError:
    gist_handler = None
    GIST_AVAILABLE = False

# Console setup - fallback to plain output if rich not available
if RICH_AVAILABLE:
    console = Console()
else:
    # Simple console fallback
    class SimpleConsole:
        def print(self, msg="", **kwargs):
            # Strip rich markup for plain output
            import re
            clean = re.sub(r'\[/?[^\]]+\]', '', str(msg))
            print(clean)
    console = SimpleConsole()


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
    Configure logging with Rich handler (if available) or basic handler.

    Args:
        verbose: If True, set logging level to DEBUG; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO

    if RICH_AVAILABLE:
        logging.basicConfig(
            level=level,
            format="%(message)s",
            handlers=[RichHandler(console=console, rich_tracebacks=True)],
        )
    else:
        logging.basicConfig(
            level=level,
            format="%(levelname)s: %(message)s",
        )


def validate_input_path(ctx, param, value):
    """Validate that input path (file or directory) exists, or is a valid gist URL."""
    # Check if it's a gist URL - if so, skip path validation
    if GIST_AVAILABLE and gist_handler.is_gist_url(str(value)):
        return value  # Return the URL string, we'll handle it later

    # Otherwise, validate as a path
    path = Path(value).resolve()
    if not path.exists():
        raise click.BadParameter(f"Path does not exist: {value}")
    if path.is_file() and not path.suffix.lower() in [".md", ".markdown"]:
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
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                        MermaidVisualizer v0.1.0                          ║
    ║          Automated Mermaid Diagram Extraction & Generation Tool          ║
    ╚══════════════════════════════════════════════════════════════════════════╝

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
      • Flowcharts (graph, flowchart)
      • Sequence Diagrams
      • Class Diagrams
      • State Diagrams (stateDiagram-v2)
      • Entity Relationship Diagrams (erDiagram)
      • Gantt Charts
      • Pie Charts
      • User Journey Diagrams
      • Git Graphs
      • Mindmaps, Timelines, and more

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
        console.print("[cyan]Mode:[/cyan] API rendering (mermaid.ink)")
    else:
        generator.set_api_mode(False)

    output_path = Path(output_dir).resolve()

    if RICH_AVAILABLE:
        console.print(
            Panel.fit(
                "[bold cyan]MermaidVisualizer - Generate Diagrams[/bold cyan]",
                border_style="cyan",
            )
        )
    else:
        console.print("=" * 50)
        console.print("MermaidVisualizer - Generate Diagrams")
        console.print("=" * 50)

    try:
        # Ensure output directory exists
        file_handler.ensure_output_dir(output_path)
        logger.info(f"Output directory: {output_path}")

        # Handle GitHub Gist input
        gist_url = None

        # Check if --gist flag was used
        if gist:
            if not GIST_AVAILABLE:
                console.print("[red]Error:[/red] Gist support requires 'requests' package.")
                console.print("Install with: pip install mermaid-visualizer[api]")
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
                console.print(f"\n[cyan]Fetching from GitHub Gist:[/cyan] {gist_url}")
                md_files = gist_handler.fetch_gist_files(gist_url, github_token)

                if not md_files:
                    console.print("\n[yellow]No markdown files found in gist.[/yellow]")
                    return

                console.print(f"[green]✓[/green] Fetched {len(md_files)} markdown file(s) from gist\n")

            except ValueError as e:
                console.print(f"\n[bold red]Invalid gist:[/bold red] {e}")
                sys.exit(1)
            except ConnectionError as e:
                console.print(f"\n[bold red]Connection error:[/bold red] {e}")
                sys.exit(1)
            except PermissionError as e:
                console.print(f"\n[bold red]Permission denied:[/bold red] {e}")
                console.print("[yellow]Tip:[/yellow] Use --github-token for private gists")
                sys.exit(1)
        else:
            # Original logic: find markdown files from input_dir
            input_type = "file" if input_dir.is_file() else "directory"
            console.print(f"\n[cyan]Input:[/cyan] {input_dir} ({input_type})")
            if input_dir.is_dir():
                console.print(f"[cyan]Recursive:[/cyan] {'Yes' if recursive else 'No'}")

            md_files = file_handler.get_markdown_files_from_path(
                input_dir, recursive=recursive
            )

        if not md_files:
            console.print("\n[yellow]No markdown files found.[/yellow]")
            return

        console.print(f"[cyan]Found:[/cyan] {len(md_files)} markdown file(s)\n")

        # Process files and generate diagrams
        result = ProcessingResult()
        mappings = []

        # Use rich progress if available, otherwise simple output
        if RICH_AVAILABLE:
            progress_ctx = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console,
            )
        else:
            # Simple progress context manager for slim mode
            class SimpleProgress:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
                def add_task(self, desc, total):
                    self.total = total
                    self.current = 0
                    return 0
                def advance(self, task_id):
                    self.current += 1
                    print(f"Processing... {self.current}/{self.total}", end="\r")
            progress_ctx = SimpleProgress()

        with progress_ctx as progress:
            task = progress.add_task("[cyan]Processing files...", total=len(md_files))

            for md_file in md_files:
                try:
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
                                linked_file = file_handler.create_linked_markdown(
                                    md_file, diagram_files, output_in_source_dir=True
                                )
                                if linked_file:
                                    logger.debug(
                                        f"Created linked markdown: {linked_file.name}"
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
        console.print("\n[bold cyan]Summary:[/bold cyan]")
        console.print(f"  Files processed: {result.files_processed}")
        console.print(
            f"  Diagrams generated: [green]{result.diagrams_generated}[/green]"
        )
        if result.diagrams_failed > 0:
            console.print(f"  Diagrams failed: [red]{result.diagrams_failed}[/red]")

        if result.errors and verbose:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in result.errors:
                console.print(f"  • {error}")

        if result.diagrams_failed > 0:
            sys.exit(1)

    except Exception as e:
        logger.exception("Error during generation")
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
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

    if RICH_AVAILABLE:
        console.print(
            Panel.fit(
                "[bold cyan]MermaidVisualizer - Scan Diagrams[/bold cyan]",
                border_style="cyan",
            )
        )
    else:
        console.print("=" * 50)
        console.print("MermaidVisualizer - Scan Diagrams")
        console.print("=" * 50)

    try:
        # Find markdown files
        input_type = "file" if input_dir.is_file() else "directory"
        console.print(f"\n[cyan]Input:[/cyan] {input_dir} ({input_type})")
        if input_dir.is_dir():
            console.print(f"[cyan]Recursive:[/cyan] {'Yes' if recursive else 'No'}\n")
        else:
            console.print()

        md_files = file_handler.get_markdown_files_from_path(
            input_dir, recursive=recursive
        )

        if not md_files:
            console.print("[yellow]No markdown files found.[/yellow]")
            return

        # Collect all diagrams
        all_diagrams = []
        for md_file in md_files:
            try:
                diagrams = extractor.extract_mermaid_blocks(md_file)
                all_diagrams.extend(diagrams)
            except Exception as e:
                logger.error(f"Error scanning {md_file.name}: {str(e)}")

        total_diagrams = len(all_diagrams)

        if total_diagrams > 0:
            if RICH_AVAILABLE:
                # Create rich table
                table = Table(title="Mermaid Diagrams Found")
                table.add_column("Source File", style="cyan")
                table.add_column("Diagram Type", style="green")
                table.add_column("Line Range", style="yellow")
                for diagram in all_diagrams:
                    table.add_row(
                        diagram.source_file.name,
                        diagram.diagram_type,
                        f"{diagram.start_line}-{diagram.end_line}",
                    )
                console.print(table)
            else:
                # Simple text table for slim mode
                console.print("\nMermaid Diagrams Found:")
                console.print("-" * 60)
                console.print(f"{'Source File':<25} {'Type':<15} {'Lines':<10}")
                console.print("-" * 60)
                for diagram in all_diagrams:
                    console.print(
                        f"{diagram.source_file.name:<25} {diagram.diagram_type:<15} "
                        f"{diagram.start_line}-{diagram.end_line}"
                    )
                console.print("-" * 60)

            console.print(
                f"\n[bold]Total:[/bold] {total_diagrams} diagram(s) in {len(md_files)} file(s)"
            )
        else:
            console.print("[yellow]No Mermaid diagrams found.[/yellow]")

    except Exception as e:
        logger.exception("Error during scan")
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
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

    if RICH_AVAILABLE:
        console.print(
            Panel.fit(
                "[bold cyan]MermaidVisualizer - Clean Diagrams[/bold cyan]",
                border_style="cyan",
            )
        )
    else:
        console.print("=" * 50)
        console.print("MermaidVisualizer - Clean Diagrams")
        console.print("=" * 50)

    if not output_path.exists():
        console.print(f"\n[yellow]Directory does not exist:[/yellow] {output_path}")
        return

    # Count files
    files = list(output_path.glob("*"))
    file_count = len([f for f in files if f.is_file()])

    if file_count == 0:
        console.print(f"\n[yellow]No files to clean in:[/yellow] {output_path}")
        return

    console.print(f"\n[yellow]This will delete {file_count} file(s) from:[/yellow]")
    console.print(f"  {output_path}\n")

    if not yes:
        if not click.confirm("Continue?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    try:
        deleted = 0
        for file in files:
            if file.is_file():
                file.unlink()
                deleted += 1

        console.print(f"\n[green]✓[/green] Deleted {deleted} file(s)")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli()

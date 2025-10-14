"""
Command-line interface for MermaidVisualizer.

This module provides a CLI using Click framework for extracting Mermaid diagrams
from markdown files and generating visualizations.
"""

import logging
import sys
from pathlib import Path
from typing import List
from dataclasses import dataclass

import click
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

# Import core modules
from . import extractor
from . import generator
from . import file_handler

console = Console()


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
    Configure logging with Rich handler.

    Args:
        verbose: If True, set logging level to DEBUG; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def validate_input_path(ctx, param, value):
    """Validate that input path (file or directory) exists."""
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
      $ mermaid generate -f svg --create-linked-markdown

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
    "--create-linked-markdown/--no-create-linked-markdown",
    default=True,
    help="Create modified markdown files with wiki-style image links [[image.png]]",
    show_default=True,
)
def generate(
    input_dir: Path,
    output_dir: str,
    format: str,
    scale: int,
    width: int,
    recursive: bool,
    verbose: bool,
    create_linked_markdown: bool,
) -> None:
    """
    Extract Mermaid diagrams from markdown files and generate visual diagrams.

    \b
    This command processes either a single markdown file or a directory
    containing markdown files with ```mermaid code blocks, extracts them,
    and generates visual diagrams using the Mermaid CLI tool.

    \b
    OUTPUT STRUCTURE:
      When --create-linked-markdown is enabled (default):
        - Diagrams are saved next to source markdown files
        - Creates *_linked.md files with embedded image references

      When disabled:
        - Diagrams are saved to --output-dir in project subdirectories
        - Generates index.html for easy browsing

    \b
    EXAMPLES:
      # Basic usage (current directory)
      $ mermaid generate

      # Process a single markdown file
      $ mermaid generate -i ./docs/architecture.md

      # Process an entire directory
      $ mermaid generate -i ./docs

      # High-resolution PNG with custom scale
      $ mermaid generate -s 5 -w 3200

      # Generate SVG diagrams
      $ mermaid generate -f svg

      # Non-recursive directory scan
      $ mermaid generate --no-recursive

      # Disable linked markdown creation
      $ mermaid generate --no-create-linked-markdown
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    output_path = Path(output_dir).resolve()

    console.print(
        Panel.fit(
            "[bold cyan]MermaidVisualizer - Generate Diagrams[/bold cyan]",
            border_style="cyan",
        )
    )

    try:
        # Ensure output directory exists
        file_handler.ensure_output_dir(output_path)
        logger.info(f"Output directory: {output_path}")

        # Find markdown files
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

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
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

                    # Determine output directory based on create_linked_markdown option
                    if create_linked_markdown:
                        # Output diagrams to the source file's directory
                        diagram_output_dir = md_file.parent
                    else:
                        # Get project name and create project-specific subdirectory
                        project_name = file_handler.get_project_name(
                            md_file, levels_up=3
                        )
                        diagram_output_dir = output_path / project_name

                    file_handler.ensure_output_dir(diagram_output_dir)

                    for diagram in diagrams:
                        output_filename = file_handler.create_output_filename(
                            diagram.source_file,
                            diagram.index,
                            diagram.diagram_type,
                            format,
                        )
                        output_file = diagram_output_dir / output_filename

                        success = generator.generate_diagram(
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
                        if create_linked_markdown:
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

    console.print(
        Panel.fit(
            "[bold cyan]MermaidVisualizer - Scan Diagrams[/bold cyan]",
            border_style="cyan",
        )
    )

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

        # Create results table
        table = Table(title="Mermaid Diagrams Found")
        table.add_column("Source File", style="cyan")
        table.add_column("Diagram Type", style="green")
        table.add_column("Line Range", style="yellow")

        total_diagrams = 0

        for md_file in md_files:
            try:
                diagrams = extractor.extract_mermaid_blocks(md_file)
                for diagram in diagrams:
                    table.add_row(
                        diagram.source_file.name,
                        diagram.diagram_type,
                        f"{diagram.start_line}-{diagram.end_line}",
                    )
                    total_diagrams += 1
            except Exception as e:
                logger.error(f"Error scanning {md_file.name}: {str(e)}")

        if total_diagrams > 0:
            console.print(table)
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

    console.print(
        Panel.fit(
            "[bold cyan]MermaidVisualizer - Clean Diagrams[/bold cyan]",
            border_style="cyan",
        )
    )

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

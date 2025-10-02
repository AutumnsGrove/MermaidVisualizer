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


def validate_input_directory(ctx, param, value):
    """Validate that input directory exists."""
    path = Path(value).resolve()
    if not path.exists():
        raise click.BadParameter(f"Directory does not exist: {value}")
    if not path.is_dir():
        raise click.BadParameter(f"Not a directory: {value}")
    return path


def validate_output_format(ctx, param, value):
    """Validate output format."""
    valid_formats = ["png", "svg"]
    if value.lower() not in valid_formats:
        raise click.BadParameter(
            f"Invalid format '{value}'. Must be one of: {', '.join(valid_formats)}"
        )
    return value.lower()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    MermaidVisualizer - Automated Mermaid diagram extraction and generation.

    Extract Mermaid diagrams from markdown files and generate visual diagrams.
    """
    pass


@cli.command()
@click.option(
    "--input-dir",
    "-i",
    default=".",
    callback=validate_input_directory,
    help="Input directory to scan for markdown files",
)
@click.option(
    "--output-dir",
    "-o",
    default="./diagrams",
    type=click.Path(),
    help="Output directory for generated diagrams",
)
@click.option(
    "--format",
    "-f",
    default="png",
    callback=validate_output_format,
    help="Output format: png or svg",
)
@click.option(
    "--scale",
    "-s",
    default=3,
    type=int,
    help="Scale factor for PNG output (default: 3 for high resolution)",
)
@click.option(
    "--width",
    "-w",
    default=2400,
    type=int,
    help="Width of output image in pixels (default: 2400)",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Recursively scan subdirectories",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--create-linked-markdown/--no-create-linked-markdown",
    default=True,
    help="Create modified markdown files with wiki-style image links (default: enabled)",
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
    Extract and generate diagrams from markdown files.

    Scans the input directory for Mermaid diagram definitions and generates
    visual diagrams in the specified format.
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
        console.print(f"\n[cyan]Scanning:[/cyan] {input_dir}")
        console.print(f"[cyan]Recursive:[/cyan] {'Yes' if recursive else 'No'}")

        md_files = file_handler.find_markdown_files(input_dir, recursive=recursive)

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
                        project_name = file_handler.get_project_name(md_file, levels_up=3)
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
                                    logger.debug(f"Created linked markdown: {linked_file.name}")
                            except Exception as e:
                                logger.warning(f"Failed to create linked markdown for {md_file.name}: {str(e)}")

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
    callback=validate_input_directory,
    help="Input directory to scan for markdown files",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Recursively scan subdirectories",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def scan(
    input_dir: Path,
    recursive: bool,
    verbose: bool,
) -> None:
    """
    Scan for Mermaid diagrams without generating files (dry run).

    Shows what diagrams would be generated without actually creating them.
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
        console.print(f"\n[cyan]Scanning:[/cyan] {input_dir}")
        console.print(f"[cyan]Recursive:[/cyan] {'Yes' if recursive else 'No'}\n")

        md_files = file_handler.find_markdown_files(input_dir, recursive=recursive)

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
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clean(output_dir: str, yes: bool) -> None:
    """
    Remove all generated diagrams from the output directory.

    This will delete all files in the output directory.
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

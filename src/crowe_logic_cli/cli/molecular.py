from __future__ import annotations

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional

from crowe_logic_cli.config import load_config
from crowe_logic_cli.providers.base import coerce_messages
from crowe_logic_cli.providers.factory import create_provider


app = typer.Typer(add_completion=False, help="Molecular dynamics and chemistry analysis")
console = Console()


@app.command()
def analyze(
    file: Path = typer.Argument(..., help="Molecular structure or trajectory file"),
    format: Optional[str] = typer.Option(
        None, "--format", "-f", help="File format (pdb, mol2, xyz, sdf)"
    ),
) -> None:
    """Analyze molecular structure or dynamics trajectory."""
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    content = file.read_text()
    detected_format = format or file.suffix.lstrip(".")

    prompt = f"""Analyze this molecular structure file ({detected_format} format).

Provide:
1. Molecule identification
2. Key structural features
3. Functional groups present
4. Potential interactions
5. Any notable properties

File content:
{content[:5000]}
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Molecular Analysis: {file.name}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def validate_structure(
    file: Path = typer.Argument(..., help="Molecular structure file to validate"),
) -> None:
    """Validate molecular structure for errors and inconsistencies."""
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    content = file.read_text()

    prompt = f"""Validate this molecular structure for errors and inconsistencies.

Check for:
1. Invalid bond lengths or angles
2. Missing atoms or incomplete structures
3. Incorrect valences
4. Stereochemistry issues
5. Format compliance

Structure content:
{content[:5000]}
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel("[bold cyan]Structure Validation[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def pubchem(
    cid: int = typer.Argument(..., help="PubChem Compound ID (CID)"),
) -> None:
    """Look up compound information from PubChem."""
    prompt = f"""Provide detailed information about PubChem compound CID {cid}.

Include:
1. Chemical name and synonyms
2. Molecular formula and weight
3. Structure description
4. Physical properties
5. Biological activity (if known)
6. Safety information
7. Common uses
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]PubChem: CID {cid}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def drugbank(
    drug_id: str = typer.Argument(..., help="DrugBank ID (e.g., DB00945)"),
) -> None:
    """Look up drug information from DrugBank."""
    prompt = f"""Provide detailed information about DrugBank compound {drug_id}.

Include:
1. Drug name and classification
2. Mechanism of action
3. Pharmacokinetics (ADME)
4. Indications and uses
5. Side effects and interactions
6. Chemical properties
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]DrugBank: {drug_id}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def compare(
    molecule1: str = typer.Argument(..., help="First molecule (name, SMILES, or formula)"),
    molecule2: str = typer.Argument(..., help="Second molecule (name, SMILES, or formula)"),
) -> None:
    """Compare two molecules."""
    prompt = f"""Compare these two molecules:

Molecule 1: {molecule1}
Molecule 2: {molecule2}

Provide:
1. Structural similarities and differences
2. Property comparison (if determinable)
3. Functional group differences
4. Potential activity differences
5. Any notable relationships (isomers, analogs, etc.)
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel("[bold cyan]Molecule Comparison[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()

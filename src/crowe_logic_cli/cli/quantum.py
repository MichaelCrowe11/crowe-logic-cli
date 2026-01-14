from __future__ import annotations

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from typing import Optional

from crowe_logic_cli.config import load_config
from crowe_logic_cli.providers.base import coerce_messages
from crowe_logic_cli.providers.factory import create_provider


app = typer.Typer(add_completion=False, help="Quantum-enhanced reasoning and analysis")
console = Console()


@app.command()
def reason(
    problem: str = typer.Argument(..., help="Problem to solve using quantum-inspired reasoning"),
    domain: str = typer.Option(
        "molecular", "--domain", "-d",
        help="Domain context: molecular, physics, optimization, general"
    ),
) -> None:
    """Apply Crowe Logic 4-stage quantum-inspired reasoning."""
    prompt = f"""Using Crowe Logic 4-stage quantum-inspired reasoning, solve this problem:

Problem: {problem}
Domain: {domain}

Apply these stages:

1. DECOMPOSITION - Break down the problem into fundamental components
2. FRAMEWORK - Establish the theoretical framework and relevant equations
3. COMPUTATION - Perform the calculations with clear steps
4. VALIDATION - Verify the results and check for consistency

Format your response as:

<reasoning>
1. DECOMPOSITION:
   [Break down the problem]

2. FRAMEWORK:
   [Establish theoretical basis]

3. COMPUTATION:
   [Show calculations]

4. VALIDATION:
   [Verify results]
</reasoning>

<answer>
[Final answer with units and interpretation]
</answer>
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Quantum Reasoning: {domain}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def vqe(
    hamiltonian: str = typer.Argument(..., help="Hamiltonian description or molecule"),
) -> None:
    """Discuss Variational Quantum Eigensolver for a system."""
    prompt = f"""Explain how to apply VQE (Variational Quantum Eigensolver) to: {hamiltonian}

Include:
1. Hamiltonian encoding
2. Ansatz selection
3. Parameter optimization strategy
4. Expected ground state energy
5. Practical implementation considerations
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]VQE Analysis: {hamiltonian}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def qaoa(
    problem: str = typer.Argument(..., help="Optimization problem description"),
) -> None:
    """Discuss QAOA for a combinatorial optimization problem."""
    prompt = f"""Explain how to apply QAOA (Quantum Approximate Optimization Algorithm) to: {problem}

Include:
1. Problem encoding as QUBO/Ising model
2. Mixer and cost Hamiltonian design
3. Circuit depth considerations
4. Classical optimization loop
5. Expected solution quality
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]QAOA Analysis: {problem}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def analyze_circuit(
    file: Path = typer.Argument(..., help="Quantum circuit file (QASM, Qiskit, etc.)"),
) -> None:
    """Analyze a quantum circuit."""
    if not file.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    content = file.read_text()

    prompt = f"""Analyze this quantum circuit.

Provide:
1. Circuit description and purpose
2. Number of qubits and gates
3. Gate breakdown (single-qubit, two-qubit, etc.)
4. Circuit depth
5. Potential optimizations
6. Expected behavior/output

Circuit content:
{content[:5000]}
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Quantum Circuit Analysis: {file.name}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def explain(
    concept: str = typer.Argument(..., help="Quantum concept to explain"),
    level: str = typer.Option(
        "intermediate", "--level", "-l",
        help="Explanation level: beginner, intermediate, advanced"
    ),
) -> None:
    """Explain a quantum computing or quantum mechanics concept."""
    level_instruction = {
        "beginner": "Explain in simple terms with analogies, avoiding mathematical formalism.",
        "intermediate": "Include some mathematical notation and assume basic physics knowledge.",
        "advanced": "Use full mathematical formalism and assume graduate-level physics background.",
    }.get(level, "Include some mathematical notation and assume basic physics knowledge.")

    prompt = f"""Explain the quantum concept: {concept}

{level_instruction}

Include:
1. Core definition
2. Key principles involved
3. Mathematical representation (appropriate to level)
4. Practical applications
5. Common misconceptions
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Quantum Concept: {concept}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def chemistry(
    molecule: str = typer.Argument(..., help="Molecule to analyze (name or formula)"),
    method: str = typer.Option(
        "dft", "--method", "-m",
        help="Computational method: dft, hf, mp2, ccsd"
    ),
) -> None:
    """Discuss quantum chemistry calculations for a molecule."""
    prompt = f"""Discuss quantum chemistry calculations for: {molecule}

Using method: {method.upper()}

Cover:
1. Appropriate basis set recommendations
2. Expected computational cost
3. Properties that can be calculated
4. Accuracy expectations
5. Practical considerations for running the calculation
6. Recommended software packages
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Quantum Chemistry: {molecule}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def algorithm(
    name: str = typer.Argument(..., help="Quantum algorithm name (e.g., grover, shor, vqe)"),
) -> None:
    """Explain a quantum algorithm."""
    prompt = f"""Explain the quantum algorithm: {name}

Include:
1. Purpose and problem it solves
2. Classical vs quantum speedup
3. Key steps and components
4. Circuit implementation overview
5. Resource requirements (qubits, gates, depth)
6. Current practical limitations
7. Real-world applications
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Quantum Algorithm: {name}[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()


@app.command()
def error_correction(
    code: str = typer.Option(
        "surface", "--code", "-c",
        help="Error correction code: surface, steane, shor, repetition"
    ),
) -> None:
    """Explain quantum error correction codes."""
    prompt = f"""Explain the {code} quantum error correction code.

Include:
1. Basic principles
2. Logical vs physical qubits
3. Error types it corrects
4. Threshold theorem relevance
5. Implementation requirements
6. Current experimental status
"""

    config = load_config()
    provider = create_provider(config)
    messages = coerce_messages(prompt)

    console.print(Panel(f"[bold cyan]Quantum Error Correction: {code.title()} Code[/bold cyan]"))

    for chunk in provider.stream(messages):
        console.print(chunk, end="")
    console.print()

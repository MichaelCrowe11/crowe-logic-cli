# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""
AICL CLI Commands

Commands for multi-model orchestration using AICL protocol.
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from ..aicl import AICLMessage
from ..orchestrator import (
    OrchestrationEngine,
    OrchestrationMode,
    create_default_engine,
)
from ..orchestrator.multi_client import (
    ModelConfig,
    Provider,
    CLAUDE_OPUS_45,
    GPT_51_CODEX,
)
from ..ui import LiveOrchestration
from ..ui.diff import DiffView

app = typer.Typer(
    name="aicl",
    help="Multi-model orchestration using AICL (AI Communication Language)",
)

console = Console()


def get_engine() -> OrchestrationEngine:
    """Get or create the orchestration engine."""
    return create_default_engine()


@app.command()
def debate(
    topic: str = typer.Argument(..., help="Topic to debate"),
    rounds: int = typer.Option(3, "--rounds", "-r", help="Number of debate rounds"),
    model_a: str = typer.Option("claude-opus-4-5-20251101", "--model-a", "-a", help="First model (argues FOR)"),
    model_b: str = typer.Option("gpt-5.1-codex", "--model-b", "-b", help="Second model (argues AGAINST)"),
    live: bool = typer.Option(True, "--live/--no-live", help="Show live updates"),
) -> None:
    """
    Start a debate between two AI models.

    One model argues FOR the topic, the other AGAINST.
    After rounds of argument and counter-argument, a synthesis is produced.
    """
    console.print(Panel(
        f"[bold]Topic:[/] {topic}\n"
        f"[green]{model_a}[/] (FOR) vs [red]{model_b}[/] (AGAINST)\n"
        f"Rounds: {rounds}",
        title="[bold bright_cyan]AICL Debate Mode[/]",
        border_style="bright_cyan",
    ))

    async def run_debate() -> None:
        engine = get_engine()

        # Ensure models are registered
        if "claude" in model_a.lower():
            engine.register_model(CLAUDE_OPUS_45)
        if "gpt" in model_b.lower():
            engine.register_model(GPT_51_CODEX)

        if live:
            display = LiveOrchestration(console)
            display.setup(OrchestrationMode.DEBATE, [model_a, model_b])

            result = await display.run_with_display(
                engine.orchestrate,
                topic,
                OrchestrationMode.DEBATE,
                [model_a, model_b],
                on_message=display.on_message,
                on_progress=display.on_progress,
                rounds=rounds,
            )

            display.print_final_output()
        else:
            def on_message(msg: AICLMessage) -> None:
                color = "magenta" if "claude" in msg.sender_model.lower() else "green"
                console.print(f"\n[{color}]{msg.sender_model}[/] [{msg.intent.value}]")
                console.print(msg.content[:500] + "..." if len(msg.content) > 500 else msg.content)

            result = await engine.orchestrate(
                topic,
                OrchestrationMode.DEBATE,
                [model_a, model_b],
                on_message=on_message,
                rounds=rounds,
            )

            console.print(Panel(result.final_output, title="[bold]Synthesis[/]"))

        await engine.close()

    asyncio.run(run_debate())


@app.command()
def verify(
    task: str = typer.Argument(..., help="Task to create and verify"),
    iterations: int = typer.Option(3, "--iterations", "-i", help="Max verification iterations"),
    creator: str = typer.Option("gpt-5.1-codex", "--creator", "-c", help="Creator model"),
    validator: str = typer.Option("claude-opus-4-5-20251101", "--validator", "-v", help="Validator model"),
) -> None:
    """
    Create and verify with two models.

    One model creates the output, the other validates it.
    Iterates until validation passes or max iterations reached.
    """
    console.print(Panel(
        f"[bold]Task:[/] {task}\n"
        f"[green]Creator:[/] {creator}\n"
        f"[cyan]Validator:[/] {validator}",
        title="[bold bright_cyan]AICL Verify Mode[/]",
        border_style="bright_cyan",
    ))

    async def run_verify() -> None:
        engine = get_engine()

        display = LiveOrchestration(console)
        display.setup(OrchestrationMode.VERIFY, [creator, validator])

        result = await display.run_with_display(
            engine.orchestrate,
            task,
            OrchestrationMode.VERIFY,
            [creator, validator],
            on_message=display.on_message,
            on_progress=display.on_progress,
            max_iterations=iterations,
        )

        console.print(f"\n[bold]Validation {'Passed' if result.consensus_reached else 'Did Not Pass'}[/]")
        display.print_final_output()

        await engine.close()

    asyncio.run(run_verify())


@app.command()
def parallel(
    task: str = typer.Argument(..., help="Task to solve in parallel"),
    models: str = typer.Option(
        "claude-opus-4-5-20251101,gpt-5.1-codex",
        "--models", "-m",
        help="Comma-separated list of models",
    ),
    compare: bool = typer.Option(True, "--compare/--no-compare", help="Show comparison"),
) -> None:
    """
    Run task on multiple models in parallel.

    All models work simultaneously on the same task.
    Results are compared and the best output is selected.
    """
    model_list = [m.strip() for m in models.split(",")]

    console.print(Panel(
        f"[bold]Task:[/] {task}\n"
        f"[bold]Models:[/] {', '.join(model_list)}",
        title="[bold bright_cyan]AICL Parallel Mode[/]",
        border_style="bright_cyan",
    ))

    async def run_parallel() -> None:
        engine = get_engine()

        display = LiveOrchestration(console)
        display.setup(OrchestrationMode.PARALLEL, model_list)

        result = await display.run_with_display(
            engine.orchestrate,
            task,
            OrchestrationMode.PARALLEL,
            model_list,
            on_message=display.on_message,
            on_progress=display.on_progress,
        )

        if compare:
            responses = {
                msg.sender_model: msg.content
                for msg in result.conversation.messages
                if msg.sender_model in model_list
            }
            if responses:
                diff = DiffView(console)
                diff.compare_responses(responses)

        display.print_final_output()

        await engine.close()

    asyncio.run(run_parallel())


@app.command()
def chain(
    task: str = typer.Argument(..., help="Task to process through chain"),
    models: str = typer.Option(
        "claude-opus-4-5-20251101,gpt-5.1-codex",
        "--models", "-m",
        help="Comma-separated list of models (in order)",
    ),
    instructions: Optional[str] = typer.Option(
        None,
        "--instructions", "-i",
        help="Comma-separated instructions for each step",
    ),
) -> None:
    """
    Process task through a chain of models.

    Each model processes the output of the previous one.
    Useful for iterative refinement.
    """
    model_list = [m.strip() for m in models.split(",")]
    instruction_list = [i.strip() for i in instructions.split(",")] if instructions else []

    console.print(Panel(
        f"[bold]Task:[/] {task}\n"
        f"[bold]Chain:[/] {' -> '.join(model_list)}",
        title="[bold bright_cyan]AICL Chain Mode[/]",
        border_style="bright_cyan",
    ))

    async def run_chain() -> None:
        engine = get_engine()

        display = LiveOrchestration(console)
        display.setup(OrchestrationMode.CHAIN, model_list)

        result = await display.run_with_display(
            engine.orchestrate,
            task,
            OrchestrationMode.CHAIN,
            model_list,
            on_message=display.on_message,
            on_progress=display.on_progress,
            chain_instructions=instruction_list,
        )

        display.print_final_output()

        await engine.close()

    asyncio.run(run_chain())


@app.command()
def interactive() -> None:
    """
    Interactive AICL session.

    Start a conversational session where you can switch modes
    and interact with multiple models.
    """
    console.print(Panel(
        "[bold]Welcome to AICL Interactive Mode[/]\n\n"
        "Commands:\n"
        "  [cyan]/debate[/] <topic>  - Start a debate\n"
        "  [cyan]/verify[/] <task>   - Create and verify\n"
        "  [cyan]/parallel[/] <task> - Parallel execution\n"
        "  [cyan]/chain[/] <task>    - Chain processing\n"
        "  [cyan]/models[/]          - List available models\n"
        "  [cyan]/quit[/]            - Exit\n",
        title="[bold bright_cyan]AICL Interactive[/]",
        border_style="bright_cyan",
    ))

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]AICL[/]")

            if user_input.startswith("/quit"):
                console.print("[dim]Goodbye![/]")
                break

            elif user_input.startswith("/models"):
                console.print("\n[bold]Available Models:[/]")
                console.print("  [magenta]claude-opus-4-5-20251101[/] - Claude Opus 4.5 (Anthropic)")
                console.print("  [green]gpt-5.1-codex[/] - GPT-5.1 Codex (OpenAI)")
                console.print("  [green]gpt-5-turbo[/] - GPT-5 Turbo (OpenAI)")

            elif user_input.startswith("/debate "):
                topic = user_input[8:].strip()
                if topic:
                    debate(topic)

            elif user_input.startswith("/verify "):
                task = user_input[8:].strip()
                if task:
                    verify(task)

            elif user_input.startswith("/parallel "):
                task = user_input[10:].strip()
                if task:
                    parallel(task)

            elif user_input.startswith("/chain "):
                task = user_input[7:].strip()
                if task:
                    chain(task)

            else:
                console.print("[dim]Use a command like /debate, /verify, /parallel, or /chain[/]")

        except KeyboardInterrupt:
            console.print("\n[dim]Use /quit to exit[/]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")


@app.command()
def spec() -> None:
    """
    Display the AICL protocol specification.
    """
    spec_text = """
[bold bright_cyan]AICL - AI Communication Language[/]
[dim]Version 1.0[/]

[bold]Purpose:[/]
AICL is a structured protocol for AI-to-AI communication, enabling
multi-model orchestration, collaborative reasoning, and consensus building.

[bold]Message Structure:[/]
┌─────────────────────────────────────────┐
│ AICL Message                            │
├─────────────────────────────────────────┤
│ sender_model: string                    │
│ sender_role: Role                       │
│ intent: Intent                          │
│ content: string                         │
│ reasoning: string                       │
│ confidence: float (0.0-1.0)             │
│ code_blocks: CodeBlock[]                │
│ citations: Citation[]                   │
└─────────────────────────────────────────┘

[bold]Roles:[/]
  • INITIATOR   - Starts the task
  • RESPONDER   - Responds to initiator
  • REVIEWER    - Reviews/critiques work
  • SYNTHESIZER - Combines perspectives
  • VALIDATOR   - Fact-checks and validates
  • EXECUTOR    - Executes code/actions

[bold]Intents:[/]
  Primary: QUERY, RESPONSE, PROPOSAL, CRITIQUE, REVISION, SYNTHESIS
  Code:    CODE_GENERATE, CODE_REVIEW, CODE_FIX, CODE_OPTIMIZE
  Debate:  ARGUE_FOR, ARGUE_AGAINST, COUNTER, CONCEDE
  Research: RESEARCH, FACT_CHECK, CITE_SOURCES

[bold]Orchestration Modes:[/]
  • DEBATE   - Models argue different perspectives
  • VERIFY   - One creates, one validates
  • PARALLEL - Simultaneous work, best wins
  • CHAIN    - Sequential processing
"""
    console.print(Panel(spec_text, border_style="bright_cyan"))


if __name__ == "__main__":
    app()

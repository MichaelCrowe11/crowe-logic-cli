# Copyright 2024-2026 Michael Benjamin Crowe
# SPDX-License-Identifier: Apache-2.0

"""
Orchestration Modes

Implements different strategies for multi-model collaboration:
- Debate: Models argue different perspectives
- Verify: One creates, one validates
- Parallel: Simultaneous work, best wins
- Chain: Sequential processing
"""

import asyncio
from typing import Any, Optional

from ..aicl import (
    AICLMessage,
    AICLRole,
    AICLIntent,
    AICLContext,
    AICLConversation,
)
from .engine import BaseOrchestrationMode, OrchestrationResult
from .multi_client import MultiModelClient


class DebateMode(BaseOrchestrationMode):
    """
    Debate Mode: Models argue different perspectives on a topic.

    Process:
    1. Present the topic to both models
    2. Model A argues FOR
    3. Model B argues AGAINST
    4. They counter each other's points
    5. A synthesizer (or one of them) creates final synthesis
    """

    async def execute(
        self,
        prompt: str,
        models: list[str],
        context: Optional[AICLContext] = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        if len(models) < 2:
            raise ValueError("Debate mode requires at least 2 models")

        ctx = context or AICLContext(original_prompt=prompt, current_objective=prompt)
        conv = AICLConversation(context=ctx)

        model_a, model_b = models[0], models[1]
        conv.add_model(model_a, AICLRole.INITIATOR, "debate_for")
        conv.add_model(model_b, AICLRole.RESPONDER, "debate_against")

        max_rounds = kwargs.get("rounds", 3)

        self.emit_progress("Starting debate", 0.0)

        # Initial arguments
        for_system = f"""You are participating in a structured debate about: {prompt}

Your role: ARGUE IN FAVOR of the proposition.
Be persuasive, use evidence, anticipate counterarguments.
Structure your argument clearly with main points and supporting evidence."""

        against_system = f"""You are participating in a structured debate about: {prompt}

Your role: ARGUE AGAINST the proposition.
Be persuasive, use evidence, anticipate counterarguments.
Structure your argument clearly with main points and supporting evidence."""

        # Model A: Opening argument FOR
        self.emit_progress(f"{model_a} opening argument", 0.1)
        for_response = await self.client.complete(
            model_a,
            [{"role": "user", "content": f"Present your opening argument FOR: {prompt}"}],
            system=for_system,
        )

        msg_for = AICLMessage(
            sender_model=model_a,
            sender_role=AICLRole.INITIATOR,
            intent=AICLIntent.ARGUE_FOR,
            content=for_response,
            confidence=0.85,
        )
        conv.add_message(msg_for)
        self.emit_message(msg_for)

        # Model B: Opening argument AGAINST
        self.emit_progress(f"{model_b} opening argument", 0.2)
        against_response = await self.client.complete(
            model_b,
            [{"role": "user", "content": f"Present your opening argument AGAINST: {prompt}\n\nYou're responding to this FOR argument:\n{for_response}"}],
            system=against_system,
        )

        msg_against = AICLMessage(
            sender_model=model_b,
            sender_role=AICLRole.RESPONDER,
            intent=AICLIntent.ARGUE_AGAINST,
            content=against_response,
            confidence=0.85,
        )
        conv.add_message(msg_against)
        self.emit_message(msg_against)

        # Debate rounds
        last_for = for_response
        last_against = against_response

        for round_num in range(max_rounds):
            progress = 0.3 + (round_num / max_rounds) * 0.5
            self.emit_progress(f"Debate round {round_num + 1}/{max_rounds}", progress)

            # Counter from FOR side
            counter_for = await self.client.complete(
                model_a,
                [{"role": "user", "content": f"Counter this AGAINST argument:\n{last_against}"}],
                system=for_system,
            )
            msg = AICLMessage(
                sender_model=model_a,
                sender_role=AICLRole.INITIATOR,
                intent=AICLIntent.COUNTER,
                content=counter_for,
                confidence=0.8,
            )
            conv.add_message(msg)
            self.emit_message(msg)

            # Counter from AGAINST side
            counter_against = await self.client.complete(
                model_b,
                [{"role": "user", "content": f"Counter this FOR argument:\n{counter_for}"}],
                system=against_system,
            )
            msg = AICLMessage(
                sender_model=model_b,
                sender_role=AICLRole.RESPONDER,
                intent=AICLIntent.COUNTER,
                content=counter_against,
                confidence=0.8,
            )
            conv.add_message(msg)
            self.emit_message(msg)

            last_for = counter_for
            last_against = counter_against

        # Synthesis
        self.emit_progress("Synthesizing conclusions", 0.9)
        synthesis_system = """Synthesize the debate into a balanced conclusion.
Consider the strongest points from both sides.
Provide a nuanced final assessment."""

        all_arguments = "\n\n".join([m.content for m in conv.messages])
        synthesis = await self.client.complete(
            model_a,  # Use first model for synthesis
            [{"role": "user", "content": f"Synthesize this debate:\n{all_arguments}"}],
            system=synthesis_system,
        )

        msg_synthesis = AICLMessage(
            sender_model=model_a,
            sender_role=AICLRole.SYNTHESIZER,
            intent=AICLIntent.SYNTHESIS,
            content=synthesis,
            confidence=0.9,
        )
        conv.add_message(msg_synthesis)
        self.emit_message(msg_synthesis)

        conv.status = "completed"
        conv.final_output = synthesis

        self.emit_progress("Debate complete", 1.0)

        return OrchestrationResult(
            conversation=conv,
            final_output=synthesis,
            consensus_reached=True,
            iterations=len(conv.messages),
            model_contributions={model_a: len(conv.get_messages_by_model(model_a)),
                               model_b: len(conv.get_messages_by_model(model_b))},
            quality_score=0.85,
        )


class VerifyMode(BaseOrchestrationMode):
    """
    Verify Mode: One model creates, another validates.

    Process:
    1. Creator produces initial output
    2. Validator reviews for correctness, security, quality
    3. Creator revises based on feedback
    4. Repeat until validation passes
    """

    async def execute(
        self,
        prompt: str,
        models: list[str],
        context: Optional[AICLContext] = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        if len(models) < 2:
            raise ValueError("Verify mode requires at least 2 models")

        ctx = context or AICLContext(original_prompt=prompt, current_objective=prompt)
        conv = AICLConversation(context=ctx)

        creator, validator = models[0], models[1]
        conv.add_model(creator, AICLRole.EXECUTOR, "creator")
        conv.add_model(validator, AICLRole.VALIDATOR, "validator")

        max_iterations = kwargs.get("max_iterations", 3)

        self.emit_progress("Starting verification workflow", 0.0)

        creator_system = """You are a code/content creator. Your job is to produce high-quality output.
When you receive feedback, incorporate it thoughtfully and explain your changes."""

        validator_system = """You are a critical validator. Your job is to review work for:
- Correctness and accuracy
- Security vulnerabilities
- Code quality and best practices
- Edge cases and error handling
- Performance considerations

Be specific in your feedback. If the work is acceptable, say "APPROVED" and explain why.
If it needs changes, list specific issues that must be addressed."""

        # Initial creation
        self.emit_progress(f"{creator} creating initial output", 0.1)
        creation = await self.client.complete(
            creator,
            [{"role": "user", "content": prompt}],
            system=creator_system,
        )

        msg_create = AICLMessage(
            sender_model=creator,
            sender_role=AICLRole.EXECUTOR,
            intent=AICLIntent.CODE_GENERATE if "code" in prompt.lower() else AICLIntent.PROPOSAL,
            content=creation,
            confidence=0.8,
        )
        conv.add_message(msg_create)
        self.emit_message(msg_create)

        current_output = creation
        approved = False

        for iteration in range(max_iterations):
            progress = 0.2 + (iteration / max_iterations) * 0.7
            self.emit_progress(f"Validation iteration {iteration + 1}/{max_iterations}", progress)

            # Validate
            validation = await self.client.complete(
                validator,
                [{"role": "user", "content": f"Review this work:\n\n{current_output}"}],
                system=validator_system,
            )

            is_approved = "APPROVED" in validation.upper()

            msg_validate = AICLMessage(
                sender_model=validator,
                sender_role=AICLRole.VALIDATOR,
                intent=AICLIntent.VALIDATION if is_approved else AICLIntent.CRITIQUE,
                content=validation,
                confidence=0.9 if is_approved else 0.7,
            )
            conv.add_message(msg_validate)
            self.emit_message(msg_validate)

            if is_approved:
                approved = True
                break

            # Revise based on feedback
            revision = await self.client.complete(
                creator,
                [{"role": "user", "content": f"Revise based on this feedback:\n{validation}\n\nOriginal:\n{current_output}"}],
                system=creator_system,
            )

            msg_revise = AICLMessage(
                sender_model=creator,
                sender_role=AICLRole.EXECUTOR,
                intent=AICLIntent.REVISION,
                content=revision,
                confidence=0.85,
            )
            conv.add_message(msg_revise)
            self.emit_message(msg_revise)

            current_output = revision

        conv.status = "completed"
        conv.final_output = current_output

        self.emit_progress("Verification complete", 1.0)

        return OrchestrationResult(
            conversation=conv,
            final_output=current_output,
            consensus_reached=approved,
            iterations=len(conv.messages),
            model_contributions={creator: len(conv.get_messages_by_model(creator)),
                               validator: len(conv.get_messages_by_model(validator))},
            quality_score=0.95 if approved else 0.7,
        )


class ParallelMode(BaseOrchestrationMode):
    """
    Parallel Mode: Both models work simultaneously, best output wins.

    Process:
    1. Send task to all models in parallel
    2. Collect all responses
    3. Evaluate and rank responses
    4. Return best output (or synthesis)
    """

    async def execute(
        self,
        prompt: str,
        models: list[str],
        context: Optional[AICLContext] = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        ctx = context or AICLContext(original_prompt=prompt, current_objective=prompt)
        conv = AICLConversation(context=ctx)

        for model in models:
            conv.add_model(model, AICLRole.RESPONDER, "parallel_worker")

        self.emit_progress("Starting parallel execution", 0.0)

        system = """Provide your best response to this request.
Be thorough, accurate, and well-structured."""

        # Execute in parallel
        self.emit_progress("All models working in parallel", 0.3)

        async def get_response(model_id: str) -> tuple[str, str]:
            response = await self.client.complete(
                model_id,
                [{"role": "user", "content": prompt}],
                system=system,
            )
            return model_id, response

        tasks = [get_response(m) for m in models]
        results = await asyncio.gather(*tasks)

        # Record all responses
        for model_id, response in results:
            msg = AICLMessage(
                sender_model=model_id,
                sender_role=AICLRole.RESPONDER,
                intent=AICLIntent.RESPONSE,
                content=response,
                confidence=0.8,
            )
            conv.add_message(msg)
            self.emit_message(msg)

        self.emit_progress("Evaluating responses", 0.7)

        # Use first model to evaluate and pick best
        evaluation_prompt = "Evaluate these responses and select the best one. Explain your choice:\n\n"
        for model_id, response in results:
            evaluation_prompt += f"=== {model_id} ===\n{response}\n\n"

        evaluator_system = """You are an impartial evaluator. Compare the responses and:
1. Identify the best response
2. Explain why it's the best
3. Note any unique strengths from other responses

Output format:
BEST: [model_id]
REASONING: [why it's best]
SYNTHESIS: [optional combined best elements]"""

        evaluation = await self.client.complete(
            models[0],
            [{"role": "user", "content": evaluation_prompt}],
            system=evaluator_system,
        )

        # Determine winner (simplified - just use first response as best)
        best_output = results[0][1]  # TODO: Parse evaluation to get actual best

        msg_eval = AICLMessage(
            sender_model=models[0],
            sender_role=AICLRole.SYNTHESIZER,
            intent=AICLIntent.SYNTHESIS,
            content=evaluation,
            confidence=0.9,
        )
        conv.add_message(msg_eval)
        self.emit_message(msg_eval)

        conv.status = "completed"
        conv.final_output = best_output

        self.emit_progress("Parallel execution complete", 1.0)

        return OrchestrationResult(
            conversation=conv,
            final_output=best_output,
            consensus_reached=True,
            iterations=len(models) + 1,
            model_contributions={m: 1 for m in models},
            quality_score=0.9,
        )


class ChainMode(BaseOrchestrationMode):
    """
    Chain Mode: Sequential processing through models.

    Process:
    1. First model processes the task
    2. Output passed to second model for enhancement
    3. Continue through all models
    4. Final output is the cumulative result
    """

    async def execute(
        self,
        prompt: str,
        models: list[str],
        context: Optional[AICLContext] = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        ctx = context or AICLContext(original_prompt=prompt, current_objective=prompt)
        conv = AICLConversation(context=ctx)

        for i, model in enumerate(models):
            role = AICLRole.INITIATOR if i == 0 else AICLRole.RESPONDER
            conv.add_model(model, role, f"chain_step_{i}")

        self.emit_progress("Starting chain execution", 0.0)

        current_output = prompt
        chain_instructions = kwargs.get("chain_instructions", [])

        for i, model in enumerate(models):
            progress = (i + 1) / len(models)
            self.emit_progress(f"Chain step {i + 1}/{len(models)}: {model}", progress * 0.9)

            # Get specific instructions for this step, or use default
            if i < len(chain_instructions):
                step_instruction = chain_instructions[i]
            else:
                step_instruction = "Improve and enhance the following"

            system = f"""You are step {i + 1} of {len(models)} in a processing chain.
Your task: {step_instruction}

Build upon the previous output. Add value without losing important information."""

            if i == 0:
                input_content = current_output
            else:
                input_content = f"Previous step output:\n{current_output}\n\nOriginal request:\n{prompt}"

            response = await self.client.complete(
                model,
                [{"role": "user", "content": input_content}],
                system=system,
            )

            msg = AICLMessage(
                sender_model=model,
                sender_role=AICLRole.INITIATOR if i == 0 else AICLRole.RESPONDER,
                intent=AICLIntent.RESPONSE,
                content=response,
                confidence=0.85,
            )
            conv.add_message(msg)
            self.emit_message(msg)

            current_output = response

        conv.status = "completed"
        conv.final_output = current_output

        self.emit_progress("Chain execution complete", 1.0)

        return OrchestrationResult(
            conversation=conv,
            final_output=current_output,
            consensus_reached=True,
            iterations=len(models),
            model_contributions={m: 1 for m in models},
            quality_score=0.85,
        )

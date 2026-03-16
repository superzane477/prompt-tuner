from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .client import AIClient, ChatMessage, ChatResponse


@dataclass
class TaskConfig:
    task: str
    input_text: str
    models: list[str]
    prompts: list[str]
    criteria: list[str] = field(default_factory=lambda: ["relevance", "conciseness", "accuracy"])
    judge_models: list[str] = field(default_factory=list)
    exclude_self_judge: bool = True
    weights: dict[str, float] = field(default_factory=dict)


@dataclass
class RunResult:
    prompt: str
    model: str
    output: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


def load_task(path: str | Path) -> TaskConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)
    scoring = raw.get("scoring", {})
    raw_judge = scoring.get("judge_models", scoring.get("judge_model", []))
    if isinstance(raw_judge, str):
        judge_models = [raw_judge] if raw_judge else []
    else:
        judge_models = raw_judge
    return TaskConfig(
        task=raw.get("task", "unnamed"),
        input_text=raw.get("input", ""),
        models=raw.get("models", []),
        prompts=raw.get("prompts", []),
        criteria=scoring.get("criteria", ["relevance", "conciseness", "accuracy"]),
        judge_models=judge_models,
        exclude_self_judge=scoring.get("exclude_self_judge", True),
        weights=scoring.get("weights", {}),
    )


class PromptRunner:
    def __init__(self, client: AIClient):
        self.client = client

    def run(self, config: TaskConfig, model_override: list[str] | None = None) -> list[RunResult]:
        models = model_override or config.models
        results: list[RunResult] = []
        for prompt_template in config.prompts:
            full_prompt = f"{prompt_template}\n\n{config.input_text}" if config.input_text else prompt_template
            for model in models:
                messages = [ChatMessage(role="user", content=full_prompt)]
                resp = self.client.chat(model, messages)
                results.append(RunResult(
                    prompt=prompt_template,
                    model=model,
                    output=resp.content,
                    prompt_tokens=resp.prompt_tokens,
                    completion_tokens=resp.completion_tokens,
                ))
        return results

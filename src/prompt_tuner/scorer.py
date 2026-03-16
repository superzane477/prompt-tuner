from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field

from .client import AIClient, ChatMessage
from .runner import RunResult


@dataclass
class Score:
    prompt: str
    model: str
    criteria_scores: dict[str, float]
    rule_scores: dict[str, float]
    judge_details: dict[str, dict[str, float]] = field(default_factory=dict)
    total: float = 0.0


def score_by_rules(result: RunResult) -> dict[str, float]:
    scores: dict[str, float] = {}
    text = result.output

    length = len(text)
    if 50 <= length <= 2000:
        scores["length"] = 8.0
    elif length < 50:
        scores["length"] = 4.0
    else:
        scores["length"] = 6.0

    bullet_count = len(re.findall(r"^[\-\*\d+\.]", text, re.MULTILINE))
    scores["structure"] = min(10.0, bullet_count * 2.0) if bullet_count > 0 else 3.0

    sentences = [s.strip() for s in re.split(r"[.!?。！？]\s*", text) if s.strip()]
    n = len(sentences)
    if n <= 1:
        scores["completeness"] = 4.0
    elif n <= 5:
        scores["completeness"] = 7.0
    else:
        scores["completeness"] = 9.0

    words = text.lower().split()
    if len(words) >= 6:
        trigrams = [" ".join(words[i:i+3]) for i in range(len(words) - 2)]
        counts = Counter(trigrams)
        repeated = sum(c - 1 for c in counts.values() if c > 1)
        ratio = repeated / len(trigrams) if trigrams else 0
        scores["repetition"] = max(3.0, round(10.0 - ratio * 30, 1))
    else:
        scores["repetition"] = 7.0

    fmt_score = 3.0
    if re.search(r"```", text):
        fmt_score += 2.0
    if re.search(r"\*\*.+?\*\*", text):
        fmt_score += 1.5
    if re.search(r"^#{1,3}\s", text, re.MULTILINE):
        fmt_score += 1.5
    scores["formatting"] = min(8.0, fmt_score)

    return scores


def score_by_ai(
    client: AIClient,
    judge_model: str,
    result: RunResult,
    criteria: list[str],
    input_text: str = "",
    prompt_text: str = "",
) -> dict[str, float]:
    criteria_str = ", ".join(criteria)

    parts = ["You are evaluating an AI's response to a task."]
    if input_text:
        parts.append(f"Original task/input:\n{input_text}")
    if prompt_text:
        parts.append(f"Prompt used:\n{prompt_text}")
    parts.append(f"AI output to rate:\n{result.output}")
    parts.append(
        f"Rate the output on a scale of 1-10 for each criterion: {criteria_str}.\n"
        f"Return ONLY a JSON object with criterion names as keys and numeric scores as values."
    )
    prompt = "\n\n".join(parts)

    resp = client.chat(judge_model, [ChatMessage(role="user", content=prompt)])

    try:
        match = re.search(r"\{[^}]+\}", resp.content)
        if match:
            parsed = json.loads(match.group())
            return {k: float(v) for k, v in parsed.items() if isinstance(v, (int, float))}
    except (json.JSONDecodeError, ValueError):
        pass
    return {c: 5.0 for c in criteria}


def _average_criteria(all_scores: list[dict[str, float]], criteria: list[str]) -> dict[str, float]:
    if not all_scores:
        return {c: 5.0 for c in criteria}
    result: dict[str, float] = {}
    for c in criteria:
        vals = [s[c] for s in all_scores if c in s]
        result[c] = sum(vals) / len(vals) if vals else 5.0
    return result


def _weighted_total(
    criteria_scores: dict[str, float],
    rule_scores: dict[str, float],
    weights: dict[str, float] | None,
    criteria: list[str],
) -> float:
    all_scores = {**rule_scores, **criteria_scores}
    if not all_scores:
        return 0.0

    if weights:
        w_sum = 0.0
        v_sum = 0.0
        for key, val in all_scores.items():
            w = weights.get(key, 1.0)
            w_sum += w
            v_sum += val * w
        return round(v_sum / w_sum, 2) if w_sum else 0.0

    rule_keys = set(rule_scores.keys())
    w_sum = 0.0
    v_sum = 0.0
    for key, val in all_scores.items():
        w = 1.0 if key in rule_keys else 2.0
        w_sum += w
        v_sum += val * w
    return round(v_sum / w_sum, 2) if w_sum else 0.0


class Scorer:
    def __init__(self, client: AIClient | None = None):
        self.client = client

    def score(
        self,
        results: list[RunResult],
        criteria: list[str],
        judge_models: list[str] | None = None,
        exclude_self_judge: bool = True,
        weights: dict[str, float] | None = None,
        input_text: str = "",
    ) -> list[Score]:
        judge_models = judge_models or []
        scores: list[Score] = []

        for r in results:
            rule_scores = score_by_rules(r)
            judge_details: dict[str, dict[str, float]] = {}

            if self.client and judge_models:
                eligible_judges = [
                    j for j in judge_models if not (exclude_self_judge and j == r.model)
                ]
                if not eligible_judges:
                    eligible_judges = judge_models

                for judge in eligible_judges:
                    judge_details[judge] = score_by_ai(
                        self.client, judge, r, criteria,
                        input_text=input_text, prompt_text=r.prompt,
                    )

                criteria_scores = _average_criteria(list(judge_details.values()), criteria)
            else:
                criteria_scores = {c: 5.0 for c in criteria}

            total = _weighted_total(criteria_scores, rule_scores, weights, criteria)

            scores.append(Score(
                prompt=r.prompt,
                model=r.model,
                criteria_scores=criteria_scores,
                rule_scores=rule_scores,
                judge_details=judge_details,
                total=total,
            ))
        return scores

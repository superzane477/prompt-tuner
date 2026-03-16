from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .runner import RunResult
from .scorer import Score


def print_report(
    scores: list[Score],
    results: list[RunResult] | None = None,
    console: Console | None = None,
):
    console = console or Console()

    prompts = sorted(set(s.prompt for s in scores))
    models = sorted(set(s.model for s in scores))

    result_map = {}
    if results:
        result_map = {(r.prompt, r.model): r for r in results}

    score_map = {(s.prompt, s.model): s for s in scores}
    best_total = max(s.total for s in scores) if scores else 0

    table = Table(title="Prompt Tuner Results", show_lines=True)
    table.add_column("Prompt", style="cyan", max_width=40)
    for m in models:
        table.add_column(m, justify="center")

    for prompt in prompts:
        row = [prompt[:40]]
        for model in models:
            s = score_map.get((prompt, model))
            if s:
                marker = " [bold green]*[/]" if s.total == best_total else ""
                row.append(f"{s.total:.1f}{marker}")
            else:
                row.append("-")
        table.add_row(*row)

    console.print(table)

    if scores:
        best = max(scores, key=lambda s: s.total)
        console.print(f"\n[bold green]Best combo:[/] {best.prompt[:60]} + {best.model} (score: {best.total})")

    console.print("\n[bold]===== Detail Breakdown =====[/]\n")

    for idx, s in enumerate(scores, 1):
        header = f"[{idx}] {s.prompt[:50]} | {s.model} | total: {s.total}"
        lines: list[str] = []

        r = result_map.get((s.prompt, s.model))
        if r:
            output_preview = r.output[:300]
            if len(r.output) > 300:
                output_preview += " ..."
            lines.append(f"[bold]Output:[/]\n{output_preview}\n")

        if s.criteria_scores:
            parts = [f"{k}={v:.1f}" for k, v in s.criteria_scores.items()]
            lines.append(f"[bold]AI Scores:[/]  {', '.join(parts)}")

        if s.judge_details:
            for judge, jscores in s.judge_details.items():
                jparts = [f"{k}={v:.1f}" for k, v in jscores.items()]
                lines.append(f"  judge [{judge}]: {', '.join(jparts)}")

        if s.rule_scores:
            parts = [f"{k}={v:.1f}" for k, v in s.rule_scores.items()]
            lines.append(f"[bold]Rule Scores:[/] {', '.join(parts)}")

        border = "green" if s.total == best_total else "dim"
        console.print(Panel("\n".join(lines), title=header, border_style=border))


def export_json(scores: list[Score], results: list[RunResult] | None, path: str | Path):
    result_map = {}
    if results:
        result_map = {(r.prompt, r.model): r for r in results}

    data = []
    for s in scores:
        entry = {
            "prompt": s.prompt,
            "model": s.model,
            "criteria_scores": s.criteria_scores,
            "rule_scores": s.rule_scores,
            "judge_details": s.judge_details,
            "total": s.total,
        }
        r = result_map.get((s.prompt, s.model))
        if r:
            entry["output"] = r.output
            entry["prompt_tokens"] = r.prompt_tokens
            entry["completion_tokens"] = r.completion_tokens
        data.append(entry)

    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False))

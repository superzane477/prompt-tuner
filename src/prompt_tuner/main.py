from __future__ import annotations

import argparse
import sys

from .client import AIClient
from .runner import PromptRunner, load_task
from .scorer import Scorer
from .reporter import print_report, export_json


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(prog="prompt-tuner", description="Iterate prompts across AI models, score outputs, find the best version")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run a prompt tuning task from a YAML config")
    run_p.add_argument("config", help="Path to YAML task config")
    run_p.add_argument("--models", help="Comma-separated model IDs to override config")
    run_p.add_argument("--output", "-o", help="Export results to JSON file")
    run_p.add_argument("--api-key", help="API key (overrides env)")
    run_p.add_argument("--base-url", help="API base URL (overrides env)")
    run_p.add_argument("--no-ai-scoring", action="store_true", help="Skip AI-based scoring, use rules only")

    models_p = sub.add_parser("models", help="List available models from the API")
    models_p.add_argument("--api-key", help="API key (overrides env)")
    models_p.add_argument("--base-url", help="API base URL (overrides env)")

    args = parser.parse_args(argv)

    if args.command == "run":
        config = load_task(args.config)
        model_override = args.models.split(",") if args.models else None

        with AIClient(api_key=args.api_key, base_url=args.base_url) as client:
            runner = PromptRunner(client)
            results = runner.run(config, model_override=model_override)

            scorer_client = None if args.no_ai_scoring else client
            scorer = Scorer(client=scorer_client)
            scores = scorer.score(
                results, config.criteria, config.judge_models,
                config.exclude_self_judge, weights=config.weights or None,
                input_text=config.input_text,
            )

        print_report(scores, results)
        if args.output:
            export_json(scores, results, args.output)
            print(f"\nResults exported to {args.output}")

    elif args.command == "models":
        with AIClient(api_key=args.api_key, base_url=args.base_url) as client:
            models = client.fetch_models()
        for m in models:
            print(f"  {m.id:30s}  {m.name:30s}  ({m.provider})")
        if not models:
            print("No models found.")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

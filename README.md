# Prompt Tuner

A CLI tool that iterates a prompt across multiple AI models, scores the outputs, and suggests the best prompt version.

## Features

- **Multi-Model Testing**: Run the same prompt variants across different AI models in one go
- **Automated Scoring**: AI-based + rule-based scoring on criteria you define (relevance, conciseness, accuracy, etc.)
- **YAML Task Configs**: Define tasks, prompts, models, and scoring criteria in simple YAML files
- **Rich Terminal Output**: Color-coded score matrix with the best prompt+model combo highlighted
- **JSON Export**: Save full results for further analysis

## Compatible API Providers

Works with any service that supports the OpenAI Chat Completions format:

| Provider | Base URL |
|----------|----------|
| OpenRouter | `https://openrouter.ai/api/v1` |
| ZenMux | `https://zenmux.com/api/v1` |
| OpenAI | `https://api.openai.com/v1` |
| Any OpenAI-compatible | `https://your-provider/v1` |

## Install

```bash
cd prompt-tuner
pip install -e ".[dev]"
```

## Setup

Copy `env.example` to `.env` and fill in your credentials:

```bash
cp env.example .env
```

| Variable | Description |
|----------|-------------|
| `API_KEY` | Your API key |
| `API_BASE_URL` | API base URL (e.g. `https://openrouter.ai/api/v1`) |

## Usage

### Run a prompt tuning task

```bash
prompt-tuner run examples/summarize.yaml
```

### Override models from CLI

```bash
prompt-tuner run examples/summarize.yaml --models gpt-5-mini,gemini-3-flash
```

### Export results to JSON

```bash
prompt-tuner run examples/summarize.yaml -o report.json
```

### List available models

```bash
prompt-tuner models
```

### Skip AI scoring (rules only)

```bash
prompt-tuner run examples/summarize.yaml --no-ai-scoring
```

## Task Config Format

```yaml
task: summarize
input: "Your input text here..."
models:
  - gpt-5-mini
  - gemini-3-flash
prompts:
  - "Summarize the following text in 3 bullet points:"
  - "TL;DR the following:"
  - "Give me the key takeaways from:"
scoring:
  criteria: [relevance, conciseness, accuracy]
  judge_model: gpt-5-mini
```

## Architecture

```
prompt-tuner run task.yaml
        │
        ▼
   ┌─────────────┐
   │ PromptRunner │─── reads YAML config
   └──────┬──────┘
          │  for each (prompt × model):
          ▼
   ┌─────────────┐
   │  AIClient    │─── POST /chat/completions
   └──────┬──────┘
          │  collect outputs
          ▼
   ┌─────────────┐
   │   Scorer     │─── AI scoring + rule scoring
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  Reporter    │─── Rich table + JSON export
   └─────────────┘
```

### File Structure

```
src/prompt_tuner/
├── main.py       # CLI entry point (argparse)
├── client.py     # AI API client (httpx, OpenAI-compatible)
├── runner.py     # Core logic: iterate prompt variants × models
├── scorer.py     # Output scoring (AI + rules)
└── reporter.py   # Results output (Rich table + JSON)
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT

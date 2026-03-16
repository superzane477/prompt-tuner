# Reddit Post Draft

**Subreddit**: r/LocalLLaMA
**Persona**: Indie hacker
**Style**: Casual "I built X"

---

**Title**: I built a CLI tool to A/B test prompts across multiple models — here's what I found

**Body**:

So I've been going back and forth between GPT-5-mini and Gemini 3 Flash for a side project, and I kept running into the same problem: a prompt that works great on one model completely falls apart on another.

Instead of manually copy-pasting prompts into different playgrounds, I threw together a small Python CLI that automates the whole thing. You write a YAML config with your prompt variants and target models, and it:

1. Runs every prompt × model combination
2. Scores each output (mix of rule-based checks and having another model judge the quality)
3. Spits out a nice terminal table showing which prompt+model combo won

Example config:

```yaml
task: summarize
input: "your long article here..."
models:
  - gpt-5-mini
  - gemini-3-flash
prompts:
  - "Summarize in 3 bullet points:"
  - "TL;DR:"
  - "Key takeaways:"
scoring:
  criteria: [relevance, conciseness]
  judge_model: gpt-5-mini
```

Some things I noticed after running it on ~20 different tasks:

- **Gemini 3 Flash** is surprisingly good at structured outputs (bullet points, numbered lists). It almost always scored higher on "conciseness" than GPT-5-mini.
- **GPT-5-mini** tends to be more verbose but catches nuances that Flash misses. For tasks requiring reasoning, it pulled ahead.
- The phrasing difference between "Summarize in 3 bullet points:" vs "TL;DR:" was bigger than I expected — sometimes 2-3 points difference on a 10-point scale.
- Having the AI judge its own output is... imperfect. I added rule-based scoring (length checks, structure detection) as a sanity check and it helps a lot.

The tool uses any OpenAI-compatible API, so it works with OpenRouter, direct OpenAI, or whatever provider you prefer. Just set your base URL and API key in a `.env` file.

It's pretty bare-bones right now but it's saved me a ton of time. Happy to open source it if there's interest.

**What prompts have you found work dramatically differently across models?**

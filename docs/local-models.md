# Choosing a local model

You can run the whole agent, or just the quiet background jobs, on a model that lives on your own machine: free forever, private, and working offline. This guide helps you pick one your computer can actually run.

**First stop: [canirun.ai](https://canirun.ai).** It reads your GPU or Mac straight from the browser, ranks the open models that fit your machine, and gives you the exact Ollama or LM Studio command for your pick. No account needed.

Two more worth knowing:

- [localllm-advisor.com](https://localllm-advisor.com) works both directions: best models for your hardware, or hardware for a model you want. Fully client-side.
- [localllm.run](https://localllm.run) walks goal, hardware, model and setup in order, with agent-use guides.

## What agent work asks of a model

The agent runs tools: it maintains your Day Board, drafts scripts, tracks appointments, keeps your routines. That puts three demands on a local model:

1. **Tool calling.** It must support function calling, or the agent cannot act. This beats raw size every time: a 14B with solid tool calling outperforms a 32B without it.
2. **Instruction following.** Your profile rules (tone, pacing ceiling, the never lists) only hold if the model follows instructions properly.
3. **Enough context.** The agent reads your profile. Look for 32k context or more.

Every pick below supports tool calling. Models move fast, so treat this as a starting shortlist and let the checkers rank what is current.

## The tiers

| Your machine | Start with (Ollama tag) | Also good |
|---|---|---|
| Modest laptop, 8 to 16 GB RAM, no dedicated GPU | `qwen3:8b` | `llama3.2:3b` on 8 GB machines |
| Capable machine, 16 to 32 GB RAM or 8 to 12 GB VRAM | `qwen3:14b` | `phi4:14b` |
| Strong machine, 32 GB+ RAM or 16 to 24 GB VRAM | `gpt-oss:20b` | `qwen3:30b-a3b` |
| Workstation, 64 GB+ RAM or 24 GB+ VRAM | `llama3.3:70b` | `gpt-oss:120b` |

All of these run in both Ollama and LM Studio. Mixture-of-experts models like `gpt-oss:20b` are fast for their size but still load all their weights, so trust the checkers on memory rather than parameter count.

## Getting one running

1. **Install the engine.** [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai), then pull or download a tag from the table.
2. **Point the agent at it.** Both serve an OpenAI-compatible endpoint on your machine: Ollama at `http://localhost:11434/v1`, LM Studio at `http://localhost:1234/v1`. Set the provider in `hermes setup` or your config, and see the [Hermes docs](https://hermes-agent.nousresearch.com/docs) for the exact keys in your version.
3. **Try it on one job.** Run a single scheduled task or a short conversation on the local model first, then widen as far as you like. Hermes can run each scheduled job on its own model, so mixing local and frontier is easy.

## Which jobs suit a local model

- **Great fit:** scheduled check-ins, routine nudges, short conversations, note taking. Simple by design.
- **Better on a bigger model:** complex planning, long drafting sessions, anything tangled. Reach for a frontier model occasionally and keep the rest local.
- **The all-local setup:** a capable machine plus a good local model plus local voice (Piper and faster-whisper, see [models.md](models.md)) keeps everything on your machine, always.

## Power tools, for the technically curious

- **whichllm** (`uvx whichllm`) ranks models from live Hugging Face data using real benchmarks. [github.com/Andyyyy64/whichllm](https://github.com/Andyyyy64/whichllm)
- **llm-checker** (`npx llm-checker hw-detect`) detects hardware, scores models, and can test tool-calling compatibility. [github.com/rumplestilzken/llm-checker](https://github.com/rumplestilzken/llm-checker)
- **llmfit** detects your specs and recommends fits with quantisation and speed estimates. [github.com/AlexsJones/llmfit](https://github.com/AlexsJones/llmfit)

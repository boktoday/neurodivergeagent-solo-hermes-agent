# Starter artifacts

| Artifact | What it is | Best for |
|---|---|---|
| `day-board.html` | One-screen daily board: today's three, meds, energy meter, meals, wins, notes. Saves per day, exports CSV, prints | Daily anchoring, therapy prep, showing patterns to someone |
| `lesson-chunks.html` | Local-first lesson planner: paste or dictate a lesson, AI breaks it into small sequential steps + a motivating overview. Text-to-speech, mark-complete, rich-text editor per step, AI feedback, saved Q&A history | Turning courses, study material, work training or therapy content into manageable steps; executive-function support |

## How to deliver one

1. Open it, personalise (med names, colours, the person's own words).
2. Send the file, or paste it as a page if they use a sharing space.
3. Three things to explain: how it saves, how to export, that print is the fallback.
4. Review after two weeks together; retire it freely if it is not earning its place.

## Instructions: `lesson-chunks.html`

**What it does.** You paste (or dictate, in Chrome/Edge) a lesson — one paragraph or a whole page. It uses an LLM (via OpenRouter, your own key) to produce a short encouraging overview and break the content into the smallest sequential steps. Work through the steps one at a time: mark a step complete, listen to it read aloud, expand any step to write a response in the built-in editor, get AI feedback on the response, and ask follow-up questions that are saved to history.

**Runs locally.** One self-contained file — no install, no account, no cloud storage. Open it with a double-click in any browser (Chrome, Edge, Firefox). All lessons and settings save in the browser's own storage on that computer. To move to another device, open the file there and re-enter content, or use **Copy** in the lesson view to export the overview + steps as Markdown.

**First-time setup (one minute).**

1. Open the file. Go to **Settings** (top right).
2. Optional: add your name, bio and learning style — this personalises how the steps are written.
3. Add an **OpenRouter API key** (free account at openrouter.ai/keys; cheap or free models work). This is the only thing that needs the internet — it sends the lesson text to the AI to chunk it, plus your questions.
4. Pick a preferred model if you like. **Save Settings.**

**Daily use.**

1. **Home:** type or dictate the lesson plan (dictation needs Chrome/Edge and a mic). Title is optional.
2. Click **Chunk Lesson**. Wait a few seconds. You get an Overview plus numbered steps.
3. Work through the steps: speaker icon reads a step aloud, check circle marks it done, chevron expands a step for writing + feedback, **Copy** exports the whole lesson as Markdown.
4. Ask questions in **Ask a Question** below the steps — answers are saved.
5. **Lessons** lists everything saved, **History** searches past Q&A by date.

**Privacy note.** The lesson content you paste is sent to the OpenRouter model only when you click Chunk Lesson or ask a question. Everything else — saved lessons, settings, history — stays on the device in the browser. Don't paste anything more sensitive than you would put in a school email.

## Contributing

New artifacts belong here when they are: local (no account, no cloud), one file, printable, and useful beyond the person they were built for. A week planner, RSD grounding card and med tracker are welcome next.

# The Individual Agent (NeuroDivergeAgent)

A free support team for one neurodivergent adult. Built on **[Hermes Agent](https://hermes-agent.nousresearch.com/docs)**, private by design, strengths-based, neurodiversity-affirming.

**Companion product:** the Family Agent (`boktoday/neurofamily-hermes-agent`) for families raising neurodiverse children. Both free. Showcase: https://neurodivergeagent.com

---

## What this is

Eleven specialist skills that work as one team around your life: a front-door Compass that knows you, an executive function coach, a sensory architect, an energy and burnout guardian, a work advocate, a money and admin ally, and more. They share one picture of you (your own folder of plain readable files), so nothing has to be explained twice.

Think of it as the support team a late-diagnosed adult never got: practical, honest about capacity, allergic to cures and toxic productivity.

---

## The team

| Skill | Focus |
|---|---|
| Compass | Front door, your profile, routing, the weekly review |
| Executive Function Coach | Task initiation, time, planning, systems that actually hold |
| Sensory Architect | Your sensory world: environment, regulation, recovery |
| Energy and Burnout Guardian | Energy accounting, masking cost, burnout warning and recovery |
| Work Advocate | Accommodation asks, disclosure decisions, scripts, meeting prep |
| Money and Admin Ally | Bills, forms, subscriptions, appointment admin, the pile |
| Routine Builder | Gentle anchors: mornings, evenings, meds, sleep |
| Emotion Regulation Coach | Big feelings, RSD, meltdown and shutdown recovery |
| Connection Coach | Friendships, family, social energy, finding your people |
| Health Appointments | Appointment prep, symptom notes, med routines |
| Toolsmith | Local trackers, dashboards, printables, mini-apps |

---

## How it works

1. **One folder.** Everything lives in `~/myfolder/` (rename it whatever you like): profile, energy log, wins, work notes. Plain files, yours.
2. **One front door.** Compass builds your profile first: strengths, sensory world, energy patterns, what has failed before. Then it routes.
3. **Schedules that respect energy.** Optional check-ins: morning anchors, evening shutdown, weekly review, monthly energy audit. All pausable with one sentence.
4. **Local first.** Runs fully offline with local models (see `docs/local-models.md` to pick one that fits your machine). Calendar and mail connections are optional and read-first.
5. **Hard rails.** Not therapy, not medical, legal or financial advice. Crises route to humans. See `SOUL.md`.

---

## Install

See `INSTALL.md`. Short version: install Hermes, copy the skills into your profile, run the folder setup script, talk to Compass.

---

## Starter artifacts

One-file tools in `templates/artifacts/` that Toolsmith can hand you, tailored to your life. They run locally in any browser — no account, no cloud, no install. Full instructions live in `templates/artifacts/README.md`.

| Artifact | What it is | When to use it |
|---|---|---|
| `day-board.html` | One-screen daily board: today's three, meds, energy meter, meals, wins, notes. Saves per day, exports CSV, prints | Daily anchoring, therapy prep, showing patterns to someone |
| `lesson-chunks.html` | Local-first lesson planner: paste or dictate a lesson, AI breaks it into small sequential steps + an encouraging overview. Text-to-speech, mark-complete, rich-text editor per step, AI feedback, saved Q&A history | Turning courses, work training or therapy content into manageable steps; executive-function support |

Quick start for either: open the file in Chrome/Edge/Firefox, use it, it saves itself. For **lesson-chunks.html**, add a free OpenRouter API key in its Settings once — that is the only internet call, and it only touches the content when you click Chunk Lesson or ask a question.

---

## Licence

PolyForm Noncommercial 1.0.0. Free to download, free to use for yourself, with credit. See `LICENSE`.

Required Notice: Copyright 2026 Brendan O'Keefe (https://neurodivergeagent.com)

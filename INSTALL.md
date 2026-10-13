# Installing the Individual Agent

## What you need

- A laptop or desktop (any modern machine)
- Hermes Agent: https://hermes-agent.nousresearch.com/docs
- 30 minutes, and a free model key (or local models for fully offline)

## Steps

1. **Get this repo.**
   ```
   git clone https://github.com/boktoday/neurodivergeagent-solo-hermes-agent.git
   ```

2. **Install Hermes** following the official quick start until `hermes --version` works.

3. **Create a profile and copy in the skills.**
   ```
   hermes profile create me
   cp -r ndagent-solo-hermes-agent/skills/* <profiles-dir>/me/skills/
   cp ndagent-solo-hermes-agent/config.yaml <profiles-dir>/me/config.yaml   # optional example
   ```
   `<profiles-dir>` is your Hermes profiles directory (Windows: `%LOCALAPPDATA%\hermes\profiles\`).

4. **Set up your folder.**
   ```
   python ndagent-solo-hermes-agent/scripts/setup-my-folder.py
   ```
   This creates `~/myfolder/` with the templates. Rename or add `--target` if you prefer another spot.

5. **Add a model.** Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` (free and cheap models available), or point at local models (LM Studio / Ollama; see `docs/models.md`).

6. **First conversation.** Say to Compass: "Let's build my profile." It takes about 20 minutes, in one or several sittings, and everything after gets better for it.

## Optional: WhatsApp or Telegram

Talk to the team from your phone: a WhatsApp bot (personal use, `hermes whatsapp` with QR pairing) or a Telegram bot. Voice notes work both ways with local whisper + Piper (see `docs/models.md`).

## Optional: connections

Calendar and mail via Maton (Google or Microsoft), read-first, writes need your yes in the moment. See `docs/connections.md`.

## Schedules

Four optional check-ins in `schedules/`: morning anchors, evening shutdown, weekly review, monthly energy audit. Each file has the exact setup. Run them on a local model to keep them free and private.

## Updating

`git pull` and re-copy `skills/`. `CHANGELOG.md` tracks what changed.

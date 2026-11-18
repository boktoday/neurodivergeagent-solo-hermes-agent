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

3. **Run the installer.**
   ```
   cd neurodivergeagent-solo-hermes-agent
   python scripts/install.py
   ```
   That copies every skill into your Hermes profile and builds your personal folder in one step. It prints the exact paths it used. Useful flags: `--profile <name>` if you do not want the default `me`, `--folder <path>` if `~/myfolder` is not where you want it, `--dry-run` to see the plan first, and `--force-config` if you want the example `config.yaml` to replace one you already have.

   Prefer to do it by hand? The equivalent is:
   ```
   hermes profile create me
   cp -r skills/* <profiles-dir>/me/skills/
   cp config.yaml <profiles-dir>/me/config.yaml   # optional example
   python scripts/setup-my-folder.py
   ```
   `<profiles-dir>` is your Hermes profiles directory (Windows: `%LOCALAPPDATA%\hermes\profiles\`, Linux and macOS: `~/.local/share/hermes/profiles/`).

4. **Check your folder.** `python scripts/setup-my-folder.py` creates `~/myfolder/` with the templates. It is safe to run twice: it never overwrites a file you have written in. Pass `--target` for a different spot.

5. **Add a model.** Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` (free and cheap models available), or point at local models (LM Studio / Ollama; see `docs/models.md`).

6. **First conversation.** Say to Compass: "Let's build my profile." It takes about 20 minutes, in one or several sittings, and everything after gets better for it.

## Optional: WhatsApp or Telegram

Talk to the team from your phone: a WhatsApp bot (personal use, `hermes whatsapp` with QR pairing) or a Telegram bot. Voice notes work both ways with local whisper + Piper (see `docs/models.md`).

## Optional: connections

Calendar and mail via Maton (Google or Microsoft), read-first, writes need your yes in the moment. See `docs/connections.md`.

## Schedules

Four optional check-ins in `schedules/`: morning anchors, evening shutdown, weekly review, monthly energy audit. Each file has the exact setup. Run them on a local model to keep them free and private.

## Updating

`git pull`, then re-run `python scripts/install.py` to refresh the skills in your profile. Your folder and your config are left untouched. `CHANGELOG.md` tracks what changed.

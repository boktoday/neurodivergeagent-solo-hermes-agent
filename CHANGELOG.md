# Changelog

## [1.1.0] - 2026-10-15

### Added
- **NDIS Guide** (`skills/ndis-guide/`): Australian NDIS navigation, backed by a shipped library of 59 current official documents in `shared/ndis/`: all operational guideline documents, the consolidated NDIS Act 2013 (as at 1 October 2026), the (Supports for Participants) Rules, the pricing schedule 2026-27, and the 2026 law-change briefings. Answers quote the documents with source and date, never model memory.
- **`scripts/fetch-ndis-docs.py`**: one-command refresh of the NDIS library.

---

## [Unreleased]

### Added
- **`scripts/ndis_watch.py`** and **`schedules/ndis-watch.md`**: a fortnightly watch over ten official NDIS sources plus the whole shipped library. Silent when nothing has moved; writes `shared/ndis/changes/<date>.md` when a source changes, and `--refresh` pulls the latest library. Blocked pages keep their previous hash.

---

## [1.0.0] - 2026-10-14

### Added
- First release of the Individual Agent: eleven specialist skills (Compass, Executive Function Coach, Sensory Architect, Energy and Burnout Guardian, Work Advocate, Money and Admin Ally, Routine Builder, Emotion Regulation Coach, Connection Coach, Health Appointments, Toolsmith).
- Shared folder system with templates: profile, energy log, wins, work notes, health notes, connections, crisis card.
- Four schedules: morning anchors, evening shutdown, weekly review, monthly energy audit.
- Day Board starter artifact: a local-first daily dashboard (tasks, meds, energy, meals, wins).
- Docs: connections (Maton), models and voice (DeepSeek Flash default, local models for schedules, Piper + whisper voice).
- Companion of the Family Agent (boktoday/neurofamily-hermes-agent). Both free.

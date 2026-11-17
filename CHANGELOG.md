# Changelog

## [1.1.0] - 2026-10-15

### Added
- **NDIS Guide** (`skills/ndis-guide/`): Australian NDIS navigation, backed by a shipped library of 59 current official documents in `shared/ndis/`: all operational guideline documents, the consolidated NDIS Act 2013 (as at 1 October 2026), the (Supports for Participants) Rules, the pricing schedule 2026-27, and the 2026 law-change briefings. Answers quote the documents with source and date, never model memory.
- **`scripts/fetch-ndis-docs.py`**: one-command refresh of the NDIS library.

---

## [Unreleased]

### Added
- **ADHD Tax Shield** (`skills/adhd-tax-shield/`): the acute end of life admin, deliberately split from Money and Admin Ally, which keeps the standing system. Three pieces: a three-line scary-mail de-escalator (is anything actually happening right now, the single action and its date, an offer of two 90-second steps), a trial and renewal register that reminds five days early and records the direct cancellation path, and a four-sentence waiver and extension drafter that asks without grovelling and without disclosing a diagnosis. Not financial, tax or legal advice; severe debt distress goes to the National Debt Helpline on 1800 007 007.
- **`scripts/ndis_watch.py`** and **`schedules/ndis-watch.md`**: a fortnightly watch over ten official NDIS sources plus the whole shipped library. Silent when nothing has moved; writes `shared/ndis/changes/<date>.md` when a source changes, and `--refresh` pulls the latest library. Blocked pages keep their previous hash.

### Fixed
- **`ndis-guide` was never fully registered.** It shipped in 1.1.0 as the twelfth skill, but `AGENTS.md` still said eleven skills, the routing table had no row for it, and none of the twelve per-skill team lists mentioned it. All thirteen team lists, the routing table and both counts now agree.

---

## [1.0.0] - 2026-10-14

### Added
- First release of the Individual Agent: eleven specialist skills (Compass, Executive Function Coach, Sensory Architect, Energy and Burnout Guardian, Work Advocate, Money and Admin Ally, Routine Builder, Emotion Regulation Coach, Connection Coach, Health Appointments, Toolsmith).
- Shared folder system with templates: profile, energy log, wins, work notes, health notes, connections, crisis card.
- Four schedules: morning anchors, evening shutdown, weekly review, monthly energy audit.
- Day Board starter artifact: a local-first daily dashboard (tasks, meds, energy, meals, wins).
- Docs: connections (Maton), models and voice (DeepSeek Flash default, local models for schedules, Piper + whisper voice).
- Companion of the Family Agent (boktoday/neurofamily-hermes-agent). Both free.

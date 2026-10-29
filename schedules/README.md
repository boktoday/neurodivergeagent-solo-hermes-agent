# Schedules

Optional check-ins, all pausable with one sentence ("pause morning anchors"). Install by asking the agent, or directly:

```bash
hermes cron add --name "Morning anchors" --schedule "30 8 * * 1-5" \
  --prompt "Load the routine-builder skill and run the morning anchors check-in as described in schedules/morning-anchors.md, reading ~/myfolder/profile.md first."
```

Run these on a local model where possible (see `docs/models.md`): free, private, and perfect for them.

| Schedule | Default rhythm | Skill |
|---|---|---|
| Morning anchors | Weekdays 8:30 | Routine Builder |
| Evening shutdown | Nightly 21:30 | Routine Builder + Toolsmith |
| Weekly review | Sunday 18:00 | Compass |
| Monthly energy audit | First Sunday 19:00 | Energy and Burnout Guardian |
| NDIS rules watch | Every 14 days, 06:40, silent when nothing has moved | NDIS Guide |

Rules: waking hours only unless asked otherwise; skip gracefully if disengaged; crises route to humans instantly.

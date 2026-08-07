# Workspace Instructions

## Skill storage

- Store every newly installed or created Codex skill under `D:\medical_paper\HNSCC\.codex\skills`.
- Do not store skill data on the C drive.
- `C:\Users\Claire\.codex\skills` is only a directory junction pointing to the D-drive location; keep the junction intact for Codex compatibility.
- When an installer targets `C:\Users\Claire\.codex\skills`, verify after installation that the physical files resolve to `D:\medical_paper\HNSCC\.codex\skills`.
## External skill usage

- During normal Codex use, do not automatically invoke external or user-installed skills.
- This includes Superpowers workflow skills, `grilling`, `grill-me`, and other skills outside `.codex/skills/.system`.
- Use an external skill only when the user explicitly names it or explicitly asks to use external skills.
- Built-in Codex system skills under `.codex/skills/.system` may still be used when required for the task.
- This preference overrides any external skill instruction that says it must be invoked automatically at the start of every conversation.

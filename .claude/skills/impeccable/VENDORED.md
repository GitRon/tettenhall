# Vendored: impeccable

A copy of the `impeccable` skill, not code written for this project.

- **Source:** https://github.com/pbakaus/impeccable, folder `plugin/skills/impeccable`
- **Commit:** `114ea1d3838fca73b253af45f873b9c4f5f213c8` (plugin 4.4.0, engine 0.1.6)
- **License:** Apache 2.0, see `LICENSE` and `NOTICE.md`. The files are unmodified; this file is the
  only addition.

Only the skill is vendored. The plugin's `hooks/hooks.json` is left out on purpose: it runs the engine
binary at every session start, after every Edit or Write, and at every stop. Here the binary runs only
when a command asks for it, such as the detector inside `critique`. It is not committed: the launcher in
`scripts/` downloads it on first use into `~/.impeccable/`, checked against a `.sha256` sidecar.

The skill's own aesthetic defaults are not this project's. `docs/patterns/visual-identity.md` overrides
them; `AGENTS.md` says where the skill is and is not used.

## Updating

Copy `plugin/skills/impeccable` from a newer commit over this folder, keep this file, and bump the
commit above. Read the diff before committing: the folder is instructions an agent follows, which puts it
in the same review class as code.

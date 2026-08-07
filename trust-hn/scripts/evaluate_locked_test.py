"""Locked-test entry point. Actual model evaluation is added only after Phase 5 freeze."""

from __future__ import annotations

from trust_hn.governance import main

if __name__ == "__main__":
    raise SystemExit(main())
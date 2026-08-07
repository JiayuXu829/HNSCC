"""Build Phase 2 unified adapter records and governance-safe descriptive outputs."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trust_hn.data.phase2 import main


if __name__ == "__main__":
    raise SystemExit(main())

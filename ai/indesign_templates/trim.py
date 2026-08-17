from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai.contracts import validate_data


def load_trim_profile(path: Path, *, require_approved: bool = False) -> dict[str, Any]:
    profile = json.loads(Path(path).read_text(encoding="utf-8", errors="strict"))
    errors = validate_data(profile, "trim-profile")
    if errors:
        raise ValueError("invalid trim profile: " + "; ".join(errors))
    if require_approved and profile["status"] != "approved":
        raise ValueError(f"trim profile is not approved: {profile['trim_profile_id']}")
    return profile

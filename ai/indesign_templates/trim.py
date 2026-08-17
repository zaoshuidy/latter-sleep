from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai.contracts import load_and_validate


def load_trim_profile(path: Path, *, require_approved: bool = False) -> dict[str, Any]:
    try:
        profile = load_and_validate(Path(path), "trim-profile")
    except json.JSONDecodeError:
        raise
    except ValueError as exc:
        raise ValueError("invalid trim profile: " + str(exc).replace("\n", "; ")) from exc
    if require_approved and profile["status"] != "approved":
        raise ValueError(f"trim profile is not approved: {profile['trim_profile_id']}")
    return profile

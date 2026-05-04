"""Adapter: fg-data-profiling reports → ox-collab-api records.

A profiling report contains multiple "findings" (per-column stats, alerts, correlations).
We convert each notable finding into a record that researchers can vote and discuss.

Usage:
    # Generate a profile report and push findings as records
    python -m oasis-extensions.ox_collab_adapter \\
        --csv path/to/data.csv \\
        --collab-url http://localhost:8001 \\
        --dataset-name my-dataset

    # Or, if you already have a profile JSON:
    python -m oasis-extensions.ox_collab_adapter \\
        --profile-json path/to/profile.json \\
        --collab-url http://localhost:8001 \\
        --dataset-name my-dataset
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx


def load_profile(args: argparse.Namespace) -> dict[str, Any]:
    """Either load an existing profile JSON or generate one from a CSV."""
    if args.profile_json:
        return json.loads(Path(args.profile_json).read_text())

    if not args.csv:
        raise SystemExit("Provide either --profile-json or --csv")

    import pandas as pd
    from ydata_profiling import ProfileReport  # upstream import; same module after fork

    df = pd.read_csv(args.csv)
    report = ProfileReport(df, minimal=False, title=args.dataset_name)
    return report.to_json() if isinstance(report.to_json(), dict) else json.loads(report.to_json())


def findings_from_profile(profile: dict[str, Any], dataset_name: str) -> list[dict[str, Any]]:
    """Walk the profile dict and emit one Record per significant finding."""
    findings: list[dict[str, Any]] = []
    variables = profile.get("variables", {})

    for col_name, col in variables.items():
        # Per-column summary
        title = f"{col_name} — {col.get('type', 'unknown')}"
        body_lines = [
            f"- Type: `{col.get('type', '?')}`",
            f"- N missing: {col.get('n_missing', 0)} ({100 * col.get('p_missing', 0):.1f}%)",
            f"- N unique: {col.get('n_unique', 0)} ({100 * col.get('p_unique', 0):.1f}%)",
        ]
        if col.get("mean") is not None:
            body_lines.append(f"- Mean: {col.get('mean'):.4g}, Std: {col.get('std', 0):.4g}")

        findings.append({
            "source": "profiling",
            "source_id": f"{dataset_name}::col::{col_name}",
            "title": title[:255],
            "body": "\n".join(body_lines),
            "extra": {
                "dataset_name": dataset_name,
                "kind": "column_summary",
                "column": col_name,
                "stats": {k: v for k, v in col.items() if not isinstance(v, (list, dict))},
            },
        })

    # Alerts (high-priority findings)
    for alert in profile.get("alerts", []):
        if isinstance(alert, dict):
            kind = alert.get("alert_type", "alert")
            cols = alert.get("column_name") or alert.get("fields") or "?"
            findings.append({
                "source": "profiling",
                "source_id": f"{dataset_name}::alert::{kind}::{cols}",
                "title": f"⚠ {kind}: {cols}",
                "body": alert.get("description", str(alert)),
                "extra": {"dataset_name": dataset_name, "kind": "alert", "alert": alert},
            })

    return findings


def push_to_collab(records: list[dict[str, Any]], collab_url: str) -> tuple[int, int]:
    created = skipped = 0
    with httpx.Client(timeout=30.0, base_url=collab_url) as client:
        for rec in records:
            r = client.post("/records", json=rec, headers={"X-Anon-Name": "profiling-adapter"})
            if r.status_code == 201:
                created += 1
            elif r.status_code == 200:
                skipped += 1
            else:
                print(f"[warn] {r.status_code} for {rec['source_id']}: {r.text[:200]}", file=sys.stderr)
    return created, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", help="Path to a CSV file to profile")
    ap.add_argument("--profile-json", help="Path to an existing profile JSON")
    ap.add_argument("--collab-url", required=True)
    ap.add_argument("--dataset-name", required=True)
    args = ap.parse_args()

    profile = load_profile(args)
    print(f"[load] {len(profile.get('variables', {}))} columns, "
          f"{len(profile.get('alerts', []))} alerts")

    findings = findings_from_profile(profile, args.dataset_name)
    print(f"[map]  {len(findings)} findings")

    created, skipped = push_to_collab(findings, args.collab_url)
    print(f"[done] created={created} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

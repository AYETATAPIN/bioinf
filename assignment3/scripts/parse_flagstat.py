#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


MAPPED_RE = re.compile(r"^\s*\d+\s+\+\s+\d+\s+mapped\s+\(([\d.]+)%\s*:", re.IGNORECASE)


def parse_mapped_percent(text: str) -> float:
    for line in text.splitlines():
        match = MAPPED_RE.search(line)
        if match:
            return float(match.group(1))
    raise ValueError("Could not find mapped percentage in samtools flagstat output.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse mapped-read percentage from samtools flagstat output.")
    parser.add_argument("flagstat", type=Path, help="Path to samtools flagstat text file")
    parser.add_argument("--threshold", type=float, default=90.0, help="OK threshold in percent")
    parser.add_argument("--out", type=Path, default=None, help="Optional output file")
    args = parser.parse_args()

    percent = parse_mapped_percent(args.flagstat.read_text(encoding="utf-8", errors="replace"))
    status = "OK" if percent > args.threshold else "not OK"
    result = f"mapped_percent={percent:.2f}\nthreshold={args.threshold:.2f}\nstatus={status}\n"

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

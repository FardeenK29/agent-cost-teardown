"""Count Ollama model loads in a time window of the server log.

    python scripts/count_reloads.py /opt/homebrew/var/log/ollama.log 20:46:41 21:09:46

Every "starting llama-server" line is one model load. A healthy run loads each
model once; a run that alternates num_ctx for the same model reloads it on every switch.
"""

import re
import sys
from collections import Counter


def main(path: str, start: str, end: str) -> None:
    loads = Counter()
    for line in open(path, errors="ignore"):
        if 'msg="starting llama-server"' not in line:
            continue
        t = re.search(r"T(\d\d:\d\d:\d\d)", line)
        if not t or not (start <= t.group(1) < end):
            continue
        model = re.search(r"--model \S*sha256-([0-9a-f]{12})", line)
        ctx = re.search(r" -c (\d+)", line)
        loads[(model.group(1) if model else "?", ctx.group(1) if ctx else "?")] += 1
    print(f"{sum(loads.values())} model loads between {start} and {end}")
    for (blob, ctx), n in loads.most_common():
        print(f"  {n:4}  blob {blob}  num_ctx {ctx}")


if __name__ == "__main__":
    main(*sys.argv[1:4])

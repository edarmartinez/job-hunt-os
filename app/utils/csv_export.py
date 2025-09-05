import csv
from typing import Iterable, Dict

def iter_csv(rows: Iterable[Dict[str, object]]):
    # Header first
    first = True
    for row in rows:
        if first:
            yield ','.join(csv_quote(k) for k in row.keys()) + '\n'
            first = False
        yield ','.join(csv_quote(v) for v in row.values()) + '\n'
    if first:
        # no rows -> emit header only is handled by caller (they pass header explicitly)
        pass

def csv_quote(value):
    if value is None:
        s = ""
    else:
        s = str(value)
    # Escape as needed
    if any(ch in s for ch in [',', '\n', '"']):
        s = '"' + s.replace('"', '""') + '"'
    return s

# -*- coding: utf-8 -*-
from __future__ import annotations
import csv, io

COLUMNS = ["ts_kst","WBC","Hb","PLT","CRP","ANC","Na","K","Cr"]

def sniff_and_parse(file_bytes: bytes, encoding: str = "utf-8"):
    text = file_bytes.decode(encoding, errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        rows.append({k: row.get(k,"") for k in COLUMNS})
    return rows

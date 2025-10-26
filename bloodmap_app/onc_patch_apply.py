
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
onc_patch_apply.py
- Adds/updates 8 hematology/oncology drugs in your DB.
- Backends: MongoDB, PostgreSQL (jsonb), SQLite (fallback), or just emit JSON.
- Safe to run multiple times (idempotent upsert by key).

USAGE EXAMPLES
--------------
# Dry-run (see what will be written)
python onc_patch_apply.py --dry-run

# Apply to MongoDB
export MONGO_URI="mongodb://user:pass@host:27017/?authSource=admin"
python onc_patch_apply.py --backend mongo --mongo-db onc --mongo-col drugs

# Apply to PostgreSQL (jsonb)
export PG_DSN="host=127.0.0.1 port=5432 dbname=onc user=onc password=secret"
python onc_patch_apply.py --backend postgres --pg-table onc_drugs

# Apply to SQLite (file will be created if missing)
python onc_patch_apply.py --backend sqlite --sqlite-path ./onc.db

# Emit the JSON payload (stdout) to pipe into your own system
python onc_patch_apply.py --backend json > payload.json

SCHEMA ASSUMPTIONS
------------------
- Each record is stored as {"key": <str>, "data": <json>}
- PRIMARY KEY / unique index on "key"
- PostgreSQL table must exist with: key text primary key, data jsonb NOT NULL
- MongoDB collection: unique index on "key" is recommended

"""

import argparse
import json
import os
import sys
from datetime import datetime

# -----------------------
# Dataset to upsert
# -----------------------

PAYLOAD = [
    {
        "key": "venetoclax",
        "data": {
            "generic": "Venetoclax",
            "korean": "베네토클락스",
            "class": "BCL-2 inhibitor",
            "indications": ["AML(특히 HMA 병용)", "CLL/SLL"],
            "common_aes": ["TLS 위험", "오심/구토", "설사", "피로", "호중구감소/감염"],
            "monitor": [
                "TLS: Cr, K, PO4, Ca, UA(요산), eGFR, 수분/알로퓨리놀",
                "CBC(호중구, 혈소판)",
                "LFT(간기능)",
            ],
            "tips": [
                "용량 점증(titration) 필수, TLS 위험군 입원 모니터",
                "강력한 CYP3A 억제제 병용 시 감량 필요"
            ],
            "updated_at": datetime.utcnow().isoformat() + "Z"
        },
    },
    {
        "key": "gilteritinib",
        "data": {
            "generic": "Gilteritinib",
            "korean": "길테리티닙",
            "class": "FLT3 inhibitor",
            "indications": ["FLT3 변이 재발/불응 AML"],
            "common_aes": ["QT 연장", "간효소↑", "설사/변비", "피로"],
            "monitor": [
                "ECG: QTc",
                "LFT(간기능)",
                "전해질(K/Mg)",
                "CBC"
            ],
            "tips": [
                "강력한 CYP3A 억제/유도제 상호작용 확인"
            ],
            "updated_at": datetime.utcnow().isoformat() + "Z"
        },
    },
    {
        "key": "midostaurin",
        "data": {
            "generic": "Midostaurin",
            "korean": "미도스타우린",
            "class": "FLT3 inhibitor, multi-kinase",
            "indications": ["FLT3 변이 AML(유도/공고 병용)", "고위험 systemic mastocytosis"],
            "common_aes": ["QT 연장", "오심/구토", "설사", "발진", "간효소↑"],
            "monitor": [
                "ECG: QTc",
                "LFT(간기능)",
                "전해질(K/Mg)",
                "CBC"
            ],
            "tips": [
                "음식과 함께 복용 시 GI 내약성 개선"
            ],
            "updated_at": datetime.utcnow().isoformat() + "Z"
        },
    },
    {
        "key": "ivosidenib",
        "data": {
            "generic": "Ivosidenib",
            "korean": "이보시데닙",
            "class": "IDH1 inhibitor",
            "indications": ["IDH1 변이 AML"],
            "common_aes": ["분화증후군", "오심/설사", "백혈구↑", "QT 연장(드묾)"],
            "monitor": [
                "분화증후군: 발열, 저산소증, 폐침윤, 체액저류",
                "ECG: QTc",
                "CBC",
                "LFT(간기능)"
            ],
            "tips": [
                "분화증후군 의심 시 스테로이드(예: 덱사) 조기 투여, 필요 시 일시중단",
            ],
            "updated_at": datetime.utcnow().isoformat() + "Z"
        },
    },
    {
        "key": "enasidenib",
        "data": {
            "generic": "Enasidenib",
            "korean": "에나시데닙",
            "class": "IDH2 inhibitor",
            "indications": ["IDH2 변이 재발/불응 AML"],
            "common_aes": ["분화증후군", "빌리루빈↑", "오심/설사", "피로"],
            "monitor": [
                "분화증후군 징후",
                "LFT(간기능) / 빌리루빈",
                "CBC"
            ],
            "tips": [
                "UGT1A1 억제로 빌리루빈 상승 가능(무증상 시 지속 가능)"
            ],
            "updated_at": datetime.utcnow().isoformat() + "Z"
        },
    },
    {
        "key": "glasdegib",
        "data": {
            "generic": "Glasdegib",
            "korean": "글라스데깁",
            "class": "Hedgehog pathway inhibitor",
            "indications": ["고령/치료불가 AML(저강도 화학요법 병용)"],
            "common_aes": ["QT 연장", "근육통/경련", "미각 변화", "오심/설사"],
            "monitor": [
                "ECG: QTc",
                "전해질(K/Mg)",
                "LFT(간기능)"
            ],
            "tips": [
                "CYP3A4 상호작용, QT 연장 병용약(예: 일부 항생제/항진균제) 주의"
            ],
            "updated_at": datetime.utcnow().isoformat() + "Z"
        },
    },
    {
        "key": "azacitidine",
        "data": {
            "generic": "Azacitidine",
            "korean": "아자시티딘",
            "class": "Hypomethylating agent",
            "indications": ["MDS", "AML(저강도)", "CMML"],
            "common_aes": ["골수억제", "오심/구토", "설사/변비", "주사부위반응(SC)", "피로"],
            "monitor": [
                "CBC(호중구/혈색소/혈소판)",
                "LFT(간기능) / Renal(신기능)"
            ],
            "tips": [
                "주로 SC/IV; 혈구저하 시 지연/감량 알고리즘 적용"
            ],
            "updated_at": datetime.utcnow().isoformat() + "Z"
        },
    },
    {
        "key": "decitabine",
        "data": {
            "generic": "Decitabine",
            "korean": "데시타빈",
            "class": "Hypomethylating agent",
            "indications": ["MDS", "AML(저강도)"],
            "common_aes": ["골수억제", "오심/구토", "설사/변비", "피로"],
            "monitor": [
                "CBC",
                "LFT(간기능) / Renal(신기능)"
            ],
            "tips": [
                "혈구저하 및 감염 예방(예: G-CSF 고려, 항감염 예방)"
            ],
            "updated_at": datetime.utcnow().isoformat() + "Z"
        },
    },
]

# -----------------------
# Backends
# -----------------------

def apply_mongo(args):
    try:
        from pymongo import MongoClient, UpdateOne
    except Exception as e:
        print("[ERROR] pymongo 불러오기 실패 - 서버에 설치되어 있는지 확인하세요:", e, file=sys.stderr)
        return 1

    uri = os.environ.get("MONGO_URI")
    if not uri:
        print("[ERROR] MONGO_URI 환경변수가 필요합니다.", file=sys.stderr)
        return 1

    client = MongoClient(uri)
    db = client[args.mongo_db]
    col = db[args.mongo_col]

    # Ensure index on key (not fatal if exists)
    try:
        col.create_index("key", unique=True, background=True)
    except Exception:
        pass

    ops = []
    for item in PAYLOAD:
        ops.append(UpdateOne({"key": item["key"]}, {"$set": item}, upsert=True))

    result = col.bulk_write(ops, ordered=False)
    print(f"[OK] MongoDB upsert 완료: matched={result.matched_count}, upserted={len(result.upserted_ids)}, modified={result.modified_count}")
    return 0


def apply_postgres(args):
    try:
        import psycopg2, psycopg2.extras
    except Exception as e:
        print("[ERROR] psycopg2 불러오기 실패 - 서버에 설치되어 있는지 확인하세요:", e, file=sys.stderr)
        return 1

    dsn = os.environ.get("PG_DSN")
    if not dsn:
        print("[ERROR] PG_DSN 환경변수가 필요합니다.", file=sys.stderr)
        return 1

    sql = f"""
    CREATE TABLE IF NOT EXISTS {args.pg_table} (
        key TEXT PRIMARY KEY,
        data JSONB NOT NULL
    );
    """
    upsert = f"""
    INSERT INTO {args.pg_table} (key, data)
    VALUES (%(key)s, %(data)s)
    ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data;
    """

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, upsert, [{"key": x["key"], "data": json.dumps(x)} for x in PAYLOAD], page_size=100)
        conn.commit()

    print(f"[OK] PostgreSQL upsert 완료 → table={args.pg_table}, rows={len(PAYLOAD)}")
    return 0


def apply_sqlite(args):
    import sqlite3
    path = args.sqlite_path
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(f"CREATE TABLE IF NOT EXISTS {args.sqlite_table} (key TEXT PRIMARY KEY, data TEXT NOT NULL)")

    for item in PAYLOAD:
        cur.execute(
            f"INSERT INTO {args.sqlite_table} (key, data) VALUES (?, ?) "
            f"ON CONFLICT(key) DO UPDATE SET data=excluded.data",
            (item["key"], json.dumps(item))
        )

    conn.commit()
    conn.close()
    print(f"[OK] SQLite upsert 완료 → {path}::{args.sqlite_table}, rows={len(PAYLOAD)}")
    return 0


def emit_json(args):
    obj = {"upsert": PAYLOAD, "count": len(PAYLOAD), "generated_at": datetime.utcnow().isoformat() + "Z"}
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Apply onc drug patch (8 AML-related agents)")
    ap.add_argument("--backend", choices=["mongo", "postgres", "sqlite", "json"], default="json")
    ap.add_argument("--dry-run", action="store_true", help="Print summary and first records, no DB writes")

    # Mongo options
    ap.add_argument("--mongo-db", default="onc", help="MongoDB database name")
    ap.add_argument("--mongo-col", default="drugs", help="MongoDB collection name")

    # Postgres options
    ap.add_argument("--pg-table", default="onc_drugs", help="PostgreSQL table name")

    # SQLite options
    ap.add_argument("--sqlite-path", default="./onc.db", help="SQLite database file path")
    ap.add_argument("--sqlite-table", default="onc_drugs", help="SQLite table name")

    args = ap.parse_args()

    if args.dry_run:
        print("[DRY-RUN] Upserting the following keys:")
        print(", ".join([x["key"] for x in PAYLOAD]))
        print("\n[Preview] First record:")
        print(json.dumps(PAYLOAD[0], ensure_ascii=False, indent=2))
        return 0

    if args.backend == "mongo":
        return apply_mongo(args)
    elif args.backend == "postgres":
        return apply_postgres(args)
    elif args.backend == "sqlite":
        return apply_sqlite(args)
    else:
        return emit_json(args)


if __name__ == "__main__":
    sys.exit(main())

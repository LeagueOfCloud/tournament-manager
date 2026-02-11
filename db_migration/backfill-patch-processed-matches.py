import os
import json
import pymysql
from typing import List

# ------------------------
# ENV
# ------------------------

DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = int(os.getenv("DB_PORT", ""))
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "")

BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "10"))


# ------------------------
# DB
# ------------------------
def create_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


FETCH_MATCHES_SQL = """
SELECT DISTINCT match_id
FROM processed_match_data
WHERE patch IS NULL
LIMIT %s;
"""

FETCH_MATCH_DATA_SQL = """
SELECT match_data
FROM match_history
WHERE match_id = %s;
"""

UPDATE_PATCH_SQL = """
UPDATE processed_match_data
SET patch = %s
WHERE match_id = %s;
"""

def extract_patch(match_data_json: str) -> str | None:
    try:
        payload = json.loads(match_data_json)
        version = payload.get("info", {}).get("gameVersion", "")
        if not version:
            return None
        return ".".join(version.split(".")[:2])
    except Exception:
        return None

def process_batch(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(FETCH_MATCHES_SQL, (BATCH_SIZE,))
        matches = cur.fetchall()

    if not matches:
        return 0

    updated = 0

    with conn.cursor() as cur:
        for row in matches:
            match_id = row["match_id"]

            cur.execute(FETCH_MATCH_DATA_SQL, (match_id,))
            result = cur.fetchone()
            if not result:
                continue

            patch = extract_patch(result["match_data"])
            if not patch:
                continue

            cur.execute(UPDATE_PATCH_SQL, (patch, match_id))
            updated += 1

    conn.commit()
    return updated

def main():
    conn = create_connection()
    total = 0

    try:
        while True:
            updated = process_batch(conn)
            if updated == 0:
                break
            total += updated
            print(f"Updated {updated} matches (total: {total})")

        print(f"Finished. Total matches updated: {total}")

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()

import argparse
import os
import pymysql
import numpy as np
from collections import defaultdict

# -------------------------
# CONFIG
# -------------------------

DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = int(os.getenv("DB_PORT", ""))
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "")

METRICS = {
    "kills_pm":   "kills",
    "deaths_pm":  "deaths",
    "assists_pm": "assists",
    "cs_pm":      "totalMinionsKilled",
    "dmg_pm":     "totalDamageDealtToChampions",
    "vision_pm":  "vision_score",
    "heal_pm": "totalHealsOnTeammates",
    "cc_pm": "totalTimeCCDealt",
    "dmg_turret_pm": "damageDealtToTurrets",
    "dmg_taken_pm": "totalDamageTaken"
}

# -------------------------
# DB
# -------------------------
def create_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
    )

# -------------------------
# ARGUMENTS
# -------------------------
parser = argparse.ArgumentParser(description="Initialize metrics_baseline table")
parser.add_argument(
    "--patches",
    nargs="+",
    help="Patch(es) to initialize baselines for (e.g. 14.3 14.4)",
)
parser.add_argument(
    "--limit",
    type=int,
    help="Limit number of matches to use (testing only)",
)
args = parser.parse_args()

if not args.patches and not args.limit:
    raise ValueError("You must provide either --patches or --limit")

if args.patches and args.limit:
    raise ValueError("Choose either --patches OR --limit, not both")

# -------------------------
# SQL
# -------------------------
PATCH_QUERY = """
SELECT
    pmd.teamPosition AS role,
    pmd.gameDuration,
    pmd.kills,
    pmd.deaths,
    pmd.assists,
    pmd.totalMinionsKilled,
    pmd.totalDamageDealtToChampions,
    pmd.vision_score,
    pmd.totalHealsOnTeammates,
    pmd.totalTimeCCDealt,
    pmd.damageDealtToTurrets,
    pmd.totalDamageTaken
FROM processed_match_data pmd
WHERE pmd.patch IN ({patches});
"""

LIMIT_QUERY = """
SELECT
    pmd.teamPosition AS role,
    pmd.gameDuration,
    pmd.kills,
    pmd.deaths,
    pmd.assists,
    pmd.totalMinionsKilled,
    pmd.totalDamageDealtToChampions,
    pmd.vision_score,
    pmd.totalHealsOnTeammates,
    pmd.totalTimeCCDealt,
    pmd.damageDealtToTurrets,
    pmd.totalDamageTaken
FROM processed_match_data pmd
LIMIT %s;
"""

UPSERT_BASELINE_SQL = """
INSERT INTO metrics_baseline (
    role,
    metric,
    mean,
    std,
    sample_size
) VALUES (%s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    mean = VALUES(mean),
    std = VALUES(std),
    sample_size = VALUES(sample_size),
    updated_at = CURRENT_TIMESTAMP;
"""


# -------------------------
# MAIN
# -------------------------
def main():
    connection = create_connection()
    try:
        with connection.cursor() as cursor:
            if args.patches:
                placeholders = ",".join(["%s"] * len(args.patches))
                query = PATCH_QUERY.format(patches=placeholders)
                cursor.execute(query, args.patches)
            else:
                cursor.execute(LIMIT_QUERY, (args.limit,))

            rows = cursor.fetchall()
        if not rows:
            print("No data found for given input.")
            return

        # (patch, role, metric) -> list of values
        buckets = defaultdict(list)

        for r in rows:
            minutes = r["gameDuration"] / 60.0
            if minutes <= 10: # ignore remakes
                continue

            for metric_name, col in METRICS.items():
                value = r[col] / minutes
                key = (r["role"], metric_name)
                buckets[key].append(value)

        with connection.cursor() as cursor:
            for (role, metric), values in buckets.items():
                arr = np.array(values)
                mean = round(float(arr.mean()), 3)
                std = round(float(arr.std()) if arr.std() > 0 else 1.0, 3)
                sample_size = len(arr)

                cursor.execute(
                    UPSERT_BASELINE_SQL,
                    (
                        role,
                        metric,
                        mean,
                        std,
                        sample_size,
                    ),
                )

        connection.commit()
        print(f"Initialized metrics_baseline for {len(buckets)} (patch, role, metric) entries.")

    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    main()

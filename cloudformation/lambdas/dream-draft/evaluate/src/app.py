import os
import json
import logging
import pymysql
import numpy as np

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ------------------
# ENV
# ------------------
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_NAME = os.environ["DB_NAME"]

# ------------------
# DB
# ------------------
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

# ------------------
# SQL
# ------------------
FETCH_MATCHES_TO_EVALUATE_SQL = """
    SELECT tournament_match_id
    FROM tournament_matches
    WHERE end_date IS NOT NULL
        AND was_evaluated = 'false'
    ORDER BY end_date ASC;
""" # go through processed_match_data for queueId = 3100

FETCH_PROCESSED_MATCH_DATA_SQL = """
    SELECT
        pmd.*
    FROM processed_match_data pmd
    JOIN tournament_matches tm ON tm.tournament_match_id = pmd.match_id
    WHERE tm.tournament_match_id = %s;
""" # is it ok to go by tournament_match_id here? multiple ids for single match thingy

FETCH_PLAYER_ID_SQL = """
    SELECT player_id 
    FROM riot_accounts 
    WHERE account_puuid = %s 
    LIMIT 1;
"""

FETCH_BASELINES_SQL = """
    SELECT role, metric, mean, std
    FROM metrics_baseline;
"""

UPSERT_MATCH_SCORE_SQL = """
    INSERT INTO dreamdraft_match_scores (
        tournament_match_id,
        player_id,
        score
    ) VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE score = VALUES(score);
"""

UPDATE_PLAYER_SCORE_SQL = """
    UPDATE players p
    SET p.score = (
        SELECT COALESCE(SUM(dms.score), 0)
        FROM dreamdraft_match_scores dms
        WHERE dms.player_id = p.id
    )
    WHERE p.id = %s;
"""

MARK_MATCH_EVALUATED_SQL = """
    UPDATE tournament_matches
    SET was_evaluated = 'true'
    WHERE tournament_match_id = %s;
"""

# ------------------
# Scoring logic  |  PLACEHOLDER - replace with actual logic
# ------------------

default_weights = {
    "kills": 2.0,
    "deaths": -2.0,
    "assists": 1.5,
    "cs": 2.0,
    "dmg": 2.0,
    "vision": 1.0,
    "heal": 1.0,
    "cc": 1.0,
    "dmg_turret": 1.0,
    "dmg_taken": -1.0,
    "win": 5.0,
}

role_weights = {
    "TOP": {"kills": 3.5, "deaths": -2.5, "assists": 1.0, "cs": 4.0, "dmg": 3.5, "vision": 0.5, "win": 5.0, "heal": 1.0, "cc": 1.0, "dmg_turret": 1.0, "dmg_taken": -1.0,},
    "JUNGLE": {"kills": 1.0, "deaths": -2.0, "assists": 3.5, "cs": 0.5, "dmg": 1.0, "vision": 4.0, "win": 5.0, "heal": 1.0, "cc": 1.0, "dmg_turret": 1.0, "dmg_taken": -1.0},
    "MIDDLE": {"kills": 3.5, "deaths": -2.5, "assists": 1.0, "cs": 4.0, "dmg": 3.5, "vision": 0.5, "win": 5.0, "heal": 1.0, "cc": 1.0, "dmg_turret": 1.0, "dmg_taken": -1.0,},
    "BOTTOM": {"kills": 3.5, "deaths": -2.5, "assists": 1.0, "cs": 4.0, "dmg": 3.5, "vision": 0.5, "win": 5.0, "heal": 1.0, "cc": 1.0, "dmg_turret": 1.0, "dmg_taken": -1.0,},
    "UTILITY": {"kills": 3.5, "deaths": -2.5, "assists": 1.0, "cs": 4.0, "dmg": 3.5, "vision": 0.5, "win": 5.0, "heal": 1.0, "cc": 1.0, "dmg_turret": 1.0, "dmg_taken": -1.0,},
}

def compute_scores(rows, baselines):
    # Per-minute
    for r in rows:
        minutes = r["gameDuration"] / 60.0
        r["kills_pm"] = r["kills"] / minutes
        r["deaths_pm"] = r["deaths"] / minutes
        r["assists_pm"] = r["assists"] / minutes
        r["cs_pm"] = r["totalMinionsKilled"] / minutes
        r["dmg_pm"] = r["totalDamageDealtToChampions"] / minutes
        r["vision_pm"] = r["vision_score"] / minutes

        r["heal_pm"] = r["totalHealsOnTeammates"] / minutes
        r["cc_pm"] = r["totalTimeCCDealt"] / minutes
        r["dmg_turret_pm"] = r["damageDealtToTurrets"] / minutes
        r["dmg_taken_pm"] = r["totalDamageTaken"] / minutes # (dmg_taken_pm | dmg_mitigated_pm) / deaths ratio
        #r["dmg_mitigated_pm"] = r["damageSelfMitigated"] / minutes

    metrics = ["kills_pm", "deaths_pm", "assists_pm", "cs_pm", "dmg_pm", "vision_pm", "heal_pm", "cc_pm", "dmg_turret_pm", "dmg_taken_pm"]

    for r in rows:
        role = r["teamPosition"]

        for metric in metrics:
            key = (role, metric)
            baseline = baselines.get(key)

            if not baseline or baseline["std"] == 0:
                r[metric + "_norm"] = 0.5
            else:
                r[metric + "_norm"] = (
                    (r[metric] - baseline["mean"]) / baseline["std"]
                ) + 0.5

    # Final score
    scores = []
    for r in rows:
        w = role_weights.get(r["teamPosition"], default_weights)

        score = (
            w["kills"]   * r["kills_pm_norm"] +
            w["deaths"]  * r["deaths_pm_norm"] +
            w["assists"] * r["assists_pm_norm"] +
            w["cs"]      * r["cs_pm_norm"] +
            w["dmg"]     * r["dmg_pm_norm"] +
            w["vision"]  * r["vision_pm_norm"] +
            
            w["heal"]    * r["heal_pm_norm"] +
            w["cc"]      * r["cc_pm_norm"] +
            w["dmg_turret"] * r["dmg_turret_pm_norm"] +
            w["dmg_taken"]  * r["dmg_taken_pm_norm"]
        )

        scores.append((r["account_puuid"], score))

    return scores

# ------------------
# Lambda handler
# ------------------
def lambda_handler(event, context):
    connection = create_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(FETCH_MATCHES_TO_EVALUATE_SQL)
            matches = cursor.fetchall()

        if not matches:
            return {"statusCode": 200, "body": json.dumps({"message": "No matches to evaluate"})}

        for m in matches:
            match_id = m["tournament_match_id"]
            
            with connection.cursor() as cursor:
                cursor.execute(FETCH_PROCESSED_MATCH_DATA_SQL, (match_id,))
                rows = cursor.fetchall()

            if not rows:
                logger.warning(f"No processed data for match {match_id}")
                continue

            with connection.cursor() as cursor:
                cursor.execute(FETCH_BASELINES_SQL)
                baseline_rows = cursor.fetchall()

            baselines = {
                (b["role"], b["metric"]): {"mean": b["mean"], "std": b["std"]}
                for b in baseline_rows
            }

            player_scores = compute_scores(rows, baselines)

            with connection.cursor() as cursor:
                cursor.execute("SELECT account_puuid FROM riot_accounts")
                tournament_players = {r["account_puuid"] for r in cursor.fetchall()}
                
                for puuid, score in player_scores:
                    if puuid not in tournament_players:
                        continue

                    cursor.execute(FETCH_PLAYER_ID_SQL, (puuid, ))
                    player_id = cursor.fetchone()["player_id"]
                    cursor.execute(UPSERT_MATCH_SCORE_SQL, (match_id, player_id, score))
                    cursor.execute(UPDATE_PLAYER_SCORE_SQL, (player_id,))
                cursor.execute(MARK_MATCH_EVALUATED_SQL, (match_id,))
        connection.commit()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Evaluation completed",
                "matches_processed": len(matches)
            })
        }

    except Exception as e:
        connection.rollback()
        logger.exception("Evaluation failed")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    finally:
        if connection:
            connection.close()
import json
import os
import pymysql
import logging
import requests
from typing import List, Dict, Any, Tuple, Set

connection = None
logger = logging.getLogger()
logger.setLevel(logging.INFO)

GET_MATCH_IDS_SQL = """
    SELECT match_id, match_data
    FROM match_history
    WHERE match_data IS NOT NULL AND was_processed = 'false'
    LIMIT 5;
"""

FETCH_KNOWN_PUUIDS_SQL_TMPL = """
    SELECT account_puuid 
    FROM riot_accounts 
    WHERE account_puuid IN ({inlist});
"""

MARK_MATCH_PROCESSED_SQL = """
    UPDATE match_history
    SET was_processed = 'true'
    WHERE match_id = %s;
"""

UPSERT_PROCESSED_MATCH_DATA_SQL = """
    INSERT INTO processed_match_data (match_id, account_puuid, account_name, champion_name, teamPosition, goldEarned, totalDamageDealtToChampions, totalDamageTaken, totalHealsOnTeammates, damageSelfMitigated, damageDealtToTurrets, totalTimeCCDealt, totalMinionsKilled, kills, deaths, assists, vision_score, objectivesStolen, win, queueId, gameDuration)
    VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        totalHealsOnTeammates = VALUES(totalHealsOnTeammates),
        totalDamageTaken = VALUES(totalDamageTaken),
        damageSelfMitigated = VALUES(damageSelfMitigated),
        damageDealtToTurrets = VALUES(damageDealtToTurrets),
        totalTimeCCDealt = VALUES(totalTimeCCDealt),
        objectivesStolen = VALUES(objectivesStolen),
        goldEarned = VALUES(goldEarned),
        kills = VALUES(kills),
        deaths = VALUES(deaths),
        assists = VALUES(assists),
        vision_score = VALUES(vision_score),
        totalMinionsKilled = VALUES(totalMinionsKilled),
        totalDamageDealtToChampions = VALUES(totalDamageDealtToChampions),
        win = VALUES(win),
        queueId = VALUES(queueId),
        gameDuration = VALUES(gameDuration),
        account_name = VALUES(account_name),
        champion_name = VALUES(champion_name),
        teamPosition = VALUES(teamPosition);
"""

def get_connection() -> pymysql.Connection:
    global connection
    if connection is None:
        connection = pymysql.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            cursorclass=pymysql.cursors.DictCursor
        )
    return connection

def close_connection():
    connection = get_connection()
    connection.close()
    connection = None

def ensure_json(data):
    if data is None:
        return None
    if isinstance(data, (dict, list)):
        return data
    try:
        return json.loads(data)
    except Exception:
        return None

def fetch_unprocessed_matches(conn: pymysql.Connection) -> List[Dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(GET_MATCH_IDS_SQL)
        return cur.fetchall()
    
def get_known_puuids(conn: pymysql.Connection, candidate_puuids: List[str]) -> Set[str]:
    if not candidate_puuids:
        return set()
    placeholders = ",".join(["%s"] * len(candidate_puuids))
    sql = FETCH_KNOWN_PUUIDS_SQL_TMPL.format(inlist=placeholders)
    with conn.cursor() as cur:
        cur.execute(sql, candidate_puuids)
        rows = cur.fetchall()
    return {r["account_puuid"] for r in rows}

def insert_participant_rows(conn: pymysql.Connection, rows: List[Tuple]):
    if not rows:
        return
    with conn.cursor() as cur:
        cur.executemany(UPSERT_PROCESSED_MATCH_DATA_SQL, rows)

def mark_match_processed(conn: pymysql.Connection, match_id: str):
    with conn.cursor() as cur:
        cur.execute(MARK_MATCH_PROCESSED_SQL, (match_id,))

def extract_rows_for_known_puuids(match_id: str, payload: Dict[str, Any], known_puuids: Set[str]) -> List[Tuple]:
    info = (payload or {}).get("info", {})
    queue_id = info.get("queueId")
    game_duration = info.get("gameDuration")
    if game_duration < 60*10:
        return []  # skip remade games
    participants = info.get("participants", []) or []

    rows: List[Tuple] = []
    for p in participants:
        puuid = p.get("puuid")
        if puuid not in known_puuids:
            continue

        account_aux = p.get("riotIdGameName")
        account_tag = p.get("riotIdTagline")
        account_name = f"{account_aux}#{account_tag}"
        champion_name = p.get("championName")
        team_position = p.get("teamPosition")

        gold = p.get("goldEarned")
        dmg = p.get("totalDamageDealtToChampions")
        dmg_turret = p.get("damageDealtToTurrets")
        dmg_taken = p.get("totalDamageTaken")
        mitigated_dmg = p.get("damageSelfMitigated")
        cs = p.get("totalMinionsKilled")
        neutral_cs = p.get("neutralMinionsKilled")
        total_cs = cs + neutral_cs
        kills = p.get("kills")
        deaths = p.get("deaths")
        assists = p.get("assists")
        vision_score = p.get("visionScore")
        heal = p.get("totalHealsOnTeammates")
        obj_stolen = p.get("objectivesStolen")
        cc = p.get("totalTimeCCDealt")

        win = str(p.get("win"))

        rows.append((
            match_id, puuid, account_name, champion_name, team_position,
            gold, dmg, dmg_taken, heal, mitigated_dmg, dmg_turret, cc, total_cs, kills,
            deaths, assists, vision_score, obj_stolen, win, queue_id, game_duration
        ))

    return rows

def lambda_handler(event, context):
    processed_matches = 0
    inserted_rows = 0
    connection = get_connection()
    
    try: 
        matches = fetch_unprocessed_matches(connection)
        if not matches:
            logger.info("No unprocessed matches found.")
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json", 
                    "Access-Control-Allow-Origin": "*"
                },
            }

        for rec in matches:
            match_id = rec["match_id"]
            raw = rec["match_data"]
            payload = ensure_json(raw)
            if not payload:
                logger.warning(f"Skipping match {match_id}: invalid JSON payload.")
                mark_match_processed(connection, match_id)  # prevent infinite loop on bad row
                continue

            participants = (payload.get("info", {}) or {}).get("participants", []) or []
            candidate_puuids = [p.get("puuid") for p in participants if p.get("puuid")]

            known = get_known_puuids(connection, candidate_puuids)
            if not known:
                logger.info(f"Match {match_id}: no known PUUIDs found; marking processed.")
                mark_match_processed(connection, match_id)
                continue

            rows = extract_rows_for_known_puuids(match_id, payload, known)
            if rows:
                insert_participant_rows(connection, rows)
                inserted_rows += len(rows)

            mark_match_processed(connection, match_id)
            processed_matches += 1

        connection.commit()
        
    except Exception as e:
        connection.rollback()
        logger.exception("Error while processing matches.")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json", 
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"message": "Error processing matches.", "error": str(e)})
        }

    return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({
                "message": "Processed matches successfully.",
                "matches_processed": processed_matches,
                "rows_upserted": inserted_rows
            })
    }

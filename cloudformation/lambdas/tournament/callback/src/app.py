import json
import os
import pymysql
from datetime import datetime
import requests
import traceback

GET_WINNING_TEAM_SQL = """
SELECT
    t.id as id
FROM riot_accounts ra
JOIN players p WHERE p.id = ra.player_id
JOIN teams t WHERE t.id = p.team_id
WHERE ra.account_puuid = %s
"""

UPDATE_WINNING_TEAM_SQL = """
UPDATE tournament_matches
SET
    winner_team_id = %s,
    end_date = %s,
    tournament_match_id = %s
WHERE id = %s
"""

INSERT_MATCH_HISTORY_SQL = """
    INSERT INTO match_history (match_id)
    VALUES (%s) ON DUPLICATE KEY UPDATE
"""


def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
    )


def lambda_handler(event, context):
    body = json.loads(event["body"])

    try:
        url = f"https://americas.api.riotgames.com/lol/tournament/v5/games/by-code/{body['shortCode']}"
        headers = {"X-Riot-Token": os.environ["RIOT_API_KEY"]}

        res = requests.get(url, headers=headers)
        games = res.json()
        connection = create_connection()

        with connection.cursor() as cur:
            for game in games:
                match_id = f"{game['region']}_{game['gameId']}"
                tournament_match_id = json.loads(game["metaData"])["id"]
                winner_puuid = game["winningTeam"][0]["puuid"]
                cur.execute(GET_WINNING_TEAM_SQL, (winner_puuid, match_id))

                winner = cur.fetchone()
                cur.execute(
                    UPDATE_WINNING_TEAM_SQL,
                    (winner["id"], datetime.now(), tournament_match_id),
                )

                cur.execute(INSERT_MATCH_HISTORY_SQL, (match_id,))

        connection.commit()

    except Exception as e:
        traceback.print_exc(e)

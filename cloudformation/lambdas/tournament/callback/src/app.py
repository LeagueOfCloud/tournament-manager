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
JOIN players p ON p.id = ra.player_id
JOIN teams t ON t.id = p.team_id
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
    VALUES (%s) ON DUPLICATE KEY UPDATE match_id = match_id
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


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    body = json.loads(event["body"])

    try:
        url = f"https://americas.api.riotgames.com/lol/tournament/v5/games/by-code/{body['shortCode']}"
        headers = {"X-Riot-Token": os.environ["RIOT_API_KEY"]}

        res = requests.get(url, headers=headers)
        games = res.json()
        connection = create_connection()

        for game in games:
            with connection.cursor() as cur:
                match_id = f"{game['region']}_{game['gameId']}"
                tournament_match_id = json.loads(game["metaData"])["id"]
                winner_puuid = game["winningTeam"][0]["puuid"]
                cur.execute(GET_WINNING_TEAM_SQL, (winner_puuid,))

                winner = cur.fetchone()
                cur.execute(
                    UPDATE_WINNING_TEAM_SQL,
                    (
                        winner["id"],
                        datetime.now(),
                        match_id,
                        tournament_match_id,
                    ),
                )

                cur.execute(INSERT_MATCH_HISTORY_SQL, (match_id,))

        connection.commit()

        return response(200, {"message": "Tournament match result has been processed"})

    except Exception as e:
        print(traceback.print_exc())
        return response(
            500,
            {
                "message": "Could not process tournament match",
                "error": f"{e}",
            },
        )

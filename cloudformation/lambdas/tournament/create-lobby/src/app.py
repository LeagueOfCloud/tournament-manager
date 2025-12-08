import json
import os
import pymysql
import logging
import requests

SELECT_MATCH_SQL = """
SELECT * FROM tournament_matches WHERE id = ?
"""

GET_TOURNAMENT_ID_SQL = """
SELECT * FROM config WHERE name = 'tournament_id'
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
    #/create-lobby/{id}
    path_params = event.get("pathParameters") or {}
    tournament_match_id = path_params.get("id")

    if not tournament_match_id:
        return response(400, {"message": "Tournament match ID is required"})

    try:
        connection = create_connection()
        with connection.cursor() as cur:
            cur.execute(SELECT_MATCH_SQL, (int(tournament_match_id),))
            match = cur.fetchone()

            if not match:
                return response(404, {"message": "Tournament match not found"})
            
            cur.execute(GET_TOURNAMENT_ID_SQL)
            tournament_id_entry = cur.fetchone()
            tournament_id = tournament_id_entry["value"]
            
            api_url = f"https://americas.api.riotgames.com/lol/tournament/v5/codes?tournamentId={tournament_id}&count=1"
            headers = {"X-Riot-Token": os.environ["RIOT_API_KEY"]}

            body = {
                "enoughPlayers": True,
                "mapType": "SUMMONERS_RIFT",
                "metadata": json.dumps({"title": f"Tournament Match {tournament_match_id}"}),
                "pickType": "BLIND_PICK",
                "spectatorType": "ALL",
                "teamSize": 1
            }
            response = requests.post(api_url, headers=headers, json=body)

            return response(200, {"message": "Lobby created successfully", "lobby_code": response.json()[0]})

    except Exception as e:
        return response(500, {"message": str(e)})
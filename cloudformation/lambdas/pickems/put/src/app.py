import json
import os
import pymysql
import requests

INSERT_PICKEMS_SQL = """
    INSERT INTO pickems (id, pickem_id, user_id, value)
    VALUES (%s, %s, %s, %s)
"""

UPDATE_PICKEMS_SQL = """
    UPDATE pickems SET value = (%s) where id = (%s)
""" 

SELECT_PICKEMS_SQL = """
    SELECT * FROM pickems WHERE id =(%s)
"""

SELECT_USER_SQL = """
    SELECT id,type FROM profiles WHERE token = (%s)
"""

SELECT_CONFIG_SQL = """
    SELECT value FROM config where name = (%s)
"""

SELECT_PLAYER_SQL = """
    SELECT id FROM players where id = (%s)
"""

SELECT_TEAM_SQL = """
    SELECT id FROM teams where id = (%s)
"""

connection = None

def select_pickem(id):
    with connection.cursor() as cursor:
        cursor.execute(SELECT_PICKEMS_SQL,
                       id)
    row = cursor.fetchone()
    return row

def create_pickem(id, pickem_id, user_id, value):
    with connection.cursor() as cursor:
        cursor.execute(
            INSERT_PICKEMS_SQL, 
            (id, pickem_id, user_id, value)
        )
        connection.commit()
        return cursor.lastrowid 
    
def update_pickens(id,value):
    with connection.cursor() as cursor:
        cursor.execute(
             UPDATE_PICKEMS_SQL,
             (value,id))
        connection.commit()
    return cursor.lastrowid 
             

def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
    )

def pickems_unlocked() -> bool:
    with connection.cursor() as cursor:
        cursor.execute(SELECT_CONFIG_SQL,
                       ("pickem_unlocked"))
    config = cursor.fetchone()
    if config["value"] == "true":
        return True
    return False

def figure_out_pickems_type(id: str):
    with connection.cursor() as cursor:
        cursor.execute(SELECT_CONFIG_SQL,
                       ("pickem_categories"))
    config = cursor.fetchone()
    row = None
    jsonconfig = json.loads(config["value"])
    for item in jsonconfig:
       if item.get("id") == str(id):
            row = item
            break
    if row is None:
        return row
    return row["type"]


def is_admin_user(user_id) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(SELECT_USER_SQL,
                       user_id)
    config = cursor.fetchone()
    if(config is None):
        return False
    if config["type"] != "admin":
        return False
    return True

def get_user_id(token):
    with connection.cursor() as cursor:
        cursor.execute(SELECT_USER_SQL,
                       token)
    user = cursor.fetchone()
    if(user["id"] is None):
       return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(f"Invalid user Id"),
        } 
    return user["id"]

def validate_player(player_value):
    with connection.cursor() as cursor:
        cursor.execute(SELECT_PLAYER_SQL,
                       player_value)
    player = cursor.fetchone()
    if(player is None):
        return False
    return True

def validate_team(team_value):
    with connection.cursor() as cursor:
        cursor.execute(SELECT_TEAM_SQL,
                       team_value)
    team = cursor.fetchone()
    if(team is None):
        return False
    return True

def validate_champion(champion_value) -> bool:
    url = "https://ddragon.leagueoflegends.com/cdn/15.23.1/data/en_US/champion.json"
    response = requests.get(url)
    response.raise_for_status() 
    
    data = response.json()
    champions = data["data"] 
    
    return any(champ["name"].lower() == champion_value.lower() for champ in champions.values())

def lambda_handler(event, context):
    global connection
    request_id = context.aws_request_id
    pickem_data = json.loads(event["body"])
    connection = create_connection()

    pickem_id = pickem_data.get("id")
    #stolen from nemi
    user_token = event["headers"].get("Authorization") or event["headers"].get("authorization")
    value = pickem_data.get("value")


    if pickems_unlocked() is False:
       if is_admin_user(user_token) is False:
            return {
            "statusCode": 403,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(f"https://uploads.dailydot.com/2024/11/nuh-uh-beocord.gif?auto=compress&fm=gif"),
        }
        
    if None in (pickem_id, value):
        return {
        "statusCode": 400,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(f"Invalid data please fix and try again."),
    }

    pickems_type = figure_out_pickems_type(pickem_id)
    user_id = get_user_id(user_token)
    valid = True
    match pickems_type:
        case "PLAYER":
            valid = validate_player(value)
        case "CHAMPION":
            valid = validate_champion(value)
        case "TEAM":
            valid = validate_team(value)
        case "COUNT":
            pass
        case _:
            return {
        "statusCode": 400,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(f"Invalid pickems Id please fix and try again."),
    }

    if(not valid):
        return {
        "statusCode": 400,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(f"Invalid data player/champion/team does not exsist"),
    }

    try:
        current_pickem = select_pickem(f"{pickem_id}-{user_id}")
        if(current_pickem is None):
            if None in (pickem_id, user_id,):
                return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(f"Invalid data please fix and try again."),
            }
            create_pickem(f"{pickem_id}-{user_id}", pickem_id, user_id, value)    
        else:
            update_pickens(f"{pickem_id}-{user_id}",value)
        return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(f"Created/Updated Pickem"),
            }
    except Exception as e:
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(f"Failed to create pickems, Error: {str(e)}"),
        }

    finally:
        if connection:
            connection.close()
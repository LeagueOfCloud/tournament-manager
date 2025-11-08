import base64
import json
import os
import pymysql
from datetime import datetime

INSERT_CONFIG_SQL = """
    INSERT INTO config (name, value)
    VALUES (%s, %s)
"""

def validate_config_item(config_item) -> bool:
    return config_item.get("name", "").strip()

def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor
    )

def lambda_handler(event, context):
    # can be { "name": "...", "value": "..." } or [ {...}, {...} ]
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": "Invalid JSON body"}),
        }
    
    # json | list of json -> list
    if isinstance(body, dict):
        items = [body]
    elif isinstance(body, list):
        items = body
    else:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": "Body must be an object or a list of objects"}),
        }
    
    valid_items = []
    invalid_items = []
    for item in items:
        if validate_config_item(item):
            val = item.get("value", None)
            if isinstance(val, str):
                val = val.strip()
            valid_items.append(
                {
                    "name": item["name"].strip(),
                    "value": val,
                }
            )
        else:
            invalid_items.append(item)

    if not valid_items and invalid_items:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": "No valid config items", "invalid": invalid_items}),
        }

    connection = None
    inserted = []
    updated = []


    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            # find existing names
            names = [item["name"] for item in valid_items]
            format_strings = ",".join(["%s"] * len(names))
            cursor.execute(
                f"SELECT name FROM config WHERE name IN ({format_strings})",
                names,
            )
            existing_rows = cursor.fetchall()
            existing_names = {row["name"] for row in existing_rows}

            to_update = [item for item in valid_items if item["name"] in existing_names]
            to_insert = [item for item in valid_items if item["name"] not in existing_names]

            # updates
            update_sql = "UPDATE config SET value = %s WHERE name = %s"
            for item in to_update:
                cursor.execute(update_sql, (item["value"], item["name"]))
                updated.append(item["name"])

            # inserts
            insert_sql = "INSERT INTO config (name, value) VALUES (%s, %s)"
            for item in to_insert:
                cursor.execute(insert_sql, (item["name"], item["value"]))
                inserted.append(item["name"])

            connection.commit()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "message": "Configs processed successfully",
                    "inserted": inserted,
                    "updated": updated,
                    "invalid": invalid_items,
                }
            ),
        }

    except Exception as e:
        if connection:
            connection.rollback()
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": f"Failed to process configs: {str(e)}"}),
        }

    finally:
        if connection:
            connection.close()

import pymysql
import os
import traceback

PATH_PERMISSIONS = {
    "POST /players": "admin",
    "DELETE /players": "admin",
    "PATCH /players": "admin",
    "POST /teams": "admin",
    "DELETE /teams": "admin",
    "PATCH /teams": "admin",
    "GET /riot-accounts": "admin",
    "GET /riot-accounts/{id}": "admin",
    "GET /riot-accounts/player/{player_id}": "admin",
    "POST /riot-accounts": "admin",
    "DELETE /riot-accounts": "admin",
    "PATCH /riot-accounts": "admin",
    "GET /config": "admin",
    "PUT /config": "admin",
    "DELETE /config": "admin",
    "GET /profiles": "admin",
    "GET /profiles/{id}": "admin",
    "PUT /pickems": ["admin", "user"],
    "PUT /dream-draft": ["admin", "user"],
    "POST /tournament/create-lobby/{id}": "admin",
    "POST /champ-select-lobby": "admin",
    "GET /champ-select-lobby": "admin",
}


def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
    )


def generatePolicy(
    principalId, effect, error_message="You are not allowed to do this."
):
    authResponse = {}
    authResponse["principalId"] = principalId
    if effect and METHOD_ARN:
        policyDocument = {}
        policyDocument["Version"] = "2012-10-17"
        policyDocument["Statement"] = []
        statementOne = {}
        statementOne["Action"] = "execute-api:Invoke"
        statementOne["Effect"] = effect
        statementOne["Resource"] = METHOD_ARN
        policyDocument["Statement"] = [statementOne]
        authResponse["policyDocument"] = policyDocument

        if effect == "Deny":
            authResponse["context"] = {"error_message": error_message}

    return authResponse


def lambda_handler(event, context):
    global METHOD_ARN
    global TOKEN
    METHOD_ARN = event["methodArn"]

    if event["httpMethod"] == "OPTIONS":
        return generatePolicy("OPTIONS", "Allow")

    TOKEN = event["headers"].get("Authorization") or event["headers"].get(
        "authorization"
    )

    connection = None

    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM profiles WHERE token = %s", (TOKEN))
            result = cursor.fetchone()

        if result == None:
            return generatePolicy("null", "Deny", "Invalid token provided")

        user_type = str(result.get("type", "null")).lower()
        http_method = event["httpMethod"]
        path = event["resource"].rstrip("/")

        required_type = PATH_PERMISSIONS.get(f"{http_method} {path}")

        if required_type and user_type not in PATH_PERMISSIONS[f"{http_method} {path}"]:
            return generatePolicy(
                user_type,
                "Deny",
                f"User type {user_type} is not allowed to execute {http_method} {path}",
            )

        return generatePolicy(user_type, "Allow")

    except Exception as e:
        traceback.print_exc()
        return generatePolicy("null", "Deny")

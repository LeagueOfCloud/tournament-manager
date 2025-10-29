import pymysql
import os
import traceback

PATH_PERMISSIONS = {
    "POST /players": "admin",
    "DELETE /players": "admin",
    "PUT /players": "admin",
    "POST /teams": "admin",
    "DELETE /teams": "admin",
    "PUT /teams": "admin",
    "POST /riot-accounts": "admin",
    "DELETE /riot-accounts": "admin",
    "PUT /riot-accounts": "admin",
}

def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor
    )

def generatePolicy(principalId, effect, error_message = "You are not allowed to do this."):
    authResponse = {}
    authResponse['principalId'] = principalId
    if (effect and METHOD_ARN):
        policyDocument = {}
        policyDocument['Version'] = '2012-10-17'
        policyDocument['Statement'] = []
        statementOne = {}
        statementOne['Action'] = 'execute-api:Invoke'
        statementOne['Effect'] = effect
        statementOne['Resource'] = METHOD_ARN
        policyDocument['Statement'] = [statementOne]
        authResponse['policyDocument'] = policyDocument

        if effect == "Deny":
            authResponse['context'] = {
                'error_message': error_message
            }

    return authResponse

def lambda_handler(event, context):
    global METHOD_ARN
    METHOD_ARN = event["methodArn"]

    connection = None

    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM profiles WHERE token = %s", 
                (event["headers"]["Authorization"])
            )
            result = cursor.fetchone()
        
        if result == None:
            return generatePolicy("null", "Deny", "Invalid token provided")

        user_type = str(result.get("type", "null")).lower()
        http_method = event['httpMethod']
        path = event['path'].rstrip("/")

        required_type = PATH_PERMISSIONS.get(f"{http_method} {path}")

        if required_type and user_type != PATH_PERMISSIONS[f"{http_method} {path}"]:
            return generatePolicy(user_type, "Deny", f"User type {user_type} is not allowed to execute {http_method} {path}")

        return generatePolicy(user_type, "Allow")

    except Exception as e:
        traceback.print_exc()
        return generatePolicy("null", "Deny")

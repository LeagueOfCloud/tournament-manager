import pymysql

def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor
    )

def generatePolicy(principalId, effect):
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

    return authResponse

def lambda_handler(event, context):
    global METHOD_ARN
    METHOD_ARN = event["methodArn"]

    connection = None

    try:
        connection = create_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM profiles WHERE token = ?", 
                (event["headers"]["Authorization"])
            )
            cursor.fetchone()
            print(result)

    except:
        return generatePolicy("null", "Deny")

    return generatePolicy("null", "Deny")
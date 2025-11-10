# Tournament Manager (EUW)
> The League of Legends Tournament Manager is a mostly-serverless application utilising technologies to create a system to easily host and handle a gaming event.

## Prerequisites
- An Amazon Web Services (AWS) Account
- Python 3.13
- AWS SAM CLI: [Installation Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started.html)

## Deploying
Clone the repository and run the following commands:
```bash
# Change Directory into the repository
cd tournament-manager

# Build & Deploy SAM application
sam build -t cloudformation/main.yaml
sam deploy
```
This will deploy all the necessary resources to the `eu-west-1` regino of your AWS account.

## Adding an API Route
Follow these steps to add a new API route:
1. Create a new folder in the `cloudformation/lambdas/` directory, give it the name of your function.
2. Inside it, add an `src/` folder and create an `app.py` file. That is where your lambda function's code will exist.
3. Write your lambda function, and add any dependencies on a `requirements.txt` file inside the same directory.
4. Edit `main.yaml`
    - Add the following template in the file and edit any values you need:
    ```yaml
    MyNewLambda:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: lambdas/<lambda-directory>/src
      Handler: app.lambda_handler
      Timeout: <lambda-timeout-seconds>
      Runtime: python3.13
      Events: # This whole parameter can be ignored if you do not want to link the lambda to an API route
        ApiEndpoint:
            Type: Api
            Properties:
              Path: /<api-route>
              Method: <api-method> # POST, DELETE, PUT, GET, PATCH, etc.
              RestApiId: !Ref Api
      Environment:
        Variables:
          ENV_KEY: "ENV_VALUE"
    ```

## Database Migrations
1. Install the [MySQL Extension](https://marketplace.visualstudio.com/items?itemName=cweijan.vscode-mysql-client2) to your Visual Studio Code.
2. Login to your Database.
3. Afterwards, you can navigate to the `db_migration/` directory and run any migrations by clicking the file and pressing the `Run` button on top.
# Tournament manager
## Deploying Lambdas
If you are **creating** a new function:
- Create a new directory in the `lambdas` folder, give it the name of the lambda function
- Create a `template.yaml` and copy-paste the contents of `lambdas/example-lambda/template.yaml` and change the values to fit your case
- Create a `src` folder and put inside `app.py` with the code of the function you want
- If you need dependencies, add a `requirements.txt` and specify them there

If you are **updating** a function, simply modify the code inside the `app.py` file.
**LAMBDA FUNCTIONS CAN HAVE MULTIPLE FILES! ADD THEM ALL TO THE `src` FOLDER**

Once you push, go to the [Actions Page](https://github.com/LeagueOfCloud/tournament-manager/actions), locate the `Deploy Lambda Functions` action, and trigger a workflow dispatch to the branch you have to deploy the lambda.

> [Documentation on Serverless Functions in template.yaml](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-function.html)

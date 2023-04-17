# JobUploader

## Install Serverless
```
curl -o- -L https://slss.io/install | bash
sls plugin install -n serverless-python-requirements
```

## Config AWS CLI
* [Install](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) 
* [Configure](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)

## Run Job Management Service locally
```
pip install -r requirements.txt
python JobManager.py
python MessageHandler.py
```

## Deploy
```
pip install -r requirements.txt
serverless deploy --stage dev --region us-west-2
```

## Test
```
python -m unittest tests.JobCommonServiceTest
```
# SageMaker Jupyter Notebooks
Run On-Demand Jupyter notebooks on AWS SageMaker.

Automate the launching of AWS SageMaker notebook instances to run Jupyter Notebooks on the cloud.

Found it difficult to run Jupyter Hub and have the spawner be tied with SageMaker especially in gov cloud where it is not possible at this time. This may be used as an alternative.

## What It Does
Launches a SageMaker notebook instance inside your created VPC. This script will return a pre-signed url that you will use to connect to the notebook instances. The script is implemented with AWS Parameter Store and AWS Lambda to control the shutdown of the Notebook instances it creates. The default timelimit for these isntances is 24 hours but can be changed when running the script.

## How To Use
sagemaker.yml contains the cloudformation that will launch the necessary resources. Notebookhandler.py can be placed anywhere as long as you have the permission stated in iam_roles.json.

## Commands
* python3 NotebookHandler.py start
* python3 NotebookHandler.py stop
* python3 NotebookHandler.py start --time-limit x
(Where x is the amount of hours to keep the instance launched)

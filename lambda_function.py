import json
from datetime import datetime, timedelta
import boto3

ssm = boto3.client('ssm')
sage_client = boto3.client('sagemaker', region_name='us-west-1')
def stop(user):
    try:
        name = user + 'NotebookInstance'
        sage_client.stop_notebook_instance(NotebookInstanceName=name)
        try:
            waiter = sage_client.get_waiter('notebook_instance_stopped')
            print('Stopping notebook\n\nThis may take a few minutes.')
            waiter.wait(NotebookInstanceName=user + 'NotebookInstance')
        except Exception as e:
            if tries > max:
                raise e
            tries += 1
            sleep(20)
    except Exception as e:
        print('Cant shutdown ' + user + 'NotebookInstance. Might be shutdown already')

def checkIfShutdown(timeLimit, launchTime):
    hours_from_now = datetime.utcnow() - timedelta(hours=timeLimit)
    hours_from_now_datetime = datetime.datetime.strptime(hours_from_now, "%H:%M:%S - %B/%d/%y")
    dateLaunchTime = datetime.datetime.strptime(launchTime, "%H:%M:%S - %B/%d/%y")
    if launchTime < hours_from_now:
        return True
    else:
        return False

def checkIfDelete(user):
    response = sage_client.describe_notebook_instance(
        NotebookInstanceName=user + 'NotebookInstance'
    )
    if response['NotebookInstanceStatus'] != 'InService':
        return True
    else:
        return False



response = ssm.get_parameter(
    Name='SageMakerData'
)

shutdownList = response['Parameter']['Value'].split('---')


for instance in shutdownList:
    jsonInstance = json.loads(instance)
    user = jsonInstance['User']
    launchTime = jsonInstance['Launch']
    timeLimit = jsonInstance['Limit']
    if checkIfShutdown(timeLimit, launchTime):
        stop(user)
        shutdownList.remove(instance)
    else:
        if checkIfDelete(user):
            shutdownList.remove(instance)
        else:
            print('Not time to shutdown.')

stringList = shutdownList.join('---')
ssm.put_parameter(
    Name='SageMakerData',
    Value=stringList,
    Type='String',
    Overwrite=True
)
import json
from datetime import datetime, timedelta
import boto3
ssm = boto3.client('ssm')
sage_client = boto3.client('sagemaker', region_name='us-gov-west-1')


def stop(user):
    try:
        name = user + 'NotebookInstance'
        sage_client.stop_notebook_instance(NotebookInstanceName=name)
    except Exception as e:
        print('Cant shutdown ' + user + 'NotebookInstance. Might be shutdown already')

def checkIfShutdown(timeLimit, launchTime):
    
    dateLaunchTime = datetime.strptime(launchTime, "%H:%M:%S - %B/%d/%y")
    hours_from_then = dateLaunchTime + timedelta(hours=timeLimit)
    print("Time to shutdown: " + str(hours_from_then))
    print("Time launched: " + str(dateLaunchTime))
    print("Time now: " + str(datetime.utcnow()))
    if datetime.utcnow() > hours_from_then:
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

def lambda_handler(event, context):
    response = ssm.get_parameter(
        Name='SageMakerData'
    )
    
    shutdownList = response['Parameter']['Value'].split('---')
    noList = ['', '']
    print(shutdownList)
    if shutdownList == noList:
        return
    
    for instance in shutdownList:
        jsonInstance = json.loads(instance)
        user = jsonInstance['User']
        launchTime = jsonInstance['Launch']
        timeLimit = jsonInstance['Limit']
        if checkIfShutdown(int(timeLimit), launchTime):
            stop(user)
            shutdownList.remove(instance)
        else:
            if checkIfDelete(user):
                shutdownList.remove(instance)
            else:
                print('Not time to shutdown.')
    
    stringList = '---'.join(map(str, shutdownList))
    print(stringList)
    if stringList == '':
        stringList = '---'
    ssm.put_parameter(
        Name='SageMakerData',
        Value=stringList,
        Type='String',
        Overwrite=True
    )

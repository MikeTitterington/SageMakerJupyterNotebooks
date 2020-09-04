import sys
import os

REGION = "us-west-1"
ACCOUNT = "123456789"
SUBNET = "subnet-"
SECURITY = ["sg-"]

homedir = os.environ['HOME']
user = homedir.split('/')
user = user[2]
option = sys.argv[1]
limit = 24
n = len(sys.argv) 
for i in range(2, n): 
    if sys.argv[i] == '--time-limit':
        limit = sys.argv[i+1]

tries = 0
max = 7

def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        import pip
        pip.main(['install', package, '--user'])
    finally:
        import site
        from importlib import reload
        reload(site)
        globals()[package] = importlib.import_module(package)


install_and_import('boto3')
import boto3

sage_client = boto3.client('sagemaker', region_name=REGION)
ssm = boto3.client('ssm', region_name=REGION)

def start():
    notebook = get_task()
    if notebook is None:
        url = _create_new_task()
        response = ssm.get_parameter(
            Name='SageMakerData'
        )
        newParameter = repsonse['Parameter']['Value']
        data = '{"User": "' + user + '","Launch": "' + datetime.strftime(datetime.utcnow(),"%H:%M:%S - %B/%d/%y") + '","Limit": "' + limit + '"}'
        if newParameter == '---':
            newParameter = newParameter + '---' + data
        else:
            newParameter = data
        ssm.put_parameter(
            Name='SageMakerData',
            Value=newParameter,
            Type='String',
            Overwrite=True
        )
        print('Press Enter for you presigned URL. Paste this into your browser to connect to the notebook.')
        x = input()
        return url
    else:
        url = sage_client.create_presigned_notebook_instance_url(NotebookInstanceName=user + 'NotebookInstance')['AuthorizedUrl']
        print('Press Enter for you presigned URL. Paste this into your browser to connect to the notebook.')
        x = input()
        return url
    raise ValueError('Not handled yet')

def stop():
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

def get_task():
    notebooks = sage_client.list_notebook_instances(
        NameContains=user,
        StatusEquals='InService'
    )
    if notebooks and len(notebooks['NotebookInstances']) > 0:
        return sage_client.describe_notebook_instance(
            NotebookInstanceName=notebooks['NotebookInstances'][0]['NotebookInstanceName']
        )['NotebookInstanceName'][0]
    else:
        print("No notebooks found 'InService'")
        return None

def _create_new_task():
    notebooks = sage_client.list_notebook_instances(
        NameContains=user,
        StatusEquals='Stopped'
    )
    if notebooks and len(notebooks['NotebookInstances']) > 0:
        sage_client.start_notebook_instance(NotebookInstanceName=user + 'NotebookInstance')
        try:
            print("Found 'Stopped' notebook... Starting notebook\n\nThis may take a few minutes.")
            waiter = sage_client.get_waiter('notebook_instance_in_service')
            waiter.wait(NotebookInstanceName=user + 'NotebookInstance')
        except Exception as e:
            if tries > max:
                raise e
            tries += 1
            sleep(20)
        response = sage_client.create_presigned_notebook_instance_url(NotebookInstanceName=user + 'NotebookInstance')

        return response['AuthorizedUrl']
    else:
        print("\nNo notebooks found 'Stopped'... Creating new notebook\n\nThis may take a few minutes.")
        notebook = sage_client.create_notebook_instance(NotebookInstanceName=user + 'NotebookInstance',
                                                        InstanceType='ml.p3.2xlarge',
                                                        RoleArn='arn:aws:iam::ACCOUNT:role/AmazonSageMaker-ExecutionRole',
                                                        SubnetId=SUBNET,
                                                        LifecycleConfigName='Configure-LDAP',
                                                        SecurityGroupIds=SECURITY
        )
        try:
            waiter = sage_client.get_waiter('notebook_instance_in_service')
            waiter.wait(NotebookInstanceName=user + 'NotebookInstance')
        except Exception as e:
            if tries > max:
                raise e
            tries += 1
            sleep(20)

        response = sage_client.create_presigned_notebook_instance_url(NotebookInstanceName=user + 'NotebookInstance')

        return response['AuthorizedUrl']

if option.lower() == 'start':
    print('Starting notebook for User: ' + user)
    print(start())
elif option.lower() == 'stop':
    print('Stopping notebook for User: ' + user)
    stop()
    print('Stopped')
else:
    print('No valid argument given. start/stop')
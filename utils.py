import boto3
from botocore.exceptions import ClientError

def alter_instance(client, instance_id, state):
    method = client.start_instances if state == 'ON' else client.stop_instances

    try:
        method(InstanceIds = [instance_id], DryRun = True)
    except ClientError as e:
        print(e)

    try:
        response = method(InstanceIds = [instance_id], DryRun = False)
        print("Successfully {} the instance. Here is the response: {}".format("started" if state == 'ON' else "stopped", 
                                                                              response))
    except ClientError as e:
        print(e)


import boto3
import sys
from datetime import datetime
import time


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 3:
        print('%s image_name cluster_name extra_args' % sys.argv[0])
        exit(-1)

    image_name = args[0]
    cluster_name = args[1]
    extra_args = args[2]
    #print(image_name, extra_args)

    print('acquiring docker image url...')
    ecr = boto3.client('ecr')
    docker_image_repo_endpoint = ecr.get_authorization_token()['authorizationData'][0]['proxyEndpoint'].replace('https://', '')
    docker_image_ref = '%s/%s:latest' % (docker_image_repo_endpoint, image_name)
    #print(docker_image_ref)

    print('\ncreating ecs cluster...')
    ecs = boto3.client('ecs')
    ret = ecs.create_cluster(clusterName=cluster_name)
    #print(ret)

    print('\ncreating task definition...')
    ret = ecs.register_task_definition(
        family=cluster_name,
        networkMode='awsvpc',
        taskRoleArn='ecsTaskExecutionRole',
        executionRoleArn='ecsTaskExecutionRole',
        containerDefinitions=[
            {
                'name': 'python',
                'image': docker_image_ref,
                'cpu': 512,
                'memory': 1024,
                'command': [extra_args],
                'logConfiguration': {
                    'logDriver': 'awslogs',
                    'options': {
                        'awslogs-group': '/ecs/datacloud-collector',
                        'awslogs-region': 'us-east-1',
                        'awslogs-stream-prefix': 'ecs'
                    }
                }
            }
        ],
        requiresCompatibilities=['FARGATE'],
        cpu='512',
        memory='1024'
    )
    #print(ret)

    print('\nrun task...')
    ret = ecs.run_task(
        cluster=cluster_name,
        taskDefinition=cluster_name,
        overrides={
            'containerOverrides': [
                {
                    'name': 'python',
                    'environment': [
                        {
                            'name': 'DATA_CLOUD_USE_CONSUL',
                            'value': 'true'
                        },
                    ]
                }
            ]
        },
        count=1,
        launchType='FARGATE',
        startedBy=datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S.%f_UTC"),
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [
                    'subnet-a7b9e388', 'subnet-3eb0b15a', 'subnet-d7c59c8a'
                ],
                'assignPublicIp': 'DISABLED'
            }
        }
    )
    #print(ret)

    print('\n%s: waiting task to finish...' % datetime.now().strftime("%H:%M:%S.%f"))
    tick0 = time.time()
    arn = ret["tasks"][0]['taskArn']
    waiter = ecs.get_waiter('tasks_stopped')
    waiter.wait(cluster=cluster_name, tasks=[arn])
    tick1 = time.time()
    print('%s: running task takes %f secs' % (datetime.now().strftime("%H:%M:%S.%f"), (tick1 - tick0)))

    print('\ndeleteing task definition...')
    ret = ecs.deregister_task_definition(taskDefinition='%s:1' % cluster_name)
    #print(ret)

    print('\ndeleting ecs cluster...')
    ecs.delete_cluster(cluster=cluster_name)
    #print(ret)


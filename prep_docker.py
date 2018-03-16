import boto3
import sys
import os
import base64


if __name__ == '__main__':
    args = sys.argv[1:]

    if len(args) < 2:
        print("%s image_name dockerfile_path" % sys.argv[0])
        exit(-1)

    image_name = args[0]
    dockerfile_path = args[1]
    print('image name: ', image_name)
    print('dockerfile path: ', dockerfile_path)

    ecr = boto3.client('ecr')

    print('\nacquiring repo info...')
    repo_info = None
    try:
        repo_info = ecr.describe_repositories(repositoryNames=[image_name])['repositories'][0]
    except Exception:
        repo_info = ecr.create_repository(repositoryName=image_name)['repository']

    print('\nacquiring auth token...')
    auth_info = ecr.get_authorization_token()['authorizationData'][0]


    print('\ndocker login...')
    os.chdir(dockerfile_path)
    print('current dir: ', os.getcwd())
    docker_pwd = base64.b64decode(auth_info['authorizationToken'].encode('ascii'))[4:].decode('utf-8')
    docker_login = 'sudo -E docker login -u AWS -p %s %s' % (docker_pwd, auth_info['proxyEndpoint'])
    os.system(docker_login)

    print('\nbuilding docker image...')
    os.system('sudo -E bash build.sh %s' % image_name)

    print('\ntagging docker image...')
    endpoint = auth_info['proxyEndpoint'].replace('https://', '')
    os.system('sudo -E docker tag %s:latest %s/%s:latest' % (image_name, endpoint, image_name))

    print('\npushing docker image to aws ecr...')
    os.system('sudo -E docker push %s/%s:latest' % (endpoint, image_name))


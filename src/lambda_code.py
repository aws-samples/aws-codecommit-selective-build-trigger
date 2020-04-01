""" 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
"""

import os

import boto3
from botocore.exceptions import ClientError

# Module level variables initialization
CODE_BUILD_PROJECT = os.getenv('CODE_BUILD_PROJECT')
ECR_REPO_NAME = os.getenv('ECR_REPO_NAME')

codecommit = boto3.client('codecommit')
cb = boto3.client('codebuild')


def getLastCommitLog(repository, commitId):
    response = codecommit.get_commit(
        repositoryName=repository,
        commitId=commitId
    )
    return response['commit']


def getFileDifferences(repository_name, lastCommitID, previousCommitID):
    response = None

    if previousCommitID != None:
        response = codecommit.get_differences(
            repositoryName=repository_name,
            beforeCommitSpecifier=previousCommitID,
            afterCommitSpecifier=lastCommitID
        )
    else:
        # The case of getting initial commit (Without beforeCommitSpecifier)
        response = codecommit.get_differences(
            repositoryName=repository_name,
            afterCommitSpecifier=lastCommitID
        )

    differences = []

    if response == None:
        return differences

    while "nextToken" in response:
        response = codecommit.get_differences(
            repositoryName=repository_name,
            beforeCommitSpecifier=previousCommitID,
            afterCommitSpecifier=lastCommitID,
            nextToken=response["nextToken"]
        )
        differences += response.get("differences", [])
    else:
        differences += response["differences"]

    return differences


def getLastCommitID(repository, branch="master"):
    response = codecommit.get_branch(
        repositoryName=repository,
        branchName=branch
    )
    commitId = response['branch']['commitId']
    return commitId


def lambda_handler(event, context):

    # Initialize needed variables
    file_extension_allowed = [".pyo", ".npy", ".py"]
    fileNames_allowed = ["DockerFile", "Dockerfile"]
    commit_hash = event['Records'][0]['codecommit']['references'][0]['commit']
    region = event['Records'][0]['awsRegion']
    repo_name = event['Records'][0]['eventSourceARN'].split(':')[-1]
    account_id = event['Records'][0]['eventSourceARN'].split(':')[4]
    branchName = os.path.basename(
        str(event['Records'][0]['codecommit']['references'][0]['ref']))

    # Get commit ID for fetching the commit log
    if (commit_hash == None) or (commit_hash == '0000000000000000000000000000000000000000'):
        commit_hash = getLastCommitID(repo_name, branchName)

    lastCommit = getLastCommitLog(repo_name, commit_hash)

    previousCommitID = None
    if len(lastCommit['parents']) > 0:
        previousCommitID = lastCommit['parents'][0]

    print('lastCommitID: {0} previousCommitID: {1}'.format(
        commit_hash, previousCommitID))

    differences = getFileDifferences(repo_name, commit_hash, previousCommitID)

    # Check whether specific file or specific extension file is added/modified
    # and set flag for build triggering
    doTriggerBuild = False
    for diff in differences:
        root, extension = os.path.splitext(str(diff['afterBlob']['path']))
        fileName = os.path.basename(str(diff['afterBlob']['path']))
        if ((extension in file_extension_allowed) or (fileName in fileNames_allowed)):
            doTriggerBuild = True

    # Trigger codebuild job to build the repository if needed
    if doTriggerBuild:
        build = {
            'projectName': CODE_BUILD_PROJECT,
            'sourceVersion': commit_hash,
            'sourceTypeOverride': 'CODECOMMIT',
            'sourceLocationOverride': 'https://git-codecommit.%s.amazonaws.com/v1/repos/%s' % (region, repo_name),
            'environmentVariablesOverride': [
                {
                    'name': 'AWS_DEFAULT_REGION',
                    'value': region,
                    'type': 'PLAINTEXT'
                },
                {
                    'name': 'ECR_REPO',
                    'value': ECR_REPO_NAME,
                    'type': 'PLAINTEXT'
                },
                {
                    'name': 'AWS_ACCOUNT_ID',
                    'value': account_id,
                    'type': 'PLAINTEXT'
                }
            ]
        }

        print("Building docker image from repo %s in region %s" %
              (repo_name, region))

        # build all the things and push to Amazon ECR!
        cb.start_build(**build)
    else:
        print('Changed files does not match any triggers. Hence docker image build is suppressed')
    return 'Success.'

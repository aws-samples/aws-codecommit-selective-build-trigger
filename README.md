# aws-codecommit-selective-build-trigger

This demo illustrates the deployment of AWS Lambda to build Docker Images of application in AWS CodeCommit repository automatically when selective files are modified and the changes are pushed to the repository. The AWS Lambda receives the AWS CodeCommit events for push to repository and triggers a AWS CodeBuild job to build the Docker image and push to AWS Elastic Container Registry.

AWS services used for the CI/CD portion:

- [AWS CodeCommit](https://aws.amazon.com/codecommit/)
- [AWS CodeBuild](https://aws.amazon.com/codebuild/)
- [AWS CloudFormation](https://aws.amazon.com/cloudformation/)
- [AWS Lambda](https://aws.amazon.com/lambda/)
- [Amazon Elastic Container Registry](https://aws.amazon.com/ecr/)

## Solution Diagram

![Solution Diagram](assets/aws-codecommit-selective-build-trigger.png)

## Stack deployment

The cloudformation stack can be deployed using Cloudoformation page in AWS Console or using the AWS CLI as shown below

First, zip and upload the lambda code to an S3 bucket

`cd src/`

`zip lambda.zip lambda_code.py`

`aws s3 cp lambda.zip s3://aws-codecommit-selective-build-trigger/`

Trigger the cloudformation stack creation pointing to that S3 bucket zip.

`aws cloudformation create-stack --stack-name myteststack --template-body file://src/aws-codecommit-selective-build-trigger.yml --parameters ParameterKey=ProjectName,ParameterValue=testproject ParameterKey=LambdaZipS3Bucket,ParameterValue=codecommit-selective-build ParameterKey=LambdaZipS3Key,ParameterValue=lambda.zip`

## Components details

[src/aws-codecommit-selective-build-trigger.yml](src/aws-codecommit-selective-build-trigger.yml) - Cloudformation template for demonstrating the solution of AWS Lambda triggered AWS CodeBuild job based on changes to specific files in AWS CodeCommit repository

[src/lambda_code.py](src/lambda_code.py) - Python code for AWS Lambda to filter the AWS CodeCommit event and find the files changed as part of the commit and trigger AWS CodeBuild job if needed.

[src/lambda.zip](src/lambda.zip) - Compressed zip file for lambda_code.py file for deploying using Cloudformation template

# License

This library is licensed under the MIT-0 License. See the LICENSE file.


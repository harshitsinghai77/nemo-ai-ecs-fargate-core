import os
from dotenv import load_dotenv

from aws_cdk import (
    Stack,
    aws_ecs as _ecs,
    aws_iam as _iam,
    aws_logs as _logs,
    aws_ec2 as _ec2,
    aws_ecr as _ecr,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct

load_dotenv(dotenv_path='.lambda.env')
open_telemetry_envs = {
    key: value for key, value in os.environ.items() if key.startswith("OTEL_")
}


class NemoAIECSFargateStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = _ec2.Vpc(self, "NemoAIVPC",
            max_azs=1,
            subnet_configuration=[
                _ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=_ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )

        cluster = _ecs.Cluster(self,"NemoAIECSCluster", cluster_name="nemo-ai-ecs-fargate-cluster", vpc=vpc)

        ecr_repo = _ecr.Repository.from_repository_name(
            self, "NemoAIEcrRepo", repository_name="nemo-ai-agent"
        )

        log_group = _logs.LogGroup(
            self, "NemoAIContainerLogGroup",
            log_group_name="/ecs/nemo-ai-container",
            retention=_logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        log_driver = _ecs.LogDriver.aws_logs(
            stream_prefix="nemo-ai-ecs",
            log_group=log_group
        )

        task_role = _iam.Role(self, "NemoAIECSTaskRole",
            assumed_by=_iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                _iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ],
            inline_policies={
                "BedrockAccess": _iam.PolicyDocument(
                    statements=[
                        _iam.PolicyStatement(
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:InvokeModelWithResponseStream",

                                "bedrock-agentcore:CreateCodeInterpreter",
                                "bedrock-agentcore:StartCodeInterpreterSession",
                                "bedrock-agentcore:InvokeCodeInterpreter",
                                "bedrock-agentcore:StopCodeInterpreterSession",
                                "bedrock-agentcore:DeleteCodeInterpreter",
                                "bedrock-agentcore:ListCodeInterpreters",
                                "bedrock-agentcore:GetCodeInterpreter"
                            ],
                            resources=["*"]
                        )
                    ]
                ),
                "SecretsAccess": _iam.PolicyDocument(
                    statements=[
                        _iam.PolicyStatement(
                            actions=[
                                "secretsmanager:GetSecretValue"
                            ],
                            resources=[f"arn:aws:secretsmanager:us-east-1:{Stack.of(self).account}:secret:github_personal_access_token-mhV2eN"],
                        )
                    ]
                )
            }
        )

        task_definition = _ecs.FargateTaskDefinition(self, "NemoAIECSTaskDefinition",
            memory_limit_mib=1024,
            cpu=512,
            execution_role=task_role,
            task_role=task_role
        )
        task_definition.add_container(
            "NemoAIECSContainer",
            image=_ecs.ContainerImage.from_ecr_repository(
                repository=ecr_repo,
                tag="latest"
            ),
            logging=log_driver,
            memory_limit_mib=1024,
            cpu=512,
            environment={
                "AWS_ACCOUNT_ID": Stack.of(self).account,
                "AGENT_OBSERVABILITY_ENABLED": "true",
                **open_telemetry_envs
            }
        )

        CfnOutput(self, "TaskDefinitionArn", value=task_definition.task_definition_arn,  description="Task Definition ARN for Nemo AI ECS Fargate Task")
        CfnOutput(self, "TaskRoleArn", value=task_role.role_arn, description="Task Role ARN for Nemo AI ECS Fargate Task")
        CfnOutput(self, "ClusterName", value=cluster.cluster_name, description="Cluster Name for Nemo AI ECS Fargate Task")


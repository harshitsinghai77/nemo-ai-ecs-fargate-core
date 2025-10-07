from aws_cdk import (
    Stack,
    aws_ecs as _ecs,
    aws_iam as _iam,
    aws_logs as _logs,
    aws_ec2 as _ec2,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct

class NemoAIECSFargateStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        aws_account = Stack.of(self).account

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

        cluster = _ecs.Cluster(self,"NemoAIECSCluster", vpc=vpc)

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
            image=_ecs.ContainerImage.from_registry(
                f"{aws_account}.dkr.ecr.us-east-1.amazonaws.com/cdk-hnb659fds-container-assets-{aws_account}-us-east-1:2fbe690d0ca765bdb0a6ea08ebe5700722be63eaf8a00e39d7442b99e7360ce8"
            ),
            logging=log_driver,
            memory_limit_mib=1024,
            cpu=512,
        )

        CfnOutput(self, "TaskDefinitionArn", value=task_definition.task_definition_arn,  description="Task Definition ARN for Nemo AI ECS Fargate Task")
        CfnOutput(self, "TaskRoleArn", value=task_role.role_arn, description="Task Role ARN for Nemo AI ECS Fargate Task")
        CfnOutput(self, "ClusterName", value=cluster.cluster_name, description="Cluster Name for Nemo AI ECS Fargate Task")


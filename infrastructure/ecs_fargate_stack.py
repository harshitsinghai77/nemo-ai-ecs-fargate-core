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

        vpc = _ec2.Vpc(self, "NemoAIVPC",
            max_azs=1,
            subnet_configuration=[
                _ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=_ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                _ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=_ec2.SubnetType.PRIVATE_WITH_EGRESS,
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
                                "bedrock:InvokeModelWithResponseStream"
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
                "850995537443.dkr.ecr.us-east-1.amazonaws.com/cdk-hnb659fds-container-assets-850995537443-us-east-1:c1e458dd0768927ad7c0ac911784e0c75dcfe9a79903324635f93b40a0a12994"
            ),
            logging=log_driver,
            memory_limit_mib=1024,
            cpu=512,
        )

        CfnOutput(self, "TaskDefinitionArn", value=task_definition.task_definition_arn,  description="Task Definition ARN for Nemo AI ECS Fargate Task")
        CfnOutput(self, "TaskRoleArn", value=task_role.role_arn, description="Task Role ARN for Nemo AI ECS Fargate Task")
        CfnOutput(self, "ClusterName", value=cluster.cluster_name, description="Cluster Name for Nemo AI ECS Fargate Task")


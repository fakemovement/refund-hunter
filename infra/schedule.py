"""Create (or update) the daily EventBridge schedule that runs Refund Hunter on AgentCore.

    python infra/schedule.py --runtime-arn arn:aws:bedrock-agentcore:...   # create/update, ENABLED
    python infra/schedule.py --disable                                     # pause it

The schedule invokes the runtime once a day with {"action": "run"}. One invocation a day keeps
the bill at pennies: the agent only runs when the schedule fires or a person presses "Run".
"""

from __future__ import annotations

import argparse
import json
import os
import time

import boto3

REGION = os.getenv("RH_AWS_REGION", "us-east-1")
NAME = "refundhunter-daily"
ROLE_NAME = "refundhunter-scheduler-role"

iam = boto3.client("iam")
scheduler = boto3.client("scheduler", region_name=REGION)
sts = boto3.client("sts")


def ensure_role(runtime_arn: str) -> str:
    trust = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": "scheduler.amazonaws.com"}, "Action": "sts:AssumeRole"}
        ],
    }
    try:
        arn = iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]
    except iam.exceptions.NoSuchEntityException:
        arn = iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust))["Role"]["Arn"]
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": ["bedrock-agentcore:InvokeAgentRuntime"], "Resource": [runtime_arn, runtime_arn + "/*"]}
        ],
    }
    iam.put_role_policy(RoleName=ROLE_NAME, PolicyName="invoke-refundhunter", PolicyDocument=json.dumps(policy))
    return arn


def upsert(runtime_arn: str, expression: str, state: str) -> None:
    role_arn = ensure_role(runtime_arn)
    target = {
        "Arn": "arn:aws:scheduler:::aws-sdk:bedrockagentcore:invokeAgentRuntime",
        "RoleArn": role_arn,
        "Input": json.dumps(
            {
                "AgentRuntimeArn": runtime_arn,
                "RuntimeSessionId": "refundhunter-daily-run-0000000000000000000000",
                "Payload": json.dumps({"action": "run", "user_id": "local", "trigger": "schedule"}),
                "ContentType": "application/json",
            }
        ),
    }
    kwargs = dict(
        Name=NAME,
        ScheduleExpression=expression,
        ScheduleExpressionTimezone="America/Los_Angeles",
        FlexibleTimeWindow={"Mode": "OFF"},
        Target=target,
        State=state,
        Description="Refund Hunter: read receipts, find refunds, ask for a yes, file claims.",
    )
    # A role created seconds ago is not always visible to Scheduler yet; retry briefly.
    for attempt in range(8):
        try:
            try:
                scheduler.get_schedule(Name=NAME)
                scheduler.update_schedule(**kwargs)
                print(f"updated schedule {NAME} ({state})")
            except scheduler.exceptions.ResourceNotFoundException:
                scheduler.create_schedule(**kwargs)
                print(f"created schedule {NAME} ({state})")
            return
        except scheduler.exceptions.ValidationException as e:
            if "assume the role" not in str(e) or attempt == 7:
                raise
            time.sleep(5)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-arn", default=os.getenv("RH_AGENT_RUNTIME_ARN"))
    ap.add_argument("--cron", default="cron(0 8 * * ? *)", help="default: 8:00 AM Pacific daily")
    ap.add_argument("--disable", action="store_true")
    a = ap.parse_args()
    if a.disable:
        s = scheduler.get_schedule(Name=NAME)
        scheduler.update_schedule(
            Name=NAME, ScheduleExpression=s["ScheduleExpression"], FlexibleTimeWindow=s["FlexibleTimeWindow"],
            Target=s["Target"], State="DISABLED", ScheduleExpressionTimezone=s.get("ScheduleExpressionTimezone", "UTC"),
        )
        print("disabled")
    else:
        if not a.runtime_arn:
            raise SystemExit("--runtime-arn required (or RH_AGENT_RUNTIME_ARN)")
        upsert(a.runtime_arn, a.cron, "ENABLED")

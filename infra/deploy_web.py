"""Put the dashboard on AWS Lambda with a public URL (the "try it" link).

    python infra/deploy_web.py                 # build the zip, create/update the function, print the URL

The function runs the FastAPI app through Mangum. It reads state from DynamoDB and forwards
"run" / "decide" to the AgentCore runtime, so it never loads the agents itself (no Strands in
the zip). Cost: a Lambda invocation per page view; the agent work is billed on the runtime.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
BUILD = ROOT / "build" / "web"
REGION = os.getenv("RH_AWS_REGION", "us-east-1")
FUNCTION = "refundhunter-web"
ROLE_NAME = "refundhunter-web-role"
TABLE = os.getenv("RH_DDB_TABLE", "refundhunter")


def env_deployed(key: str) -> str | None:
    p = BACKEND / ".env.deployed"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip()
    return os.getenv(key)


iam = boto3.client("iam")
lam = boto3.client("lambda", region_name=REGION)
sts = boto3.client("sts")
ACCOUNT = sts.get_caller_identity()["Account"]

DEPS = [
    "fastapi", "mangum", "pydantic", "pydantic-settings", "python-dotenv", "pyyaml",
    "httpx", "beautifulsoup4", "boto3",
]


def build_zip() -> bytes:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    pkg = BUILD / "pkg"
    subprocess.run(
        [
            "uv", "pip", "install", "--target", str(pkg), "--python-platform", "x86_64-manylinux2014",
            "--python-version", "3.12", "--only-binary", ":all:", "--quiet", *DEPS,
        ],
        check=True,
    )
    shutil.copytree(BACKEND / "refundhunter", pkg / "refundhunter", ignore=shutil.ignore_patterns("__pycache__"))
    (pkg / "lambda_handler.py").write_text(
        "from mangum import Mangum\n"
        "from refundhunter.api import app, run_via_runtime\n"
        "_http = Mangum(app, lifespan='off')\n\n"
        "def handler(event, context):\n"
        "    # A background self-invocation carries {'action': 'run'}; everything else is HTTP.\n"
        "    if isinstance(event, dict) and event.get('action') == 'run':\n"
        "        return run_via_runtime(event)\n"
        "    return _http(event, context)\n",
        encoding="utf-8",
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in pkg.rglob("*"):
            if f.is_file() and "__pycache__" not in f.parts and not f.suffix == ".pyc":
                z.write(f, f.relative_to(pkg).as_posix())
    data = buf.getvalue()
    print(f"zip: {len(data) / 1e6:.1f} MB")
    return data


def ensure_role(runtime_arn: str) -> str:
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    try:
        arn = iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]
    except iam.exceptions.NoSuchEntityException:
        arn = iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust))["Role"]["Arn"]
        iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
        time.sleep(8)
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query", "dynamodb:DescribeTable"],
             "Resource": f"arn:aws:dynamodb:{REGION}:{ACCOUNT}:table/{TABLE}"},
            {"Effect": "Allow", "Action": ["bedrock-agentcore:InvokeAgentRuntime"], "Resource": [runtime_arn, runtime_arn + "/*"]},
            {"Effect": "Allow", "Action": ["lambda:InvokeFunction"],
             "Resource": f"arn:aws:lambda:{REGION}:{ACCOUNT}:function:{FUNCTION}"},
        ],
    }
    iam.put_role_policy(RoleName=ROLE_NAME, PolicyName="refundhunter-web", PolicyDocument=json.dumps(policy))
    return arn


def deploy(zip_bytes: bytes, role_arn: str, runtime_arn: str) -> str:
    env = {
        "RH_STORE": "dynamodb", "RH_DDB_TABLE": TABLE, "RH_AWS_REGION": REGION,
        "RH_AGENT_RUNTIME_ARN": runtime_arn, "RH_DATA_DIR": "/tmp/refundhunter", "RH_MAIL_SOURCE": "fixtures",
        "PYTHONUTF8": "1",
    }
    try:
        lam.get_function(FunctionName=FUNCTION)
        lam.update_function_configuration(FunctionName=FUNCTION, Environment={"Variables": env}, Timeout=300, MemorySize=512, Role=role_arn)
        lam.get_waiter("function_updated").wait(FunctionName=FUNCTION)
        lam.update_function_code(FunctionName=FUNCTION, ZipFile=zip_bytes)
        lam.get_waiter("function_updated").wait(FunctionName=FUNCTION)
        print("updated function")
    except lam.exceptions.ResourceNotFoundException:
        for attempt in range(6):
            try:
                lam.create_function(
                    FunctionName=FUNCTION, Runtime="python3.12", Role=role_arn, Handler="lambda_handler.handler",
                    Code={"ZipFile": zip_bytes}, Timeout=300, MemorySize=512, Environment={"Variables": env},
                    Description="Refund Hunter dashboard (public demo)",
                )
                break
            except lam.exceptions.InvalidParameterValueException as e:
                if "role" in str(e).lower() and attempt < 5:
                    time.sleep(6)
                    continue
                raise
        lam.get_waiter("function_active").wait(FunctionName=FUNCTION)
        print("created function")
    # Public entry point: an HTTP API in front of the function. (A plain Lambda function URL
    # answered 403 on this account, so API Gateway is the reliable route.)
    apig = boto3.client("apigatewayv2", region_name=REGION)
    existing = [a for a in apig.get_apis()["Items"] if a["Name"] == FUNCTION]
    if existing:
        return existing[0]["ApiEndpoint"] + "/"
    fn_arn = lam.get_function(FunctionName=FUNCTION)["Configuration"]["FunctionArn"]
    api = apig.create_api(Name=FUNCTION, ProtocolType="HTTP", Target=fn_arn)
    lam.add_permission(
        FunctionName=FUNCTION, StatementId="apigw-invoke", Action="lambda:InvokeFunction",
        Principal="apigateway.amazonaws.com",
        SourceArn=f"arn:aws:execute-api:{REGION}:{ACCOUNT}:{api['ApiId']}/*",
    )
    return api["ApiEndpoint"] + "/"


if __name__ == "__main__":
    runtime_arn = env_deployed("RH_AGENT_RUNTIME_ARN")
    if not runtime_arn:
        sys.exit("RH_AGENT_RUNTIME_ARN not set (backend/.env.deployed)")
    zip_bytes = build_zip()
    role = ensure_role(runtime_arn)
    url = deploy(zip_bytes, role, runtime_arn)
    print("URL:", url)

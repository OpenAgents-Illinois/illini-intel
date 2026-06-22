from __future__ import annotations

import os

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "us.meta.llama3-3-70b-instruct-v1:0"
)
DEFAULT_LEAGUE = os.environ.get("DEFAULT_LEAGUE", "mens-college-basketball")
DEFAULT_TEAM_A = os.environ.get("DEFAULT_TEAM_A", "356")  # Illinois
DEFAULT_TEAM_B = os.environ.get("DEFAULT_TEAM_B", "41")   # UConn

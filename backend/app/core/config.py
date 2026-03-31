from __future__ import annotations

import os

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "us.meta.llama3-3-70b-instruct-v1:0"
)
ILLINOIS_TEAM_ID = os.environ.get("ILLINOIS_TEAM_ID", "356")
UCONN_TEAM_ID = os.environ.get("UCONN_TEAM_ID", "41")
DEFAULT_GOAL = os.environ.get(
    "DEFAULT_GOAL", "Analyze Illinois basketball team for the upcoming game"
)
ESPN_BASE_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/"
    "mens-college-basketball"
)

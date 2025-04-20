# Example to illustrate code-gen
#   filename:  .jira_cache/system/issue_type_fields/Test.json
#   timestamp: 2025-04-20T20:03:40+00:00

from pydantic import BaseModel

class Schema(BaseModel):
    type: str
    system: str

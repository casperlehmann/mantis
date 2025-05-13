from pprint import pprint
from typing import Any

from pydantic import BaseModel

class IssueTypeFields(BaseModel):
    startAt: int
    maxResults: int
    total: int
    fields: list[dict[str, Any]]


class ProjectFieldKeys:
    def __init__(self, name: str, issue_type_fields: IssueTypeFields) -> None:
        self.name = name
        self.data = issue_type_fields

    @property
    def fields(self) -> list[str]:
        fields = self.data.fields
        assert fields, 'Issue_types does not contain "fields" field'
        assert len(fields) > 0
        return list([_['key'] for _ in fields])

    def show(self) -> None:
        pprint(", ".join(self.fields))

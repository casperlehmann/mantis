from pprint import pprint
from typing import Any

from pydantic import BaseModel


class IssueType(BaseModel):
    id: str
    description: str
    iconUrl: str
    name: str
    untranslatedName: str
    subtask: bool
    hierarchyLevel: int
    expand: str
    fields: dict[str, Any]


class Project(BaseModel):
    issuetypes: list[IssueType]
    expand: str
    id: str
    key: str
    name: str
    avatarUrls: dict[str, str]


class IssueTypeFields(BaseModel):
    projects: list[Project]
    expand: str


class ProjectFieldKeys:
    def __init__(self, name: str, issuetype_fields: IssueTypeFields) -> None:
        self.name = name
        self.data = issuetype_fields

    @property
    def fields(self) -> list[str]:
        projects = self.data.projects
        assert projects, 'Data does not contain "projects" field'
        assert len(projects) == 1, "Expected exactly one project"
        project = projects[0]
        issuetypes = project.issuetypes
        assert issuetypes, 'Projects does not contain "issuetypes" field'
        assert len(issuetypes) == 1, "Expected exactly one issuetype"
        issuetype = issuetypes[0]
        fields = issuetype.fields
        assert fields, 'Issue_types does not contain "fields" field'
        assert len(fields) > 0
        return list(fields.keys())

    def show(self) -> None:
        pprint(", ".join(self.fields))

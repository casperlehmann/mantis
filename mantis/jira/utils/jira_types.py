from typing import Any, Mapping

class IssueType(Mapping[str, dict[str, Any]]):
    fields = dict[str, dict]

class Project(Mapping[str, list[IssueType]]):
    issuetypes = list[IssueType]

class IssueTypeFields(Mapping[str, list[Project]]):
    projects = list[Project]


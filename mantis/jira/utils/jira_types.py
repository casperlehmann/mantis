from typing import Any, Mapping

class IssueType(Mapping[str, dict[str, Any]]):
    fields = dict[str, dict]

class Project(Mapping[str, list[IssueType]]):
    issuetypes = list[IssueType]

class IssueTypeFields(Mapping[str, list[Project]]):
    projects = list[Project]

class ProjectFieldKeys:
    def __init__(self, name: str, data: IssueTypeFields) -> None:
        self.name = name
        self.raw_data = data
        self.data = IssueTypeFields(**data)

    @property
    def fields(self) -> list[str]:
        projects = self.data.projects
        assert projects, 'Data does not contain "projects" field'
        assert len(projects) == 1, 'Expected exactly one project'
        project = projects[0]
        issue_types = project.issuetypes
        assert issue_types, 'Projects does not contain "issuetypes" field'
        assert len(issue_types) == 1, 'Expected exactly one issue_type'
        issue_type = issue_types[0]
        fields = issue_type.fields
        assert fields, 'Issue_types does not contain "fields" field'
        assert len(fields) > 0
        return list(fields.keys())

    def show(self) -> None:
        pprint(', '.join(self.fields))


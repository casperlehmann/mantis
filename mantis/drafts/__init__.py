import re
from typing import Callable, TYPE_CHECKING

import frontmatter

# To-do: Create converter for Jira syntax to markdown.
j2m: Callable[[str], str] = lambda x: x

if TYPE_CHECKING:
    from mantis.jira import JiraIssue
    from mantis.jira.jira_client import JiraClient


class Draft:
    def __init__(self, jira: "JiraClient", issue: "JiraIssue") -> None:
        self.template = self.load_template()
        assert jira.drafts_dir
        self.jira = jira
        self.issue = issue
        self.draft_path = self.jira.drafts_dir / f"{self.key}.md"
        self.summary = self.issue.get_field("summary", "")
        assert self.required_frontmatter == ['ignore', 'header', 'project', 'parent', 'summary', 'status', 'issuetype', 'assignee', 'reporter']
        self._materialize()

    @property
    def key(self):
        key = self.issue.get("key")
        assert key, "No key in issue"
        assert (len(key) < 20), f'The length of the key is suspiciously long: "{key[:20]}..."'
        return key

    @property
    def formatted_header(self):
        return f'[{self.key}] {self.summary}'

    @property
    def required_frontmatter(self):
        return list(self.template.metadata.keys())

    def load_template(self):
        with open('mantis/drafts/template.md', 'r') as f:
            return frontmatter.load(f)

    def generate_frontmatter(self):
        for field_name in self.required_frontmatter:
            value = self.issue.get_field(field_name, None)
            template_value = self.template.metadata.get(field_name)
            if str(template_value) in ('True', 'False'):
                self.template.metadata[field_name] = template_value
            elif isinstance(value, dict):
                for nested_field in ('displayName', 'name'):
                    if nested_field in value:
                        self.template.metadata[field_name] = value.get(nested_field)
            else:
                self.template.metadata[field_name] = value
        # The header is not a Jira field.
        self.template.metadata['header'] = self.formatted_header

    def generate_body(self):
        description = self.issue.get_field("description")
        self.template.content = (self.template.content
            .replace('{summary}', self.summary)
            .replace('{description}', j2m(description))
        )

    def _materialize(self) -> None:
        self.generate_frontmatter()
        self.generate_body()
        with open(self.draft_path, "wb") as f:
            frontmatter.dump(self.template, f)

    def remove_draft_header(self, post: frontmatter.Post):
        extra_header = f'# {self.summary}'
        post.content = re.sub("^" + re.escape(extra_header)+'\\n*', '', post.content)
        return post

    def read_draft(self):
        with open(self.draft_path, "r") as f:
            draft_data = frontmatter.load(f)
        draft_data = self.remove_draft_header(draft_data)
        return draft_data

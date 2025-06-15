import re
from typing import Any, Callable, TYPE_CHECKING, Generator

import frontmatter  # type: ignore

# To-do: Create converter for Jira syntax to markdown.
j2m: Callable[[str], str] = lambda x: x

if TYPE_CHECKING:
    from mantis.jira import JiraIssue
    from mantis.jira.jira_client import JiraClient


class Draft:
    def __init__(self, jira: "JiraClient", issue: "JiraIssue") -> None:
        self.template = self._load_template()
        assert jira.drafts_dir
        self.jira = jira
        self.issue = issue
        self.draft_path = self.jira.drafts_dir / f"{self.key}.md"
        self.summary = self.issue.get_field("summary", "")
        assert self._required_frontmatter == ['header', 'project', 'parent', 'summary', 'status', 'issuetype', 'assignee', 'reporter']
        self._materialize()

    @property
    def key(self) -> dict:
        key = self.issue.get("key")
        assert key, "No key in issue"
        assert (len(key) < 20), f'The length of the key is suspiciously long: "{key[:20]}..."'
        return key

    @property
    def formatted_header(self) -> str:
        return f'[{self.key}] {self.summary}'

    @property
    def _required_frontmatter(self) -> list[str]:
        return list(self.template.metadata.keys())

    def _load_template(self) -> frontmatter.Post:
        with open('mantis/drafts/template.md', 'r') as f:
            return frontmatter.load(f)

    def _generate_frontmatter(self) -> None:
        for field_name in self._required_frontmatter:
            value = self.issue.get_field(field_name, None)
            template_value = self.template.metadata.get(field_name)
            if str(template_value) in ('True', 'False'):
                self.template.metadata[field_name] = template_value
            elif isinstance(value, dict):
                for nested_field in (
                    'displayName', # Users
                    'name', # Most other fields
                    'key' # Parent
                    # To-do...
                ):
                    if nested_field in value:
                        self.template.metadata[field_name] = value.get(nested_field)
                        # Note: We break, in order to avoid `key` overwriting `name` in cases like:
                        # - name: E-Commerce Checkout System
                        # = key: ECS
                        break
            else:
                self.template.metadata[field_name] = value
        # The header is not a Jira field.
        self.template.metadata['header'] = self.formatted_header

    def _generate_body(self) -> None:
        description = self.issue.get_field("description") or "Placeholder description"
        if self.jira.options.chat_gpt_activated:
            description = self.jira.assistant.convert_text_format(
                input_text=description,
                target_format=self.jira.assistant.TextFormat.MARKDOWN
            )
        self.template.content = (
            self.template.content
                .replace('{summary}', self.summary)
                .replace('{description}', description)
        )

    def _materialize(self) -> None:
        # Only write if not exists!
        if not self.draft_path.exists():
            self._generate_frontmatter()
            self._generate_body()
            with open(self.draft_path, "wb") as f:
                frontmatter.dump(self.template, f)
                
    def _validate_draft(self) -> None:
        if '---' not in self.raw_draft:
            raise ValueError(f'Draft file at {self.draft_path} does not contain the expected separator: "---": {self.raw_draft}')
        if f'# {self.summary}' not in self.raw_draft:
            raise ValueError(f'Draft file at {self.draft_path} does not contain the expected header: "# {self.summary}"')

    def _remove_draft_header(self, post: frontmatter.Post) -> frontmatter.Post:
        extra_header = f'# {self.summary}'
        post.content = re.sub("^" + re.escape(extra_header)+'\\n*', '', post.content)
        return post

    @property
    def raw_draft(self) -> str:
        with open(self.draft_path, "r") as f:
            data = f.read()
        if not data:
            raise ValueError('Draft file does not contain any content')
        return data

    @property
    def header_from_raw(self) -> str:
        try:
            content = self.raw_draft.split('---')[2].strip()
        except IndexError:
            raise ValueError('Draft file has no content')
        try:
            header = content.split('\n')[0]
        except IndexError:
            raise ValueError('Draft file is empty')
        if not header.startswith('# '):
            raise ValueError(f'Expected draft to start with a markdown header ("#"). Got: "{header}"')
        if not header == f'# {self.summary}':
            raise ValueError(f'Expected draft header to match summary. Got: "{header}" || "{self.summary}"')
        return header

    def read_draft(self) -> frontmatter.Post:
        with open(self.draft_path, "r") as f:
            draft_data = frontmatter.load(f)
        draft_data = self._remove_draft_header(draft_data)
        return draft_data

    def iter_draft_field_items(self) -> Generator[tuple[str, Any], None, None]:
        local_vars = ('header')
        draft_data = self.read_draft()
        for draft_field_key in draft_data.keys():
            if draft_field_key in local_vars:  # E.g. Local custom fields
                continue
            yield draft_field_key, draft_data.get(draft_field_key)

    def iter_draft_field_keys(self) -> Generator[str, None, None]:
        local_vars = ('header')
        draft_data = self.read_draft()
        for draft_field_key in draft_data.keys():
            if draft_field_key in local_vars:  # E.g. Local custom fields
                continue
            yield draft_field_key

    def get(self, key: str, default: Any = None) -> Any:
        local_vars = ('header')
        draft_data = self.read_draft()
        return draft_data.get(key, default)

    @property
    def content(self) -> str:
        """Return the content of the draft."""
        return self.read_draft().content

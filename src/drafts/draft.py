from pathlib import Path
import re
from typing import Any, TYPE_CHECKING, Generator
import frontmatter  # type: ignore

from enums import TextFormat
from .template_md import template

# To-do: Create converter for Jira syntax to markdown.
def j2m(x: str) -> str:
        return x

if TYPE_CHECKING:
    from jira import JiraIssue
    from mantis.mantis_client import MantisClient

class Draft:
    """Represents a draft file for a Jira issue."""
    # Local custom fields that are not in Jira.
    LOCAL_VARS = {'header'}
    REQUIRED_FRONTMATTER = ['header', 'project', 'parent', 'summary', 'status', 'issuetype', 'assignee', 'reporter']

    def __init__(self, mantis: 'MantisClient', issue: "JiraIssue") -> None:
        self.mantis = mantis
        self.issue = issue
        self.template = self._load_template()
        self.summary = self.issue.get_field("summary", "")
        assert self.mantis.drafts_dir
        assert self._required_frontmatter == self.REQUIRED_FRONTMATTER, (
            f'Unexpected required frontmatter: {self._required_frontmatter}'
        )
        self._materialize()

    @property
    def draft_path(self) -> Path:
        return self.mantis.drafts_dir / f"{self.key}.md"

    @property
    def key(self) -> str:
        key = self.issue.get("key")
        assert key, "No key in issue"
        assert len(key) < 20, f'The length of the key is suspiciously long: "{key[:20]}..."'
        return key

    @property
    def formatted_header(self) -> str:
        return f'[{self.key}] {self.summary}'

    @property
    def _required_frontmatter(self) -> list[str]:
        return list(self.template.metadata.keys())

    def _load_template(self) -> frontmatter.Post:
        return frontmatter.loads(template)

    def _generate_frontmatter(self) -> None:
        """Populate the template's metadata with values from the issue."""
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
        """Fill in the template body with summary and description."""
        description = self.issue.get_field("description") or "Placeholder description"
        if self.mantis.options.chat_gpt_activated:
            description = self.mantis.assistant.convert_text_format(
                input_text=description,
                target_format=TextFormat.MARKDOWN
            )
        self.template.content = (
            self.template.content
                .replace('{summary}', self.summary)
                .replace('{description}', description)
        )

    def _materialize(self) -> None:
        """Write the draft file if it does not already exist."""
        if not self.draft_path.exists():
            self._generate_frontmatter()
            self._generate_body()
            with open(self.draft_path, "wb") as f:
                frontmatter.dump(self.template, f)

    def _validate_draft(self) -> None:
        """Ensure the draft file has the expected structure."""
        raw = self.raw_draft
        if '---' not in raw:
            raise ValueError(f'Draft file at {self.draft_path} does not contain the expected separator: "---": {raw}')
        if f'# {self.summary}' not in raw:
            raise ValueError(f'Draft file at {self.draft_path} does not contain the expected header: "# {self.summary}"')

    def _remove_draft_header(self) -> str:
        """Remove the extra header from the draft file content and return the result as a string."""
        extra_header = f'# {self.summary}'
        content = self.load_frontmatter().content
        new_content = re.sub(rf"^{re.escape(extra_header)}\n*", '', content)
        return new_content

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
        if header != f'# {self.summary}':
            raise ValueError(f'Expected draft header to match summary. Got: "{header}" || "{self.summary}"')
        return header

    def load_frontmatter(self) -> frontmatter.Post:
        """Load the frontmatter from the draft file."""
        with open(self.draft_path, "r") as f:
            return frontmatter.load(f)
            
    def read_draft(self) -> frontmatter.Post:
        draft_data = self.load_frontmatter()
        draft_data.content = self._remove_draft_header()
        return draft_data

    def iter_draft_field_items(self) -> Generator[tuple[str, Any], None, None]:
        draft_data = self.read_draft()
        for draft_field_key in draft_data.keys():
            if draft_field_key in self.LOCAL_VARS:
                continue
            yield draft_field_key, draft_data.get(draft_field_key)

    def iter_draft_field_keys(self) -> Generator[str, None, None]:
        draft_data = self.read_draft()
        for draft_field_key in draft_data.keys():
            if draft_field_key in self.LOCAL_VARS:
                continue
            yield draft_field_key

    def get(self, key: str, default: Any = None) -> Any:
        draft_data = self.read_draft()
        return draft_data.get(key, default)

    @property
    def content(self) -> str:
        """Return the content of the draft."""
        return self.read_draft().content

    @content.setter
    def content(self, new_content: str) -> None:
        self._validate_draft()
        if not self.draft_path.exists():
            raise FileNotFoundError(f'Draft file at {self.draft_path} does not exist.')
        with open(self.draft_path, "r") as f:
            data = frontmatter.load(f)
        data.content = self.header_from_raw + '\n\n' + new_content
        with open(self.draft_path, "wb") as f:
            frontmatter.dump(data, f)

    def make_verbose(self) -> dict[str, str]:
        """Expand the content of the draft using the assistant."""
        original_content = self.content
        verbose_content = self.mantis.assistant.make_verbose(original_content)
        self.content = verbose_content
        return {'original_content': original_content, 'verbose_content': verbose_content}

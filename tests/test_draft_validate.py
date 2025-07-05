import pytest
from types import SimpleNamespace

class DummyDraft:
    def __init__(self, raw, summary="Summary", path="/tmp/draft.md"):
        self.raw_draft = raw
        self.summary = summary
        self.draft_path = path
    def _validate_draft(self):
        raw = self.raw_draft
        if '---' not in raw:
            raise ValueError(f'Draft file at {self.draft_path} does not contain the expected separator: "---": {raw}')
        if f'# {self.summary}' not in raw:
            raise ValueError(f'Draft file at {self.draft_path} does not contain the expected header: "# {self.summary}"')


def test_validate_draft_missing_separator():
    draft = DummyDraft("no frontmatter here\n# Summary\nBody text")
    with pytest.raises(ValueError, match='expected separator'):
        draft._validate_draft()

def test_validate_draft_missing_header():
    draft = DummyDraft("---\nmeta\n---\n# NotTheSummary\nBody text")
    with pytest.raises(ValueError, match='expected header'):
        draft._validate_draft()

def test_validate_draft_valid():
    draft = DummyDraft("---\nmeta\n---\n# Summary\nBody text")
    # Should not raise
    draft._validate_draft()

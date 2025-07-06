import pytest
from types import SimpleNamespace
import tempfile
import os
from src.drafts.draft import Draft

class DummyDraft:
    def __init__(self, raw, summary="Summary", path="/tmp/draft.md"):
        self._raw = raw
        self.summary = summary
        self.draft_path = path
    def _validate_draft(self):
        raw = self.raw_draft
        if '---' not in raw:
            raise ValueError(f'Draft file at {self.draft_path} does not contain the expected separator: "---": {raw}')
        if f'# {self.summary}' not in raw:
            raise ValueError(f'Draft file at {self.draft_path} does not contain the expected header: "# {self.summary}"')
    @property
    def raw_draft(self):
        return self._raw


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

def test_raw_draft_returns_content():
    content = '---\nmeta\n---\n# Summary\nBody text'
    with tempfile.NamedTemporaryFile('w+', delete=False) as tf:
        tf.write(content)
        tf.flush()
        class DummyDraftFile:
            draft_path = tf.name
            @property
            def raw_draft(self):
                with open(self.draft_path, 'r') as f:
                    content = f.read()
                if not content.strip():
                    raise ValueError(f'Draft file at {self.draft_path} does not contain any content')
                return content
        draft = DummyDraftFile()
        result = draft.raw_draft
        assert result == content
    os.unlink(tf.name)

def test_raw_draft_empty_raises():
    with tempfile.NamedTemporaryFile('w+', delete=False) as tf:
        tf.write('')
        tf.flush()
        class DummyDraftFile:
            draft_path = tf.name
            @property
            def raw_draft(self):
                with open(self.draft_path, 'r') as f:
                    content = f.read()
                if not content.strip():
                    raise ValueError(f'Draft file at {self.draft_path} does not contain any content')
                return content
        draft = DummyDraftFile()
        with pytest.raises(ValueError, match='does not contain any content'):
            draft.raw_draft
    os.unlink(tf.name)

# test header_from_raw

def test_header_from_raw_valid():
    class DummyDraft(Draft):
        def __init__(self): pass
        @property
        def raw_draft(self):
            return "---\nmeta\n---\n# Summary\nBody text"
        @property
        def summary(self):
            return "Summary"
    draft = DummyDraft()
    assert draft.header_from_raw == '# Summary'

def test_header_from_raw_no_content():
    class DummyDraft(Draft):
        def __init__(self): pass
        @property
        def raw_draft(self):
            return "---\nmeta\n---"
        @property
        def summary(self):
            return "Summary"
    draft = DummyDraft()
    with pytest.raises(ValueError, match='markdown header'):
        draft.header_from_raw

def test_header_from_raw_empty():
    class DummyDraft(Draft):
        def __init__(self): pass
        @property
        def raw_draft(self):
            return "---\nmeta\n---\n"
        @property
        def summary(self):
            return "Summary"
    draft = DummyDraft()
    with pytest.raises(ValueError, match='markdown header'):
        draft.header_from_raw

def test_header_from_raw_not_markdown():
    class DummyDraft(Draft):
        def __init__(self): pass
        @property
        def raw_draft(self):
            return "---\nmeta\n---\nNotAHeader\nBody text"
        @property
        def summary(self):
            return "Summary"
    draft = DummyDraft()
    with pytest.raises(ValueError, match='markdown header'):
        draft.header_from_raw

def test_header_from_raw_mismatch():
    class DummyDraft(Draft):
        def __init__(self): pass
        @property
        def raw_draft(self):
            return "---\nmeta\n---\n# NotTheSummary\nBody text"
        @property
        def summary(self):
            return "Summary"
    draft = DummyDraft()
    with pytest.raises(ValueError, match='header to match summary'):
        draft.header_from_raw

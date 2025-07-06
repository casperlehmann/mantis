import pytest
from mantis.mantis_client import MantisClient
from jira.config_loader.config_loader import JiraSystemConfigLoader
import tempfile
import pathlib

class DummyCache:
    def get_projects_from_system_cache(self): return None
    def get_issuetypes_from_system_cache(self): return None
    def get_createmeta_from_cache(self, _): return None
    def get_editmeta_from_cache(self, _): return None
    def write_to_system_cache(self, name, data): pass
    def write_issuetypes_to_system_cache(self, data): pass
    def write_createmeta(self, name, data): pass
    def write_editmeta(self, key, data): pass
    def iter_dir(self, name): return []
    @property
    def createmeta(self):
        d = tempfile.TemporaryDirectory()
        return pathlib.Path(d.name)
    @property
    def editmeta(self):
        d = tempfile.TemporaryDirectory()
        return pathlib.Path(d.name)

class DummyMantis:
    def __init__(self):
        self._no_read_cache = True
        self.cache = DummyCache()

class DummyJira:
    def __init__(self):
        self.mantis = DummyMantis()
        self.issues = type('I', (), {'load_allowed_types': lambda self: ['Epic', 'Task']})()
    def get_projects(self):
        return []
    def get_issuetypes(self):
        return {}
    def get_createmeta(self, _):
        return {}
    def get_editmeta(self, _):
        return {}
    def issuetype_name_to_id(self, name):
        return 1

@pytest.fixture
def loader():
    jira = DummyJira()
    return JiraSystemConfigLoader(jira)

def test_get_issuetypes_empty(loader):
    with pytest.raises(ValueError, match='length of zero'):
        loader.get_issuetypes(force_skip_cache=True)

def test_get_createmeta_empty(loader):
    with pytest.raises(ValueError, match='No content in createmeta'):
        loader.get_createmeta('Task', force_skip_cache=True)

def test_get_createmeta_no_fields():
    class J(DummyJira):
        def get_createmeta(self, _): return {'foo': 1}
    loader = JiraSystemConfigLoader(J())
    with pytest.raises(ValueError, match='has no fields'):
        loader.get_createmeta('Task', force_skip_cache=True)

def test_get_editmeta_empty(loader):
    with pytest.raises(ValueError, match='No content in editmeta'):
        loader.get_editmeta('KEY-1', force_skip_cache=True)

def test_get_editmeta_no_fields():
    class J(DummyJira):
        def get_editmeta(self, _): return {'foo': 1}
    loader = JiraSystemConfigLoader(J())
    with pytest.raises(ValueError, match='has no fields'):
        loader.get_editmeta('KEY-1', force_skip_cache=True)

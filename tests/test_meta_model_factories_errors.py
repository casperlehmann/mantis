import pytest
from jira.config_loader import meta_model_factories as mmf

class DummyJira:
    class mantis:
        class cache:
            @staticmethod
            def write_createmeta_schema(*a, **kw): pass
            @staticmethod
            def write_editmeta_schema(*a, **kw): pass
        plugins_dir = '.'

class DummySchema:
    key = 'customfield_1'
    name = 'Test Field'
    required = True
    schema_as_python_type = str
    @classmethod
    def model_validate(cls, val):
        return cls()

def test_createmeta_factory_type_errors():
    # meta_fields as dict triggers ValueError
    with pytest.raises(ValueError, match='should be of type list'):
        mmf.CreatemetaModelFactory({'fields': {}}, 'Bug', DummyJira())
    # meta_fields as wrong type triggers TypeError
    with pytest.raises(TypeError, match='should be of type list'):
        mmf.CreatemetaModelFactory({'fields': 123}, 'Bug', DummyJira())

def test_editmeta_factory_type_errors():
    # meta_fields as list triggers ValueError
    with pytest.raises(ValueError, match='should be of type dict'):
        mmf.EditmetaModelFactory({'fields': []}, 'Bug', DummyJira(), 'KEY-1')
    # meta_fields as wrong type triggers TypeError
    with pytest.raises(TypeError, match='should be of type dict'):
        mmf.EditmetaModelFactory({'fields': 123}, 'Bug', DummyJira(), 'KEY-1')

def test_iter_meta_fields_schema_errors():
    class BadMeta(mmf.MetaModelFactory):
        process = 'bad'
        ignored_non_meta_field = set()
        def __init__(self):
            self.metadata = {'fields': 123}
            self.out_fields = {}
            self.getters = {}
            self.attributes = []
        def field_by_key(self, key): pass
        def _write_plugin(self): pass
    b = BadMeta()
    with pytest.raises(ValueError, match='unexpected schema'):
        list(b._iter_meta_fields)
    b.metadata = {'fields': [123]}
    with pytest.raises(ValueError, match='unexpected schema'):
        list(b._iter_meta_fields)

def test_assign_python_type_optional():
    class F(mmf.MetaModelFactory):
        process = 'p'
        ignored_non_meta_field = set()
        def __init__(self):
            self.out_fields = {}
            self.getters = {}
            self.attributes = []
        def field_by_key(self, key): pass
        def _write_plugin(self): pass
    f = F()
    meta = DummySchema()
    meta.required = False
    f.assign_python_type(meta, 'foo')
    assert f.out_fields['foo'][1] is None

def test_assign_attributes_and_getters_customfield():
    class F(mmf.MetaModelFactory):
        process = 'p'
        ignored_non_meta_field = set()
        def __init__(self):
            self.out_fields = {}
            self.getters = {}
            self.attributes = []
        def field_by_key(self, key): pass
        def _write_plugin(self): pass
    f = F()
    meta = DummySchema()
    meta.name = 'Test Field'
    f.assign_attributes_and_getters(meta, 'customfield_123')
    assert 'test field' in f.attributes
    assert 'test_field' in f.getters

def test_field_by_key_editmeta():
    # Add required 'schema' fields to avoid ValidationError
    factory = mmf.EditmetaModelFactory(
        {'fields': {'foo': {
            'key': 'foo',
            'name': 'Foo',
            'required': True,
            'schema_as_python_type': str,
            'schema': {'type': 'string', 'system': 'foo-system'}
        }}},
        'Bug', DummyJira(), 'KEY-1', write_plugin=False)
    assert factory.field_by_key('foo')['key'] == 'foo'
    assert factory.field_by_key('bar', default=123) == 123

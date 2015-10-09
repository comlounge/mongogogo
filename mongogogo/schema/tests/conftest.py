from mongogogo.schema.filters import *
from mongogogo.schema.nodes import *

class SomeType(Schema):
    
    url = String()
    description = String()

class Bio(Schema):
    name = String()
    url = String()

class TestSchema1(Schema):
    """very simply schema to get started"""
    not_required = String()
    required = String(required=True)
    with_default = String(on_serialize=[Default("default")])

class TestSchema2(Schema):
    """very simply schema with a sub schema"""
    name = String()
    bio1 = Bio(on_serialize=[Default({'name': 'foobar'})])
    bio2 = Bio(required = True)

    
class UnderscoreTestSchema(Schema):
    """very simply schema with a sub schema"""
    _name = String()

class TestSchema12(Schema):
    name = String()
    permissions = List(String(), on_serialize = [Default([])])
    links = List(SomeType())
    bio = Bio(on_serialize=[Default({'name': 'foobar'})])

class SubSchema(TestSchema1):
    name2 = String()

def pytest_funcarg__schema1(request):
    return TestSchema1()

def pytest_funcarg__schema2(request):
    return TestSchema2()

def pytest_funcarg__subschema1(request):
    return SubSchema()

def pytest_funcarg__underscoreschema(request):
    return UnderscoreTestSchema()


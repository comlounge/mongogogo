from mongogogo.schema.filters import *
from mongogogo.schema.nodes import *

class SomeType(Schema):
    
    url = String()
    description = String()

class BioType(Schema):
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
    bio1 = BioType(on_serialize=[Default({'name': 'foobar'})])
    bio2 = BioType(required = True)

class TestSchema12(Schema):
    name = String()
    permissions = ListType(String(), on_serialize = [Default([])])
    links = ListType(SomeType())
    bio = BioType(on_serialize=[Default({'name': 'foobar'})])


def pytest_funcarg__schema1(request):
    return TestSchema1()

def pytest_funcarg__schema2(request):
    return TestSchema2()





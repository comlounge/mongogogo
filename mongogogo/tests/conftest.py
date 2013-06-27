import pymongo
import datetime
from mongogogo import Record, Collection
from mongogogo import String, DateTime, Integer, Dict, Default
from mongogogo import SchemaNode, Schema

DB_NAME = "mongogogo_testing_78827628762"

def setup_db():
    db = pymongo.Connection()[DB_NAME]
    return db

def teardown_db(db):
    #pymongo.Connection().drop_database(DB_NAME)
    db.persons.remove()
    db.barcamps.remove()

def pytest_funcarg__db(request):
    return request.cached_setup(
        setup = setup_db,
        teardown = teardown_db,
        scope = "function")

class Incrementor(SchemaNode):  

    def do_deserialize(self, value, data, **kw):
        return int(value)+1

class BioType(Schema):
    name = String()
    url = String()

class PersonSchema(Schema):
    firstname = String(required=True)
    lastname = String(default="foobar", required=True)
    creation = DateTime(required=True, default = datetime.datetime.utcnow)
    age = Integer(default=24)
    incr = Incrementor(default=1)
    d = Dict(default={}, dotted=True)
    e = Dict(default={}, dotted=False)
    #bio = BioType(on_serialize=[Default({'name': 'foobar'})])

class Person(Record):
    schema = PersonSchema()
    default_values = {
        'lastname' : 'foobar',
        'creation' : datetime.datetime.utcnow,
        'age'      : 24,
        'incrementor'      : 1,
        'd'      : {},
        'e'      : {},
        'bio'    : {'name' : 'foobar'},
    }

class Persons(Collection):
    data_class = Person

class SchemalessPerson(Record):
    schema = PersonSchema()
    schemaless = True

class SchemalessPersons(Collection):
    data_class = SchemalessPerson

def pytest_funcarg__persons(request):
    db = request.getfuncargvalue("db")
    return Persons(db.persons)

def pytest_funcarg__schemaless_persons(request):
    db = request.getfuncargvalue("db")
    return SchemalessPersons(db.persons)

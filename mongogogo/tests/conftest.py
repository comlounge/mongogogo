import pymongo
from mongogogo import Record, Collection, Schema, String

DB_NAME = "mongogogo_testing_78827628762"

def setup_db():
    db = pymongo.Connection()[DB_NAME]
    return db

def teardown_db(db):
    #pymongo.Connection().drop_database(DB_NAME)
    db.persons.remove()

def pytest_funcarg__db(request):
    return request.cached_setup(
        setup = setup_db,
        teardown = teardown_db,
        scope = "module")


class PersonSchema(Schema):
    firstname = String()
    lastname = String(default="foobar", required=True)

class Person(Record):
    schema = PersonSchema()

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

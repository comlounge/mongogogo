import pytest
import datetime

def test_add(db, persons):
    p = persons.data_class(firstname="Christian", lastname="Scholz")
    persons.save(p)
    assert p._id is not None

def test_get(db, persons):
    p = persons.data_class(firstname="Christian", lastname="Scholz")
    persons.save(p)
    p2 = persons[p._id]
    assert p2.lastname == "Scholz"

def test_defaults(db, persons):
    p = persons.data_class()
    assert p.lastname == "foobar"

def test_schemaless(db, schemaless_persons):
    p = schemaless_persons.data_class(firstname="Christian", lastname="Scholz", extra=1)
    schemaless_persons.save(p)
    p2 = schemaless_persons[p._id]
    assert p2.extra == 1

def test_schemaenforce(db, persons):
    p = persons.data_class(firstname="Christian", lastname="Scholz", extra=1)
    persons.save(p)
    p2 = persons[p._id]
    pytest.raises(AttributeError, lambda : p2.extra)

def test_callable_defaults(db, persons):
    p = persons.data_class()
    assert p.creation < datetime.datetime.utcnow()

def test_integerfield(db, persons):
    p = persons.data_class(firstname="Christian", lastname="Scholz", age="24")
    persons.save(p)
    p2 = persons[p._id]
    assert p2.age == 24

def test_dictfield_not_dotted(db, persons):
    p = persons.data_class(firstname="Christian", lastname="Scholz", e={'foo' : 'bar'})
    persons.save(p)
    p2 = persons[p._id]
    assert p2.e['foo'] == "bar"
    pytest.raises(AttributeError, lambda: p2.e.foo)


def test_dictfield_dotted(db, persons):
    p = persons.data_class(firstname="Christian", lastname="Scholz", d={'foo' : 'bar'})
    persons.save(p)
    p2 = persons[p._id]
    assert p2.d.foo == "bar"

def test_find(db, persons): 
    # insert some records into the database
    for i in range(1,10):
        p = persons.data_class(firstname="Christian%s" %i, lastname="Scholz%s" %i)
        persons.save(p)
    res = persons.find({'firstname':"Christian1"})
    assert res.count() == 1
    assert isinstance(res[0], persons.data_class)

def test_find_and_sort(db, persons): 
    # insert some records into the database
    for i in range(1,10):
        p = persons.data_class(firstname="Christian%s" %i, lastname="Scholz%s" %i, age=17)
        persons.save(p)
    res = persons.find({'age':17}).sort("firstname", 1)
    assert res[0].firstname == "Christian1"
    res = persons.find({'age':17}).sort("firstname", -1)
    assert res[0].firstname == "Christian9"


def test_find_one(db, persons): 
    # insert some records into the database
    for i in range(1,10):
        p = persons.data_class(firstname="Christian%s" %i, lastname="Scholz%s" %i)
        persons.save(p)
    person = persons.find_one({'firstname':"Christian1"})
    assert person.firstname == "Christian1"

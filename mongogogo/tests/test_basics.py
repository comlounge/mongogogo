import pytest
import datetime
from conftest import Person

def test_add(db, persons):
    p = persons.data_class(firstname="Foo", lastname="Bar")
    persons.save(p)
    assert p._id is not None

def test_add_via_class(db, persons):
    p = Person(firstname="Foo", lastname="Bar")
    persons.save(p)
    assert p._id is not None

def test_get(db, persons):
    p = persons.data_class(firstname="Foo", lastname="Bar")
    persons.save(p)
    p2 = persons[p._id]
    assert p2.lastname == "Bar"

def test_defaults(db, persons):
    p = persons.data_class()
    assert p.lastname == "foobar"

def test_callable_defaults(db, persons):
    p = persons.data_class()
    assert isinstance(p.creation,datetime.datetime)

def test_schemaless(db, schemaless_persons):
    p = schemaless_persons.data_class(firstname="Foo", lastname="Bar", extra=1)
    schemaless_persons.save(p)
    p2 = schemaless_persons[p._id]
    assert p2.extra == 1

def test_schemaenforce(db, persons):
    p = persons.data_class(firstname="Foo", lastname="Bar", extra=1)
    persons.save(p)
    p2 = persons[p._id]
    pytest.raises(AttributeError, lambda : p2.extra)

def test_callable_defaults(db, persons):
    p = persons.data_class()
    assert p.creation < datetime.datetime.utcnow()

def test_integerfield(db, persons):
    p = persons.data_class(firstname="Foo", lastname="Bar", age="24")
    persons.save(p)
    p2 = persons[p._id]
    assert p2.age == 24

def test_dictfield_not_dotted(db, persons):
    p = persons.data_class(firstname="Foo", lastname="Bar", e={'foo' : 'bar'})
    persons.save(p)
    p2 = persons[p._id]
    assert p2.e['foo'] == "bar"
    pytest.raises(AttributeError, lambda: p2.e.foo)


def test_dictfield_dotted(db, persons):
    p = persons.data_class(firstname="Foo", lastname="Bar", d={'foo' : 'bar'})
    persons.save(p)
    p2 = persons[p._id]
    assert p2.d.foo == "bar"

def test_find(db, persons): 
    # insert some records into the database
    for i in range(1,10):
        p = persons.data_class(firstname="Foo%s" %i, lastname="Bar%s" %i)
        persons.save(p)
    res = persons.find({'firstname':"Foo1"})
    assert res.count() == 1
    assert isinstance(res[0], persons.data_class)

def test_find_and_sort(db, persons): 
    # insert some records into the database
    for i in range(1,10):
        p = persons.data_class(firstname="Foo%s" %i, lastname="Bar%s" %i, age=17)
        persons.save(p)
    res = persons.find({'age':17}).sort("firstname", 1)
    assert res[0].firstname == "Foo1"
    res = persons.find({'age':17}).sort("firstname", -1)
    assert res[0].firstname == "Foo9"

def test_find_one(db, persons): 
    # insert some records into the database
    for i in range(1,10):
        p = persons.data_class(firstname="Foo%s" %i, lastname="Bar%s" %i)
        persons.save(p)
    person = persons.find_one({'firstname':"Foo1"})
    assert person.firstname == "Foo1"

def test_with_id(db, persons): 
    p = persons.data_class(firstname="Foo", lastname="Bar", _id=u"cs")
    persons.save(p)
    p2 = persons[u"cs"]
    assert p2._id == u"cs"

def test_with_id_and_find(db, persons): 
    p = persons.data_class(firstname="Foo", lastname="Bar", _id=u"cs")
    persons.save(p)
    p2 = persons.find_one({'_id' : u'cs'})
    assert p2._id == u"cs"

def test_deserialize_on_get(db, persons): 
    """check if the schema is properly deserialized on find(). We use a schema for it
    which increments the ``inc`` field by one on each retrieve."""
    p = persons.data_class(firstname="Foo", lastname="Bar", _id=u"cs")
    persons.save(p)
    p2 = persons.get(u'cs')
    assert p2.incr == 2
    persons.save(p2)
    p2 = persons.get(u'cs')
    assert p2.incr == 3

def test_deserialize_on_find_one(db, persons): 
    """check if the schema is properly deserialized on find(). We use a schema for it
    which increments the ``inc`` field by one on each retrieve."""
    p = persons.data_class(firstname="Foo", lastname="Bar", _id=u"cs")
    persons.save(p)
    p2 = persons.find_one({'_id' : u'cs'})
    assert p2.incr == 2
    persons.save(p2)
    p2 = persons.find_one({'_id' : u'cs'})
    assert p2.incr == 3

def test_initialize_with_doc(db, persons):
    # this initially gave an error because we serialized first
    # before storing the doc
    p = persons.data_class(firstname="Foo")
    persons.save(p)
    p2 = persons[p._id]
    assert p2.firstname == "Foo"


import pytest

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


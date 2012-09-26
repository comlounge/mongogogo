
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


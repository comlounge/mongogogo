"""

test script added for testing sub documents as they might overwrite each other and we
want this to be prevented. This is taken from camper so hence the names

"""

from mongogogo import *
import datetime

class Location(Schema):
    name = String()

class BarcampSchema(Schema):
    name                = String()
    location            = Location()
    locations           = List(Location())

class Barcamp(Record):

    schema = BarcampSchema()
    default_values = {
        'location'      : {}, # this might be a problem due to being an object
        'locations'     : [], # this might be a problem due to being an object
    }

class Barcamps(Collection):
    
    data_class = Barcamp

def test_subdict_with_default(db):
    """initially we had a bug where the dict in default_values was overwritten all the time
    because we did not copy it, yielding strange results in batch operations. This test makes sure 
    we don't run into it again for sub documents
    """
    barcamps = Barcamps(db.barcamps)
    for i in range(1,4):
        data = dict(
            name = str(i),
            location = {
                'name' : str(i)
            },
            locations = [{'name' : str(i)}]
        )
        barcamp = Barcamp(data, collection = barcamps)
        barcamp.put()

    # also in a loop we should keep the correct location information
    bcs = barcamps.find()
    a = []
    for b in bcs:
        a.append(b)
    for b in a:
        # all names should be equal here as this is how we set this up
        assert b['name'] == b.location['name']

def test_lists_with_default(db):
    """we test the same here for the list default"""
    barcamps = Barcamps(db.barcamps)
    for i in range(1,4):
        data = dict(
            name = str(i),
            locations = [{'name' : str(i)}]
        )
        barcamp = Barcamp(data, collection = barcamps)
        barcamp.put()

    # also in a loop we should keep the correct location information
    bcs = barcamps.find()
    a = []
    for b in bcs:
        a.append(b)
    for b in a:
        assert b['locations'][0]['name'] == b['name']

from mongogogo.schema import *
from conftest import TestSchema1
import pytest

class MyDict(dict):
    """custom dict for testing"""
    myname = "NameSchema"
    CUSTOM = True

def test_deserialize_to_class_simple():
    schema1 = TestSchema1(kls=MyDict)
    data = {'not_required' : 'n/a',
         'required' : 'Required',
         'with_default' : 'no default'}
    res = schema1.serialize(data)
    res = schema1.deserialize(res)
    assert res.CUSTOM == True



##############################################


def test_deserialize_to_class_list(schema1):

    class NameSchema(Schema):
        name = String()

    class Name(Schema):
        """content class for name schema"""

    class NamesSchema(Schema):
        """schema containing a list of names"""
        names = List(NameSchema(kls=Name)) 

    class Names(dict):
        """Content class for NamesSchema""" 
        myname = "NamesSchema"

    names = NamesSchema(kls=Names)
    data = {'names' : [{'name' : 'one'}, {'name' : 'two'}, {'name' : 'three'}]}
    res = names.serialize(data)
    res = names.deserialize(res)
    assert res.__class__.__name__ == "Names"

    # now check children
    assert res['names'][0].__class__.__name__ == "Name"



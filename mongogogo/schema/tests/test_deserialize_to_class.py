from mongogogo.schema import null, Invalid
import pytest

class MyDict(dict):
    """custom dict for testing"""

    CUSTOM = True


def test_deserialize_to_class(schema1):
    schema1.set_class(MyDict)
    data = {'not_required' : 'n/a',
         'required' : 'Required',
         'with_default' : 'no default'}
    res = schema1.serialize(data)
    res = schema1.deserialize(res)
    assert res.CUSTOM == True
    

    

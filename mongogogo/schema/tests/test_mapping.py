from mongogogo.schema import null, Invalid
import pytest

def test_basic_serialize_ok(schema1):
    
    data = {'not_required' : 'n/a',
         'required' : 'Required',
         'with_default' : 'no default'}
    res = schema1.serialize(data)
    assert res['not_required'] == "n/a"
    assert res['required'] == "Required"
    assert res['with_default'] == "no default"

def test_basic_serialize_with_default(schema1):
    
    data = {'not_required' : 'n/a',
         'required' : 'Required'}
    res = schema1.serialize(data)
    assert res['not_required'] == "n/a"
    assert res['required'] == "Required"
    assert res['with_default'] == "default"

def test_basic_serialize_with_missing(schema1):
    
    data = {'required' : 'Required'}
    res = schema1.serialize(data)
    assert res['not_required'] is null
    assert res['required'] == "Required"
    assert res['with_default'] == "default"

def test_basic_serialize_not_required(schema1):
    
    data = {'not_required' : 'Required'}
    pytest.raises(Invalid, schema1.serialize, data)

def test_basic_serialize_submapping_ok(schema2):
    data = {
        'bio1' : {
            'name' : 'Foo', 
            'url' : 'http://example.com', 
        },
        'bio2' : {
            'name' : 'Foo', 
            'url' : 'http://example.com', 
        }
    }
    res = schema2.serialize(data)
    assert res['bio1']['name'] == "Foo"
    assert res['bio2']['name'] == "Foo"
    assert res['bio1']['url'] == "http://example.com"
    assert res['bio2']['url'] == "http://example.com"

            
def test_basic_serialize_submapping_missing_bio2(schema2):
    data = {
        'bio1' : {
            'name' : 'Foo', 
            'url' : 'http://example.com', 
        },
    }
    pytest.raises(Invalid, schema2.serialize, data)

def test_basic_serialize_submapping_missing_bio1(schema2):

    data = {
        'bio2' : {
            'name' : 'Foo', 
            'url' : 'http://example.com', 
        },
    }

    res = schema2.serialize(data)
    assert res['bio1']['name'] == "foobar"
    assert res['bio2']['name'] == "Foo"
    assert res['bio1']['url'] == null
    assert res['bio2']['url'] == "http://example.com"
            

def test_basic_serialize_with_subclass(subschema1):
    
    data = {'not_required' : 'n/a',
         'name2' : 'hansi', # new field in this subschema
         'required' : 'Required',
         'with_default' : 'no default'}
    res = subschema1.serialize(data)
    assert res['not_required'] == "n/a"
    assert res['required'] == "Required"
    assert res['with_default'] == "no default"
    assert res['name2'] == "hansi"


def test_underscore_mapping(underscoreschema):
    
    data = {'_name' : 'foobar'}
    res = underscoreschema.serialize(data)
    assert res['_name'] == "foobar"

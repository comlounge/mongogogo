from mongogogo.schema import null, Invalid, String
import pytest

def test_basic_string_serialize_ok(schema1):
    s = String()
    v = s.serialize("foobar")
    assert v == "foobar"

def test_basic_string_serialize_not_required_and_missing(schema1):
    s = String()
    v = s.serialize()
    assert v == null

def test_basic_string_serialize_required_and_missing(schema1):
    s = String(required = True)
    pytest.raises(Invalid, s.serialize)

def test_basic_string_serialize_default_and_missing(schema1):
    s = String(required = True, default="foobar")
    v = s.serialize()
    assert v == "foobar"

def test_basic_string_serialize_default_and_missing(schema1):
    s = String(required = True, default="foobar")
    v = s.serialize()
    assert v == "foobar"


def test_basic_string_serialize_default_and_missing(schema1):
    s = String(required = True, default="foobar")
    v = s.serialize()
    assert v == "foobar"



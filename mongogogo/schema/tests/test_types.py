from mongogogo.schema import *
import pytest
import datetime

def test_datetime():
    s = DateTime()
    v = s.serialize(datetime.datetime.utcnow())
    assert v <= datetime.datetime.utcnow()
    assert isinstance(v, datetime.datetime)

def test_date():
    s = Date()
    v = s.serialize(datetime.date(2012, 3, 17))
    assert v.day == 17
    assert v.month == 3
    assert v.year == 2012
    assert isinstance(v, datetime.date)

def test_date_from_datetime():
    s = Date()
    v = s.serialize(datetime.datetime(2012, 3, 17, 18, 2))
    assert v.day == 17
    assert v.month == 3
    assert v.year == 2012
    assert isinstance(v, datetime.date)

def test_integer():
    s = Integer()
    v = s.serialize(2)
    assert v == 2

def test_integer_from_string():
    s = Integer()
    v = s.serialize("2")
    assert v == 2

def test_integer_min_ok():
    s = Integer(min=17)
    v = s.serialize(17)
    assert v == 17
    
def test_integer_min_not_ok():
    s = Integer(min=17)
    pytest.raises(Invalid, lambda : s.serialize(16))

def test_integer_max_ok():
    s = Integer(max=17)
    v = s.serialize(16)
    assert v == 16
    
def test_integer_max_not_ok():
    s = Integer(max=17)
    pytest.raises(Invalid, lambda : s.serialize(19))

def test_invalid_integer():
    s = Integer()
    pytest.raises(Invalid, lambda : s.serialize("a"))

def test_float():
    s = Float()
    v = s.serialize(2.3)
    assert v == 2.3

def test_float_from_string():
    s = Float()
    v = s.serialize("2.3")
    assert v == 2.3

def test_invalid_float():
    s = Float()
    pytest.raises(Invalid, lambda : s.serialize("a"))

def test_float_min_ok():
    s = Float(min=17.6)
    v = s.serialize(17.61)
    assert v == 17.61
    
def test_float_min_not_ok():
    s = Float(min=17.6)
    pytest.raises(Invalid, lambda : s.serialize(17.59))

def test_float_max_ok():
    s = Float(max=17.6)
    v = s.serialize(17.59)
    assert v == 17.59
    
def test_float_max_not_ok():
    s = Float(max=17.6)
    pytest.raises(Invalid, lambda : s.serialize(18.59))



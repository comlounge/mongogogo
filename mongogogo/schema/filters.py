from utils import Invalid, null

class Filter(object):
    """A Filter can be used on serialization and deserialization. It can either convert an incoming value to something
    else but also can do validation. In case it fails it's supposed to raise an ``Invalid`` exception."""

    def __call__(self, value, data, **kw):
        """call the actual filter. Passed in is the value to process in ``value`` and the complete incoming record
        in ``data``. Additional keyword arguments passed to ``serialize()`` or ``deserialize()`` are also passed into
        each filter. That way you can e.g. pass in database connections or similar constructs you might need inside
        a filter."""

        return value


class Default(Filter):
    """a filter which sets a default value if it is missing. Beware to not set this if you set required to True."""

    def __init__(self, item):
        """initialize the Default filter with the value to set. If ``item`` is callable then it will be called
        and the result will be set as default value"""
        self.item = item

    def __call__(self, value, data, **kw):
        """process the value"""
        if value is null:
            if callable(self.item):
                return self.item()
            else:
                return self.item
        return value

class EqualTo(Filter):
    """a filter which sets a default value if it is missing. Beware to not set this if you set required to True"""

    def __init__(self, field):
        self.field  = field

    def __call__(self, value, data, coll = None, **kw):
        """process the value"""
        if value != data[self.field]:
            raise Invalid(self, "fields do not match")
        return value


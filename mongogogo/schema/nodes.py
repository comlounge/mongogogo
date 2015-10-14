from utils import null, Invalid, marker, AttributeMapper
import datetime
import types
import dateutil.parser
import re

__all__ = [
    "SchemaNode",
    "Schema",
    "String",
    "Regexp",
    "Integer",
    "Float",
    "Boolean",
    "Date",
    "DateTime",
    "Dict",
    "List",
]

def get_class( kls ):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m


###
### nodes
###

class SchemaNode(object):
    """base class for all schema nodes which have to derive from it.

    It handles marking this node as schema node and doing instance counting
    in case the schema needs a defined sequence of nodes.
    """

    _schemanode = True # marker for meta class that this is part of the schema
    #_counter = 0 # this is a global counter which is incremented on instantiation of a type.

    def __new__(cls, *args, **kwargs):
        # increment the counter so we know which the original sequence of type nodes is. 
        #SchemaNode._counter += 1
        kls = kwargs.get("kls")
        if "kls" in kwargs:
            del kwargs['kls']
        instance = super(SchemaNode, cls).__new__(cls, *args, **kwargs)
        #instance._counter = SchemaNode._counter

        # now collect the nodes in this instance
        instance._mg_class = kls
        instance._nodes = []
        for name in dir(instance):
            if not name.startswith('__') and not name.startswith('_mg_'):
                field = getattr(instance, name)

                # filter out only the type elements. We have marker in the base class for that
                if hasattr(field, '_schemanode'):
                    field.name = name
                    instance._nodes.append((name, field))
        return instance

    def __init__(self, on_serialize = [], on_deserialize = [], default = marker, required = False, name = None, **kw): 
        """initialize the ``SchemaNode`` with generic parameters like queues, default and required flag

        :param on_serialize: a list of filters to be run before the actual serialization
        :param on_deserialize: a list of filters to be run before the actual deserialization
        :param default: If given this is the default for both serialization and deserialization. If you want
            separate values for serialization and deserialization use the ``Default`` filter in the
            respective filter queue. Also note that setting a default and required to True makes no sense
            as default is set before required is tested
        :param required: Define whether the field is required in both serialization and deserialization. The
            same like for default applies regarding separate queues. 
        :param name: the name of the field. In case it is included in a schema this will be set automatically
        """
        self.on_serialize = on_serialize
        self.on_deserialize = on_deserialize
        self.default = default
        self.required = required
        self.name = name


    def serialize(self, value = null, data = null, **kw):
        """serialize data to a data structure for MongoDB. If this is a combined node then 
        serialization on all sub nodes is called as well with it's respective value (or null in case
        it does not exist in the source data.

        The sequence is as follows:
        - first all filters in ``on_serialize`` are applied to the data. 
            Each filter is called with the ``value``, ``data`` and any passed additional keywords.
        - then the default check is done. If no value is available and ``default`` is set then this is used
        - lastly the required check is done.

        .. note:: Is this sequence right?

        :param value: The individual value for this node to serialize
        :param data: The whole record e.g. in case you need access to a different field for e.g. a 
            password test in a filter. Note that the this record is always the source record and not
            the serialized version as this can not be complete.  
        :param kw: Additional keywords which will be passed to the actual serialization code and filters
        :return: The serialized version of the data.
        
        """

        # this is for bootstrapping the master schema / mapping
        if data is null: 
            data = value

        for filter in self.on_serialize:
            value = filter(value, data, **kw)

        # check default
        if value is null and self.default is not marker:
            if callable(self.default):
                value = self.default()
            else:
                value = self.default

        # check required
        if value is null and self.required:
            raise Invalid(self, "required data missing")

        # now run the actual serialization
        return self.do_serialize(value, data, **kw)

    def deserialize(self, value = null, data = null, **kw):
        """deserialize MongoDB data to a python usable data structure. If this is a combined node then 
        deserialization on all sub nodes is called as well with it's respective value (or null in case
        it does not exist in the source data.)

        It will return the deserialized data of the complete source value.

        :param value: The individual value for this node to deserialize
        :param data: The whole record e.g. in case you need access to a different field for e.g. a 
            password test in a filter. Note that the this record is always the source record and not
            the deserialized version as this can not be complete.  
        :param kw: Additional keywords which will be passed to the actual deserialization code and filters
        :return: The deserialized version of the data.
        
        """

        # this is for bootstrapping the master schema / mapping
        if data is null: data = value

        for filter in self.on_deserialize:
            value = filter(value, data, **kw)

        # check default
        if value is null and self.default is not marker:
            value = self.default

        # check required
        if value is null and self.required:
            raise Invalid(self, "required data missing")

        # now run the actual deserialization
        data = self.do_deserialize(value, data, **kw)
        if self._mg_class is not None:
            return self._mg_class(data)
        return data

    def do_serialize(self, value, data, **kw):
        """the actual serialization code which you have to override in your own node implementations.
        The implementation has to return the single serialized value.
        """
        return value

    def do_deserialize(self, value, data, **kw):
        """the actual deserialization code which you have to override in your own node implementations.
        The implementation has to return the single deserialized value.
        """
        return value


class Schema(SchemaNode):

    def do_serialize(self, value, data = null, **kw):
        """serialize mapping data"""

        output = {} # of course we have a mapping as output
        for name, field in self._nodes:
            if value is None:
                raise ValueError, "node %s is missing from data and no default was given" %self.name
            # TODO: here exceptions with a detailed description of which field actually failed and why!
            sub_value = value.get(name, null)
            output[name] = field.serialize(sub_value, data = data, **kw)
        return output

    def deserialize(self, value, data = null, **kw):
        """deserialize from MongoDB to Python"""

        output = {} # of course we have a mapping as output
        for name, field in self._nodes:
            # TODO: here exceptions!
            sub_value = value.get(name, null)
            output[name] = field.deserialize(sub_value, data = data, **kw)
        if self._mg_class is not None:
            return self._mg_class(output)
        return output

class String(SchemaNode):
    """a string type. """

    def __init__(self, encoding = None, max_length = None, *args, **kw):
        """initialize the String Type"""
        super(String, self).__init__(*args, **kw)
        self.encoding = encoding
        self.max_length = max_length

    def do_serialize(self, value, data, **kw):
        """serialize data"""
        if value is None:
            if self.required:
                raise Invalid(self, "required data missing")
            else:
                # return something mongo compatible so not the null object
                return None
        if self.max_length is not None and len(value) > self.max_length:
            raise Invalid(self, "string too long")
        try:
            if isinstance(value, unicode):
                if self.encoding:
                    result = value.encode(self.encoding)
                else:
                    result = value
            else:
                encoding = self.encoding
                if encoding:
                    result = unicode(value, encoding).encode(encoding)
                else:
                    result = unicode(value)
            return result
        except Exception, e:
            raise Invalid(self, "Value '%s' cannot be serialized: %s" %(value, e))

class Regexp(String):
    """a string which has to conform to a regular expression"""

    def __init__(self, regexp, *args, **kw):
        """initialize the regexp node

        :param regexp: needs to be a re.compile instance or a pattern string 
        """
        super(Regexp, self).__init__(*args, **kw)
        if type(regexp) in [types.StringType, types.UnicodeType]:
            self.regexp = re.compile(regexp)
        else:
            self.regexp = regexp

    def do_serialize(self, value, data, **kw):
        """check the regexp"""

        # first the normal string checks
        value = super(Regexp, self).do_serialize(value, data, **kw)
        if self.regexp.match(value) is None:
            raise Invalid(self, "Value '%s' does not match regular expression" %(value))
        return value


class Date(SchemaNode):
    """a date type which converts DateTime objects to Date objects"""

    def do_serialize(self, value, data, **kw):
        if isinstance(value, datetime.datetime):
            value = value.date()
        elif value is None and not self.required:
            return None
        elif value is None and self.required:
            raise Invalid(self, "required data missing")
        elif not isinstance(value, datetime.date):
            raise Invalid(self, "Value '%s' is not an instance of datetime.datetime.Date" %(value))
        # we need to return a datetime object as mongo does not understand something else
        return datetime.datetime.combine(value, datetime.time())

    def do_deserialize(self, value, data, **kw):
        """convert datetime back to date"""
        if value is None:
            return value
        return value.date()

class DateTime(SchemaNode):
    """a datetime type. """

    def __init__(self, ignore_tz = False, *args, **kw):
        """initialize the datetime object"""
        super(DateTime, self).__init__(*args, **kw)
        self.ignore_tz = ignore_tz

    def do_serialize(self, value, data, **kw):
        # datetime.datetime also returns True for testing datetime.date

        # if datetime is a string try to convert it to a datetime object
        if isinstance(value, types.UnicodeType) or isinstance(value, types.StringType):
            value = dateutil.parser.parse(value, ignoretz = self.ignore_tz)
        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            value = datetime.datetime.combine(value, datetime.time())
        elif value is None and not self.required:
            return None
        elif value is None and self.required:
            raise Invalid(self, "required data missing")
        elif not isinstance(value, datetime.date):
            raise Invalid(self, "Value '%s' is not an instance of datetime.datetime" %(value))
        return value


class Dict(SchemaNode):
    """a dict type. """

    def __init__(self, subtype = None, dotted = False, *args, **kw):
        """initialize the Dict Type.

        :param dotted: if set to ``True`` then this dictionary will also allow dotted access using AttributeMapper
        
        """
        super(Dict, self).__init__(*args, **kw)
        self.dotted = dotted
        self.subtype = subtype

    def do_serialize(self, value, data, **kw):
        """serialize the dict"""
        if value is null and not self.required:
            value = {}
        elif value is null and self.required:
            raise Invalid(self, "required data missing")
        result = {}
        if self.subtype != None:
            for key, data in value.items():
                result[key] = self.subtype.serialize(data, data, **kw)
            return result
        else:
            return value

    def do_deserialize(self, value, data, **kw):
        """deserialize either into a normal dictionary or into an AttributeMapper allowing dotted notation
        """
        if self.dotted:
            return AttributeMapper(value)
        else:
            return dict(value)


class Integer(SchemaNode):
    """an integer type. """

    def __init__(self, min = None, max = None, *args, **kw):
        """initialize the String Type"""
        super(Integer, self).__init__(*args, **kw)
        self.min = min
        self.max = max

    def do_serialize(self, value, data, **kw):
        """serialize data"""
        if value is null and not self.required:
            return None
        try:
            v = int(value)
        except Exception, e: 
            raise Invalid(self, "Value '%s' cannot be serialized: %s" %(value, e))
        if self.min is not None and v < self.min:
            raise Invalid(self, "Value '%s' is too low, minimum value is %s" %(value, self.min))
        if self.max is not None and v > self.max:
            raise Invalid(self, "Value '%s' is too big, maximum value is %s" %(value, self.max))
        return v

class Float(Integer):
    """a float type. """

    def do_serialize(self, value, data, **kw):
        """serialize data"""
        if value is null and not self.required:
            return None
        try:
            v = float(value)
        except Exception, e: 
            raise Invalid(self, "Value '%s' cannot be serialized: %s" %(value, e))

        if self.min is not None and v < self.min:
            raise Invalid(self, "Value '%s' is too low, minimum value is %s" %(value, self.min))
        if self.max is not None and v > self.max:
            raise Invalid(self, "Value '%s' is too big, maximum value is %s" %(value, self.max))
        return v

class Boolean(SchemaNode):
    """an integer type. """

    def do_serialize(self, value, data, **kw):
        """serialize data"""
        if value is null and not self.required:
            return False
        try:
            v = bool(value)
        except Exception, e: 
            raise Invalid(self, "Value '%s' cannot be serialized: %s" %(value, e))
        return v

class List(SchemaNode):
    """a node which consists of a list of sub nodes"""

    def __init__(self, subtype, *args, **kw):
        """initialize the list with a list of subtypes which are allowed to be in the document"""
        super(List, self).__init__(*args, **kw)
        self.subtype = subtype

    def do_serialize(self, value, data, **kw):
        """serialize the list"""
        if value is null and not self.required:
            value = []
        elif value is null and self.required:
            raise Invalid(self, "required data missing")
        result = []
        for item in value:
            result.append(self.subtype.serialize(item, data, **kw))
        return result

    def do_deserialize(self, value, data, **kw):
        """deserialize a list object. This includes checking the destination schema and deserializing this
        as well while taking the destination class into account.

        :param value: The individual value for this node to deserialize
        :param data: The whole record e.g. in case you need access to a different field for e.g. a 
            password test in a filter. Note that the this record is always the source record and not
            the deserialized version as this can not be complete.  
        :param kw: Additional keywords which will be passed to the actual deserialization code and filters
        :return: The deserialized version of the data.
        
        """

        result = []
        for item in value:
            item = self.subtype.deserialize(item, data, **kw)
            result.append(item)
        return result

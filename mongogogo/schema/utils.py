import types

class Null(object):
    """a null object. We use a separate class here so that we can control the representation"""

    def __init__(self, label = "<null>"):
        """initialize the null object with a label describing it's use"""
        self.label = label

    def __repr__(self):
        return self.label

null = None
#null = Null("<null>")
marker = Null("<marker>")


class Invalid(Exception):
    """exception which is called whenever serialization or deserialization has not worked"""

    def __init__(self, node, msg=""):
        """something went wrong when serializing or deserializing something"""
        self.node = node
        self.msg = msg

    def __str__(self):
        """return something printable"""
        return "<%s: %s in %s>" %(self.__class__.__name__, self.msg, self.node.name)


class AttributeMapper(dict):
    """a dictionary like object which also is accessible via getattr/setattr"""

    __slots__ = []

    def __init__(self, default={}, *args, **kwargs):
        super(AttributeMapper, self).__init__(*args, **kwargs)
        self.update(default)
        self.update(kwargs)

    def __getattr__(self, k):
        """retrieve some data from the dict"""
        if self.has_key(k):
            return self[k]
        raise AttributeError(k)

    def __setattr__(self, k,v):
        """store an attribute in the map"""
        self[k] = v

    def _clone(self):
        """return a clone of this object"""
        d = copy.deepcopy(self) 
        return AttributeMapper(d)

    def update(self, d):
        """update the dictionary but make sure that existing included AttributeMappers are only updated aswell"""
        for a,v in d.items():
            if a not in self:
                self[a] = v
            elif isinstance(self[a], AttributeMapper) and type(v) == types.DictType:
                self[a].update(v)
            elif type(self[a]) == types.DictType and type(v) == types.DictType:
                self[a].update(v)
            else:
                self[a] = v

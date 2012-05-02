class Null(object):
    """a null object. We use a separate class here so that we can control the representation"""

    def __init__(self, label = "<null>"):
        """initialize the null object with a label describing it's use"""
        self.label = label

    def __repr__(self):
        return self.label

null = Null("<null>")
marker = Null("<marker>")


class Invalid(Exception):
    """exception which is called whenever serialization or deserialization has not worked"""

    def __init__(self, node, msg=""):
        """something went wrong when serializing or deserializing something"""
        self.node = node
        self.msg = msg


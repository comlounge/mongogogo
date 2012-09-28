import uuid
import types
import copy
from cursor import Cursor

class DatabaseError(Exception):
    """master class for all mongogogo exceptions"""

class CollectionMissing(DatabaseError):
    """raised if a collection is missing or closed""" 

class InvalidData(DatabaseError):
    """exception raised if the data is invalid on serialize"""

    def __init__(self, errors):
        """initialize the exception.

        :param errors: A dictionary containing the field names associated with messages

        """
        self.errors = errors

    def __str__(self):
        """return a printable representation of the errors"""
        fs = ["%s: %s" %(a,v) for a,v in self.errors.items()]
        return """<Invalid Data: %s>""" %", ".join(fs)

class ObjectNotFound(DatabaseError):
    """exception raised if an object was not found"""

    def __init__(self, _id):
        """initialize the exception"""
        self._id = _id


class Record(dict):
    
    _schema = None
    _protected = ['_collection', '_protected', '_from_db', '_schemaless']
    schemaless = False # set to true to allow arbitrary data. If set to False, then additional data will be filtered out

    def __init__(self, doc={}, _from_db = False, _collection = None, _md = None, *args, **kwargs):
        """initialize a record with data

        :param doc: The initial document. Note that this will be deserialized in case _from_db is True
        :param _from_db: flag to declare whether the record is new or loaded from the database
        :param _collection: the collection instance this data object belongs to
        :param _md: additional metadata which is not saved but can be accessed as obj._id
        """

        # schemaless means that we also store values from the doc which are not present in the schema
        # otherwise we will just ignore them. Defaults and kwargs are not bound to it though.
        self.update(self.schema.serialize({})) # set defaults
        doc = copy.copy(doc) # copy so that we don't change it in place
        doc.update(kwargs)
        if self.schemaless:
            super(Record, self).__init__(doc, *args, **kwargs)
        else:
            super(Record, self).__init__(*args, **kwargs)
        self._id = None

        # only deserialize it if it's coming from the database
        if _from_db:
            self.update(self.schema.deserialize(doc))
        else:
            self.update(doc)

        self._id = doc.get("_id", None)
        self._collection = _collection

        if not _from_db:
            # lets initialize it
            self.after_initialize()

    def __getattr__(self, k):
        """retrieve some data from the dict"""
        if k in self._protected:
            return dict.__getattr__(self, k)
        if self.has_key(k):
            return self[k]
        raise AttributeError(k)

    def __setattr__(self, k,v):
        """store an attribute in the map"""
        if k in self._protected:
            dict.__setattr__(self, k, v)
        else:
            self[k] = v

    def update(self, d):
        """update the dictionary but make sure that existing included AttributeMappers are only updated aswell"""
        for a,v in d.items():
            if a not in self:
                self[a] = v
            elif isinstance(self[a], Record) and type(v) == types.DictType:
                self[a].update(v)
            elif type(self[a]) == types.DictType and type(v) == types.DictType:
                self[a].update(v)
            else:
                self[a] = v
    
    def after_initialize(self):
        """initialize this object. This method is called when it's a new object meaning
        that it has no unique id"""
        pass

    def save(self):
        """save this record"""
        if self._collection is None:
            raise ConnectionMissing()
        self._collection.save(self)

    put = save
            

class Collection(object):
    """collection class for handling objects"""

    data_class = Record
    create_ids = False # if True then you can override gen_id to generate a new id, otherwise a UUID will be used. If False then we use mongo objectids 

    def __init__(self, collection, md = {}):
        """initialize the collection

        :param collection: The pymongo collection object to use
        :param md: Additional Metadata to be stored in this collection (link to some config etc. maybe useful for validation)
        """
        self.collection = collection
        self.md = md

    def new_id(self):
        """create a new unique id"""
        return unicode(uuid.uuid4())

    def put(self, obj):
        """store an object"""

        # check if we need to create an id
        _id = None
        if "_id" not in obj and self.create_ids:
            _id = self.new_id()
        else:
            _id = obj._id

        # now serialize and validate the object
        if obj.schemaless:
            data = obj
            data.update(obj.schema.serialize(obj))
        else:
            data = obj.schema.serialize(obj)
        if _id is not None:
            data['_id'] = _id
        data = self.before_put(obj, data) # hook for handling additional validation etc.
        self.collection.save(data, True)
        obj._id = data['_id']
        obj._collection = self
        obj._from_db = True
        self.after_put(obj)
        return obj

    save = put

    def before_put(self, obj, data):
        """hook for handling additional validation etc."""
        return data

    def after_put(self, obj):
        """hook for changing data after the object from the database has been instantiated"""
        pass

    def get(self, _id):
        """return an object by it's id"""
        data = self.collection.find_one({'_id' : _id})
        if data is None:
            raise ObjectNotFound(_id)
        #if self.data_class.schemaless:
            #data.update(self.data_class.schema.deserialize(data))
        #else:
            #data = self.data_class.schema.deserialize(data)
        data['_id'] = _id
        return self.data_class(data, _collection=self, _from_db = True)

    def remove(self, *args, **kwargs):
        return self.collection.remove(*args, **kwargs)

    def find(self, *args, **kwargs):
        return Cursor(self, wrap = self.data_class, *args, **kwargs)
        
    def find_one(self, spec_or_id=None, *args, **kwargs):

        if spec_or_id is not None and not isinstance(spec_or_id, dict):
            spec_or_id = {"_id": spec_or_id}

        for result in self.find(spec_or_id, *args, **kwargs).limit(-1):
            return result
        return None

    __getitem__ = get
        


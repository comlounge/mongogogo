import uuid
import types
import copy
from cursor import Cursor

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
    
    schema = None
    _protected = ['schema', 'collection', '_protected', '_schemaless', 'default_values']
    schemaless = False # set to true to allow arbitrary data. If set to False, then additional data will be filtered out
    default_values = {} # default values for a newly created record. Will only be used if from_db is None 

    def __init__(self, doc={}, from_db = None, collection = None, *args, **kwargs):
        """initialize a record with data

        :param doc: The initial document coming from python. This will be merged with keyword
            arguments but won't get serialized or deserialized with the schema as it's already python.
            If ``doc`` and ``from_db`` are both given then only from_db will be used. 
        :param from_db: a record coming from the database. This will be deserialized. If it's None then
            we assume that it's a new object. Note that default values from the schema will not be set.
            This will only happen on the serialization step on save.
        :param collection: the collection instance this data object belongs to
        """

        self._id = None
        if self.schemaless:
            super(Record, self).__init__(from_db if from_db is not None else doc, *args, **kwargs)
        else:
            super(Record, self).__init__(*args, **kwargs)

        # only deserialize it if it's coming from the database
        if from_db is not None:
            self.update(self.schema.deserialize(from_db))
            self._id = from_db.get("_id", None)
        else:
            self._initialize_defaults()
            self.update(doc)
            self.update(kwargs)

        self._collection = collection

        if from_db is None:
            # lets initialize it
            self.after_initialize()
            self.after_create()
        else:
            self.after_load()

        # set the schema class to this class
        self.schema._mg_class = self.__class__

    def _initialize_defaults(self):
        """initialize the record with the default values"""
        def ini(value):
            if callable(value):
                value = value()
            if type(value) == types.DictType:
                value = copy.copy(value)
                for a,v in value.items():
                    value[a] = ini(v)
            if type(value) == types.ListType:
                n = []
                for v in value:
                    n.append(ini(v))
                value = n
            return value
        self.update(ini(self.default_values))

    def __getattr__(self, k):
        """retrieve some data from the dict"""
        if k in self._protected:
            return dict.__getattribute__(self, k)
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

    def after_create(self):
        """hook, which is called after an object has been created and defaults have been initialized"""
        pass

    def after_load(self):
        """hook, which is called after an object has been loaded from the database"""
        pass

    def save(self):
        """save this record"""
        if self._collection is None:
            raise CollectionMissing()
        self._collection.save(self)

    put = save

    def remove(self):
        """remove this record"""
        if self._collection is None:
            raise CollectionMissing()
        self._collection.remove(self)

class Collection(object):
    """collection class for handling objects"""

    data_class = Record
    create_ids = False # if True then you can override gen_id to generate a new id, otherwise a UUID will be used. If False then we use mongo objectids 
    convert_objectids = True # if True then get() will convert string _ids to object ids

    def __init__(self, collection, md = {}, **kwargs):
        """initialize the collection

        :param collection: The pymongo collection object to use
        :param md: Additional Metadata to be stored in this collection (link to some config etc. maybe useful for validation)
        :param kwargs: Additional parameters which will be stored inside the metadata dict
        """
        self.collection = collection
        self.md = AttributeMapper(md)
        self.md.update(kwargs)

    def new_id(self):
        """create a new unique id"""
        return unicode(uuid.uuid4())

    def create(self):
        """create a new instance of the data class and store the collection inside"""
        return self.data_class(collection = self)

    def put(self, obj):
        """store an object"""

        # check if we need to create an id
        _id = None
        if "_id" not in obj and self.create_ids:
            _id = self.new_id()
        else:
            _id = obj._id

        # now serialize and validate the object
        obj = self.before_serialize(obj)
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
        self.after_put(obj)
        return obj

    save = put

    def before_serialize(self, obj):
        """hook for changing the object before it's serialized"""
        return obj

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
        return self.data_class(from_db = data, collection=self)

    def remove(self, obj):
        """high level method to remove an object"""
        q = {'_id' : obj._id}
        return self._remove(q)

    def _remove(self, *args, **kwargs):
        """raw remove method for using a query to remove one or more objects"""
        return self.collection.remove(*args, **kwargs)

    def find(self, *args, **kwargs):
        return Cursor(self, wrap = self.data_class, *args, **kwargs)
        
    def find_one(self, spec_or_id=None, *args, **kwargs):

        if spec_or_id is not None and not isinstance(spec_or_id, dict):
            spec_or_id = {"_id": spec_or_id}

        for result in self.find(spec_or_id, *args, **kwargs).limit(-1):
            return result
        return None

    def __call__(self, data = {}, **kw):
        """create a new object and return it. It is not saved yet.

        :param data: Data with which the new object should be initialized
        :param kw: Additional keyword argument will overwrite the initial data
        """
        data.update(kw)
        obj = self.data_class(data, collection = self)
        return obj

    __getitem__ = get
        


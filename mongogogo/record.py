from helpers import AttributeMapper
import uuid

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
    _protected = ['collection', '_protected', '_from_db']

    def __init__(self, default={}, _from_db = False, _collection = None, _md = None, *args, **kwargs):
        """initialize a record with data

        :param data: the data to initialize this record with
        :param _from_db: flag to declare whether the record is new or loaded from the database
        :param _collection: the collection instance this data object belongs to
        :param _md: additional metadata which is not saved but can be accessed as obj._id
        """
        super(Record, self).__init__(*args, **kwargs)
        self.update(default)
        self.update(kwargs)
        self._collection = _collection
        self._id = self.get("_id", None)

        if not _from_db:
            self.initialize()

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
    
    def initialize(self):
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
        self.md = AttributeMapper(md)

    def new_id(self):
        """create a new unique id"""
        return unicode(uuid.uuid4())

    def put(self, obj):
        """store an object"""

        # check if we need to create an id
        if "_id" in obj and obj._id is not None and self.create_ids:
            obj._id = self.new_id()

        # now serialize and validate the object
        data = obj.schema.serialize(obj)
        data = self.before_put(obj, data) # hook for handling additional validation etc.
        self.collection.save(data, True)
        obj._collection = self
        obj._from_db = True
        self.after_put(obj)
        return obj

    def before_put(self, obj, data):
        """hook for handling additional validation etc."""
        return data

    def after_put(self, obj):
        """hook for changing data after the object from the database has been instantiated"""
        pass


    def get(self, _idkwargs):
        """return an object by it's id"""
        data = self.collection.find_one({'_id' : _id})
        if data is None:
            raise ObjectNotFound(_id)
        
        return self.data_class.deserialize(data, collection=self)

    __getitem__ = get
        

    


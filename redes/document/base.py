from lucenequerybuilder import Q as LQ

from ..properties import BaseProperty
from ..query import QueryManager
from ..utils import get_doc_type
from ..exceptions import DocSaveError, DocNotFoundError


def get_declared_variables(bases, attrs):
    properties = {}
    f_update = properties.update
    attrs_pop = attrs.pop
    for variable_name, obj in attrs.items():
        if isinstance(obj, BaseProperty):
            f_update({variable_name:attrs_pop(variable_name)})
        
    for base in bases:
        if hasattr(base, '_base_properties'):
            if len(base._base_properties) > 0:
                f_update(base._base_properties)
    return properties


class DeclarativeVariablesMetaclass(type):
    """
    Partially ripped off from Django's forms.
    http://code.djangoproject.com/browser/django/trunk/django/forms/forms.py
    """
    def __new__(cls, name, bases, attrs):
        attrs['_base_properties'] = get_declared_variables(bases, attrs)
        new_class = super(DeclarativeVariablesMetaclass,
            cls).__new__(cls, name, bases, attrs)

        return new_class

class BaseDocument(object):
    """
    Base class for all CloudantDB Documents classes.
    """       
    Q = LQ

    def __init__(self,**kwargs):
        self._doc = kwargs
        self._db = self.get_db()
        if self._doc.has_key('_id'):
            self.set_pk(self._doc['_id'])
        self._index_change_list = []

    def __getattr__(self,name):
        if name in self._base_properties.keys():
            prop = self._base_properties[name]
            return prop.get_python_value(self._doc.get(name))
    
    def __setattr__(self,name,value):
        if name in self._base_properties.keys():
            if name in self.get_indexed_props():
                if value != self._doc[name] and self._doc.get(name) != None:
                    self._index_change_list.append(
                        self.get_index_name(name,self._doc[name]))
            self._doc[name] = value
        else:
            super(BaseDocument,self).__setattr__(name,value)

    def set_pk(self, pk):
        self._doc['_id'] = pk
        self.id = pk
        self._id = self.id
        self.pk = self.id

    def create_pk(self):
        db = self.get_db()
        pk = db.incr('{0}:id._pk'.format(self.__class__.__name__.lower()))
        self.set_pk('{0}:id:{1}'.format(self.__class__.__name__.lower(),pk))

    def add_to_model_set(self,pipeline):
        pipeline.sadd('{0}:all'.format(self.__class__.__name__.lower()),self._id)
        return pipeline

    def remove_from_model_set(self,pipeline):
        pipeline.srem('{0}:all'.format(self.__class__.__name__.lower()), self._id)
        return pipeline

    def get_indexed_props(self):
        index_list = []
        for key,prop in self._base_properties.items():
            if prop.index == True:
                index_list.append(key)
        return index_list

    def get_index_name(self,prop,index_value):
        return '{0}:indexes:{1}:{2}'.format(
                    self.get_class_name(),prop,index_value).lower()

    def get_indexes(self):
        index_list = []
        for i in self.get_indexed_props():
            try:
                index_list.append(self.get_index_name(i,self._doc[i]))
            except KeyError:
                pass
        return index_list

    def add_indexes(self,doc,pipeline):
        index_list = self.get_indexed_props()
        for prop in index_list:
            index_value = doc.get(prop)
            if index_value:
                pipeline.sadd(self.get_index_name(prop,index_value),
                    self._id
                )
        return pipeline

    def remove_indexes(self,doc,pipeline):
        for index_v in self._index_change_list:
            pipeline.srem(index_v,self._id)
        return pipeline

    def save(self):
        doc = self._doc.copy()
        for key,prop in self._base_properties.items():
            raw_value = prop.get_python_value(doc.get(key) or prop.get_default_value())
            prop.validate(raw_value,key)
            value = prop.get_db_value(raw_value)
            doc[key] = value

        doc['doc_type'] = get_doc_type(self.__class__)

        if not self._doc.has_key('_id'):
            self.create_pk()
            doc['_id'] = self._id
        pipe = self._db.pipeline()
        pipe.hmset(self._id,doc)


        pipe = self.add_to_model_set(pipe)
        pipe = self.add_indexes(doc,pipe)
        pipe = self.remove_indexes(doc,pipe)
        resp = pipe.execute()
        if resp[0] != True:
            raise DocSaveError('Doc {0} ({1}) did not save.'.format(self._id, self.__class__.__name__))
        self._doc = doc
        return self
       
    @classmethod
    def get_db(cls):
        raise NotImplementedError

    @classmethod
    def objects(cls):
        return QueryManager(cls)

    def get_doc_id(self,id):
        return '{0}:id:{1}'.format(self.__class__.__name__.lower(),id)

    def get_class_name(self):
        return self.__class__.__name__.lower()

    @classmethod    
    def get(cls,doc_id):
        db = cls.get_db()
        doc = db.hgetall(cls().get_doc_id(doc_id))
        if len(doc.keys()) == 0:
            raise DocNotFoundError
        return cls(**doc)

    @classmethod
    def all(cls):
        klass = cls()
        id_list = klass._db.smembers('{0}:all'.format(
            klass.get_class_name()))
        pipe = klass._db.pipeline()
        for id in id_list:
            pipe.hgetall(id)
        return [cls(**doc) for doc in pipe.execute()]

    def delete(self):
        pipe = self.get_db().pipeline()
        pipe.delete(self._doc['_id'])
        pipe = self.remove_from_model_set(pipe)
        self._index_change_list = self.get_indexes()
        pipe = self.remove_indexes(self._doc,pipe)
        pipe.execute()

    class Meta:
        use_db = 'default'
        cql_indexes = []
        design_indexes = []
        
        
class Document(BaseDocument):
    __metaclass__ = DeclarativeVariablesMetaclass

    @classmethod
    def get_db(cls):
        return cls.Meta.use_db
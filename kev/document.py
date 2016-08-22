from six import with_metaclass

from .properties import BaseProperty
from .query import QueryManager
import inspect

BUILTIN_DOC_ATTRS = ('_id','_doc_type')

def get_declared_variables(bases, attrs):
    properties = {}
    f_update = properties.update
    attrs_pop = attrs.pop
    for variable_name, obj in list(attrs.items()):
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
    Base class for all Kev Documents classes.
    """

    def __init__(self,**kwargs):
        self._doc = self.process_doc_kwargs(kwargs)
        self._db = self.get_db()
        if '_id' in self._doc:
            self.set_pk(self._doc['_id'])
        self._index_change_list = []

    def __repr__(self):
        return '<{class_name}: {uni}:{id} >'.format(
            class_name=self.__class__.__name__, uni=self.__unicode__(),
                                                    id=self.pk)

    def __unicode__(self):
        return '({0} Object)'.format(self.__class__.__name__)

    def __getattr__(self,name):
        if name in list(self._base_properties.keys()):
            prop = self._base_properties[name]
            return prop.get_python_value(self._doc.get(name))
    
    def __setattr__(self,name,value):
        if name in list(self._base_properties.keys()):
            if name in self.get_indexed_props() and value \
                    != self._doc.get(name) and self._doc.get(name) != None:
                    self._index_change_list.append(
                        self.get_index_name(name,self._doc[name]))
            self._doc[name] = value
        else:
            super(BaseDocument,self).__setattr__(name,value)

    def process_doc_kwargs(self,kwargs):
        doc = {}
        for key,prop in list(self._base_properties.items()):
            try:
                value = prop.get_python_value(kwargs.get(key) or prop.get_default_value())
            except ValueError:
                value = kwargs.get(key) or prop.get_default_value()
            if value:
                doc[key] = value
        for i in BUILTIN_DOC_ATTRS:
            if kwargs.get(i):
                doc[i] = kwargs[i]
        return doc

    def set_pk(self, pk):
        self._doc['_id'] = pk
        self._id = pk
        self.id = self._db.parse_id(pk)
        self.pk = self.id

    def get_indexed_props(self):
        index_list = []
        for key,prop in list(self._base_properties.items()):
            if prop.index == True:
                index_list.append(key)
        return index_list

    def get_unique_props(self):
        unique_list = []
        for key, prop in list(self._base_properties.items()):
            if prop.unique == True:
                unique_list.append(key)
        return unique_list

    def get_indexes(self):
        index_list = []
        for i in self.get_indexed_props():
            try:
                index_list.append(self.get_index_name(i,self._doc[i]))
            except KeyError:
                pass
        return index_list

    @classmethod
    def get_db(cls):
        raise NotImplementedError

    @classmethod
    def objects(cls):
        return QueryManager(cls)

    @classmethod
    def get_doc_id(cls,id):
        return '{0}:{1}:id:{2}'.format(cls.get_db().backend_id,cls.get_class_name(),id)

    @classmethod
    def get_class_name(cls):
        return cls.__name__.lower()

    @classmethod
    def get_index_name(cls, prop, index_value):
        return '{0}:{1}:indexes:{2}:{3}'.format(
            cls.get_db().backend_id,cls.get_class_name(), prop, index_value).lower()

    #Basic Operations

    @classmethod
    def get(cls,doc_id):
        return cls.get_db().get(cls,doc_id)

    @classmethod
    def all(cls):
        return cls.get_db().all(cls)

    def flush_db(self):
        self._db.flush_db()

    def delete(self):
        self._db.delete(self)

    def save(self):
        self._db.save(self)


    class Meta:
        use_db = 'default'
        handler = None

        
class Document(with_metaclass(DeclarativeVariablesMetaclass, BaseDocument)):
    @classmethod
    def get_db(cls):
        return cls.Meta.handler.get_db(cls.Meta.use_db)
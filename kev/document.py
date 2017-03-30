from six import with_metaclass
from valley.declarative import DeclaredVars as DV, \
    DeclarativeVariablesMetaclass as DVM
from valley.schema import BaseSchema

from .properties import BaseProperty
from .query import QueryManager


class DeclaredVars(DV):
    base_field_class = BaseProperty
    base_field_type = '_base_properties'


class DeclarativeVariablesMetaclass(DVM):
    declared_vars_class = DeclaredVars


class BaseDocument(BaseSchema):
    """
    Base class for all Kev Documents classes.
    """
    BUILTIN_DOC_ATTRS = ('_id', '_doc_type')

    def __init__(self, **kwargs):
        self._data = self.process_schema_kwargs(kwargs)
        self._db = self.get_db()
        if '_id' in self._data:
            self.set_pk(self._data['_id'])
        self._index_change_list = []

    def __repr__(self):
        return '<{class_name}: {uni}:{id} >'.format(
            class_name=self.__class__.__name__, uni=self.__unicode__(),
            id=self.pk)

    def __setattr__(self, name, value):
        if name in list(self._base_properties.keys()):
            if name in self.get_indexed_props() and value \
                    != self._data.get(name) and self._data.get(name) is not None:
                self._index_change_list.append(
                    self.get_index_name(name, self._data[name]))
            self._data[name] = value
        else:
            super(BaseDocument, self).__setattr__(name, value)

    def set_pk(self, pk):
        self._data['_id'] = pk
        self._id = pk
        self.id = self._db.parse_id(pk)
        self.pk = self.id

    def get_indexed_props(self):
        index_list = []
        for key, prop in list(self._base_properties.items()):
            if prop.index:
                index_list.append(key)
        return index_list

    def get_unique_props(self):
        unique_list = []
        for key, prop in list(self._base_properties.items()):
            if prop.unique:
                unique_list.append(key)
        return unique_list

    def get_indexes(self):
        index_list = []
        for i in self.get_indexed_props():
            try:
                index_list.append(self.get_index_name(i, self._data[i]))
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
        return cls.get_db().doc_id_string.format(
            doc_id=id,backend_id=cls.get_db().backend_id,class_name=cls.get_class_name())

    @classmethod
    def get_index_name(cls, prop, index_value):
        if cls.get_db().backend_id != 'dynamodb':
            index_value = index_value.lower()
        return '{0}:{1}:indexes:{2}:{3}'.format(
            cls.get_db().backend_id.lower(),
            cls.get_class_name().lower(),
            prop.lower(),
            index_value)

    # Basic Operations

    @classmethod
    def get(cls, doc_id):
        return cls.get_db().get(cls, doc_id)

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

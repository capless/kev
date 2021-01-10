import json
import boto3
from urllib.parse import urlparse

from valley.declarative import DeclaredVars as DV, \
    DeclarativeVariablesMetaclass as DVM
from valley.exceptions import ValidationException
from valley.schema import BaseSchema

from .properties import BaseProperty
from .query import QueryManager

try:
    import brotli
    BROTLI_ENABLED = True
except ImportError:
    BROTLI_ENABLED = False


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
        self._create_error_dict = kwargs.get('create_error_dict') or self._create_error_dict
        if self._create_error_dict:
            self._errors = {}
        if '_id' in self._data:
            self.set_pk(self._data['_id'])
        self._index_change_list = []

    def _s3(self):
        return boto3.resource('s3', **self.get_restore_kwargs())

    def __repr__(self):
        return '<{class_name}: {uni}:{id}>'.format(
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

    def check_unique(self):
        
        for key in self.get_unique_props():
            try:
                self._db.check_unique(self,key,self.cleaned_data.get(key))
            except ValidationException as e:
                if self._create_error_dict:
                    self._errors[key] = e.error_msg
                else:
                    raise e

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

    def get_restore_kwargs(self):
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
        if cls.get_db().backend_id != 'dynamodb' and cls.get_db().backend_id != 'cloudant':
            if isinstance(index_value,str):
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
    def all(cls, skip=None, limit=None):
        if skip and skip < 0:
            raise AttributeError("skip value should be an positive integer")
        if limit is not None and limit < 1:
            raise AttributeError("limit value should be an positive integer, valid range 1-inf")
        return cls.get_db().all(cls, skip, limit)

    def flush_db(self):
        self._db.flush_db()

    def delete(self):
        self._db.delete(self)

    def save(self):
        self._db.save(self)

    def get_restore_json(self,restore_path,path_type,bucket=None):
        if path_type == 's3':
            obj = self._s3().Object(
                bucket, restore_path).get().get('Body').read().decode()
        else:
            with open(restore_path) as f:
                obj = f.read()

        if restore_path.endswith('.brotli'):
            return json.load(brotli.decompress(obj))
        else:
            return json.loads(obj)

    def get_path_type(self,path):
        if path.startswith('s3://'):
            result = urlparse(path)

            return (result.path[1:],'s3',result.netloc)
        else:
            return (path,'local',None)

    def restore(self,restore_path):
        file_path, path_type, bucket = self.get_path_type(restore_path)
        docs = self.get_restore_json(file_path,path_type,bucket)
        for doc in docs:
            self.__class__(**doc).save()

    def remove_id(self,doc):
        doc._data.pop('_id')
        return doc

    def backup(self, export_path, use_brotli= False):

        file_path, path_type, bucket = self.get_path_type(export_path)

        json_docs = [self._db.prep_doc(
            self.remove_id(doc)) for doc in self.all()]

        # Compress using Brotli
        if use_brotli and BROTLI_ENABLED:
            json_docs_enc = json.dumps(json_docs).encode('UTF-8')
            json_docs = brotli.compress(json_docs_enc)
            if path_type == 'local': # Add Extension
                export_path += ".brotli"
            else:
                file_path += ".brotli"
            

        if path_type == 'local':
            with open(export_path, 'w') as f:
                json.dump(json_docs, f)
        else:
            #Use tmp directory if we are uploading to S3 just in case we
            #are using Lambda
            self._s3().Object(bucket, file_path).put(
                Body=json.dumps(json_docs))

    class Meta:
        use_db = 'default'
        handler = None


class Document(BaseDocument,metaclass=DeclarativeVariablesMetaclass):

    @classmethod
    def get_db(cls):
        return cls.Meta.handler.get_db(cls.Meta.use_db)

    def get_restore_kwargs(self):
        return self.get_db()._kwargs.get('restore')

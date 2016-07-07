import boto3
import json
import redis

from kev.exceptions import DocSaveError
from kev.backends import DocDB

class S3DB(DocDB):

    conn_class = boto3.resource
    cache_class = redis.StrictRedis
    backend_id = 's3'
    def __init__(self,**kwargs):
        if kwargs.has_key('aws_secret_access_key') and kwargs.has_key('aws_access_key_id'):
            boto3.Session(aws_secret_access_key=kwargs['aws_secret_access_key'],
                aws_access_key_id=kwargs['aws_access_key_id'])
        self._db = boto3.resource('s3')
        self.bucket = kwargs['bucket']
        self._cache = self.cache_class(kwargs['redis_host'],port=kwargs['redis_port'])

    def save(self,doc_obj):
        doc_obj, doc = self._save(doc_obj)
        self._db.Object(self.bucket, doc_obj._id).put(
            Body=json.dumps(doc))
        pipe = self._cache.pipeline()
        pipe = self.add_to_model_set(doc_obj, pipe)
        pipe = self.add_indexes(doc_obj, doc, pipe)
        pipe = self.remove_indexes(doc_obj, pipe)
        resp = pipe.execute()
        if resp[0] != True:
            raise DocSaveError('Doc {0} ({1}) did not save.'.format(
                self._id, self.__class__.__name__))
        doc_obj._doc = doc
        return doc_obj

    def get(self,doc_obj,doc_id):
        doc = json.loads(self._db.Object(
            self.bucket, doc_obj.get_doc_id(doc_id)).get().get('Body').read())
        return doc_obj.__class__(**doc)

    def create_pk(self,doc_obj):
        pk = self._cache.incr('{0}:{1}:id._pk'.format(self.backend_id,doc_obj.__class__.__name__.lower()))
        doc_obj.set_pk('{0}:id:{1}'.format(doc_obj.__class__.__name__.lower(), pk))
        return doc_obj

    def delete(self, doc_obj):
        self._db.Object(self.bucket,doc_obj._id).delete()
        pipe = self._cache.pipeline()
        pipe = self.remove_from_model_set(doc_obj, pipe)
        doc_obj._index_change_list = doc_obj.get_indexes()
        pipe = self.remove_indexes(doc_obj, pipe)
        pipe.execute()

    def all(self,cls):
        klass = cls()
        id_list = [id.rsplit(':',1)[1] for id in self._cache.smembers('{0}:all'.format(
            klass.get_class_name()))]
        obj_list = []

        for id in id_list:
            obj_list.append(self.get(klass,id))
        return obj_list

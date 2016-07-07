import redis

from kev.backends import DocDB
from kev.exceptions import DocSaveError, DocNotFoundError
from kev.utils import get_doc_type


class RedisDB(DocDB):

    conn_class = redis.StrictRedis
    backend_id = 'redis'

    def __init__(self,**kwargs):
        self._db = redis.StrictRedis(**kwargs)

    def save(self,doc_obj):
        doc_obj, doc = self._save(doc_obj)
        pipe = self._db.pipeline()
        pipe.hmset(doc_obj._id, doc)

        pipe = self.add_to_model_set(doc_obj,pipe)
        pipe = self.add_indexes(doc_obj, doc, pipe)
        pipe = self.remove_indexes(doc_obj, pipe)
        resp = pipe.execute()
        if resp[0] != True:
            raise DocSaveError('Doc {0} ({1}) did not save.'.format(
                self._id, self.__class__.__name__))
        doc_obj._doc = doc
        return doc_obj

    def create_pk(self,doc_obj):
        pk = self._db.incr('{0}:{1}:id._pk'.format(self.backend_id,doc_obj.__class__.__name__.lower()))
        doc_obj.set_pk('{0}:id:{1}'.format(doc_obj.__class__.__name__.lower(), pk))
        return doc_obj

    def delete(self,doc_obj):
        pipe = self._db.pipeline()
        pipe.delete(doc_obj._doc['_id'])
        pipe = self.remove_from_model_set(doc_obj,pipe)
        doc_obj._index_change_list = doc_obj.get_indexes()
        pipe = self.remove_indexes(doc_obj, pipe)
        pipe.execute()

    def all(self,cls):
        klass = cls()
        id_list = self._db.smembers('{0}:all'.format(
            klass.get_class_name()))
        pipe = self._db.pipeline()
        for id in id_list:
            pipe.hgetall(id)
        return [cls(**doc) for doc in pipe.execute()]


    def get(self, doc_obj, doc_id):

        doc = self._db.hgetall(doc_obj.get_doc_id(doc_id))
        if len(doc.keys()) == 0:
            raise DocNotFoundError
        return doc_obj.__class__(**doc)
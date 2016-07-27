import redis

from kev.backends import DocDB
from kev.exceptions import DocSaveError, DocNotFoundError


class RedisDB(DocDB):

    conn_class = redis.StrictRedis
    backend_id = 'redis'

    def __init__(self,**kwargs):
        self._redis = redis.StrictRedis(**kwargs)

    def create_pk(self,doc_obj):
        pk = self._redis.incr('{0}:{1}:id._pk'.format(self.backend_id,doc_obj.__class__.__name__.lower()))
        doc_obj.set_pk('{0}:id:{1}'.format(doc_obj.__class__.__name__.lower(), pk))
        return doc_obj

    #CRUD Operations

    def save(self,doc_obj):
        doc_obj, doc = self._save(doc_obj)
        pipe = self._redis.pipeline()
        pipe.hmset(doc_obj._id, doc)

        pipe = self.add_to_model_set(doc_obj,pipe)
        pipe = self.add_indexes(doc_obj, doc, pipe)
        pipe = self.remove_indexes(doc_obj, pipe)
        pipe.execute()
        doc_obj._doc = doc_obj.process_doc_kwargs(doc)
        return doc_obj

    def delete(self,doc_obj):
        pipe = self._redis.pipeline()
        pipe.delete(doc_obj._doc['_id'])
        pipe = self.remove_from_model_set(doc_obj,pipe)
        doc_obj._index_change_list = doc_obj.get_indexes()
        pipe = self.remove_indexes(doc_obj, pipe)
        pipe.execute()

    def all(self,cls):
        klass = cls()
        id_list = self._redis.smembers('{0}:all'.format(
            klass.get_class_name()))
        pipe = self._redis.pipeline()
        for id in id_list:
            pipe.hgetall(id)
        return [cls(**doc) for doc in pipe.execute()]

    def get(self, doc_obj, doc_id):

        doc = self._redis.hgetall(doc_obj.get_doc_id(doc_id))
        if len(doc.keys()) == 0:
            raise DocNotFoundError
        return doc_obj.__class__(**doc)

    def flush_db(self):
        self._redis.flushdb()

    #Indexing Methods

    def add_to_model_set(self, doc_obj, pipeline):
        pipeline.sadd('{0}:all'.format(doc_obj.__class__.__name__.lower()), doc_obj._id)
        return pipeline

    def remove_from_model_set(self, doc_obj, pipeline):
        pipeline.srem('{0}:all'.format(doc_obj.__class__.__name__.lower()), doc_obj._id)
        return pipeline

    def remove_indexes(self, doc_obj, pipeline):
        for index_v in doc_obj._index_change_list:
            pipeline.srem(index_v, doc_obj._id)
        return pipeline

    def add_indexes(self, doc_obj, doc, pipeline):
        index_list = doc_obj.get_indexed_props()
        for prop in index_list:
            index_value = doc.get(prop)
            if index_value:
                pipeline.sadd(doc_obj.get_index_name(prop, index_value),
                              doc_obj._id
                              )
        return pipeline

    def evaluate(self, filters_list, doc_class):
        if len(filters_list) == 1:
            id_list = self._redis.smembers(filters_list[0])
        else:
            id_list = self._redis.sinter(*filters_list)
        pipe = self._redis.pipeline()
        for id in id_list:
            pipe.hgetall(id)
        return [doc_class(**doc) for doc in pipe.execute()]
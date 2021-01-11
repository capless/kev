import redis

from kev.backends import DocDB
from kev.exceptions import DocNotFoundError



class RedisDB(DocDB):

    db_class = redis.StrictRedis
    backend_id = 'redis'

    def __init__(self, **kwargs):
        self._db = self._indexer = self.db_class(
            kwargs['host'], port=kwargs['port'])
        self._kwargs = kwargs

    # CRUD Operations
    def save(self, doc_obj):
        doc_obj, doc = self._save(doc_obj)
        pipe = self._db.pipeline()
        pipe.hset(doc_obj._id, mapping=doc)

        pipe = self.add_to_model_set(doc_obj, pipe)
        pipe = self.add_indexes(doc_obj, doc, pipe)
        pipe = self.remove_indexes(doc_obj, pipe)
        pipe.execute()

        return doc_obj

    def delete(self, doc_obj):
        pipe = self._db.pipeline()
        pipe.delete(doc_obj._data['_id'])
        pipe = self.remove_from_model_set(doc_obj, pipe)
        doc_obj._index_change_list = doc_obj.get_indexes()
        pipe = self.remove_indexes(doc_obj, pipe)
        pipe.execute()

    def all(self, cls, skip, limit):
        id_list = self._db.smembers('{0}:all'.format(
            cls.get_class_name()))
        pipe = self._db.pipeline()
        for id in id_list:
            pipe.hgetall(id)

        raw_docs = pipe.execute()
        for doc in raw_docs:
            if skip and skip > 0:
                skip -= 1
                continue
            if limit is not None and limit == 0:
                break
            elif limit:
                limit -= 1
            yield cls(**{k.decode('utf-8'): v.decode('utf-8') for k, v in doc.items()})

    def get(self, doc_obj, doc_id):
        doc = self._db.hgetall(doc_obj.get_doc_id(doc_id))
        if len(list(doc.keys())) == 0:
            raise DocNotFoundError

        return doc_obj(**{k.decode(): v.decode() for k, v in doc.items()})

    def flush_db(self):
        self._db.flushdb()

    # Indexing Methods
    def add_to_model_set(self, doc_obj, pipeline):
        pipeline.sadd(
            '{0}:all'.format(
                doc_obj.__class__.__name__.lower()),
            doc_obj._id)
        return pipeline

    def remove_from_model_set(self, doc_obj, pipeline):
        pipeline.srem(
            '{0}:all'.format(
                doc_obj.__class__.__name__.lower()),
            doc_obj._id)
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
                              doc_obj._id)
        return pipeline

    def evaluate(self, filters_list, sortingp_list, all_param, doc_class):
        if all_param.all and len(sortingp_list) > 0:
            docs_list = list(self.all(doc_class, skip=all_param.skip, limit=all_param.limit))
            for doc in self.sort(sortingp_list, docs_list, doc_class):
                yield doc
        elif all_param.all:
            for doc in self.all(doc_class, skip=all_param.skip, limit=all_param.limit):
                yield doc
        else:
            id_list = self.get_id_list(filters_list)
            pipe = self._db.pipeline()
            for id in id_list:
                pipe.hgetall(id)
            raw_docs = pipe.execute()
            if len(sortingp_list) > 0:
                docs_list = [doc_class(**{k.decode(): v.decode() for k, v in doc.items()})\
                             for doc in raw_docs]
                sorted_list = self.sort(sortingp_list, docs_list, doc_class)
                for doc in sorted_list:
                      yield doc
            else:
                for doc in raw_docs:
                    yield doc_class(**{k.decode(): v.decode() for k, v in doc.items()})

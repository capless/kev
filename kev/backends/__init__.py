from kev.utils import get_doc_type


class DocDB(object):
    conn_class = None
    backend_id = None
    def __init__(self,db,doc=None):
        self._doc = doc
        self._db = db

    def save(self):
        pass

    def delete(self):
        pass

    @classmethod
    def get(cls,doc_id):
        pass

    def create_pk(self):
        raise NotImplementedError

    def _save(self,doc_obj):
        doc = doc_obj._doc.copy()
        for key, prop in doc_obj._base_properties.items():
            raw_value = prop.get_python_value(doc.get(key) or prop.get_default_value())
            prop.validate(raw_value, key)
            value = prop.get_db_value(raw_value)
            doc[key] = value

        doc['doc_type'] = get_doc_type(doc_obj.__class__)

        if not doc.has_key('_id'):
            self.create_pk(doc_obj)
            doc['_id'] = doc_obj._id
        return (doc_obj,doc)

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
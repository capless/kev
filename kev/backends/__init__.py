import six

from kev.exceptions import QueryError, ValidationException
from kev.utils import get_doc_type


class DocDB(object):
    db_class = None
    indexer_class = None
    backend_id = None

    def save(self,doc_obj):
        raise NotImplementedError

    def delete(self, doc_obj):
        raise NotImplementedError

    def get(self, doc_obj, doc_id):
        raise NotImplementedError

    def parse_id(self, doc_id):
        try:
            return doc_id.split(':')[3]
        except TypeError:
            return doc_id.decode().split(':')[3]

    def create_pk(self):
        raise NotImplementedError

    def check_unique(self,doc_obj,key,value):
        obj = doc_obj.objects().filter({key:value})
        if len(obj) == 0:
            return True
        if hasattr(doc_obj,'_id') and len(obj) == 1:
            if doc_obj._id == obj[0]._id:
                return True
        raise ValidationException(
                'There is already a {key} with the value of {value}'\
                    .format(key=key,value=value))

    def _save(self,doc_obj):
        doc = doc_obj._doc.copy()
        for key, prop in list(doc_obj._base_properties.items()):
            prop.validate(doc.get(key), key)
            raw_value = prop.get_python_value(doc.get(key))
            if prop.unique:
                self.check_unique(doc_obj,key,raw_value)
            value = prop.get_db_value(raw_value)
            doc[key] = value


        doc['_doc_type'] = get_doc_type(doc_obj.__class__)

        if '_id' not in doc:
            self.create_pk(doc_obj)
            doc['_id'] = doc_obj._id
        return (doc_obj,doc)

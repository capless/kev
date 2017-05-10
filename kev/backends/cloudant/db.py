from kev.backends import DocDB
from cloudant import client
from cloudant.document import Document
from cloudant.query import Query


class CloudantDB(DocDB):
    db_class = client
    backend_id = 'cloudant'
    special_character = ':'

    def __init__(self, **kwargs):
        self._client = self.db_class.Cloudant(kwargs.get('username'), kwargs.get('password'),
                                          account=kwargs.get('account_name', None),
                                          url=kwargs.get('url', None),
                                          connect=True)
        self.table = kwargs['table']
        self._db = self._client[self.table]

    # CRUD Operations
    def save(self, doc_obj):
        doc_obj, doc = self._save(doc_obj)
        for key in doc.keys():
            # workaround for the 'Bad special document member' error
            if key.startswith('_') and key is not '_id':
                new_key = self.special_character + key
                doc[new_key] = doc.pop(key)
        self._db.create_document(doc)

    def delete(self, doc_obj):
        document = Document(self._db, document_id=doc_obj._data['_id'])
        document.fetch()
        document.delete()

    def all(self, cls, skip, limit):
        for doc in self._db.all_docs(
                skip=skip, limit=limit, include_docs=True)['rows']:
            yield cls(**doc['doc'])

    def get(self, doc_obj, doc_id):
        doc = self._db[doc_obj.get_doc_id(doc_id)]
        return doc_obj(**doc)

    def flush_db(self):
        for doc in self._db.all_docs()['rows']:
            document = Document(self._db, document_id=doc['id'])
            document.fetch()
            document.delete()

    # Indexing Methods
    def get_doc_list(self, filters_list):
        query_params = self.parse_filters(filters_list)
        response = Query(self._db, **query_params)
        return response()['docs']

    def parse_filters(self, filters):
        query_params = {'selector': {}}
        for filter in filters:
            prop_name, prop_value = filter.split(':')[3:5]
            query_params['selector'].update({prop_name: prop_value})
        return query_params

    def evaluate(self, filters_list, doc_class):
        docs_list = self.get_doc_list(filters_list)
        for doc in docs_list:
            for key in doc.keys():
                if key.startswith(self.special_character):
                    new_key = key[1:]
                    doc[new_key] = doc.pop(key)
            yield doc_class(**doc)

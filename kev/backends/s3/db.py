import boto3
import json
import re

from kev.backends import DocDB


class S3DB(DocDB):
    db_class = boto3.resource
    backend_id = 's3'
    doc_id_string = '{doc_id}:id:{backend_id}:{class_name}'
    index_pattern = r'^(?P<backend_id>[-\w]+):(?P<class_name>[-\w]+)' \
                    ':indexes:(?P<index_name>[-\w]+):(?P<index_value>' \
                    '[-\W\w\s]+)/(?P<doc_id>[-\w]+):id:' \
                    '(?P<backend_id_b>[-\w]+):(?P<class_name_b>[-\w]+)$'
    session_kwargs = ['aws_secret_access_key', 'aws_access_key_id', 'endpoint_url']

    def __init__(self, **kwargs):
        session_kwargs = {k: v for k, v in kwargs.items() if k in
                          self.session_kwargs}

        self._db = boto3.resource('s3', **session_kwargs)
        self.bucket = kwargs['bucket']
        self._indexer = self._db.Bucket(self.bucket)
        self._kwargs = kwargs

    # CRUD Operation Methods

    def all_prefix(self, doc_class):
        return '{0}:all/'.format(
            doc_class.get_class_name())

    def get_full_id(self, doc_class, doc_id):
        return '{}{}'.format(self.all_prefix(doc_class), doc_id)

    def save(self, doc_obj):
        doc_obj, doc = self._save(doc_obj)
        self._db.Object(self.bucket, self.get_full_id(
            doc_obj.__class__, doc_obj._id)).put(
            Body=json.dumps(doc))
        self.add_indexes(doc_obj, doc)
        self.remove_indexes(doc_obj)
        return doc_obj

    def get(self, doc_class, doc_id):
        doc = json.loads(self._db.Object(
            self.bucket, self.get_full_id(doc_class,
                                          doc_class.get_doc_id(doc_id))).get().get('Body').read().decode())
        return doc_class(**doc)

    def get_raw(self, doc_class, doc_id):
        doc = json.loads(self._db.Object(self.bucket, doc_id).get().get(
            'Body').read().decode())
        return doc_class(**doc)

    def flush_db(self):
        obj_list = self._db.Bucket(self.bucket).objects.all()
        for i in obj_list:
            i.delete()

    def delete(self, doc_obj):
        self._db.Object(
            self.bucket,
            self.get_full_id(doc_obj.__class__, doc_obj._id)).delete()
        self.remove_from_model_set(doc_obj)
        doc_obj._index_change_list = doc_obj.get_indexes()
        self.remove_indexes(doc_obj)

    def all(self, doc_class, skip, limit):
        all_prefix = self.all_prefix(doc_class)
        if limit is None:
            response = self._indexer.objects.filter(Prefix=all_prefix)
        else:
            response = self._indexer.objects.filter(Prefix=all_prefix).limit(limit)
        id_list = [id.key for id in response]
        for id in id_list:
            if skip and skip > 0:
                skip -= 1
                continue
            yield self.get_raw(doc_class, id)

    # Indexing Methods

    def remove_from_model_set(self, doc_obj):
        self._db.Object(self.bucket, self.get_full_id(
            doc_obj.__class__, doc_obj._id)).delete()

    def remove_indexes(self, doc_obj):
        for index_v in doc_obj._index_change_list:
            self._db.Object(self.bucket, '{0}/{1}'.format(index_v, doc_obj._id)).delete()

    def add_indexes(self, doc_obj, doc):
        index_list = doc_obj.get_indexed_props()
        for prop in index_list:
            index_value = doc.get(prop)
            # if index_value:
            self._db.Object(self.bucket, '{0}/{1}'.format(
                doc_obj.get_index_name(prop, index_value),
                doc_obj._id)).put(Body='')

    def evaluate(self, filters_list, sortingp_list, all_param, doc_class):
        if all_param.all and len(sortingp_list) > 0:
            docs_list = list(self.all(doc_class, skip=all_param.skip, limit=all_param.limit))
            for doc in self.sort(sortingp_list, docs_list, doc_class):
                yield doc
        elif all_param.all:
            for doc in self.all(doc_class, skip=all_param.skip, limit=all_param.limit):
                yield doc
        else:
            if len(filters_list) == 1:
                filter_value = '{}/'.format(filters_list[0])
                raw_id_list = self._indexer.objects.filter(Prefix=filter_value)
                id_list = [re.match(self.index_pattern, id.key).groupdict()['doc_id'] \
                           for id in raw_id_list]
            else:
                raise ValueError('There should only be one filter for S3 backends')
            if len(sortingp_list) > 0:
                docs_list = [doc_class.get(id) for id in id_list]
                sorted_list = self.sort(sortingp_list, docs_list, doc_class)
                for doc in sorted_list:
                    yield doc
            else:
                for id in id_list:
                    yield self.get(doc_class, id)

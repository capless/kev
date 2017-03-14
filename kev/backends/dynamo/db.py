import decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from kev.backends import DocDB
from kev.exceptions import DocNotFoundError


class DynamoDB(DocDB):

    db_class = boto3.resource
    backend_id = 'dynamo'

    def __init__(self, **kwargs):
        if 'aws_secret_access_key' in kwargs and 'aws_access_key_id' in kwargs:
            boto3.Session(aws_secret_access_key=kwargs['aws_secret_access_key'],
                aws_access_key_id=kwargs['aws_access_key_id'])
        self._db = boto3.resource('dynamodb')
        self.table = kwargs['table']
        self._indexer = self._db.Table(self.table)

    # CRUD Operations
    def save(self, doc_obj):
        doc_obj, doc = self._save(doc_obj)
        # DynamoDB requires Decimal type instead of Float
        for key, value in list(doc.items()):
            if type(value) == float:
                doc[key] = decimal.Decimal(str(value))
        try:
            self._indexer.put_item(Item=doc)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print('Table doesn\'t exist.')
        return doc_obj

    def delete(self, doc_obj):
        self._indexer.delete_item(Key={'_id': doc_obj._doc['_id']})

    def all(self, cls):
        obj_list = self._indexer.scan()['Items']
        for doc in obj_list:
            yield cls(**doc)

    def get(self, doc_obj, doc_id):
        response = self._indexer.get_item(Key={'_id': doc_obj.get_doc_id(doc_id)})
        doc = response.get('Item', None)
        if not doc:
            raise DocNotFoundError
        return doc_obj(**doc)

    def flush_db(self):
        obj_list = self._indexer.scan()['Items']
        for i in obj_list:
            self._indexer.delete_item(Key={'_id': i['_id']})

    # # Indexing Methods
    def get_id_list(self, filters_list):
        result = []
        l = self.parse_filters(filters_list)
        list_of_sets = []
        for filter in l:
            ids_set = set()
            index, value = filter.split(':')[3:5]
            index_name = '{0}-index'.format(index)
            key_expression = Key(index).eq(value)
            if index != '_id':
                response = self._indexer.query(IndexName=index_name,KeyConditionExpression=key_expression)
            else:
                response = self._indexer.query(KeyConditionExpression=key_expression)
            for item in response['Items']:
                ids_set.add(item['_id'])
            list_of_sets.append(ids_set)
            result = list(set.intersection(*list_of_sets))
        return result

    def parse_filters(self, filters):
        s = set()
        for f in filters:
            s.add(f)
        if not s:
            return filters
        return list(s)

    def evaluate(self, filters_list, doc_class):
         id_list = self.get_id_list(filters_list)
         for id in id_list:
             yield doc_class.get(self.parse_id(id))

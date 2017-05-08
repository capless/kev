import decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr, And
from botocore.exceptions import ClientError

from kev.backends import DocDB
from kev.exceptions import DocNotFoundError, ResourceError


class DynamoDB(DocDB):

    db_class = boto3
    backend_id = 'dynamodb'
    default_index_name = '{0}-index'
    index_field_name = 'index_name'

    def __init__(self, **kwargs):
        if 'aws_secret_access_key' in kwargs and 'aws_access_key_id' in kwargs:
            boto3.Session(aws_secret_access_key=kwargs['aws_secret_access_key'],
                aws_access_key_id=kwargs['aws_access_key_id'])
        self._db = self.db_class.resource('dynamodb', endpoint_url=kwargs.get('endpoint_url', None))
        self.table = kwargs['table']
        self._indexer = self._db.Table(self.table)

    # CRUD Operations
    def save(self, doc_obj):
        doc_obj, doc = self._save(doc_obj)
        # DynamoDB requires Decimal type instead of Float
        for key, value in doc.items():
            if type(value) == float:
                doc[key] = decimal.Decimal(str(value))
        try:
            self._indexer.put_item(Item=doc)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                raise ResourceError('Table doesn\'t exist.')
        return doc_obj

    def delete(self, doc_obj):
        self._indexer.delete_item(Key={'_id': doc_obj._data['_id']})

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

    # Indexing Methods
    def get_doc_list(self, filters_list, doc_class):
        query_params = self.parse_filters(filters_list, doc_class)
        response = self._indexer.query(**query_params)
        return response['Items']

    def parse_filters(self, filters, doc_class):
        index_name = None
        filter_expression_list = []
        query_params = {}
        for idx, filter in enumerate(filters):
            prop_name, prop_value = filter.split(':')[3:5]
            if idx == 0:
                prop = doc_class()._base_properties[prop_name]
                index_name = prop.kwargs.get(self.index_field_name, None) or \
                             self.default_index_name.format(prop_name)
                query_params['KeyConditionExpression'] = Key(prop_name).eq(prop_value)
            else:
                filter_expression_list.append(Attr(prop_name).eq(prop_value))
        if len(filter_expression_list) > 1:
            query_params['FilterExpression'] = And(*filter_expression_list)
        elif len(filter_expression_list) == 1:
            query_params['FilterExpression'] = filter_expression_list[0]
        if index_name != '_id':
            query_params['IndexName'] = index_name
        return query_params

    def evaluate(self, filters_list, doc_class):
         docs_list = self.get_doc_list(filters_list, doc_class)
         for doc in docs_list:
             yield doc_class(**doc)

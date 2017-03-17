import boto3
import json
import re
import logging
from kev.backends import DocDB

from pprint import pprint

class DynamoDB(DocDB):

    db_class   = boto3.resource
    backend_id = 'dynamodb'
    doc_id_string = '{doc_id}:id:{backend_id}:{class_name}'
    index_pattern = r'^(?P<backend_id>[-\w]+):(?P<class_name>[-\w]+)' \
                    ':indexes:(?P<index_name>[-\w]+):(?P<index_value>' \
                    '[-\W\w\s]+)/(?P<doc_id>[-\w]+):id:' \
                    '(?P<backend_id_b>[-\w]+):(?P<class_name_b>[-\w]+)$'

### client operations
# batch_get_item()
# batch_write_item()
# can_paginate()
# create_table()
# delete_item()
# delete_table()
# describe_limits()
# describe_table()
# describe_time_to_live()
# generate_presigned_url()
# get_item()
# get_paginator()
# get_waiter()
# list_tables()
# list_tags_of_resource()
# put_item()
# query()
# scan()
# tag_resource()
# untag_resource()
# update_item()
# update_table()
# update_time_to_live()

### table operations
## These are the resource's available identifiers:
# name

## These are the resource's available attributes:
# attribute_definitions
# creation_date_time
# global_secondary_indexes
# item_count
# key_schema
# latest_stream_arn
# latest_stream_label
# local_secondary_indexes
# provisioned_throughput
# stream_specification
# table_arn
# table_name
# table_size_bytes
# table_status

## These are the resource's available actions:
# batch_writer()
# delete()
# delete_item()
# get_available_subresources()
# get_item()
# load()
# put_item()
# query()
# reload()
# scan()
# update()
# update_item()
# These are the resource's available waiters:

# wait_until_exists()
# wait_until_not_exists()


    def __init__(self,**kwargs):

        if 'aws_secret_access_key' in kwargs and 'aws_access_key_id' in kwargs:
            boto3.Session(aws_secret_access_key=kwargs['aws_secret_access_key'],
                aws_access_key_id=kwargs['aws_access_key_id'])

        self._db      = boto3.resource('dynamodb')
        self._client  = boto3.client('dynamodb')
        self.table    = kwargs['table']
        self._indexer = self._db.Table(self.table)

        # setup logger
        self.logName  = str(self.__class__.__name__)
        self.log      = logging.getLogger(self.logName)

        # TODO create helper methods to create/delete tables for testing

    # CRUD Operation Methods

    def save(self,doc_obj):
        # TODO: allow configuration of auto override
        self.log.debug("starting save " + str((doc_obj)))
        doc_obj, doc = self._save(doc_obj)
        resp = self._indexer.put_item(Item=doc)

        self.log.debug("endind save")
        return doc_obj

    def get(self,doc_class,doc_id):
        self.log.debug("*starting get")
        # self.log.debug(doc_class)
        # self.log.debug(doc_id)

        doc = self._indexer.get_item(Key=doc_id)

        return doc_class(**(doc["Item"]))

    def flush_db(self):
        self.log.debug("starting flush_db")

        # TODO: improve efficiency for large tables, delete and recreate table
        # TODO: check UnprocessedItems response for missed items

        # process: scan then delete each item

        # describe table to get primary key
        resp = self._client.describe_table(TableName=self.table)
        keys = [k['AttributeName'] for k in resp['Table']['KeySchema']]
        self.log.debug("Primary keys: {}".format(str(keys)))

        # TODO try table.load() instead of direct client call
        # TODO what does get_available_subresources return?

        # scan table to get item list
        resp  = self._indexer.scan()
        items = resp["Items"]
        self.log.debug("Items to delete: {}".format(len(items)))

        # delete items 1 by 1
        if len(items) == 0:
            return
        with self._indexer.batch_writer() as batch:
            for item in items:
                self.log.debug("Items to delete: {}".format(str(item)))
                pk = {k: item[k] for k in keys}
                batch.delete_item(Key=pk)

    def delete(self, doc_obj):
        # TODO not working!!!!
        self.log.debug("starting delete " + str(doc_obj))
        self._indexer.delete_item(Key=doc_id)

        # self._db.Object(
        #     self.bucket,
        #     self.get_full_id(doc_obj.__class__,doc_obj._id)).delete()
        # self.remove_from_model_set(doc_obj)
        # doc_obj._index_change_list = doc_obj.get_indexes()
        # self.remove_indexes(doc_obj)

    def all(self,doc_class):
        # TODO verify object type returned
        self.log.debug("starting all")
        # TODO: verify scans > 1MB still work
        resp  = self._indexer.scan()  # TODO filter scan
        id_list = resp["Items"]
        self.log.debug("respssss: '{}', {}".format(len(id_list),str(resp)))
        for id in id_list:
            yield id
        self.log.debug("ending all")


        # all_prefix = self.all_prefix(doc_class)
        # id_list = [id.key for id in self._indexer.tables.filter(Prefix=all_prefix)]

        # for id in id_list:
        #     yield self.get_raw(doc_class,id)

    # Indexing Methods

    def evaluate(self, filters_list, doc_class):
#DynamoDB: DEBUG: starting evaluate: ['dynamodb:dynamodbtestdocumentslug:indexes:name:great mountain']
#DynamoDB: DEBUG: Sdfsd: <class 'kev.tests.documents.DynamoDBTestDocumentSlug'>


        self.log.debug("starting evaluate: " + str(filters_list))
        self.log.debug("Sdfsd: " + str(doc_class))
        # TODO what does this do?



        if len(filters_list) == 1:
            filter_value = filters_list[0]
            resp  = self._indexer.scan()  # TODO filter scan
            id_list = resp["Items"]

       #     id_list = self._indexer.tables.filter(Prefix=filter_value)

        # else:
        #     raise ValueError('There should only be one filter for DynamoDB backends')
        # for id in id_list:

        #     index_dict = re.match(self.index_pattern,id.key).groupdict()
        #     yield self.get(doc_class,index_dict['doc_id'])
    #    id_list = self.get_id_list(filters_list)
        for id in id_list:
            self.log.debug("dsssssssssss: " + str(id))
            yield doc_class.get(self.parse_id(id))
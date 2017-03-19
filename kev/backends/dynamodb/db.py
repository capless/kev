import boto3
import json
import re
import logging
from kev.backends import DocDB

from pprint import pprint
from boto3.dynamodb.conditions import Key


class DynamoDB(DocDB):

    db_class   = boto3.resource
    backend_id = 'dynamodb'
    doc_id_string = '{doc_id}:id:{backend_id}:{class_name}'
    index_pattern = r'^(?P<backend_id>[-\w]+):(?P<class_name>[-\w]+)' \
                    ':indexes:(?P<index_name>[-\w]+):(?P<index_value>' \
                    '[-\W\w\s]+)/(?P<doc_id>[-\w]+):id:' \
                    '(?P<backend_id_b>[-\w]+):(?P<class_name_b>[-\w]+)$'


    ############################################################################
    # Desc: dynamodb DB constructor
    #
    # @param  kwargs[aws_secret_access_key]; aws secret key
    # @param  kwargs[aws_access_key_id]; aws acess key id
    # @param  kwargs[table]; aws dynamodb table name
    ############################################################################
    def __init__(self,**kwargs):
        # FUTURE: create helper methods to create/delete tables(useful for testing)

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


    ##############################################################################################
    # CRUD Operation Methods
    ##############################################################################################

    ############################################################################
    # Desc: query for item using specified document id
    #
    # @param  doc_class; document class
    # @param  doc_id; document id
    #
    # @ret Document DynamoDB object list
    ############################################################################
    def save(self,doc_obj):
        # TODO: allow configuration of auto override
        self.log.debug("`````````````starting save " + str((doc_obj)))
        doc_obj, doc = self._save(doc_obj)
        self._indexer.put_item(Item=doc)

        self.log.debug("ending save")
        return doc_obj


    ############################################################################
    # Desc: query for item using specified document id
    #
    # @param  doc_class; document class
    # @param  doc_id; document id
    #
    # @ret Document DynamoDB object list
    ############################################################################
    def get(self,doc_class,doc_id):
        self.log.debug("getting item: {}".format(doc_id))
        doc = self._indexer.get_item(Key=doc_id)
        return doc_class(**(doc["Item"]))


    ############################################################################
    # Desc: empty table
    #
    ############################################################################
    def flush_db(self):
        # FUTURE: potentially improve efficiency for large tables, delete and recreate table

        # describe table to get primary key
        resp = self._client.describe_table(TableName=self.table)
        keys = [k['AttributeName'] for k in resp['Table']['KeySchema']]

        # scan table to get item list
        resp  = self._indexer.scan()
        items = resp["Items"]
        self.log.debug("found {} items to delete".format(len(items)))

        # delete items using batch delete
        if len(items) == 0:
            return
        with self._indexer.batch_writer() as batch:
            for item in items:
                pk = {k: item[k] for k in keys}
                self.log.debug("\t deleting: {}".format(pk))
                batch.delete_item(Key=pk)


    ############################################################################
    # Desc: delete single object from table
    #
    # @param  doc_obj; document object to be deleted
    ############################################################################
    def delete(self, doc_obj):
        # # TODO why do I need to use save before the delete?
        # doc_obj2, doc = self._save(doc_obj)

        # get table primary key
        resp = self._client.describe_table(TableName=self.table)
        keys = [k['AttributeName'] for k in resp['Table']['KeySchema']]

        # create key/value dict of primary key for item to be deleted
        pk = {k: getattr(doc_obj,k) for k in keys}

        # delete item
        self.log.debug("deleting item: {}".format(pk))
        self._indexer.delete_item(Key=pk)


    ############################################################################
    # Desc: return all currently stored items
    #
    # @param  doc_class; document class
    #
    # @ret Document DynamoDB object list
    ############################################################################
    def all(self,doc_class):
        # TODO: verify scans > 1MB still work
        resp = self._indexer.scan()
        item_list = resp["Items"]
        self.log.debug("scanning for all items, '{}' found".format(len(item_list)))

        for item in item_list:
            yield doc_class(**item)


    ##############################################################################################
    # Indexing Methods
    ##############################################################################################

    ############################################################################
    # Desc: return items matching provided filter
    #
    # @param  filters_list; list of filters
    # @param  doc_class; document class
    #
    # @ret Document DynamoDB object list
    ############################################################################
    def evaluate(self, filters_list, doc_class):
        fv = ""
        id_list = list()
        if len(filters_list) == 1:
            fv = filters_list[0]
            fe = Key('_id').eq(fv)
            resp = self._indexer.scan(FilterExpression=fe)
            id_list = resp["Items"]

        self.log.debug("{} records found for filter: {}".format(fv,len(id_list)))
        for id in id_list:
            yield doc_class.get(self.parse_id(id))

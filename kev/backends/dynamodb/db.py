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
        doc_obj, doc = self._save(doc_obj)
        self.log.debug("saving doc: {}".format(doc))
        self._indexer.put_item(Item=doc)
        return doc_obj


    ############################################################################
    # Desc: query for item using specified document id
    #
    # @param  doc_class; document class
    # @param  dict; document id
    #
    # @ret Document DynamoDB object list
    ############################################################################
    def get(self,doc_class,doc_id):
        # FUTURE: all other getters provided as a string, ddb requires dict
        #   since multiple attributes could be used as a primary key
        self.log.debug("getting item: {}".format(doc_id))
        doc = self._indexer.get_item(Key=doc_id)
        return doc_class(**(doc["Item"]))


    ############################################################################
    # Desc: empty table
    #
    ############################################################################
    def flush_db(self):
        # FUTURE: potentially improve efficiency for large tables, delete and recreate table

        # scan table to get item list
        resp  = self._indexer.scan()
        items = resp["Items"]
        self.log.debug("flush_db: found {} items to delete".format(len(items)))

        # delete items using batch delete
        if len(items) == 0:
            return
        with self._indexer.batch_writer() as batch:
            for item in items:
                pk = {k: item[k] for k in self._getPK()}
                self.log.debug("\tflush_db: deleting: {}".format(pk))
                batch.delete_item(Key=pk)


    ############################################################################
    # Desc: delete single object from table
    #
    # @param  doc_obj; document object to be deleted
    ############################################################################
    def delete(self, doc_obj):
        # # TODO why do I need to use save before the delete?
        # doc_obj2, doc = self._save(doc_obj)

        # create key/value dict of primary key for item to be deleted
        pk = {k: getattr(doc_obj,k) for k in self._getPK()}

        # delete item
        self.log.debug("delete: deleting item: {}".format(pk))
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
            # FUTURE: db-side advanced filtering would require elastic search integration
            # Current solutions
            #  1. assume client filter criteria match item values exactly
            #  2. return all records and filter application side (current approach)
            # FUTURE: allow chaining of filters

            # generate lookup attribute list
            fv = filters_list[0]
            grps = re.search(r'indexes:([-\W\w\s]+):([-\W\w\s]+)$', fv)
            attrList = self._getPK()

            filt_key = grps.group(1)
            filt_val = grps.group(2)
            attrList.append(filt_key)

            # generate expression map to avoid keywords
            projExpList = list()
            expAttrMap = dict()
            counter = 0
            for attrName in attrList:
                attrKey = "#p{}".format(counter)
                if attrName in expAttrMap:
                    continue
                projExpList.append(attrKey)
                expAttrMap[attrName] = attrKey       # eliminate duplicates
                counter = counter+1

            # invert map for scan
            expAttrMap = {v: k for k, v in expAttrMap.iteritems()}
            projExpStr = ",".join(projExpList)
            resp = self._indexer.scan(Select="SPECIFIC_ATTRIBUTES",
                ProjectionExpression=projExpStr, ExpressionAttributeNames=expAttrMap)
            items = resp["Items"]

            # filter results
            id_list = list()
            for item in items:
                if (filt_key in item) and re.match(filt_val, item[filt_key], re.IGNORECASE):
                    id_list.append(item)
        else:
            raise ValueError('There should only be one filter for DynamoDB backends')

        self.log.debug("evaluate: {} records found for filter '{}'".format(len(id_list),fv))
        for id in id_list:
            pkList = self._getPK()
            lookupId = {k: id[k] for k in pkList}
            yield doc_class.get(lookupId)



    ##############################################################################################
    # Internal Methods
    #
    # @ret list; primary key attr list
    ##############################################################################################
    def _getPK(self):
                # get table primary key
        resp = self._client.describe_table(TableName=self.table)
        keys = [k['AttributeName'] for k in resp['Table']['KeySchema']]

        return keys

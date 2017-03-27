import boto3
import json
import re
from kev.backends import DocDB

from pprint import pprint
from boto3.dynamodb.conditions import Key


"""Example function with PEP 484 type annotations.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        The return value. True for success, False otherwise.

"""
class DynamoDB(DocDB):

    db_class   = boto3.resource
    backend_id = 'dynamodb'
    doc_id_string = '{doc_id}:id:{backend_id}:{class_name}'
    index_pattern = r'^(?P<backend_id>[-\w]+):(?P<class_name>[-\w]+)' \
                    ':indexes:(?P<index_name>[-\w]+):(?P<index_value>' \
                    '[-\W\w\s]+)/(?P<doc_id>[-\w]+):id:' \
                    '(?P<backend_id_b>[-\w]+):(?P<class_name_b>[-\w]+)$'


    def __init__(self,**kwargs):
        """Dynamodb DB constructor

        Boto3 dynamodb resource/session.

        FUTURE: create helper methods to create/delete tables(useful for testing)

        Args:
            kwargs[aws_secret_access_key] (str): aws secret key
            kwargs[aws_access_key_id] (str): aws acess key id
            kwargs[table] (str): aws dynamodb table name

        """

        if 'aws_secret_access_key' in kwargs and 'aws_access_key_id' in kwargs:
            boto3.Session(aws_secret_access_key=kwargs['aws_secret_access_key'],
                aws_access_key_id=kwargs['aws_access_key_id'])

        self._db      = boto3.resource('dynamodb')
        self._client  = boto3.client('dynamodb')
        self.table    = kwargs['table']
        self._indexer = self._db.Table(self.table)


    ##############################################################################################
    # CRUD Operation Methods
    ##############################################################################################

    def save(self,doc_obj):
        """Query for item using specified document id

        Args:
            doc_obj (dict): document map to save

        Returns:
            doc_obj (dict): saved document map (with primary key attr set)

        """
        doc_obj, doc = self._save(doc_obj)
        self._indexer.put_item(Item=doc)
        return doc_obj


    def get(self,doc_class,doc_id):
        """Query for item using specified document id

        FUTURE: all other getters provided as a string, ddb requires dict
            since multiple attributes could be used as a primary key

        Args:
            doc_class (class): document class
            doc_id (dict): table primary key

        Returns:
            object; document object of retrieved item
        """

        doc = self._indexer.get_item(Key=doc_id)
        return doc_class(**(doc["Item"]))


    ############################################################################
    # Desc: empty table
    #
    ############################################################################
    def flush_db(self):
        """Empty table

        Performs batch delete of all items within table.

        FUTURE: potentially improve efficiency for large tables, delete and recreate table

        """

        # scan table to get item list
        resp  = self._indexer.scan()
        items = resp["Items"]

        # delete items using batch delete
        if len(items) == 0:
            return
        with self._indexer.batch_writer() as batch:
            for item in items:
                pk = {k: item[k] for k in self._get_pk()}
                batch.delete_item(Key=pk)


    def delete(self, doc_obj):
        """Delete single object from table

        Args:
            doc_obj (dict): item dict to delete from table

        """
        # create key/value dict of primary key for item to be deleted
        pk = {k: getattr(doc_obj,k) for k in self._get_pk()}

        # delete item
        self._indexer.delete_item(Key=pk)


    def all(self,doc_class):
        """Return all currently stored items from table

        Args:
            doc_class (class): document class

        Returns:
            object list: list of items from table, converted to document objects

        TODO: verify scans > 1MB still work
        """
        resp = self._indexer.scan()
        item_list = resp["Items"]

        for item in item_list:
            yield doc_class(**item)


    ##############################################################################################
    # Indexing Methods
    ##############################################################################################

    def evaluate(self, filters_list, doc_class):
        """Return items matching provided filter

        FUTURE: db-side advanced filtering would require elastic search integration

        Current solutions
            1. assume client filter criteria match item values exactly
            2. return all records and filter application side (current approach)
        FUTURE: allow chaining of filters

        Args:
            filters_list (list): list of fitlers to apply to result set
            doc_class (class): document class

        Returns:
            object list: list of items that pass provided filters

        """
        id_list = list()

        if len(filters_list) > 0:
            # generate lookup attribute list, grabbing all fields required for later filtering
            # attr_list: return only the data required for filtering
            # filt_map: used to provide client-side filtering
            attr_list = self._get_pk()
            filt_map = dict();
            for filts in filters_list:
                grps = re.search(r'indexes:([-\W\w\s]+):([-\W\w\s]+)$', filts)

                filt_key = grps.group(1)
                filt_val = grps.group(2)
                filt_map[filt_key] = filt_val
                attr_list.append(filt_key)

            # generate expression map to avoid keywords
            proj_exp_list = list()
            exp_attr_map = dict()
            counter = 0
            for attr_name in attr_list:
                attr_key = "#p{}".format(counter)
                if attr_name in exp_attr_map:
                    continue
                proj_exp_list.append(attr_key)
                exp_attr_map[attr_name] = attr_key       # eliminate duplicates
                counter = counter+1


            # invert map for scan
            exp_attr_map = {v: k for k, v in exp_attr_map.iteritems()}
            proj_exp_str = ",".join(proj_exp_list)
            resp = self._indexer.scan(Select="SPECIFIC_ATTRIBUTES",
                ProjectionExpression=proj_exp_str, ExpressionAttributeNames=exp_attr_map)
            items = resp["Items"]

            # filter results
            id_list = list()
            for item in items:
                is_passed = True
                for fk in filt_map:
                    # apply each filter to every item
                    fv = filt_map[fk]
                    if not ((fk in item) and re.match(fv, item[fk], re.IGNORECASE)):
                        is_passed = False

                if is_passed:
                    id_list.append(item)

        for id in id_list:
            pk_list = self._get_pk()
            lookup_id = {k: id[k] for k in pk_list}
            yield doc_class.get(lookup_id)



    ##############################################################################################
    # Internal Methods
    ##############################################################################################
    def _get_pk(self):
        """Retrieve primary key for the table

        Returns:
            keys (dict): table primary key
        """
                # get table primary key
        resp = self._client.describe_table(TableName=self.table)
        keys = [k['AttributeName'] for k in resp['Table']['KeySchema']]

        return keys

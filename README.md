![alt text](https://s3.amazonaws.com/capless/images/kev-small.png "KEV - Keys, Extra Stuff, and Values")


# kev
K.E.V. (Keys, Extra Stuff, and Values) is a Python ORM for key-value stores and document databases based on [**Valley**](https://www.github.com/capless/valley). Currently supported backends are Redis, S3, DynamoDB and a S3/Redis hybrid backend.

[![Build Status](https://travis-ci.org/capless/kev.svg?branch=master)](https://travis-ci.org/capless/kev)

## Python Versions

Kev should work on Python 2.7, 3.3, 3.4, and 3.5. It will not work on 3.2.
## Install
```
pip install kev
```

## Example Project Using KEV

- [flask-capless-blog](https://github.com/capless/flask-capless-blog)
## Example Usage

### Setup the Connection
**Example:** loading.py
```python
from kev.loading import KevHandler


kev_handler = KevHandler({
    's3':{
        'backend':'kev.backends.s3.db.S3DB',
        'connection':{
            'bucket':'your-bucket-name'
        }
    },
    's3redis':{
        'backend':'kev.backends.s3redis.db.S3RedisDB',
        'connection':{
            'bucket':'your-bucket-name',
            'indexer':{
                'host':'your.redis.host.com',
                'port':6379,
            }
        }
    },
    'redis': {
        'backend': 'kev.backends.redis.db.RedisDB',
        'connection': {
            'host': 'your-redis-host.com',
            'port': 6379,
        }
    },
    'dynamodb': {
        'backend': 'kev.backends.dynamodb.db.DynamoDB',
        'connection': {
            'table': 'your-dynamodb-table',
        }
    }
})
```
### Setup the Models
**Example:** models.py
```python
from kev import (Document,CharProperty,DateTimeProperty,
                 DateProperty,BooleanProperty,IntegerProperty,
                 FloatProperty)
from .loading import kev_handler

class TestDocument(Document):
    name = CharProperty(required=True,unique=True,min_length=5,max_length=20)
    last_updated = DateTimeProperty(auto_now=True)
    date_created = DateProperty(auto_now_add=True)
    is_active = BooleanProperty(default_value=True,index=True)
    city = CharProperty(required=False,max_length=50)
    state = CharProperty(required=True,index=True,max_length=50)
    no_subscriptions = IntegerProperty(default_value=1,index=True,min_value=1,max_value=20)
    gpa = FloatProperty()

    def __unicode__(self):
        return self.name
        

    class Meta:
        use_db = 's3redis'
        handler = kev_handler

```

### Use the model
#### How to Save a Document
```python
>>>from .models import TestDocument

>>>kevin = TestDocument(name='Kev',is_active=True,no_subscriptions=3,state='NC',gpa=3.25)

>>>kevin.save()

>>>kevin.name
'Kev'

>>>kevin.is_active
True

>>>kevin.pk
ec640abfd6

>>>kevin.id
ec640abfd6

>>>kevin._id
'ec640abfd6:id:s3redis:testdocument'
```
#### Query Documents

##### First Save Some More Docs
```python

>>>george = TestDocument(name='George',is_active=True,no_subscriptions=3,gpa=3.25,state='VA')

>>>george.save()

>>>sally = TestDocument(name='Sally',is_active=False,no_subscriptions=6,gpa=3.0,state='VA')

>>>sally.save()
```
##### Show all Documents
```python
>>>TestDocument.all()

[<TestDocument: Kev:ec640abfd6>,<TestDocument: George:aff7bcfb56>,<TestDocument: Sally:c38a77cfe4>]

```
##### Get One Document
```python
>>>TestDocument.get('ec640abfd6')
<TestDocument: Kev:ec640abfd6>

>>>TestDocument.objects().get({'state':'NC'})
<TestDocument: Kev:ec640abfd6>

```
##### Filter Documents
```python
>>>TestDocument.objects().filter({'state':'VA'})

[<TestDocument: George:aff7bcfb56>,<TestDocument: Sally:c38a77cfe4>]

>>>TestDocument.objects().filter({'no_subscriptions':3})
[<TestDocument: Kev:ec640abfd6>,<TestDocument: George:aff7bcfb56>]

>>>TestDocument.objects().filter({'no_subscriptions':3,'state':'NC'})
[<TestDocument: Kev:ec640abfd6>]
```
##### Chain Filters
The chain filters feature is only available for Redis and S3/Redis backends.
```python
>>>TestDocument.objects().filter({'no_subscriptions':3}).filter({'state':'NC'})
[<TestDocument: Kev:ec640abfd6>]

```

##### Wildcard Filters
Wildcard filters currently only work with the Redis and S3/Redis backend. Use prefixes with the S3 backend.
```python
>>>TestDocument.objects().filter({'state':'N*'})
[<TestDocument: Kev:ec640abfd6>]

```

##### Prefix Filters
Prefix filters currently only work with the S3 backend. Use wildcard filters with the Redis or S3/Redis backends.
```python
>>>TestDocument.objects().filter({'state':'N'})
[<TestDocument: Kev:ec640abfd6>]
```
### DynamoDB setup
#### Create a table
* **Table name** should be between 3 and 255 characters long. (A-Z,a-z,0-9,_,-,.)
* **Primary key** (partition key) should be equal to `_id`

#### Filter Documents
If you want to make `filter()` queries, you should create an index for every attribute that you want to filter by.
* **Primary key** should be equal to attribute name.
* **Index name** should be equal to attribute name postfixed by *"-index"*. (It will be filled by AWS automatically).
For example, for attribute *"city"*: *Primary key* = *"city"* and index name = *"city-index"*. 
- **IMPORTANT: In other words if your indexed attribute is named city, then your index name should be city-index.**
* **Projected attributes**: *All*.

### Use DynamoDB locally
#### Run DynamoDB
* with persistent storage `docker run -d -p 8000:8000 -v /tmp/data:/data/ dwmkerr/dynamodb -dbPath /data/`

#### Configuration
**Example:** loading.py
```python
from kev.loading import KevHandler


kev_handler = KevHandler({
    'dynamodb': {
        'backend': 'kev.backends.dynamodb.db.DynamoDB',
        'connection': {
            'table': 'your-dynamodb-table',
            'endpoint_url': 'http://127.0.0.1:8000'
        }
    }
})
```

#### Testing
##### Run DynamoDB
* in memory (best performance) `docker run -d -p 8000:8000 dwmkerr/dynamodb -inMemory`

##### Create a table for testing.

```python
import boto3


table_wcu = 2000
table_rcu = 2000
index_wcu = 3000
index_rcu = 2000
table_name = 'localtable'

dynamodb = boto3.resource('dynamodb', endpoint_url="http://127.0.0.1:8000")
dynamodb.create_table(TableName=table_name, KeySchema=[{'AttributeName': '_id', 'KeyType': 'HASH'}],
                      ProvisionedThroughput={'ReadCapacityUnits': table_rcu,
                                             'WriteCapacityUnits': table_wcu},
                      AttributeDefinitions=[{'AttributeName': '_id', 'AttributeType': 'S'},
                                            {u'AttributeName': u'city', u'AttributeType': u'S'},
                                            {u'AttributeName': u'email', u'AttributeType': u'S'},
                                            {u'AttributeName': u'name', u'AttributeType': u'S'},
                                            {u'AttributeName': u'slug', u'AttributeType': u'S'}],
                      GlobalSecondaryIndexes=[
                          {'IndexName': 'city-index', 'Projection': {'ProjectionType': 'ALL'},
                           'ProvisionedThroughput': {'WriteCapacityUnits': index_wcu,
                                                     'ReadCapacityUnits': index_rcu},
                           'KeySchema': [{'KeyType': 'HASH', 'AttributeName': 'city'}]},
                          {'IndexName': 'name-index', 'Projection': {'ProjectionType': 'ALL'},
                           'ProvisionedThroughput': {'WriteCapacityUnits': index_wcu,
                                                     'ReadCapacityUnits': index_rcu},
                           'KeySchema': [{'KeyType': 'HASH', 'AttributeName': 'name'}]},
                          {'IndexName': 'slug-index', 'Projection': {'ProjectionType': 'ALL'},
                           'ProvisionedThroughput': {'WriteCapacityUnits': index_wcu,
                                                     'ReadCapacityUnits': index_rcu},
                           'KeySchema': [{'KeyType': 'HASH', 'AttributeName': 'slug'}]},
                          {'IndexName': 'email-index', 'Projection': {'ProjectionType': 'ALL'},
                           'ProvisionedThroughput': {'WriteCapacityUnits': index_wcu,
                                                     'ReadCapacityUnits': index_rcu},
                           'KeySchema': [{'KeyType': 'HASH', 'AttributeName': 'email'}]}])
```
##### Setup environment variables.
```bash
export DYNAMO_TABLE_TEST='localtable'
export DYNAMO_ENDPOINT_URL_TEST='http://127.0.0.1:8000'
```

### Author

**Twitter:**:[@brianjinwright](https://twitter.com/brianjinwright)
**Github:** [bjinwright](https://github.com/bjinwright)

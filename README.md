![alt text](https://s3.amazonaws.com/capless/images/kev-small.png "KEV - Keys, Extra Stuff, and Values")


# kev
K.E.V. (Keys, Extra Stuff, and Values) is a Python ORM for key-value stores and document databases based on [**Valley**](https://www.github.com/capless/valley). Currently supported backends are Redis, S3 and a S3/Redis hybrid backend.

[![Build Status](https://github.com/capless/kev/workflows/Unittests/badge.svg?branch=master)](https://github.com/capless/kev/actions?query=workflow%3AUnittests+branch%3Amaster)

## Python Versions

Kev should work on Python 3.5+ and higher

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
    name = CharProperty(required=True,unique=True,min_length=3,max_length=20)
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
>>>TestDocument.objects().all()

[<TestDocument: Kev:ec640abfd6>,<TestDocument: George:aff7bcfb56>,<TestDocument: Sally:c38a77cfe4>]

>>>TestDocument.objects().all(skip=1)

[<TestDocument: George:aff7bcfb56>,<TestDocument: Sally:c38a77cfe4>]

>>>TestDocument.objects().all(limit=2)

[<TestDocument: Kev:ec640abfd6>,<TestDocument: George:aff7bcfb56>]

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

##### Sort Documents
```python
>>>TestDocument.objects().filter({'no_subscriptions':3}).sort_by('name')
[<TestDocument: George:aff7bcfb56>, <TestDocument: Kev:ec640abfd6>]
>>>TestDocument.objects().filter({'no_subscriptions':3}).sort_by('name', reverse=True)
[<TestDocument: Kev:ec640abfd6>, <TestDocument: George:aff7bcfb56>]
>>>TestDocument.objects().all().sort_by('gpa')
[<TestDocument: Sally:c38a77cfe4>, <TestDocument: Kev:ec640abfd6>, <TestDocument: George:aff7bcfb56>]
TestDocument.objects().all().sort_by('name').sort_by('gpa')
[<TestDocument: Sally:c38a77cfe4>, <TestDocument: George:aff7bcfb56>>, <TestDocument: Kev:ec640abfd6]
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

### Backup and Restore

Easily backup or restore your model locally or from S3. The backup method creates a JSON file backup. 

#### Backup 

##### Local Backup

```python
TestDocument().backup('test-backup.json')
```

##### S3 Backup

```python

TestDocument().backup('s3://your-bucket/kev/test-backup.json')
```

#### Restore

##### Local Restore

```python

TestDocument().restore('test-backup.json')
```

#### S3 Restore

```python

TestDocument().restore('s3://your-bucket/kev/test-backup.json')
```

### Author

**Twitter:**:[@brianjinwright](https://twitter.com/brianjinwright)
**Github:** [bjinwright](https://github.com/bjinwright)

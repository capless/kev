# kev
K.E.V. (Keys, Extra Stuff, and Values) is a Python ORM for key-value stores and ElasticSearch. Currently supported backends are Redis and a S3/Redis hybrid backend.

##Python Versions

Kev should work on Python 2.7, 3.3, 3.4, and 3.5. It will not work on 3.2.

##Example Usage

###Setup the Connection
**Example:** loading.py
```python
from kev.loading import KevHandler


kev_handler = KevHandler({
    's3':{
        'backend':'kev.backends.s3.db.S3DB',
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
            'host': 'your-redis-host.com,
            'port': 6379,
        }
    }
})
```
###Setup the Models
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
        use_db = 's3'
        handler = kev_handler

```

###Use the model
####How to Save a Document
```python
>>>from .models import TestDocument

>>>kevin = TestDocument(name='Kev',is_active=True,no_subscriptions=3,state='NC',gpa=3.25)

>>>kevin.save()

>>>kevin.name
'Kev'

>>>kevin.is_active
True

>>>kevin.pk
1

>>>kevin.id
1

>>>kevin._id
'testdocument:id:1'
```
####Query Documents

#####First Save Some More Docs
```python

>>>george = TestDocument(name='George',is_active=True,no_subscriptions=3,gpa=3.25,state='VA')

>>>george.save()

>>>sally = TestDocument(name='Sally',is_active=False,no_subscriptions=6,gpa=3.0,state='VA')

>>>sally.save()
```
#####Show all Documents
```python
>>>TestDocument.all()

[<TestDocument: Kev:1>,<TestDocument: George:2>,<TestDocument: Sally:3>]

```
#####Get One Document
```python
>>>TestDocument.get(1)
<TestDocument: Kev:1>

>>>TestDocument.objects().get({'state':'NC'})
<TestDocument: Kev:1>

```
#####Filter Documents
```python
>>>TestDocument.objects().filter({'state':'VA'})

[<TestDocument: George:2>,<TestDocument: Sally:3>]

>>>TestDocument.objects().filter({'no_subscriptions':3})
[<TestDocument: Kev:1>,<TestDocument: George:2>]

>>>TestDocument.objects().filter({'no_subscriptions':3,'state':'NC'})
[<TestDocument: Kev:1>]
```
#####Chain Filters
```python
>>>TestDocument.objects().filter({'no_subscriptions':3}).filter({'state':'NC'})
[<TestDocument: Kev:1>]

```
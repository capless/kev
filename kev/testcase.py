import unittest
from kev.loading import KevHandler
from envs import env

kev_handler = KevHandler({
    's3redis':{
        'backend':'kev.backends.s3redis.db.S3RedisDB',
        'connection':{
            'bucket':env('S3_BUCKET_TEST'),
            'indexer':{
                'host':env('REDIS_HOST_TEST'),
                'port':env('REDIS_PORT_TEST'),
            }
        }
    },
    's3': {
        'backend': 'kev.backends.s3.db.S3DB',
        'connection': {
            'bucket': env('S3_BUCKET_TEST')
        }
    },
    'redis': {
        'backend': 'kev.backends.redis.db.RedisDB',
        'connection': {
            'host': env('REDIS_HOST_TEST'),
            'port': env('REDIS_PORT_TEST'),
        }
    },
    'dynamodb': {
        'backend': 'kev.backends.dynamodb.db.DynamoDB',
        'connection': {
            'table': env('DYNAMO_TABLE_TEST'),
            'endpoint_url': env('DYNAMO_ENDPOINT_URL_TEST')
        }
    },
    'cloudant': {
        'backend': 'kev.backends.cloudant.db.CloudantDB',
        'connection': {
            'username': env('CLOUDANT_USERNAME_TEST'),
            'password': env('CLOUDANT_PASSWORD_TEST'),
            'url': env('CLOUDANT_URL_TEST'),
            'account': env('CLOUDANT_ACCOUNT_TEST'),
            'table': env('CLOUDANT_TABLE_TEST'),
        }
    }
})


class KevTestCase(unittest.TestCase):

    def tearDown(self):
        for db_label in list(kev_handler._databases.keys()):
            kev_handler.get_db(db_label).flush_db()

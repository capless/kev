import unittest
from kev.loading import KevHandler
from envs import env

kev_handler = KevHandler({
    's3':{
        'backend':'kev.backends.s3.db.S3DB',
        'connection':{
            'bucket':env('S3_BUCKET_TEST'),
            'indexer':{
                'host':env('REDIS_HOST_TEST'),
                'port':env('REDIS_PORT_TEST'),
            }
        }
    },
    'redis': {
        'backend': 'kev.backends.redis.db.RedisDB',
        'connection': {
            'host': env('REDIS_HOST_TEST'),
            'port': env('REDIS_PORT_TEST'),
        }
    }
})

class KevTestCase(unittest.TestCase):

    def tearDown(self):
        for db_label in list(kev_handler._databases.keys()):
            kev_handler.get_db(db_label).flush_db()
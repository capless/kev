import unittest
import boto3
from kev.loading import KevHandler
from envs import env

bucket_a = env('S3_BUCKET_TEST', 'kevtest')
bucket_b = env('S3_BUCKET_TEST_B', 'kevtestb')

kev_handler = KevHandler({
    's3redis': {
        'backend': 'kev.backends.s3redis.db.S3RedisDB',
        'connection': {
            'bucket': bucket_a,
            'endpoint_url': 'http://localstack:4566',
            'restore': {
                'endpoint_url': 'http://localstack:4566'
            },
            'indexer': {
                'host': env('REDIS_HOST_TEST', 'redis'),
                'port': env('REDIS_PORT_TEST', 6379, var_type='integer'),
            }
        }
    },
    's3': {
        'backend': 'kev.backends.s3.db.S3DB',
        'connection': {
            'bucket': bucket_b,
            'endpoint_url': 'http://localstack:4566',
            'restore': {
                'endpoint_url': 'http://localstack:4566'
            }
        }
    },
    'redis': {
        'backend': 'kev.backends.redis.db.RedisDB',
        'connection': {
            'host': env('REDIS_HOST_TEST', 'redis'),
            'port': env('REDIS_PORT_TEST', 6379, var_type='integer'),
            'restore': {
                'endpoint_url': 'http://localstack:4566'
            }
        }
    },
})

session = boto3.session.Session()

s3_client = session.client(
    service_name='s3',
    aws_access_key_id=env('AWS_ACCESS_KEY_ID', 'test'),
    aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY', 'test'),
    endpoint_url='http://localstack:4566',
)


class KevTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        s3_client.create_bucket(Bucket=bucket_a)
        s3_client.create_bucket(Bucket=bucket_b)

    def tearDown(self):
        for db_label in list(kev_handler._databases.keys()):
            kev_handler.get_db(db_label).flush_db()

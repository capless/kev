'''
Created on Sep 17, 2014

@author: brian
'''
import sys

from django.conf import settings

from redes.loading.base import RedisDBHandler
if 'test' in sys.argv:
    redis_handler = RedisDBHandler(settings.REDIS_DBS_TEST)
else:
    redis_handler = RedisDBHandler(settings.REDIS_DBS)
get_db = redis_handler.get_db
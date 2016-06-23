'''
Created on Sep 18, 2014

@author: brian
'''
from .base import RedisDBHandler
from ..utils import import_util, env

redis_config = import_util(env('REDIS_CONFIG'))
redis_handler = RedisDBHandler(redis_config)

get_db = redis_handler.get_db
import sys
import redis

class RedisDBHandler(object):
    
    def __init__(self,databases):
        #Created for get_db method
        self._databases = dict()
        self._labels = list()
        for db_label,db_info in databases.iteritems():
            db = redis.StrictRedis(db_info.get('DATABASE_HOST'),port=db_info.get('DATABASE_PORT'))
            self._databases[db_label] = db
            self._labels.append(db_label)
            
    def get_db(self,db_label):
        
        return self._databases.get(db_label)
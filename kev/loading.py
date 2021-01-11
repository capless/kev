import valley.utils


class KevHandler(object):

    def __init__(self, databases):
        # Created for get_db method
        self._databases = dict()
        self._connections = dict()
        self._labels = list()

        for db_label, db_info in databases.items():
            db_klass = valley.utils.import_util(db_info.get('backend'))
            self._databases[db_label] = db_klass(**db_info.get('connection'))

    def get_db(self, db_label):
        return self._databases.get(db_label)


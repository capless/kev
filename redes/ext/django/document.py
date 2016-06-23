from ...document.base import BaseDocument, DeclarativeVariablesMetaclass
from .loading import get_db

class Document(BaseDocument):
    __metaclass__ = DeclarativeVariablesMetaclass
    
    @classmethod
    def get_db(cls):
        return get_db(cls.Meta.use_db)
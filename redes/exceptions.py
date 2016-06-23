class RequiredException(Exception):
    def __init__(self,msg):
        self.error_msg = msg
        
    def __str__(self):
        return self.error_msg
    
class ValidationException(Exception):
    def __init__(self,msg):
        self.error_msg = msg
        
    def __str__(self):
        return self.error_msg
    
class RequestError(Exception):
    def __init__(self,msg):
        self.error_msg = msg
        
    def __str__(self):
        return self.error_msg
    
class DocNotFoundError(Exception):
    pass

class QueryIndexError(Exception):
    pass

class QueryError(Exception):
    pass

class ResourceNotFound(Exception):
    pass

class DocSaveError(Exception):
    pass

class ResourceError(Exception):
    pass
from .exceptions import QueryError

REPR_OUTPUT_SIZE = 20

class QuerySetMixin(object):
    query_type = None

    def __init__(self,doc_class,q=None,parent_q=None):
        self.parent_q=parent_q
        self._result_cache = None
        self._doc_class = doc_class
        self.q = q
        self.evaluated = False
        self._db = self._doc_class.get_db()
        if q and parent_q:
            self.q = self.combine_qs()

    def combine_qs(self):
        raise NotImplementedError    

    def prepare_filters(self):
        filter_list = []
        for k,v in self.q.items():
            if isinstance(v,list):
                for index_v in v:
                    filter_list.append(self._doc_class().get_index_name(k,index_v))
            else:
                filter_list.append(self._doc_class().get_index_name(k,v))
        return filter_list

    def __len__(self):
        self._fetch_all()
        return len(self._result_cache)
           
    def __repr__(self):
        data = list(self[:REPR_OUTPUT_SIZE + 1])
        if len(data) > REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return repr(data)   
    
    def __iter__(self):
        self._fetch_all()
        return iter(self._result_cache)
    
    def _fetch_all(self):
        if self._result_cache is None:
            self._result_cache = list(self.evaluate())
        
    def count(self):
        return len(list(self.evaluate()))

    def delete(self):
        pass
            
    def __nonzero__(self):
        self._fetch_all()
        return bool(self._result_cache)
    
    def __getitem__(self,index):
        if self._result_cache is not None:
            return self._result_cache[index]
        else:
            self._fetch_all()
            return self._result_cache[index]
    
    def evaluate(self):
        raise NotImplementedError


def combine_list(a,b):
    if isinstance(a,(set,tuple,list)):
        a = list(a)
    else:
        a = [a]
    if isinstance(b,(set,tuple,list)):
        b = list(b)
    else:
        b = [b]
    a.extend(b)
    return a

def combine_dicts(a, b, op=combine_list):
    z = a.copy()
    z.update(b)
    z.update([(k, op(a[k], b[k])) for k in set(b) & set(a)])
    doc_type = z.get('doc_type')
    if isinstance(doc_type,list):
        doc_type = set(doc_type)
        if len(doc_type) == 1:
            doc_type = doc_type[0]
            z['doc_type'] = doc_type
    return z
    
    
class QuerySet(QuerySetMixin):
    
    def __init__(self, doc_class,q=None, parent_q=None):

        super(QuerySet,self).__init__(doc_class,q=q,parent_q=parent_q)

    def filter(self,q):
        return QuerySet(self._doc_class,q,self.q)

    def combine_qs(self):
        return combine_dicts(self.parent_q, self.q)


    def evaluate(self):
        filters_list = self.prepare_filters()

        if len(filters_list) == 1:
            id_list = self._db.smembers(filters_list[0])
        else:
            id_list = self._db.sinter(*filters_list)
        pipe = self._db.pipeline()
        for id in id_list:
            pipe.hgetall(id)
        return [self._doc_class(**doc) for doc in pipe.execute()]

    
class SearchSet(QuerySetMixin):
    
    def __init__(self, doc_class,index_id=None,index_name=None,q=None, parent_q=None,include_docs=True):
        self._index_id = index_id
        self._index_name = index_name
        self._include_docs = include_docs
        super(SearchSet,self).__init__(doc_class,q,parent_q)
        
    def __call__(self,index_id,index_name,q,include_docs=True):
        return SearchSet(self._doc_class,index_id=index_id,
                         index_name=index_name,q=q,include_docs=include_docs)
        
    def combine_qs(self):
        if self.q and self.parent_q:
            return self.parent_q & self.q    
        return self.q
             
    def search(self,q,include_docs=True):
        return SearchSet(self._doc_class,self._index_id,
                         self._index_name,self.q,self.parent_q,include_docs)
    
    def evaluate(self):
        doc = dict(query=self.q,include_docs=self._include_docs)
        resp = self._db.get('_design/{0}/_search/{1}'.format(
                            self._index_id,self._index_name),params=doc)
        json_data = resp.json()

        error = json_data.get('error',None) 
        docs = json_data.get('rows',None)
        
        if error:
            raise QueryError(json_data.get('reason'))
        doc_set = list()
        if doc:

            for i in docs:
                if not self._include_docs:
                    i['fields']['_id'] = i.pop('id')
                    doc_set.append(self._doc_class(**i['fields']))
                else:
                    doc_set.append(self._doc_class(**i['doc']))
            return doc_set
        else:
            return doc_set
        
    
class QueryManager(object):
    
    def __init__(self,cls):
        self._doc_class = cls
        
        self.filter = QuerySet(self._doc_class).filter
        self.search = SearchSet(self._doc_class)

from .exceptions import QueryError

REPR_OUTPUT_SIZE = 20


def combine_list(a, b):
    if isinstance(a, (set, tuple, list)):
        a = list(a)
    else:
        a = [a]
    if isinstance(b, (set, tuple, list)):
        b = list(b)
    else:
        b = [b]
    a.extend(b)
    return a


def combine_dicts(a, b, op=combine_list):
    z = a.copy()
    z.update(b)
    z.update([(k, op(a[k], b[k])) for k in set(b) & set(a)])
    doc_type = z.get('_doc_type')
    if isinstance(doc_type, list):
        doc_type = set(doc_type)
        if len(doc_type) == 1:
            doc_type = doc_type[0]
            z['_doc_type'] = doc_type
    return z


class QuerySetMixin(object):
    query_type = None

    def __init__(self, doc_class, q=None, parent_q=None, sorting_p=None,
                 parent_sorting_p=None, all_param=None):
        self.parent_q = parent_q
        self._result_cache = None
        self._doc_class = doc_class
        self.q = q
        self.sortingp_list = [sorting_p] if sorting_p is not None else []
        self.evaluated = False
        self.all_param = all_param if all_param else AllParam()
        self._db = self._doc_class.get_db()
        if q and parent_q:
            self.q = self.combine_qs()
        if sorting_p and parent_sorting_p:
            self.sortingp_list = combine_list(self.sortingp_list, parent_sorting_p)

    def combine_qs(self):
        return combine_dicts(self.parent_q, self.q)

    def prepare_filters(self):
        filter_list = []
        for k, v in list(self.q.items()):
            if isinstance(v, list):
                for index_v in v:
                    filter_list.append(
                        self._doc_class.get_index_name(
                            k, index_v))
            else:
                filter_list.append(self._doc_class.get_index_name(k, v))
        return filter_list

    def __len__(self):
        self._fetch_all()
        return len(self._result_cache)

    def __repr__(self):  # pragma: no cover
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

    def __bool__(self):
        self._fetch_all()
        return bool(self._result_cache)

    def __getitem__(self, index):
        if self._result_cache is not None:
            return self._result_cache[index]
        else:
            self._fetch_all()
            return self._result_cache[index]

    def evaluate(self):
        raise NotImplementedError


class QuerySet(QuerySetMixin):

    def filter(self, q):
        return QuerySet(self._doc_class, q, self.q)

    def sort_by(self, key, reverse=False):
        sorting_p = SortingParam(key, reverse)
        return QuerySet(self._doc_class, self.q, None, sorting_p, self.sortingp_list, all_param=self.all_param)

    def get(self, q):
        qs = QuerySet(self._doc_class, q, self.q)
        if len(qs) > 1:
            raise QueryError(
                'This query should return exactly one result. Your query returned {0}'.format(
                    len(qs)))
        if len(qs) == 0:
            raise QueryError('This query did not return a result.')
        return qs[0]

    def all(self, skip=None, limit=None):
        all_param = AllParam(all=True, skip=skip, limit=limit)
        return QuerySet(self._doc_class, None, None, all_param=all_param)

    def evaluate(self):
        filters_list = None
        if not self.all_param.all:
            filters_list = self.prepare_filters()
        return self._doc_class.get_db().evaluate(filters_list, self.sortingp_list,
                                                 self.all_param, self._doc_class)


class QueryManager(object):

    def __init__(self, cls):
        self._doc_class = cls

        self.filter = QuerySet(self._doc_class).filter
        self.get = QuerySet(self._doc_class).get
        self.sort_by = QuerySet(self._doc_class).sort_by
        self.all = QuerySet(self._doc_class).all


class SortingParam(object):

    def __init__(self, key, reverse=False):
        self.key = key
        self.reverse = reverse

    def __repr__(self):
        return "%s(key='%s', reverse=%s)" % (self.__class__, self.key, self.reverse)

    @staticmethod
    def needs_multiple_passes(sortingp_list):
        """Helper method to check if a list should be sorted in multiple passes."""
        assert len(sortingp_list) > 0
        is_different = False
        initial_reverse = sortingp_list[0].reverse
        for sortingp in sortingp_list:
            if sortingp.reverse != initial_reverse:
                is_different = True
        return is_different

    @staticmethod
    def attr_sort(sortinp_list):
        """Helper method to sort by the attributes named by strings of attrs in order"""
        return lambda x: [getattr(x, sortingp.key) for sortingp in sortinp_list]


class AllParam(object):

    def __init__(self, all=False, skip=None, limit=None):
        self.all = all
        self.skip = skip
        self.limit = limit

    def __repr__(self):
        return "%s(all='%s', skip='%s', limit=%s)" % (self.__class__, self.all,self.skip,
                                                      self.limit)

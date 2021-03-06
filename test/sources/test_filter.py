''' test filter.py '''

import pytest

from col_desc import CDXState
from filter import Filter
from sql_util import JoinState
from tbl_desc import TblDesc
import tbl_descs

def test_results():
    def check_pickling(f):
        saved = f.get_state()
        restored = Filter.from_state(saved, td.row_desc.col_descs)
        if not(restored == f):
            assert restored == f

    def check(t, exp_sql=None, exp_joins=None):
        what = '%s(%r)' % (td.db_tbl_cls.__name__, t)
        try:
            f = Filter(t)
            js = JoinState(td)
        except Exception:
            raise Exception("can'f make Filter or JoinState for %s", what)
        try:
            sql = f.sql_str(js, CDXState())
        except Exception:
            raise Exception("can'f get SQL string for %s" % what)
        if exp_sql is None or exp_joins is None:
            print('hey')
        else:
            if sql != exp_sql:
                assert sql == exp_sql
            for got_join, exp_join in zip(js.sql_strs, exp_joins):
                if got_join != got_join:
                    assert got_join == exp_join
        check_pickling(f)
        pass

    TblDesc.complete_tbl_descs()

    td = TblDesc.lookup_tbl_desc('DbFolder')
    t_lt_id = ('<', td.lookup_col_desc('id'), 123)
    check(t_lt_id, 'WHERE db_folder.id < 123', [])
    t_lt_name = ('==', td.lookup_col_desc('name'), 'diana')
    check(t_lt_name, 'WHERE item_0.name == "diana"',
        ['JOIN item AS item_0 ON db_folder.id == item_0.id'])
    t_lt_and = ('&', t_lt_id, t_lt_name)
    check(t_lt_and, 'WHERE db_folder.id < 123 AND item_0.name == "diana"',
        ['JOIN item AS item_0 ON db_folder.id == item_0.id'])
    t_lt_minus = ('-', t_lt_id, t_lt_name)
    check(t_lt_minus, 'WHERE db_folder.id < 123 AND  NOT item_0.name == "diana"',
        ['JOIN item AS item_0 ON db_folder.id == item_0.id'])
    t_lt_or = ('|', t_lt_id, t_lt_name)
    check(t_lt_or, 'WHERE db_folder.id < 123 OR item_0.name == "diana"',
        ['JOIN item AS item_0 ON db_folder.id == item_0.id'])
    t_lt_orand = ('|', t_lt_or, t_lt_and)
    check(t_lt_orand,
        'WHERE db_folder.id < 123 OR item_0.name == "diana" OR db_folder.id < 123 AND item_0.name == "diana"',
        ['JOIN item AS item_0 ON db_folder.id == item_0.id'])
    t_lt_andor = ('&', t_lt_and, t_lt_or)
    check(t_lt_andor,
        'WHERE db_folder.id < 123 AND item_0.name == "diana" AND (db_folder.id < 123 OR item_0.name == "diana")',
        ['JOIN item AS item_0 ON db_folder.id == item_0.id'])


''' search filter tuples '''

from typing import Any, Tuple

from sql_util import JoinState

class Filter(object):
    tup: Tuple[Any]
    ''' filter-tup:
            ('</<=/==/!=/>=/>', col-desc, value)
            ('begins/ends/contains', col-desc, str-expr)
            ('null/nonnull', col-desc)
            ('tag', tag-expr)
            ('note', note-expr)
            ('|/&', filter-tup,...)
            ('-', filter-tup, filter-tup)
            ('!', filter-tup)
        tag-expr:
            'tag-str'
            ('|/&', tag-expr,...)
            ('-', tag-expr, tag-expr)
        note-expr:
            ('begins/ends/contains', col-desc, str-expr)
            ('|/&', note-expr,...)
            ('-', note-expr, note-expr)
        str-expr:
            str
            ('|/&', str-expr,...)
            ('-', str-expr, str-expr)
    '''
    def __init__(self, arg):
        self.tup = arg

    @staticmethod
    def _tup_str(t, js: JoinState, parent_pri):
        # TODO insert parentheses
        map = {
            '<':        lambda t: Filter._relop_str(t, js, '<'),
            '<=':       lambda t: Filter._relop_str(t, js, '<='),
            '==':       lambda t: Filter._relop_str(t, js, '=='),
            '!=':       lambda t: Filter._relop_str(t, js, '!='),
            '>=':       lambda t: Filter._relop_str(t, js, '>='),
            '>':        lambda t: Filter._relop_str(t, js, '>'),
            '&':        lambda t: Filter._many_str(t, js, 'AND', 6, parent_pri),
            '|':        lambda t: Filter._many_str(t, js, 'OR', 7, parent_pri),
            '!':        lambda t: Filter._uni_str(t, js, 'NOT', 5, parent_pri),
            '-':        lambda t: Filter._minus_str(t, js, parent_pri)
        }
        try:
            return map[t[0]](t)
        except KeyError:
            raise KeyError(str(t))

    @staticmethod
    def _parens(child_str, child_pri, parent_pri):
        return child_str if child_pri <= parent_pri else  '(' + child_str + ')'

    @staticmethod
    def _relop_str(t, js: JoinState, op):
        return '%s %s %s' % (
            js.sql_col_ref(t[1]), op, t[1].sql_literal_str(t[2]))

    @staticmethod
    def _many_str(t, js: JoinState, op, my_pri, parent_pri):
        operands = [Filter._tup_str(operand, js, my_pri) for operand in t[1:]]
        if len(operands) == 1:
            return operands[0]
        else:
            return Filter._parens((' %s ' % op).join(operands), my_pri, parent_pri)

    @staticmethod
    def _uni_str(t, js: JoinState, op, my_pri, parent_pri):
        operand = Filter._tup_str(t[1], js, my_pri)
        return Filter._parens(' %s %s' % (op, operand), my_pri, parent_pri)

    @staticmethod
    def _minus_str(t, js: JoinState, parent_pri):
        t2 = ('&', t[1], ('!', t[2]))
        return Filter._tup_str(t2, js, parent_pri)

    def sql_str(self, js: JoinState):
        return 'WHERE ' + Filter._tup_str(self.tup, js, parent_pri=9)

if __name__ == '__main__':
    import tbl_descs
    from tbl_desc import TblDesc

    def check(t, exp_sql=None, exp_joins=None):
        global td
        what = '%s(%r)' % (td.db_tbl_cls.__name__, t)
        try:
            f = Filter(t)
            js = JoinState(td)
        except Exception:
            raise Exception("can't make Filter or JoinState for %s", what)
        try:
            sql = f.sql_str(js)
        except Exception:
            raise Exception("can't get SQL string for %s" % what)
        if exp_sql is None or exp_joins is None:
            print('hey')
        else:
            assert sql == exp_sql
            for got_join, exp_join in zip(js.sql_strs, exp_joins):
                assert got_join == exp_join
        pass

    TblDesc.complete_tbl_descs()

    td = TblDesc.lookup_tbl_desc('DbFolder')
    t_lt_id = ('<', td.row_desc.col_descs[0], 123)
    check(t_lt_id, 'WHERE db_folder.id < 123', [])
    t_lt_name = ('==', td.row_desc.col_descs[1], 'diana')
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
    pass



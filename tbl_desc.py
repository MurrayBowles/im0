""" database Table Descriptor classes """

import re
from typing import Any, List, Mapping, Optional, Type

from col_desc import ChildrenCD, ColDesc, DataColDesc, LinkColDesc, VirtualColDesc
from col_desc import IdCD, ShortcutCD, SuperCD
from row_desc import RowDesc
from sorter import Sorter, SorterCol
from util import force_list

import db
ImTblCls = Type[db.Base] # a database table class


class TblDesc(object):
    db_tbl_cls: ImTblCls        # the Python database-table class
    disp_names: List[str]       # display names, in decreasing length
    row_desc: RowDesc           # this table's predefined columns
    def_viewed_row: Mapping[Type[Any], RowDesc]  # FIXME: Any=>TblTP
    sorter: Optional[Sorter]
    # TODO tag_field

    objs = []  # List[TblDesc]

    def __init__(self, db_tbl_cls, disp_names, col_desc_list, def_viewed_cols, sorter_str):
        self.db_tbl_cls = db_tbl_cls
        self.disp_names = force_list(disp_names)
        self.row_desc = RowDesc(col_desc_list)
        self.def_viewed_row = def_viewed_cols
        self.sorter_str = sorter_str
        self.sorter = None
        TblDesc.objs.append(self)
        pass

    def __eq__(self, other):
        # TblDescs are only created statically in tbl_descs.py, and not copied
        return self is other

    def menu_text(self):
        if hasattr(self, '_menu_text'):
            return self._menu_text
        else:
            return self.disp_names[0] + 's'

    @classmethod
    def lookup_tbl_desc(cls, db_name):
        for td in cls.objs:
            if td.db_tbl_cls.__name__ == db_name:
                return td
        raise KeyError('%s is not a known TblDesc' % db_name)

    def lookup_col_desc(self, db_name):
        for cd in self.row_desc.col_descs:
            if cd.db_name == db_name:
                if not hasattr(cd, 'db_attr'):
                    cd.db_attr = getattr(self.db_tbl_cls, db_name, None)
                return cd
        raise KeyError('%s has no column %s' % (self.db_tbl_cls.__name__, db_name))

    def col_idx(self, col_desc):
        return self.row_desc.col_descs.index(col_desc)

    def sql_name(self, suffix=None):
        n = self.db_tbl_cls.__tablename__
        if suffix is not None:
            n += '_' + suffix
        sql_bad = r'\W'  # not very precise...
        if re.compile(sql_bad).search(n):
            n = '"' + n + '"'
        return n

    def set_sorter(self, sorter: Sorter):
        self.sorter = sorter

    def set_sorter_by_col_name(self, key_str):
        ''' Set the Sorter for this table.
            key_str is {{+-}col_spec,...  (with no spaces)
        '''
        col_specs = key_str.split(',')
        sorter_cols = []
        for col_spec in col_specs:
            cd = self.lookup_col_desc(col_spec[1:])
            sorter_cols.append(SorterCol(cd, col_spec[0] == '-'))
        sorter = Sorter(sorter_cols)
        self.set_sorter(sorter)

    def complete_col_desc(self, col_desc: ColDesc):
        ''' Complete a ColDesc's definition. '''
        if isinstance(col_desc, DataColDesc) or isinstance(col_desc, LinkColDesc):
            col_desc.db_attr = getattr(self.db_tbl_cls, col_desc.db_name, None)
            if isinstance(col_desc, LinkColDesc):
                col_desc.foreign_cd = self.lookup_col_desc(col_desc.foreign_key_name)
                col_desc.foreign_td = TblDesc.lookup_tbl_desc(col_desc.foreign_tbl_name)
                if col_desc.disp_col_name is not None:
                    col_desc.disp_cd = self.lookup_col_desc(col_desc.disp_col_name)
                pass
        elif isinstance(col_desc, ChildrenCD):
            col_desc.db_attr = None
            col_desc.foreign_td = TblDesc.lookup_tbl_desc(col_desc.foreign_tbl_name)
            col_desc.foreign_cd = col_desc.foreign_td.lookup_col_desc(col_desc.foreign_key_name)
        elif isinstance(col_desc, ShortcutCD):
            tbl_desc = self
            col_desc.path_cds = []
            if col_desc.db_name == 'folder_date2':
                print('cc')
            for step_name in col_desc.path_str.split('.'):
                if tbl_desc is None:
                    raise ValueError('no TblDesc to evaluate %s' % (step_name))
                step_cd = tbl_desc.lookup_col_desc(step_name)
                if isinstance(step_cd, ShortcutCD):
                    # flatten any embedded ShortcutCDs
                    try:
                        if step_cd.path_cds is None:
                            tbl_desc.complete_col_desc(step_cd)
                        if isinstance(step_cd.path_cds[-1], LinkColDesc):
                            tbl_desc = step_cd.path_cds[-1].foreign_td
                        else:
                            tbl_desc = None
                        col_desc.path_cds.extend(step_cd.path_cds)
                    except Exception as ed:
                        print('hey')
                elif isinstance(step_cd, LinkColDesc):
                    try:
                        if step_cd.foreign_td is None:
                            tbl_desc.complete_col_desc(step_cd)
                        tbl_desc = step_cd.foreign_td
                        col_desc.path_cds.append(step_cd)
                    except Exception as ed:
                        print('hey')
                elif isinstance(step_cd, DataColDesc) or isinstance(step_cd, VirtualColDesc):
                    tbl_desc = None
                    col_desc.path_cds.append(step_cd)
                else:
                    print('hey')
        elif isinstance(col_desc, VirtualColDesc):
            col_desc.dependency_cds = []
            for name in col_desc.dependencies:
                dcd = self.lookup_col_desc(name)
                self.complete_col_desc(dcd)
                col_desc.dependency_cds.append(dcd)

    def _complete(self):
        for col_desc in self.row_desc.col_descs:
            self.complete_col_desc(col_desc)
        self.set_sorter_by_col_name(self.sorter_str)

    @classmethod
    def complete_tbl_descs(cls):
        for tbl_desc in cls.objs:
            tbl_desc._complete()

    def viewed_cols(self, view_cls):
        # TODO: per-table cfg bindings
        if view_cls not in self.def_viewed_row:
            return self.def_viewed_row[TblReportTP]
        else:
            return self.def_viewed_row[view_cls]

    def __repr__(self):
        return '%s(%r, %r, %r, %r)' % (
            self.__class__.__name__,
            self.db_tbl_cls.__name__, self.disp_names,
            self.row_desc,
            self.def_viewed_row)


class ItemTblDesc(TblDesc):
    ''' describes a table which is a subclass of db.Item '''

    def __init__(self, db_tbl_cls, disp_names, col_descs, def_viewed_cols, sorter_str):
        extended_col_descs = [
            IdCD(),
            SuperCD('item', 'Item', path_str='id->Item', hidden=True),
            ShortcutCD('name', 'Name', path_str='item.name'),
            ShortcutCD('type', 'Type', path_str='item.type', hidden=True)
        ]
        extended_col_descs.extend(col_descs)
        super().__init__(db_tbl_cls, disp_names, extended_col_descs, def_viewed_cols, sorter_str)
    pass


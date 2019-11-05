''' table, block, and row buffers '''

from dataclasses import dataclass
from typing import Int, List, Tuple

from col_desc import ColDesc
from row_buf import RowBuf
from tbl_query import TblQuery


@dataclass
class BlkBuf(object):
    first: Any              # key of first element
    last: Any               # key of last element
    rows: List[RowBuf]

    @classmethod
    def from_row_buf_list(cls, row_buf_list: List[RowBuf]):
        if len(row_buf_list) == 0:
            return BlkBuf(first=None, last=None, rows=[])



class TblBuf(object):
    tbl_query: TblQuery     # the access interface to the table
    blks: List[BlkBuf]      # sorted by key of first element

    def __init__(self, tbl_query: TblQuery):
        self.set_query(tbl_query)

    def set_query(self, tbl_query):
        self.tbl_query = tbl_query
        self.blks = []

    def get(self, limit=None, skip=0):
        row_bufs = self.tbl_query.get(*kwargs)
        bb = BlkBuf()
        self.blks = []

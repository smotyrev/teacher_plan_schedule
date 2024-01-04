from enum import Enum

import PySimpleGUI as sg
import sqlite3
from sqlite3 import Connection, Cursor

from config import DEBUG, DB_NAME, datetime, date

con = sqlite3.connect(DB_NAME)


class ColType(Enum):
    INT = 1
    STR = 2
    DATE = 3
    STR_LIST = 4
    RELATION = 5


class Relation:
    __select: str
    __many: bool
    __cache: dict[int: list[tuple]] = {}

    def __init__(self, src_tbl: str, join_tbl: str | None = None) -> None:
        if join_tbl is not None:
            self.__many = True
            self.__select = f"SELECT `{src_tbl}`.* FROM `{src_tbl}` " \
                            f"JOIN `{join_tbl}` ON `{join_tbl}`.{src_tbl}_id = `{src_tbl}`.id " \
                            f"WHERE `{join_tbl}`.#tbl#_id = #id#"
        else:
            self.__many = False
            self.__select = f"SELECT * FROM `{src_tbl}` " \
                            f"WHERE id = #id#"

    def query(self, tbl: str, dst_id: int) -> list[tuple] | tuple:
        query = self.__select.replace(
            '#tbl#', tbl).replace(
            '#id#', str(dst_id))
        h = hash(query)
        if h in self.__cache:
            DEBUG and print("...cached query", h)
            return self.__cache[h]
        DEBUG and print("Query relation:", query)
        cur = con.cursor()
        if self.__many:
            res = cur.execute(query).fetchall()
        else:
            res = cur.execute(query).fetchone()
        cur.close()
        self.__cache[h] = res
        return res

    @staticmethod
    def clear_cache():
        Relation.__cache.clear()


class Col:
    name: str
    dispName: str
    ctype: ColType | None
    relation: Relation | None

    def __init__(self, name: str, disp_name: str, ctype: ColType | None = None,
                 relation: Relation | None = None) -> None:
        self.name = name
        self.dispName = disp_name
        self.ctype = ctype
        self.relation = relation

    def __hash__(self) -> int:
        return hash(self.name) | hash(self.dispName)

    def __eq__(self, o: object) -> bool:
        return hash(o) == hash(self)

    def __repr__(self) -> str:
        return f"`{self.name}`"


class FancyTable:
    tblName: str
    dispName: str
    # Columns:
    id = Col('id', 'id', ColType.INT)
    columns: (Col, ...)

    @staticmethod
    def row_to_str(row: {Col: any}) -> str:
        return str(row)


class Row:
    __f: type[FancyTable]
    __columnsRow: {Col: any}

    def __init__(self, row: tuple, f: type[FancyTable]) -> None:
        DEBUG and print(f"new> Row[{f.tblName}], data:", row)
        self.__f = f
        self.__columnsRow = {}
        for i, col in enumerate(f.columns):
            if col.relation is None:
                self.__columnsRow[col] = row[i]
            elif i < len(row):  # one--<many relation
                self.__columnsRow[col] = row[i]
        DEBUG and print(f"<res Row[{f.tblName}]:", self.__columnsRow)

    def __eq__(self, o: object) -> bool:
        return repr(self) == repr(o)

    def __hash__(self) -> int:
        return hash(self.__columnsRow.values())

    def __str__(self) -> str:
        return self.__f.row_to_str(self.__columnsRow) if self.__f is not None else self.__str__()

    def __repr__(self) -> str:
        return f'db.Row[{repr(self.__columnsRow)}]'

    def get(self, col: Col) -> any:
        if col.ctype == ColType.DATE:
            return date.fromtimestamp(self.__columnsRow[col])
        return self.__columnsRow[col]

    def get_row(self, col: Col, f: type[FancyTable]):
        return self.get_row_static(col, self.__columnsRow, self.__f, f)

    @staticmethod
    def get_row_static(src_col: Col, data: {Col: any}, src_f: type[FancyTable], dst_f: type[FancyTable]):
        if src_col.relation is None:
            raise Exception('Column', src_col, 'in table', src_f.tblName, 'is regular field!')
        if src_col in data:                     # one--<many relation, use external_id
            external_id = data[src_col]
        else:                               # many>--<many relation
            external_id = data[dst_f.id]
        raw_data = src_col.relation.query(dst_f.tblName, external_id)
        if type(raw_data) == list:
            return [Row(x, dst_f) for x in raw_data]
        return Row(raw_data, dst_f)


class Table(FancyTable):

    def on_clicked(self, col: int, row: list[any, ...]) -> bool:
        pass

    def query(self, sel='*', where='1=1') -> dict[int, Row]:
        return self.raw_query(f"SELECT {sel} FROM '{self.tblName}' WHERE {where}")

    def raw_query(self, query: str) -> dict[int, Row]:
        DEBUG and print("Query:", query)
        cur = con.cursor()
        res = {}
        rows = cur.execute(query).fetchall()
        cur.close()
        for row in rows:
            res[row[0]] = Row(row, self.__class__)
        return res

    def show_list(self):
        layout = [
            [sg.Text(self.dispName)],
        ]
        table = []
        for row in self.query().values():
            item = []
            # item = [row.get(col) for col in columns]
            for col in self.columns:
                item.append(row.get(col))
            table.append(item)
        layout.append([sg.Table(
            values=table,
            headings=[col.dispName for col in self.columns],
            justification='center',
            enable_click_events=True,
            max_col_width=100,
            key='tbl'
        )])
        layout.append([sg.Button('Close')])
        w = sg.Window('Список ' + self.dispName, layout, finalize=True, resizable=True, auto_size_text=True,
                      auto_size_buttons=True, )
        w['tbl'].expand(True, True)
        w['tbl'].table_frame.pack(expand=True, fill='both')
        while True:
            event, values = w.read()
            if event == sg.WIN_CLOSED or event == 'Close':
                w.close()
                break
            print("ev:", event, "t:", type(event), "val:", values)
            if event[0] == 'tbl' and event[1] == '+CLICKED+':
                (x, y) = event[2]
                if x is not None and 0 <= x < len(table):
                    if self.on_clicked(y, table[x]):
                        w.close()
                        break


def sql_exec(sql: str) -> Cursor:
    DEBUG and print('Execute sql:', sql)
    res = con.execute(sql)
    con.commit()
    res.close()
    Relation.clear_cache()
    return res
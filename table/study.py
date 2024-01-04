from config import edit_str_dialog
from db import Table, Col, ColType, sql_exec

import PySimpleGUI as sg


class Study(Table):
    tblName = 'study'
    dispName = 'Предмет'
    # Columns:
    id = Col('id', 'id', ColType.INT)
    name = Col('name', 'Название', ColType.STR)
    columns = (id, name)

    @staticmethod
    def row_to_str(row: dict[Col: any]) -> str:
        return row.get(Study.name)

    def on_clicked(self, col: int, row: list[any, ...]) -> bool:
        if col == 0:
            return False
        field = row[col]
        _id = row[0]
        return edit_str_dialog(field, self._upd_name, _id=_id)

    def _upd_name(self, new_name: str, _id: int):
        res = sql_exec(f'UPDATE `{self.tblName}` SET `{self.name.name}`="{new_name}" WHERE id={_id}')
        print(f"UPD new_name[{_id}]:", new_name, res)

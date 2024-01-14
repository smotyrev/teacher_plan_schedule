from db import Table, Col, ColType, sql_exec
from typing import Dict

import PySimpleGUI as sg


class Study(Table):
    tblName = 'study'
    dispName = 'Предмет'
    # Columns:
    id = Col('id', 'id', ColType.INT)
    name = Col('name', 'Название', ColType.STR)
    columns = (id, name)

    @staticmethod
    def row_to_str(row: Dict[Col, any]) -> str:
        return row.get(Study.name)

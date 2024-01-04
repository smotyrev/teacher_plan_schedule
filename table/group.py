from db import Table, Col, ColType


class Group(Table):
    tblName = 'group'
    dispName = 'Группа'
    # Columns:
    id = Col('id', 'id', ColType.INT)
    name = Col('name', 'Название', ColType.STR)
    columns = (id, name)

    @staticmethod
    def row_to_str(row: dict[Col: any]) -> str:
        return row.get(Group.name)





from db import Table, Col, ColType, Relation, Row
from table.study import Study
from typing import Dict, Tuple


class Teacher(Table):
    tblName = 'teacher'
    dispName = 'Преподаватель'
    # Columns:
    id = Col('id', 'id', ColType.INT)
    name = Col('name', 'ФИО', ColType.STR)
    studies = Col('studies', 'Предметы', relation=Relation(Study.tblName, Study, join_tbl="teacher_study"))
    columns = (id, name)

    @staticmethod
    def row_to_str(row: Dict[Col, any]) -> str:
        return str(row.get(Teacher.name))

    def on_clicked(self, col: int, row: Tuple[any, ...]) -> bool:
        col = self.columns[col]
        print(col.dispName, ":", row)
        if col.relation is not None:
            col.relation


class TeacherStudy(Table):
    tblName = 'teacher_study'
    dispName = 'Преп./Предм.'
    canBeDeleted = True
    # Columns:
    id = Col('id', 'id', ColType.INT)
    teacher = Col('teacher_id', Teacher.dispName, relation=Relation(Teacher.tblName, Teacher))
    study = Col('study_id', Study.dispName, relation=Relation(Study.tblName, Study))
    columns = (id, teacher, study)

    @staticmethod
    def row_to_str(row: Dict[Col, any]) -> str:
        t = Row.get_row_static(TeacherStudy.teacher, row, Teacher)
        s = Row.get_row_static(TeacherStudy.study, row, Study)
        return f'{t} / {s}'



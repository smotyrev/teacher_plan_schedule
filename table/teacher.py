from db import Table, Col, ColType, Relation, Row
from table.study import Study


class Teacher(Table):
    tblName = 'teacher'
    dispName = 'Преподаватель'
    # Columns:
    id = Col('id', 'id', ColType.INT)
    name = Col('name', 'ФИО', ColType.STR)
    studies = Col('studies', 'Предметы', relation=Relation(Study.tblName, join_tbl="teacher_study"))
    columns = (id, name)

    @staticmethod
    def row_to_str(row: dict[Col: any]) -> str:
        return str(row.get(Teacher.name))

    def on_clicked(self, col: int, row: tuple[any, ...]) -> bool:
        col = self.columns[col]
        print(col.dispName, ":", row)
        if col.relation is not None:
            col.relation


class TeacherStudy(Table):
    tblName = 'teacher_study'
    dispName = 'TS'
    # Columns:
    id = Col('id', 'id', ColType.INT)
    teacher = Col('teacher_id', Teacher.dispName, relation=Relation(Teacher.tblName))
    study = Col('study_id', Study.dispName, relation=Relation(Study.tblName))
    columns = (id, teacher, study)

    @staticmethod
    def row_to_str(row: dict[Col: any]) -> str:
        t = Row.get_row_static(TeacherStudy.teacher, row, TeacherStudy, Teacher)
        s = Row.get_row_static(TeacherStudy.study, row, TeacherStudy, Study)
        return f'{t} / {s}'



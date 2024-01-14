from db import Table, Col, ColType, Relation, Row
from table.group import Group
from table.semester import Semester
from table.teacher import TeacherStudy
from typing import Dict


class Plan(Table):
    tblName = 'plan'
    dispName = 'План на семестр'
    canBeDeleted = True
    # Columns:
    id = Col('id', 'id', ctype=ColType.INT)
    hours = Col('hours', 'План часов', ctype=ColType.INT)
    semester = Col('semester_id', Semester.dispName, relation=Relation(Semester.tblName, Semester))
    teacher_study = Col('teacher_study_id', TeacherStudy.dispName, relation=Relation(TeacherStudy.tblName, TeacherStudy))
    group = Col('group_id', Group.dispName, relation=Relation(Group.tblName, Group))
    columns = (id, hours, semester, teacher_study, group)

    @staticmethod
    def row_to_str(row: Dict[Col, any]) -> str:
        ts = Row.get_row_static(Plan.teacher_study, row, TeacherStudy)
        return f'{row.get(Plan.hours)}ч. {ts}'





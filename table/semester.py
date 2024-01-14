import calendar

import config
from config import date
from db import Table, Col, ColType
from typing import Dict


class Semester(Table):
    tblName = 'semester'
    dispName = 'Семестр'
    # Columns:
    id = Col('id', 'id', ColType.INT)
    date_start = Col('date_start', 'Дат. начала', ColType.DATE)
    date_end = Col('date_end', 'Дат. конца', ColType.DATE)
    columns = (id, date_start, date_end)

    @staticmethod
    def row_to_str(row: Dict[Col, any]):
        d_start = date.fromtimestamp(row[Semester.date_start])
        d_end = date.fromtimestamp(row[Semester.date_end])
        date_format = "%B %d.%m.%Y"
        return d_start.strftime(date_format) + '  >  ' + d_end.strftime(date_format)







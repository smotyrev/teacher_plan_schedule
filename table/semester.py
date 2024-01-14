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
    columns = (id, date_start)

    @staticmethod
    def get_end_date(start_date: date) -> date:
        end_m = start_date.month + config.MONTHS_IN_SEMESTER - 1
        end_y = start_date.year
        if end_m > 12:
            end_m = end_m - 12
            end_y += 1
        _, n_of_days = calendar.monthrange(end_y, end_m)
        return date(end_y, end_m, n_of_days)

    @staticmethod
    def row_to_str(row: Dict[Col, any]):
        d_start = date.fromtimestamp(row[Semester.date_start])
        d_end = Semester.get_end_date(d_start)
        date_format = "%B %d.%m.%Y"
        return d_start.strftime(date_format) + '  >  ' + d_end.strftime(date_format)







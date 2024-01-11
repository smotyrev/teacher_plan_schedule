import tkinter
from datetime import datetime as system_datetime, date as system_date
from typing import Self

import PySimpleGUI as sg

DB_NAME = "data.db"             # имя файла, куда сохраняется база данных
DB_VERSION = 1
DB_CFG_KEY_VERSION = 1

DEBUG = False
VERBOSE = True
MONTHS_IN_SEMESTER = 4          # кол-во месяцев в семестре
NUMBER_OF_LESSONS = 6           # кол-во уроков (часов) в 1-ом учебном дне


# date / datetime override
class date(system_date):

    @classmethod
    def fromtimestamp(cls: type[Self], __timestamp: float) -> Self:
        d = super().fromtimestamp(__timestamp)
        return cls(d.year, d.month, d.day)

    def __str__(self):
        return self.strftime("%A %d.%m.%Y")

    def timestamp(self) -> int:
        return int(system_datetime(self.year, self.month, self.day).timestamp())

    @classmethod
    def now(cls: type[Self]):
        now = datetime.now()
        return cls(now.year, now.month, now.day)


class datetime(system_datetime):
    def __str__(self):
        return self.strftime("%A %d. %B %Y")


def get_display_size():
    root = tkinter.Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()
    return width, height


# dialog functions
def edit_str_dialog(prev_val: str, cb_action, *args, **kwargs) -> bool:
    event, values = sg.Window('Rename', [
        [sg.T('Переименовать'), sg.In(prev_val, key='-UPD-')],
        [sg.B('OK'), sg.B('Cancel')]
    ]).read(close=True)
    print(event, values)
    if event == 'OK':
        cb_action(values['-UPD-'], *args, **kwargs)
        return True
    return False

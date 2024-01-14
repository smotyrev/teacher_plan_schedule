# windows:
# https://www.python.org/downloads/release/python-3117/
# https://www.pysimplegui.org/en/latest/cookbook/#recipe-no-console-launching
import calendar

from PySimpleGUI import Window

import config
from config import date, DEBUG, VERBOSE

import PySimpleGUI as sg

from db import Row
from table.group import Group
from table.plan import Plan
from table.schedule import Schedule
from table.semester import Semester
from table.study import Study
from table.teacher import Teacher, TeacherStudy

# GUI tweaks
sg.theme('SystemDefault')
dw, dh = config.get_display_size()
if dw > 2560:
    scaling = 2
    font = ('Sans', 16)
    border_width = 2
    sg.set_options(scaling=scaling, font=font, border_width=border_width)
SHOW_SCHEDULE_GROUPS_IN_ONE_LINE = int(dw / 250)
print(SHOW_SCHEDULE_GROUPS_IN_ONE_LINE)

# Prepare semester data
now = date.now()
VERBOSE and print('First day timestamp of current month:', date(now.year, now.month, 1).timestamp())
semesters = list(Semester().query().values())
default_semester: "Row | None" = None
months = [i + 1 for i in range(0, 12)]
for s in semesters:
    d_start: date = s.get(Semester.date_start)
    d_end: date = s.get(Semester.date_end)
    VERBOSE and print('SEMESTER:', s.get(Semester.id), 'start:', d_start, 'end:', d_end, 'now:', now)
    if default_semester is None and d_start <= now <= d_end:
        default_semester = s
        break

layout = [
    [sg.B('Преподаватели', k='teacher'), sg.B('Предметы', k='study'), sg.B('Преп./Предм.', k='pp'),
     sg.B('Группы', k='group'), sg.B('Семестры', k='semester'), sg.B('Планы', k='plan')],
    [sg.HSep()],
    [sg.Column([[sg.T(f'Семестр')],
                [sg.Combo(semesters, default_value=default_semester, k='selSem', change_submits=True, readonly=True)]]),
     sg.Column(
         [[sg.T('день, месяц, год')],
          [
              sg.Combo([], k='selDate', size=(3, 1), change_submits=True, readonly=True),
              sg.Combo(months, default_value=now.month, k='selMonth', change_submits=True, readonly=True),
              sg.Combo([], size=(5, 1), k='selYear', change_submits=True, readonly=True),
          ]]
     ),

     sg.Column([[sg.T('')], [sg.B('Расписание', k='btnSchedule')]])],
    [sg.Button('Exit')]
]


def update_date_selectors(w: Window, semester: Row, def_d, new_y, new_m: int = 0):
    DEBUG and print('Update date selectors:', semester, f'(new_y: {new_y}, new_m: {new_m}, def_d: {def_d})')
    d_start: date = semester.get(Semester.date_start)
    d_end: date = semester.get(Semester.date_end)
    # years
    combo_y: sg.Combo = w['selYear']
    def_y = int(new_y) if new_y is not None and type(new_y) != str else d_start.year
    years: list[int] = []
    if d_start.year not in years:
        years.append(d_start.year)
    if d_end.year not in years:
        years.append(d_start.year)
    combo_y.update(def_y, years)
    # months
    combo_m: sg.Combo = w['selMonth']
    def_m = new_m if new_m is not None else d_start.month
    combo_m.update(def_m, months)
    # days
    combo_d: sg.Combo = w['selDate']
    first_day_of_month, n_of_days = calendar.monthrange(def_y, def_m)
    days = [i + 1 for i in range(0, n_of_days)]
    if def_d is None or type(def_d) == str:
        def_d = 1
    elif def_d > n_of_days:
        def_d = n_of_days
    combo_d.update(def_d, days)


# Create the Window
window = sg.Window('Расписание 1.0', layout, finalize=True)
if default_semester is not None:
    update_date_selectors(window, default_semester, now.day, now.year, now.month)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    DEBUG and print('MAIN event:', event, 'values:', values)
    if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
        break
    if event == 'teacher':
        Teacher().show_list()
    elif event == 'study':
        Study().show_list()
    elif event == 'pp':
        TeacherStudy().show_list()
    elif event == 'group':
        Group().show_list()
    elif event == 'semester':
        Semester().show_list()
    elif event == 'plan':
        Plan().show_list()
    elif event == 'selSem' or event == 'selMonth' or event == 'selYear':
            update_date_selectors(window, values['selSem'], values['selDate'], values['selYear'], values['selMonth'])
    elif event == 'btnSchedule':
            (d, m, y) = (values['selDate'], values['selMonth'], values['selYear'])
            _shd = Schedule()
            _close = False
            while not _close:
                _close = _shd.show_table(values['selSem'], date(int(y), int(m), int(d)),
                                         groups_in_one_line=SHOW_SCHEDULE_GROUPS_IN_ONE_LINE)
            continue

window.close()

import math
import os
import subprocess
import sys

import xlsxwriter
from PySimpleGUI import LISTBOX_SELECT_MODE_SINGLE, LISTBOX_SELECT_MODE_MULTIPLE, GREENS
from typing import List

from config import date, DEBUG, VERBOSE
from datetime import timedelta

import PySimpleGUI as sg

from db import Row
from table.group import Group
from table.plan import Plan
from table.schedule import Schedule
from table.study import Study
from table.teacher import TeacherStudy, Teacher


def _export_for_day(workbook, worksheet, dat: date, groups: List[Row], offset=0) -> int:
    print('_export_for_day, offset:', offset, 'date:', dat)
    schedule = Schedule()
    gr_ids = [str(gr.get(Group.id)) for gr in groups]
    schedule_items = schedule.query(where=f"{Schedule.group} IN ({','.join(gr_ids)}) "
                                          f"AND {Schedule.dateField} == {dat.timestamp()}")
    # header
    h_11 = workbook.add_format({'bold': True, 'top': 2, 'left': 2, 'bottom': 2, 'right': 1,
                                'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
    h_12 = workbook.add_format({'bold': True, 'top': 2, 'left': 1, 'bottom': 2, 'right': 2,
                                'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
    h_1_ = workbook.add_format({'bold': True, 'border': 2, 'align': 'center', 'valign': 'vcenter'})
    worksheet.set_row(1+offset, 30)
    worksheet.write(f'B{2+offset}', 'день недели', h_11)
    worksheet.write(f'C{2+offset}', '№\r\nпары', h_12)

    next_col = 'D'

    rows: dict[str, list[Row]] = {}
    max_lesson = 0
    for gr in groups:
        print('gr:', gr)
        char = next_col
        worksheet.set_column(f'{char}:{char}', 20)
        next_col = chr(ord(next_col) + 1)
        worksheet.write(f'{char}{2+offset}', gr.get(Group.name), h_1_)
        rows[char] = []
        for item in schedule_items.values():
            if item.get(Schedule.group) == gr.get(Group.id):
                print('\titem:', item)
                lesson: int = item.get(Schedule.lesson)
                if max_lesson < lesson:
                    max_lesson = lesson
                rows[char].append(item)
    max_pair = math.ceil(max_lesson / 2)
    print("max_pair", max_pair)
    merge_f = workbook.add_format({'border': 2, 'right': 1, 'align': 'center', 'valign': 'vcenter', 'rotation': 90})
    worksheet.merge_range(f'B{3+offset}:B{2 + max_pair + offset}', str(dat), merge_f)
    pair_ff = {'border': 1, 'right': 2, 'align': 'center', 'valign': 'vcenter'}
    pair_f = workbook.add_format(pair_ff)
    for i in range(1, max_pair + 1):
        worksheet.set_row(1 + i + offset, 30)
        if i == max_pair:
            pair_f = workbook.add_format(pair_ff)
            pair_f.bottom = 2
        worksheet.write(f'C{2+i+offset}', str(i), pair_f)
    cell_ff = {'border': 1, 'left': 2, 'right': 2, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
    cell_f = workbook.add_format(cell_ff)
    cell_f_end = workbook.add_format(cell_ff)
    cell_f_end.set_bottom(2)
    for char in rows:
        items = rows[char]
        filled_pairs = []
        for item in items:
            lesson: int = item.get(Schedule.lesson)
            if lesson % 2 == 1:
                pair = math.ceil(lesson / 2)
                plan: Row = item.get_row(Schedule.plan, Plan)
                ts: Row = plan.get_row(Plan.teacher_study, TeacherStudy)
                study = ts.get_row(TeacherStudy.study, Study)
                teacher = ts.get_row(TeacherStudy.teacher, Teacher)
                worksheet.write(f'{char}{2 + pair + offset}', f'{study}\n{teacher}',
                                cell_f_end if pair == max_pair else cell_f)
                print("lesson", item, lesson, pair)
                filled_pairs.append(pair)
        for i in range(1, max_pair + 1):
            if i in filled_pairs:
                continue
            worksheet.write(f'{char}{2 + i + offset}', '', cell_f_end if i == max_pair else cell_f)
    max_pair = max_pair if max_pair > 0 else 1
    return max_pair + offset + 1


def export_groups_for_5days(start_dat: date, groups: List[Row]):
    file = 'export.xlsx'
    workbook = xlsxwriter.Workbook(file)
    worksheet = workbook.add_worksheet()
    worksheet.set_column('A:A', 20)
    worksheet.set_row(0, 40)
    #
    offset = 0
    for i in range(0, 5):
        dat = start_dat + timedelta(days=i)
        offset = _export_for_day(workbook, worksheet, dat, groups, offset)
    #
    workbook.close()
    if sys.platform.startswith('win'):
        os.startfile(file)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, file])



def show_window(dat: date):
    groups = Group().query()
    layout = [
        [sg.T('Выгрузка на'), sg.T(dat, background_color=GREENS[1]),  sg.T(', выберете группы:')],
        [sg.Listbox(list(groups.values()), select_mode=LISTBOX_SELECT_MODE_MULTIPLE, size=(18, len(groups)),
                    k='-list-', bind_return_key=True),
         sg.B('Export', k='-export-')]
    ]
    w = sg.Window('Expor Excel', layout, finalize=True)
    while True:
        event, values = w.read()
        VERBOSE and print('Excel event:', event, 'values:', values)
        if event == sg.WIN_CLOSED:
            break
        if event == '-export-':
            exp_groups = values['-list-']
            export_groups_for_5days(dat, exp_groups)

import PySimpleGUI as sg
from PySimpleGUI import GREENS, YELLOWS, TANS

from config import date, NUMBER_OF_LESSONS, DEBUG, VERBOSE
from db import Table, Row, sql_exec, Col, ColType, Relation
from table.group import Group
from table.plan import Plan
from table.semester import Semester
from table.teacher import Teacher, TeacherStudy


class PlanScheduleItem:
    def __init__(self, ts: Row, hours: int, pl_id: int) -> None:
        self.ts = ts
        self.hours = hours
        self.pl_id = pl_id

    def __str__(self) -> str:
        return f"{self.hours}ч. {self.ts}"


class Schedule(Table):
    tblName = 'schedule'
    dispName = 'Расписание'
    # Columns:
    id = Col('id', 'id', ColType.INT)
    dateField = Col('date', 'Дата', ColType.DATE)
    lesson = Col('lesson', 'Номер урока', ColType.INT)
    plan = Col('plan_id', Plan.dispName, relation=Relation(Plan.tblName))
    group = Col('group_id', Group.dispName, relation=Relation(Group.tblName))
    teacher = Col('teacher_id', Teacher.dispName, relation=Relation(Teacher.tblName))
    columns = (id, dateField, lesson, plan)

    def show_table(self, row_semester: Row, dat: date):
        print(dat, repr(row_semester))

        # [gr_id](Group)
        groups: dict[int, Row] = {}

        # { (lesson, gr_id): (schedule_id, pl_id, t_id) }
        reserved_lesson_group: dict[tuple[int, int], tuple[int, int, int]] = {}

        semester_id = row_semester.get(Semester.id)
        columns = [sg.Column(
            [[sg.T('зан.\\гр.')]] +
            [[sg.T(f'{i}-е')] for i in range(1, NUMBER_OF_LESSONS + 1)]
            , element_justification='c')]

        # Prepare WHOLE semester plans:
        plans: dict[int, Row] = {}  # [pl_id](Plan)
        tss: dict[int, Row] = {}  # [ts_id](TeacherStudy)
        ts_plans: dict[int, dict[int, tuple]] = {}  # [gr_id][ts_id](pl_id, hours)
        for pl_id, row in Plan().query(where=f"semester_id={semester_id}").items():
            # pl_id = row.get(Plan.id)
            plans[pl_id] = row
            group = row.get_row(Plan.group, Group)
            gr_id = group.get(Group.id)
            groups[gr_id] = group
            ts_id = row.get(TeacherStudy.id)
            tss[ts_id] = row.get_row(Plan.teacher_study, TeacherStudy)
            if gr_id not in ts_plans:
                ts_plans[gr_id] = {}
            ts_plans[gr_id][ts_id] = (pl_id, row.get(Plan.hours))

        # Prepare CURREN selected date data:
        reserved_plans: dict[int, int] = {}                 # { pl_id, cnt_hours }
        reserved_lesson_teachers: dict[int, [int]] = {}     # { lesson: [t_id] }
        plan_ids = ','.join([str(x) for x in plans.keys()])
        for schedule_id, row in self.query(where=f"plan_id in ({plan_ids})").items():
            plan = row.get_row(self.plan, Plan)
            if plan.get(Plan.semester) != semester_id:
                continue
            lesson = row.get(self.lesson)
            _dat = row.get(self.dateField)
            ts = plan.get_row(Plan.teacher_study, TeacherStudy)
            pl_id: int = plan.get(Plan.id)
            if pl_id in reserved_plans:
                reserved_plans[pl_id] += 1
            else:
                reserved_plans[pl_id] = 1
            if _dat == dat:
                t_id: int = ts.get(TeacherStudy.teacher)
                gr_id = plan.get(Plan.group)
                reserved_lesson_group[(lesson, gr_id)] = (schedule_id, pl_id, t_id)
                if lesson not in reserved_lesson_teachers:
                    reserved_lesson_teachers[lesson] = []
                reserved_lesson_teachers[lesson].append(t_id)
            DEBUG and print("# schedule: plan:", pl_id, "dat:", _dat, "lesson:", lesson)

        # Format layout date:
        for gr_id, group in groups.items():
            _plan_shed_items = []
            for ts_id in ts_plans[gr_id]:
                pl_id, hours = ts_plans[gr_id][ts_id]
                if pl_id in reserved_plans:
                    hours -= reserved_plans[pl_id]
                if hours <= 0:
                    print(f'Plan {pl_id} hours are completed:', hours)
                ts = tss[ts_id]
                _plan_shed_items.append(PlanScheduleItem(ts, hours, pl_id))
            plan_selectors = []
            def_values = {str: PlanScheduleItem}
            for lesson in range(1, NUMBER_OF_LESSONS + 1):
                filtered = []
                key_def = f'ts-{lesson}-{gr_id}'
                for tsi in _plan_shed_items:
                    t_id = tsi.ts.get(TeacherStudy.teacher)
                    _r = reserved_lesson_group.get((lesson, gr_id))
                    _, pl_id, _t_id = _r if _r is not None else (None, None, None)
                    if _t_id == t_id:
                        if pl_id == tsi.pl_id:
                            VERBOSE and print(f'Lesson [{lesson}, {gr_id}]; plan: {pl_id}, teacher {t_id}, '
                                              f'selected: {tsi}')
                            def_values[key_def] = tsi
                    else:
                        rlt = reserved_lesson_teachers.get(lesson)
                        if rlt is not None and t_id in rlt:
                            VERBOSE and print(f'Lesson [{lesson}, {gr_id}]; exclude teacher {t_id}, '
                                              f'already reserved for another group')
                            continue
                    filtered.append(tsi)
                plan_selectors.append([
                    sg.Combo(filtered, default_value=def_values.get(key_def), k=key_def, size=(24, 1),
                             change_submits=True, readonly=True)
                ])
            columns.append(sg.Column([[sg.T(group)]] + plan_selectors))
        # SHOW TABLE LAYOUT
        layout = [
            [sg.T(f"{self.dispName} на"), sg.T(dat, background_color=GREENS[2]),
             sg.T('Семестр:'), sg.T(row_semester, background_color=YELLOWS[1])],
            columns,
        ]
        w = sg.Window(f'{self.dispName} на {dat}', layout, finalize=True, resizable=True, auto_size_text=True,
                      auto_size_buttons=True, )
        while True:
            event, values = w.read()
            if event == sg.WIN_CLOSED or event == 'Close':
                w.close()
                return True
            print("ev:", event, "t:", type(event), "val:", values)
            if event.startswith('ts-'):
                # Handle selector
                _, lesson, gr_id = event.split('-')
                gr_id = int(gr_id)
                lesson = int(lesson)
                psi: PlanScheduleItem = values[event]
                t_id = psi.ts.get(TeacherStudy.teacher)
                _r = reserved_lesson_group.get((lesson, gr_id))
                schedule_id, prev_pl_id, _ = _r if _r is not None else (None, None, None)
                DEBUG and print(f'SELECTED: ts: {repr(psi.ts)}', f'hours: {psi.hours}', f'pl_id: {psi.pl_id}',
                                f'lesson: {lesson}', f'gr_id: {gr_id}', f't_id: {t_id}')
                if self.confirm_schedule(dat, psi, lesson, groups[gr_id], schedule_id):
                    pass
                else:
                    el: sg.Combo = w[event]
                    print("!psi!", psi)
                    el.update(value='')
                w.close()
                return False

    def confirm_schedule(self, dat: date, psi: PlanScheduleItem, lesson: int, group: Row,
                         schedule_id: int | None) -> bool:
        event, values = sg.Window('Зарезервировать час в расписании', [
            [sg.T(f'Зарезервировать {lesson}-ый урок для'), sg.T(psi.ts, background_color=TANS[0])],
            [sg.T('Дата/Группа'), sg.T(dat, background_color=TANS[1]), sg.T(group, background_color=TANS[2])],
            [sg.B('Save', k='-SAVE-'), sg.B('Cancel', k='-CANCEL-')]
        ]).read(close=True)
        if event == '-SAVE-':
            gr_id = group.get(Group.id)
            t_id = psi.ts.get(TeacherStudy.teacher)
            if schedule_id is None:
                sql_exec(f'INSERT INTO {self.tblName} '
                         f'{(self.dateField, self.lesson, self.plan, self.group, self.teacher)} '
                         f'VALUES {(dat.timestamp(), lesson, psi.pl_id, gr_id, t_id)}')
            else:
                sql_exec(f'UPDATE {self.tblName} '
                         f'SET {self.group}={gr_id}, {self.plan}={psi.pl_id}, {self.teacher}={t_id} '
                         f'WHERE {self.id}={schedule_id}')
            return True
        return False

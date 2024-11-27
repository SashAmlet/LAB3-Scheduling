import csv

def load_csv(filename):
    with open(filename, newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

DAYS_PER_WEEK = 5
SLOTS_PER_DAY = 4
NUM_OF_WEEKS = 14

def print_schedule(schedule, group=None):
    """
    Друкує весь розклад для всіх днів і слотів.
    """
    # Сортування розкладу за днем і слотом
    sorted_schedule = {
        key: value
        for key, value in sorted(schedule.items(), key=lambda item: (item[1][2], item[1][3]))
        if group==None or group in key[0] 
    }

    
    # Перебір днів тижня
    for day in range(1, DAYS_PER_WEEK + 1):
        print(f"Day {day}")
        for time_slot in range(1, SLOTS_PER_DAY + 1):
            print(f"  Slot {time_slot}:")
            
            # Фільтруємо записи для поточного дня і слота
            slots= [
                (key, entry) for key, entry in sorted_schedule.items()
                if entry[2] == day and entry[3] == time_slot
            ]

            
            # Друкуємо записи
            if slots:
                for key, entry in slots:
                    print(f"    Group: {key[0]}, Subject: {key[1]} ({key[2]}), "
                          f"Lecturer: {entry[1]}, Room: {entry[0]}")
            else:
                print("    No classes")
        print()

# Жорсткі обмеження
def no_time_conflict(assignment, var, value):
    """
    Жодна група/аудиторія/лектор не можуть бути зайняті одночасно в одному слоті.
    """
    group, subject, type_ = var
    room, lecturer, day, time_slot = value

    for assigned_var, assigned_value in assignment.items():
        if assigned_value is None:
            continue

        _, _, assigned_type = assigned_var
        assigned_room, assigned_lecturer, assigned_day, assigned_time_slot = assigned_value

        # Перевірка збігу слота (день + пара)
        if (assigned_day, assigned_time_slot) == (day, time_slot):
            # Аудиторія
            if assigned_room == room:
                return False
            # Лектор
            if assigned_lecturer == lecturer:
                return False
            # Група
            if ('.' not in group or '.' not in assigned_var[0]) and assigned_var[0].split('.')[0] == group.split('.')[0] \
                or assigned_var[0] == group:
                return False

    return True


def check_constraints(assignment, var, value):
    """
    Перевіряє виконання всіх обмежень.
    """
    for constraint in constraints:
        if not constraint(assignment, var, value):
            return False
    return True

def count_conflicts(assignment, var, value):
    """
    Рахує кількість конфліктів, які створює значення для інших змінних.
    """
    conflicts = 0
    for other_var in variables:
        if other_var not in assignment:
            if not check_constraints({**assignment, var: value}, other_var, domains[other_var]):
                conflicts += 1
    return conflicts

def select_unassigned_variable(assignment):
    """
    Вибираємо змінну з найменшою кількістю можливих значень (MRV).
    """
    unassigned = [v for v in variables if v not in assignment]
    return min(unassigned, key=lambda var: len(domains[var]))

def has_gap_in_schedule(group, assignment):
    """
    Перевіряє, чи є вікно (перерва) в розкладі для заданої групи.
    """
    # Для кожного дня тижня перевіряємо, чи є перерва (вікно)
    group_schedule = {}  # Словник для зберігання розкладу групи

    for (variable, value) in assignment.items():
        if variable[0] == group:
            day, time_slot = value[2], value[3]
            if day not in group_schedule:
                group_schedule[day] = []
            group_schedule[day].append(time_slot)

    # Перевірка на перерви: чи є пропуск між заняттями
    for day, time_slots in group_schedule.items():
        time_slots.sort()
        for i in range(1, len(time_slots)):
            if time_slots[i] > time_slots[i - 1] + 1:  # Якщо є пропуск між слотами
                return True

    return False

def room_capacity_exceeded(group, room):
    """
    Перевіряє, чи перевищена місткість аудиторії для групи.
    """
    def get_group_size(group_name):
        for group in groups:
            if group['GroupName'] == group_name.split('.')[0]:
                if '.' in group_name:
                    return int(group['NumStudents']) // 2
                else:
                    return int(group['NumStudents'])
            
        return None  # Якщо група не знайдена
    
    def get_room_capacity(room_name):
        for room in rooms:
            if room['Room'] == room_name:
                return int(room['Capacity'])
            
        return None  # Якщо кімната не знайдена

    # Припускаємо, що для кожної групи є інформація про кількість студентів
    group_size = get_group_size(group)
    
    # Місткість аудиторії
    room_capacity = get_room_capacity(room)

    if group_size > room_capacity:
        return True
    return False


def cost(assignment):
    total_cost = 0
    # Нежорсткі обмеження
    for variable, value in assignment.items():
        group, subject, class_type = variable
        room, lecturer, day, time_slot = value
        
        # Додаємо вартість за "вікна" в розкладі
        if has_gap_in_schedule(group, assignment):
            total_cost += 5
        
        # Додаємо вартість за перевищення місткості аудиторії
        if room_capacity_exceeded(group, room):
            total_cost += 10

    return total_cost


def select_value(variable, values, assignment):    
    # Сортуємо значення за зростанням вартості
    sorted_values = sorted(values, key=lambda value: cost({**assignment, variable: value}))
    return sorted_values


def backtrack(assignment):
    if len(assignment) == len(variables):
        return assignment

    # Вибір змінної (MRV)
    var = select_unassigned_variable(assignment)

    # Проходимо по значеннях
    for value in select_value(var, domains[var], assignment):
        if check_constraints(assignment, var, value):
            assignment[var] = value
            result = backtrack(assignment)
            if result is not None:
                return result
            assignment.pop(var)

    return None




# Завантаження даних
subjects = load_csv("subjects.csv")
rooms = load_csv("rooms.csv")
lecturers = load_csv("lecturers.csv")
groups = load_csv("groups.csv")

variables = []
domains = {}
days = range(1, 6)  # Понеділок - П'ятниця
time_slots = range(1, 5)  # Чотири пари на день



# Попередньо створюємо карту доступних викладачів і аудиторій для кожного предмета та типу занять
lecturer_map = {
    (subject, class_type): [
        lecturer['Lecturer']
        for lecturer in lecturers
        if lecturer['Subject'] == subject and lecturer['ClassType'] == class_type
    ]
    for subject in set(subj['Subject'] for subj in subjects)
    for class_type in ['Lecture', 'Lab']
}

room_map = [room['Room'] for room in rooms]

# Додавання змінних і доменів
for subj in subjects:
    group = subj['GroupName']
    subject = subj['Subject']
    lecture_hours = int(subj['LectureHours'])
    lab_hours = int(subj['LabHours'])
    needs_division = subj['NeedsDivision'] == "Yes"

    # Лекції
    variables.append((group, subject, 'Lecture'))
    domains[(group, subject, 'Lecture')] = [
        (room, lecturer, day, time_slot)
        for room in room_map
        for lecturer in lecturer_map.get((subject, 'Lecture'), [])
        for day in days
        for time_slot in time_slots
    ]

    # Лабораторні
    if lab_hours > 0:
        if needs_division:
            # Створення змінних для підгруп
            for subgroup in [f"{group}.1", f"{group}.2"]:
                variables.append((subgroup, subject, 'Lab'))
                domains[(subgroup, subject, 'Lab')] = [
                    (room, lecturer, day, time_slot)
                    for room in room_map
                    for lecturer in lecturer_map.get((subject, 'Lab'), [])
                    for day in days
                    for time_slot in time_slots
                ]
        else:
            # Без поділу на підгрупи
            variables.append((group, subject, 'Lab'))
            domains[(group, subject, 'Lab')] = [
                (room, lecturer, day, time_slot)
                for room in room_map
                for lecturer in lecturer_map.get((subject, 'Lab'), [])
                for day in days
                for time_slot in time_slots
            ]



constraints = []

constraints.append(no_time_conflict)

# Початковий стан: пустий розклад
assignment = {}

# Запуск CSP
assignment = {}
solution = backtrack(assignment)

# Вивід розкладу
if solution:
    print("Schedule:")
    print_schedule(solution)
    print('//////////////////////////////////////////////////////////////////////////////')
    print_schedule(solution, 'G1')
    print('//////////////////////////////////////////////////////////////////////////////')
    print_schedule(solution, 'G2')
    print('//////////////////////////////////////////////////////////////////////////////')
    print_schedule(solution, 'G3')
    print('//////////////////////////////////////////////////////////////////////////////')
    print_schedule(solution, 'G4')
else:
    print("Error")

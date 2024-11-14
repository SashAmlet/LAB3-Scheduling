import csv
import random
from collections import defaultdict


# Кількість днів, пар на день та тижнів
DAYS_PER_WEEK = 5
SLOTS_PER_DAY = 4
NUM_OF_WEEKS = 14
TOTAL_SLOTS = DAYS_PER_WEEK * SLOTS_PER_DAY

# Функція для зчитування груп
def load_groups(file_path="groups.csv"):
    groups = {}
    with open(file_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            groups[row["GroupName"]] = {
                "NumStudents": int(row["NumStudents"])
            }
    return groups

# Функція для зчитування предметів
def load_subjects(file_path="subjects.csv"):
    subjects = defaultdict(list)
    with open(file_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            subjects[row["GroupName"]].append({
                "Subject": row["Subject"],
                "LectureHours": int(row["LectureHours"]),
                "LabHours": int(row["LabHours"]),
                "NeedsDivision": row["NeedsDivision"] == "Yes"
            })
    return subjects

# Функція для зчитування викладачів
def load_lecturers(file_path="lecturers.csv"):
    lecturers = defaultdict(lambda: defaultdict(list))
    with open(file_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            lecturers[row["Lecturer"]][row["Subject"]].append(row["ClassType"])
    return lecturers

# Функція для зчитування аудиторій
def load_rooms(file_path="rooms.csv"):
    rooms = []
    with open(file_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rooms.append({"Room": row["Room"], "Capacity": int(row["Capacity"])})
    return rooms

def print_schedule(schedule):
    for day in range(DAYS_PER_WEEK):
        print(f"Day {day + 1}")
        for time in range(SLOTS_PER_DAY):
            print(f"  Lecture {time + 1}:")
            for entry in schedule[time][day]:
                print(f"    Group: {entry['Group']}, Class: {entry['Subject']} ({entry['Type']}), "
                      f"Lecturer: {entry['Lecturer']}, Room: {entry['Room']}")
            print()

def get_schedule_for_entity(schedule, entity, entity_type):
    """
    Функція для отримання розкладу для заданого викладача, групи чи аудиторії, 
    включаючи підгрупи для групи, якщо entity_type="Group".
    
    Args:
        schedule (list): Розклад у вигляді списку списків за слотами.
        entity (str): Назва викладача, групи або аудиторії.
        entity_type (str): Тип сутності ("Lecturer", "Group", "Room").
        
    Returns:
        list: Відсортований список розкладу для сутності за днями і часом.
    """
    filtered_schedule = []

    # Якщо тип сутності — "Group", включаємо також підгрупи entity.1, entity.2 тощо
    if entity_type == "Group":
        group_entities = [entity, f"{entity}.1", f"{entity}.2"]
    else:
        group_entities = [entity]

    for day in range(DAYS_PER_WEEK):
        for time in range(SLOTS_PER_DAY):
            for entry in schedule[time][day]:
                # Перевіряємо, чи група або інша сутність відповідає entity або одній із підгруп
                if entry[entity_type] in group_entities:
                    filtered_schedule.append({
                        "Day": day + 1,
                        "Time": time + 1,
                        "Group": entry["Group"],
                        "Subject": entry["Subject"],
                        "Type": entry["Type"],
                        "Lecturer": entry["Lecturer"],
                        "Room": entry["Room"]
                    })

    # Сортуємо розклад за днем і часом
    return sorted(filtered_schedule, key=lambda x: (x["Day"], x["Time"]))


def print_entity_schedule(schedule, entity, entity_type):
    """
    Друкує розклад для конкретного викладача, групи або аудиторії.
    """
    filtered_schedule = get_schedule_for_entity(schedule, entity, entity_type)
    print(f"Schedule for {entity_type} '{entity}':")
    
    current_day = None
    for entry in filtered_schedule:
        if entry["Day"] != current_day:
            current_day = entry["Day"]
            print(f"\nDay {current_day}")
        
        print(f"  Slot {entry['Time']}: Group {entry['Group']}, Subject: {entry['Subject']} ({entry['Type']}), "
              f"Lecturer: {entry['Lecturer']}, Room: {entry['Room']}")
    print()

def initialize_schedule(groups, subjects, lecturers, rooms):
    schedule = [[[] for _ in range(DAYS_PER_WEEK)] for _ in range(SLOTS_PER_DAY)]
    tasks = []
    remaining_hours = {}
    #full_groups = groups.copy()
    

    for group, subject_list in subjects.items():
        for subject in subject_list:
            # Розрахунок занять на тиждень
            lecture_hours_weekly = subject["LectureHours"] / (1.5 * NUM_OF_WEEKS)
            lab_hours_weekly = subject["LabHours"] / (1.5 * NUM_OF_WEEKS)

            lecture_hours = round(lecture_hours_weekly)
            lab_hours = round(lab_hours_weekly)
            remaining_lecture_hours = subject["LectureHours"] - lecture_hours * NUM_OF_WEEKS * 1.5
            remaining_lab_hours = subject["LabHours"] - lab_hours * NUM_OF_WEEKS * 1.5
            remaining_hours[(group, subject["Subject"], "Lecture")] = remaining_lecture_hours
            remaining_hours[(group, subject["Subject"], "Lab")] = remaining_lab_hours

            # Визначаємо, чи потрібно розділяти групу
            groups_to_add = [group]
            if subject["NeedsDivision"]:
                groups_to_add = [f"{group}.1", f"{group}.2"]

            for _ in range(lecture_hours):
                tasks.append((group, subject["Subject"], "Lecture", groups[group]["NumStudents"]))

            for i, sub_group in enumerate(groups_to_add):
                for _ in range(lab_hours):
                    num_of_stud = groups[sub_group.split(".")[0]]["NumStudents"]
                    if subject["NeedsDivision"]:
                        num_of_stud /= 2
                    num_of_stud = num_of_stud if num_of_stud.is_integer() else num_of_stud + (0.5 if i else -0.5)
                    tasks.append((sub_group, subject["Subject"], "Lab", num_of_stud))
                    groups.setdefault(sub_group, {'NumStudents': num_of_stud})

    random.shuffle(tasks)
    room_occupancy = [[[] for _ in range(DAYS_PER_WEEK)] for _ in range(SLOTS_PER_DAY)]
    lecturer_occupancy = [[set() for _ in range(DAYS_PER_WEEK)] for _ in range(SLOTS_PER_DAY)]
    group_occupancy = [[set() for _ in range(DAYS_PER_WEEK)] for _ in range(SLOTS_PER_DAY)]

    for slot in range(TOTAL_SLOTS):
        day = slot % DAYS_PER_WEEK
        time = slot // DAYS_PER_WEEK
        available_rooms = rooms.copy()
        available_lecturers = set(lecturers.keys())

        # Використовуємо новий список для незавершених task-ів
        remaining_tasks = []
        
        while tasks and available_rooms and available_lecturers:
            group, subject, class_type, num_of_stud = tasks.pop()
            room = available_rooms.pop(random.randrange(len(available_rooms)))
            lecturer = random.choice(list(available_lecturers))

            # Перевірка обмежень
            if (
                subject in lecturers[lecturer] and 
                class_type in lecturers[lecturer][subject] and

                # Обмеження 1: Лектор не може викладати в різних аудиторіях одночасно
                lecturer not in lecturer_occupancy[time][day] and
                # Обмеження 2: Група не може мати більше одного заняття в один час
                group.split('.')[0] not in group_occupancy[time][day] and
                # Обмеження 3: Аудиторія може використовуватися одночасно лише для одного заняття (крім лекцій для кількох груп)
                not (any(entry["Room"] == room for entry in room_occupancy[time][day]) and (
                    class_type == "Lab" or room_occupancy[time][day]["Type"] == "Lab"))
            ):

                # Додаємо заняття до розкладу
                schedule[time][day].append({
                    "Group": group,
                    "NumOfStudents": num_of_stud,
                    "Subject": subject,
                    "Type": class_type,
                    "Lecturer": lecturer,
                    "Room": room["Room"]
                })

                # Встановлюємо заняття в аудиторії, якщо це лаборантське заняття або лекція з однією групою
                if class_type == "Lab" or room_occupancy[time][day] is None:
                    room_occupancy[time][day].append({"Room": room, "Type": class_type})

                # Зайнятість лектора та групи
                lecturer_occupancy[time][day] = lecturer
                group_occupancy[time][day].add(group.split('.')[0])
                
                available_lecturers.remove(lecturer)
            else:
                # Якщо додати не можна, зберігаємо task у новому списку
                remaining_tasks.append((group, subject, class_type, num_of_stud))
            
        # Повертаємо незавершені task-и назад у tasks для подальшої обробки
        tasks.extend(remaining_tasks)

    #group = full_groups.copy()
    #print_schedule(schedule)
    return schedule, remaining_hours



def fitness_function(schedule, remaining_hours):
    penalty = 0
    # М'які обмеження
    
    # 4. Мінімізація "вікон" для груп
    # Формуємо розклад занять кожної групи
    group_slots = {}
    for day in range(DAYS_PER_WEEK):
        for slot in range(SLOTS_PER_DAY):
            for entry in schedule[slot][day]:
                group = entry['Group'].split('.')[0]
                group_slots.setdefault(group, []).append((day, slot))

    for group, slots in group_slots.items():
        slots.sort()
        for i in range(1, len(slots)):
            prev_day, prev_slot = slots[i - 1]
            curr_day, curr_slot = slots[i]
            if curr_day == prev_day and curr_slot != prev_slot + 1:
                penalty += 10  # Штраф за "вікно" в розкладі групи

    # 5. Перевірка відповідності аудиторії розміру групи
    for day in range(DAYS_PER_WEEK):
        for slot in range(SLOTS_PER_DAY):
            for entry in schedule[slot][day]:
                room_name = entry['Room']
                room = next((r for r in rooms if r['Room'] == room_name), None)
                room_capacity = room['Capacity']
                group_size = entry['NumOfStudents']
                if group_size > room_capacity:
                    penalty += 5  # Штраф за невідповідність розміру аудиторії

    # 6. Перевірка залишкових годин
    for (group, subject, class_type), remaining in remaining_hours.items():
        if abs(remaining) > 0:
            penalty += abs(remaining)  # Штраф за незаповнені години

    return penalty


def select_parent(population, fitness_scores):
    """
    Виконує вибір батьків за методом рулетки з урахуванням залишкових годин для кожного індивіда.
    
    Parameters:
    - population: список індивідів поточної популяції (розкладів).
    - fitness_scores: список значень фітнесу для кожного індивіда.
    
    Returns:
    - обраний індивід (розклад) для використання як батьківський.
    """
    # Перетворюємо фітнес-значення в обернені, щоб кращі значення мали вищі ймовірності
    inverse_fitness = [1 / (score + 1) for score in fitness_scores]  # Додаємо 1, щоб уникнути ділення на нуль
    total_inverse_fitness = sum(inverse_fitness)
    
    # Обчислення ймовірностей для кожного індивіда
    probabilities = [score / total_inverse_fitness for score in inverse_fitness]
    
    # Виконання вибору за методом рулетки
    chosen_index = random.choices(range(len(population)), weights=probabilities, k=1)[0]
    
    return population[chosen_index]


def crossover(parent1, parent2):
    """
    Виконує двоточкове схрещування між двома батьками на рівні окремих слотів.
    
    Parameters:
    - parent1: перший батьківський індивід (розклад).
    - parent2: другий батьківський індивід (розклад).
    
    Returns:
    - child1, child2: два нащадки, створені в результаті схрещування.
    """
    # Ініціалізація дітей як копій батьків, щоб мати основу для замін
    child1 = [day.copy() for day in parent1]
    child2 = [day.copy() for day in parent2]

    # Вибір двох точок для схрещування
    point1_day, point1_slot = random.randint(0, DAYS_PER_WEEK - 1), random.randint(0, SLOTS_PER_DAY - 1)
    point2_day, point2_slot = random.randint(0, DAYS_PER_WEEK - 1), random.randint(0, SLOTS_PER_DAY - 1)

    # Гарантуємо, що point1 буде меншим за point2
    if (point1_day, point1_slot) > (point2_day, point2_slot):
        point1_day, point2_day = point2_day, point1_day
        point1_slot, point2_slot = point2_slot, point1_slot

    # Обмін парами між point1_day.point1_slot та point2_day.point2_slot для child1 і child2
    for day in range(point1_day, point2_day + 1):
        start_slot = point1_slot if day == point1_day else 0
        end_slot = point2_slot if day == point2_day else SLOTS_PER_DAY - 1
        for slot in range(start_slot, end_slot):
            child1[slot][day], child2[slot][day] = child2[slot][day], child1[slot][day]

    return child1, child2


def mutate(schedule, mutation_rate=0.1):
    """
    Виконує мутацію індивіда (розкладу) із заданою ймовірністю.
    
    Parameters:
    - schedule: індивід (розклад), який буде мутувати.
    - mutation_rate: ймовірність мутації для кожного слоту розкладу.
    
    Returns:
    - mutated_schedule: розклад після внесення мутацій.
    """
    # Копіюємо розклад, щоб уникнути змін в оригінальному індивіді
    mutated_schedule = schedule.copy()
    
    # Для кожного слоту розкладу розглядаємо можливість мутації
    for slot in range(len(mutated_schedule)):
        for day in range(len(mutated_schedule[slot])):
            # Генеруємо випадкове число, щоб перевірити, чи відбудеться мутація
            if random.random() < mutation_rate:
                # Отримуємо випадковий вибір для зміни параметра заняття
                current_entry = mutated_schedule[slot][day]
                # Вибираємо тип зміни: змінити предмет, викладача, аудиторію або час
                options = ["subject", "lecturer", "room", "time", "add", "delete"]
                weights = [0.1225, 0.1225, 0.1225, 0.1225, 0.5, 0.001]
                mutation_choice = random.choices(options, weights=weights, k=1)[0]

                if current_entry == [] and mutation_choice == "add":
                    # Знаходимо випадковий вільний слот у будь-якої групи
                    random_group = random.choice(list(groups.keys()))
                    available_subjects = subjects.get(random_group.split('.')[0], [])
                    
                    # Вибираємо випадковий предмет і перевіряємо доступність викладача
                    if available_subjects:
                        # Вибираємо предмет
                        subject_entry = random.choice(available_subjects)
                        # Вибираємо лектора для відповідного предмета
                        possible_lecturers = [lect for lect, details in lecturers.items() 
                                            if subject_entry["Subject"] in details.keys()]
                        random_lecturer = random.choice(possible_lecturers)
                        # Чи відповідає вибраний лектор жорстким умовам?
                        busy_lecturers = [entry["Lecturer"] for entry in current_entry]

                        # Вибираємо кімнату
                        possible_rooms = [room['Room'] for room in rooms if room['Capacity'] >= groups[random_group]["NumStudents"]]
                        random_room = random.choice(possible_rooms)
                        # Чи відповідає вибрана аудиторія жорстким умовам?
                        busy_rooms = [entry["Room"] for entry in current_entry]
                        
                        if random_lecturer not in busy_lecturers and random_room not in busy_rooms:
                            # Додаємо новий запис до розкладу
                            new_entry = {
                                "Group": random_group,
                                "NumOfStudents": groups[random_group]["NumStudents"],
                                "Subject": subject_entry["Subject"],
                                "Type": "Lab" if '.' in random_group else "Lecture",
                                "Lecturer": random_lecturer,
                                "Room": random_room
                            }
                            current_entry.append(new_entry)
                    continue
                elif current_entry == []:
                    continue
            
                
                random_index = random.randint(0, len(current_entry)-1)
                
                if mutation_choice == "subject":
                    # Змінити предмет на інший випадковий із переліку доступних предметів
                    
                    lecturer = current_entry[random_index]["Lecturer"]
                    # Вибираємо довільний предмет, який веде цей викладач
                    possible_subjects = list(lecturers.get(lecturer, {}).keys())

                    random_subject = random.choice(list(possible_subjects))
                    current_entry[random_index]["Subject"] = random_subject
                
                elif mutation_choice == "lecturer":
                    # Змінити викладача на іншого, який може викладати цей предмет
                    possible_lecturers = [lect for lect, details in lecturers.items() 
                                          if current_entry[random_index]["Subject"] in details.keys()]
                    random_lecturer = random.choice(possible_lecturers)
                    # Чи відповідає вибраний лектор жорстким умовам?
                    busy_lecturers = [entry["Lecturer"] for entry in current_entry]
                    if random_lecturer not in busy_lecturers:
                        current_entry[random_index]["Lecturer"] = random_lecturer
                
                elif mutation_choice == "room":
                    # Змінити аудиторію на іншу, яка може вмістити групу
                    group_size = current_entry[random_index]["NumOfStudents"]
                    possible_rooms = [room['Room'] for room in rooms if room['Capacity'] >= group_size]
                    random_room = random.choice(possible_rooms)
                    # Чи відповідає вибрана аудиторія жорстким умовам?
                    busy_rooms = [entry["Room"] for entry in current_entry]
                    if random_room not in busy_rooms:
                        current_entry[random_index]["Room"] = random_room
                
                elif mutation_choice == "time":
                    # Перемістити заняття на інший слот у той або інший день
                    new_slot = random.randint(0, len(mutated_schedule) - 1)
                    new_day = random.randint(0, len(mutated_schedule[new_slot]) - 1)
                    
                    # Переміщаємо заняття до нового слоту
                    mutated_schedule[slot][day], mutated_schedule[new_slot][new_day] = \
                    mutated_schedule[new_slot][new_day], mutated_schedule[slot][day]
                    
                elif mutation_choice == "delete":
                    # Видалити випадковий предмет з розкладу
                    del current_entry[random.randint(0, len(current_entry) - 1)]
                    
    
    return mutated_schedule

def calculate_remaining_hours(schedule):
    """ Обчислює надмірні години для кожного предмета на основі розкладу."""
    
    remaining_hours = {}
    
    for group, subject_list in subjects.items():
        for subject_info in subject_list:
            subject = subject_info['Subject']
            lecture_hours = subject_info['LectureHours']
            lab_hours = subject_info['LabHours']
            
            # Ініціалізація для лекційного заняття
            remaining_hours[(group, subject, 'Lecture')] = lecture_hours
            
            # Ініціалізація для лабораторного заняття
            remaining_hours[(group, subject, 'Lab')] = lab_hours


    for day in schedule:
        for slot in day:
            for entry in slot:
                
                # Зменшуємо повні години, на години, прописані розкладом
                if "." in entry['Group']:
                    # Витягуємо інформацію про пару: група, предмет та тип заняття
                    task_key = (entry['Group'].split('.')[0], entry['Subject'], entry['Type'])
                    remaining_hours[task_key] -= 0.75 * NUM_OF_WEEKS
                else:
                    # Витягуємо інформацію про пару: група, предмет та тип заняття
                    task_key = (entry['Group'], entry['Subject'], entry['Type'])
                    remaining_hours[task_key] -= 1.5 * NUM_OF_WEEKS


    return remaining_hours

def print_separate_gr_schedules(schedule):
    for G  in groups.keys():
        print("---------------------------------------")
        print_entity_schedule(schedule, G, "Group")
        print("---------------------------------------")

    

def genetic_algorithm_schedule(population_size, generations):
    # Ініціалізуємо популяцію, де кожен індивід містить розклад та залишкові години
    population = [initialize_schedule(groups, subjects, lecturers, rooms) for _ in range(population_size)]

    #groups = full_groups
    #print_separate_gr_schedules(population[0][0])
    
    
    
    for generation in range(generations):
        # Оцінка фітнесу для кожного індивіда
        fitness_scores = []
        for schedule, remaining_hours in population:
            fitness_score = fitness_function(schedule, remaining_hours)  # Оцінка фітнесу
            fitness_scores.append(((schedule, remaining_hours), fitness_score))
        
        # Сортуємо за фітнесом, найкращі мають мінімальні значення (менші штрафи)
        fitness_scores.sort(key=lambda x: x[1])
        fitness_scores = fitness_scores[:population_size]
        
        # Оновлюємо популяцію, залишаючи тільки розклади
        population = [x[0] for x in fitness_scores]
        
        # Перевірка умови зупинки
        if fitness_scores[0][1] == 0:  # Якщо фітнес без штрафів (ідеальне рішення)
            print(f"Solution found at generation {generation}")
            best_schedule, _ = fitness_scores[0][0]
            print_schedule(best_schedule)
            return best_schedule
        
        # Відбір батьків і формування нового покоління
        new_population = []
        elite_count = int(0.1 * population_size)  # Елітарність: 10%
        new_population.extend(population[:elite_count])
        
        while len(new_population) < population_size:
            parent1 = select_parent([schedule for schedule, _ in population], [score for _, score in fitness_scores])
            parent2 = select_parent([schedule for schedule, _ in population], [score for _, score in fitness_scores])
            
            # Створюємо нащадків, передаючи і schedule, і remaining_hours
            child1, child2 = crossover(parent1, parent2)
            
            # Мутація, яка змінює і schedule, і remaining_hours
            child1 = mutate(child1)
            child2 = mutate(child2)

            # Перераховуємо remaining_hours для кожного нащадка після мутації
            child1_remaining_hours = calculate_remaining_hours(child1)
            child2_remaining_hours = calculate_remaining_hours(child2)
            
            # Додаємо нових нащадків до нової популяції
            new_population.extend([(child1, child1_remaining_hours), 
                                (child2, child2_remaining_hours)])
        
        # Оновлюємо популяцію, обрізаємо зайві елементи
        population.extend(new_population)
    
    # Повертаємо найкращий розклад після завершення всіх поколінь
    best_schedule, _ = population[0]  # Беремо розклад з найменшим фітнесом
    #print_separate_gr_schedules(best_schedule)
    #print(fitness_scores[0][0][1])
    return best_schedule




groups = load_groups()
#full_groups = groups.copy()
subjects = load_subjects()
lecturers = load_lecturers()
rooms = load_rooms()

schedule = genetic_algorithm_schedule(100, 200)
print_separate_gr_schedules(schedule)
print_schedule(schedule)
# print_entity_schedule(schedule, "Lecturer_2", "Lecturer")
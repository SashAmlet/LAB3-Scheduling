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
    Функція для отримання розкладу для заданого викладача, групи чи аудиторії.
    
    Args:
        schedule (list): Розклад у вигляді списку списків за слотами.
        entity (str): Назва викладача, групи або аудиторії.
        entity_type (str): Тип сутності ("Lecturer", "Group", "Room").
        
    Returns:
        list: Відсортований список розкладу для сутності за днями і часом.
    """
    filtered_schedule = []

    for day in range(DAYS_PER_WEEK):
        for time in range(SLOTS_PER_DAY):
            for entry in schedule[time][day]:
                if entry[entity_type] == entity:
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
                group not in group_occupancy[time][day] and
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
                group_occupancy[time][day].add(group)
                
                available_lecturers.remove(lecturer)
            else:
                # Якщо додати не можна, зберігаємо task у новому списку
                remaining_tasks.append((group, subject, class_type, num_of_stud))
            
        # Повертаємо незавершені task-и назад у tasks для подальшої обробки
        tasks.extend(remaining_tasks)

    #print_schedule(schedule)
    return schedule, remaining_hours



def fitness_function(schedule, remaining_hours):
    penalty = 0

    # Жорсткі обмеження
    
    # 1. Перевірка на конфлікти по викладачах
    lecturer_slots = {}
    for day in range(DAYS_PER_WEEK):
        for slot in range(SLOTS_PER_DAY):
            for entry in schedule[slot][day]:
                lecturer = entry['Lecturer']
                if (day, slot) in lecturer_slots.get(lecturer, []):
                    penalty += 100  # Штраф за конфлікт у викладача
                else:
                    lecturer_slots.setdefault(lecturer, []).append((day, slot))

    # 2. Перевірка на конфлікти по групах
    group_slots = {}
    for day in range(DAYS_PER_WEEK):
        for slot in range(SLOTS_PER_DAY):
            for entry in schedule[slot][day]:
                group = entry['Group']
                if (day, slot) in group_slots.get(group, []):
                    penalty += 100  # Штраф за конфлікт у групи
                else:
                    group_slots.setdefault(group, []).append((day, slot))

    # 3. Перевірка на конфлікти по аудиторіях
    room_slots = {}
    for day in range(DAYS_PER_WEEK):
        for slot in range(SLOTS_PER_DAY):
            for entry in schedule[slot][day]:
                room = entry['Room']
                if (day, slot) in room_slots.get(room, []):
                    penalty += 100  # Штраф за конфлікт в аудиторії
                else:
                    room_slots.setdefault(room, []).append((day, slot))

    # М'які обмеження
    
    # 4. Мінімізація "вікон" для груп
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
            penalty += abs(remaining) * 2  # Штраф за незаповнені години

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
    Виконує двоточкове схрещування між двома батьками.
    
    Parameters:
    - parent1: перший батьківський індивід (розклад).
    - parent2: другий батьківський індивід (розклад).
    
    Returns:
    - child1, child2: два нащадки, створені в результаті схрещування.
    """
    # Кількість генів в одному індивіді (розкладі) - 20, по одному на кожен слот тижня
    num_slots = len(parent1)
    
    # Вибір двох точок для схрещування
    point1, point2 = sorted(random.sample(range(num_slots), 2))
    
    # Створення дітей шляхом комбінування частин батьків
    child1 = parent1[:point1] + parent2[point1:point2] + parent1[point2:]
    child2 = parent2[:point1] + parent1[point1:point2] + parent2[point2:]
    
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
    for day in range(len(mutated_schedule)):
        for slot in range(len(mutated_schedule[day])):
            # Генеруємо випадкове число, щоб перевірити, чи відбудеться мутація
            if random.random() < mutation_rate:
                # Отримуємо випадковий вибір для зміни параметра заняття
                current_entry = mutated_schedule[day][slot]
                if current_entry == []:
                    continue
                
                # Вибираємо тип зміни: змінити предмет, викладача, аудиторію або час
                mutation_choice = "time" #random.choice(["subject", "lecturer", "room", "time"])
                random_index = random.randint(0, len(current_entry)-1)
                
                if mutation_choice == "subject":
                    # Змінити предмет на інший випадковий із переліку доступних предметів
                    # Збираємо всі предмети зі структури `subjects`
                    all_subjects = set()
                    for group_subjects in subjects.values():
                        for entry in group_subjects:
                            all_subjects.add(entry["Subject"])

                    current_entry[random_index]["Subject"] = random.choice(list(all_subjects))
                
                elif mutation_choice == "lecturer":
                    # Змінити викладача на іншого, який може викладати цей предмет
                    possible_lecturers = [lect for lect, details in lecturers.items() 
                                          if current_entry[random_index]["Subject"] in details.keys()]
                    current_entry[random_index]["Lecturer"] = random.choice(possible_lecturers)
                
                elif mutation_choice == "room":
                    # Змінити аудиторію на іншу, яка може вмістити групу
                    group_size = current_entry[random_index]["NumOfStudents"]
                    possible_rooms = [room['Room'] for room in rooms if room['Capacity'] >= group_size]
                    current_entry[random_index]["Room"] = random.choice(possible_rooms)
                
                elif mutation_choice == "time":
                    # Перемістити заняття на інший слот у той же день або інший день
                    new_day = random.randint(0, len(mutated_schedule) - 1)
                    new_slot = random.randint(0, len(mutated_schedule[new_day]) - 1)
                    
                    # Переміщаємо заняття до нового слоту
                    mutated_schedule[day][slot], mutated_schedule[new_day][new_slot] = \
                    mutated_schedule[new_day][new_slot], mutated_schedule[day][slot]
    
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


def genetic_algorithm_schedule(population_size, generations):
    # Ініціалізуємо популяцію, де кожен індивід містить розклад та залишкові години
    population = [initialize_schedule(groups, subjects, lecturers, rooms) for _ in range(population_size)]
    
    for generation in range(generations):
        # Оцінка фітнесу для кожного індивіда
        fitness_scores = []
        for schedule, remaining_hours in population:
            fitness_score = fitness_function(schedule, remaining_hours)  # Оцінка фітнесу
            fitness_scores.append(((schedule, remaining_hours), fitness_score))
        
        # Сортуємо за фітнесом, найкращі мають мінімальні значення (менші штрафи)
        fitness_scores.sort(key=lambda x: x[1])
        
        # Оновлюємо популяцію, залишаючи тільки розклади
        population = [x[0] for x in fitness_scores[:population_size]]
        
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

            # Пересчитываем remaining_hours для каждого потомка после мутации
            child1_remaining_hours = calculate_remaining_hours(child1)
            child2_remaining_hours = calculate_remaining_hours(child2)
            
            # Додаємо нових нащадків до нової популяції
            new_population.extend([(child1, child1_remaining_hours), 
                                (child2, child2_remaining_hours)])
        
        # Оновлюємо популяцію, обрізаємо зайві елементи
        population.extend(new_population)
    
    # Повертаємо найкращий розклад після завершення всіх поколінь
    best_schedule, _ = population[0]  # Беремо розклад з найменшим фітнесом
    print_schedule(best_schedule)
    return best_schedule




groups = load_groups()
subjects = load_subjects()
lecturers = load_lecturers()
rooms = load_rooms()

print_schedule(genetic_algorithm_schedule(50, 100))
# print_entity_schedule(initialize_schedule(groups, subjects, lecturers, rooms), "G1", "Group")
import csv
import random

NUM_OF_GROUPS = 4
NUM_OF_CLASSES = 6
NUM_OF_LECTURERS = 8
NUM_OF_ROOMS = 20

# Генерація списку груп
with open("groups.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["GroupName", "NumStudents"])
    for i in range(NUM_OF_GROUPS):
        group_name = f"G{i+1}"
        num_students = random.randint(20, 50)
        writer.writerow([group_name, num_students])

# Генерація списку предметів
with open("subjects.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["GroupName", "Subject", "LectureHours", "LabHours", "NeedsDivision"])
    for i in range(NUM_OF_GROUPS):
        group_name = f"G{i+1}"
        for j in range(NUM_OF_CLASSES):
            subject = f"Subject_{j+1}"
            lecture_hours = random.randint(10, 20)
            lab_hours = random.randint(5, 15)
            needs_division = "Yes" if random.choice([True, False]) else "No"
            writer.writerow([group_name, subject, lecture_hours, lab_hours, needs_division])

# Генерація списку викладачів з вказівкою предметів та типів занять
with open("lecturers.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Lecturer", "Subject", "ClassType"])
    
    for i in range(NUM_OF_LECTURERS):
        lecturer = f"Lecturer_{i+1}"
        subjects = [f"Subject_{j+1}" for j in random.sample(range(5), k=3)]  # кожен викладач викладає 3 предмети
        
        for subject in subjects:
            # Випадковим чином обираємо, які типи занять може проводити викладач для цього предмету
            available_class_types = random.sample(["Lecture", "Lab"], k=random.randint(1, 2))
            for class_type in available_class_types:
                writer.writerow([lecturer, subject, class_type])

# Генерація списку аудиторій
with open("rooms.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Room", "Capacity"])
    for i in range(NUM_OF_ROOMS):
        room_name = f"Room_{i+1}"
        capacity = random.randint(20, 60)
        writer.writerow([room_name, capacity])

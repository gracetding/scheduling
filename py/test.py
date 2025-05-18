import pandas as pd
from ortools.sat.python import cp_model

# Load course requests spreadsheet
df = pd.read_excel("course_requests.xlsx")  # Assumes columns: Student, Course, Priority

# Configuration
NUM_PERIODS = 6
MAX_STUDENTS_PER_COURSE = 25

# Step 1: Extract unique students and courses
students = df['Student'].unique().tolist()
courses = df['Course'].unique().tolist()

# Step 2: Build student-course request map and priority map
student_course_map = {}
priority_map = {}
for _, row in df.iterrows():
    student = row['Student']
    course = row['Course']
    priority = row.get('Priority', 1)
    student_course_map.setdefault(student, []).append(course)
    priority_map[(student, course)] = priority

# Step 3: Initialize the model
model = cp_model.CpModel()

# Variables: (student, course, period) = 1 if assigned
student_course_period = {}
course_period = {}

for course in courses:
    for period in range(NUM_PERIODS):
        course_period[(course, period)] = model.NewBoolVar(f"course_{course}_p{period}")

for student in students:
    for course in student_course_map[student]:
        for period in range(NUM_PERIODS):
            student_course_period[(student, course, period)] = model.NewBoolVar(f"{student}_{course}_p{period}")

# Step 4: Constraints

# 1. Each course must be scheduled in exactly one period
for course in courses:
    model.Add(sum(course_period[(course, p)] for p in range(NUM_PERIODS)) == 1)

# 2. A student can take each requested course only once, and only in the period it's scheduled
for student in students:
    for course in student_course_map[student]:
        model.Add(sum(student_course_period[(student, course, p)] for p in range(NUM_PERIODS)) <= 1)
        for p in range(NUM_PERIODS):
            model.AddImplication(student_course_period[(student, course, p)], course_period[(course, p)])

# 3. No student can be in more than one class per period
for student in students:
    for p in range(NUM_PERIODS):
        model.Add(sum(
            student_course_period[(student, course, p)]
            for course in student_course_map[student]
        ) <= 1)

# 4. Enforce max students per course per period
for course in courses:
    for p in range(NUM_PERIODS):
        enrolled = [student_course_period[(s, course, p)]
                    for s in students if course in student_course_map[s]]
        if enrolled:
            model.Add(sum(enrolled) <= MAX_STUDENTS_PER_COURSE)

# Step 5: Objective — weighted priorities (1: 3 pts, 2: 2 pts, 3: 1 pt)
model.Maximize(sum(
    (3 if priority_map.get((student, course), 3) == 1 else
     2 if priority_map.get((student, course), 3) == 2 else
     1) * student_course_period[(student, course, period)]
    for (student, course, period) in student_course_period
))

# Step 6: Solve
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Step 7: Output results
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    assignments = []
    for (student, course, period), var in student_course_period.items():
        if solver.Value(var):
            assignments.append((student, course, period + 1))  # Periods are 1-based

    result_df = pd.DataFrame(assignments, columns=["Student", "Course", "Period"])
    result_df.to_excel("final_schedule.xlsx", index=False)
    print("Schedule created: final_schedule.xlsx")
else:
    print("No feasible solution found.")

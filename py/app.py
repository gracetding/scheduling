import pandas as pd
from ortools.sat.python import cp_model

# Load course requests spreadsheet
df = pd.read_excel("py/CourseReqsParsed1.xlsx")  # Assumes columns: Student, Course, Priority
secs = pd.read_excel("py/CourseReqsParsed1.xlsx", sheet_name="Classes")

# Configuration
required_periods = { # Format: {'CourseName_SectionID': required_period (int)}
    'Multivar Calc_0': 0,
    'Chorus_0': 8,
    'US String Orchestra_0': 1,
    'US Winds_0': 1
}
NUM_PERIODS = 9  # number of timeslots
MAX_STUDENTS_PER_SECTION = 20
SECTIONS_PER_COURSE = {}
for _, row in secs.iterrows():
    course = row['Name']
    sections = row["# Sections"]
    SECTIONS_PER_COURSE[course] = int(sections)
    #could add in the required periods thing here


# get unique students and course lists
students = df['Student'].unique().tolist()
courses = df['Course'].unique().tolist()

# build student-course request map (with priorities)
student_course_map = {}
priority_map = {}
for _, row in df.iterrows():
    student = row['Student']
    course = row['Course']
    priority = row.get('Priority', 1)
    student_course_map.setdefault(student, []).append(course) #if the course reqs list exists, appends the course; if not, makes a list & appends course
    priority_map[(student, course)] = priority
# initialize model
model = cp_model.CpModel()

# Variables
student_course_section_period = {}  # (student, course, section, period) => bool
course_section_period = {}          # (course, section, period) => bool

for course in courses:
    for section in range(SECTIONS_PER_COURSE[course]):
        for period in range(NUM_PERIODS):
            key = (course, section, period)
            course_section_period[key] = model.NewBoolVar(f"course_{course}_sec{section}_p{period}") #value is 1 if the section is scheduled in that period

for student in students:
    for course in student_course_map[student]:
        for section in range(SECTIONS_PER_COURSE[course]):
            for period in range(NUM_PERIODS):
                key = (student, course, section, period)
                student_course_section_period[key] = model.NewBoolVar(f"{student}_{course}_sec{section}_p{period}")

# Step 4: Constraints

# 1. Each section must be scheduled in exactly one period (unless required)
for course in courses:
    for section in range(SECTIONS_PER_COURSE[course]):
        if f"{course}_{section}" in required_periods:
            for p in range(NUM_PERIODS):
                if p == required_periods[f"{course}_{section}"]:
                    model.Add(course_section_period[(course, section, p)] == 1)
                else:
                    model.Add(course_section_period[(course, section, p)] == 0)
        else:
            model.Add(sum(course_section_period[(course, section, p)] for p in range(NUM_PERIODS)) == 1)

# 2. A student can be in at most one section of a course
for student in students:
    for course in student_course_map[student]:
        model.Add(sum(
            student_course_section_period[(student, course, section, p)]
            for section in range(SECTIONS_PER_COURSE[course])
            for p in range(NUM_PERIODS)
        ) <= 1)
        for section in range(SECTIONS_PER_COURSE[course]):
            for p in range(NUM_PERIODS):
                # Students can only be assigned if the section is scheduled then
                model.AddImplication(
                    student_course_section_period[(student, course, section, p)],
                    course_section_period[(course, section, p)]
                )

# 3. No student in more than one class per period
for student in students:
    for p in range(NUM_PERIODS):
        model.Add(sum(
            student_course_section_period[(student, course, section, p)]
            for course in student_course_map[student]
            for section in range(SECTIONS_PER_COURSE[course])
        ) <= 1)

# 4. Enforce max students per section per period
for course in courses:
    for section in range(SECTIONS_PER_COURSE[course]):
        for p in range(NUM_PERIODS):
            enrolled = [
                student_course_section_period[(s, course, section, p)]
                for s in students if course in student_course_map[s]
            ]
            if enrolled:
                model.Add(sum(enrolled) <= MAX_STUDENTS_PER_SECTION)

# Step 5: Objective — weighted priority-based scheduling
model.Maximize(sum(
    student_course_section_period[(student, course, section, period)]
    for (student, course, section, period), var in student_course_section_period.items()
    if priority_map.get((student, course), 1) == 1
))

# Step 6: Solve
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Step 7: Output results
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    assignments = []
    for (student, course, section, period), var in student_course_section_period.items():
        if solver.Value(var):
            assignments.append((student, course, section + 1, period + 1))  # 1-based index

    result_df = pd.DataFrame(assignments, columns=["Student", "Course", "Section", "Period"])
    result_df.to_excel("final_schedule.xlsx", index=False)
    print("Schedule created: final_schedule.xlsx")
else:
    print("No feasible solution found.")

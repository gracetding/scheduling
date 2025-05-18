import pandas as pd
from ortools.sat.python import cp_model

# Load course requests spreadsheet
df = pd.read_excel("py/CourseReqs.xlsx")  # columns: Course, Student, Category, Priority (int)
secs = pd.read_excel("py/CourseReqsParsed1.xlsx", sheet_name="Classes")

seniors = pd.read_excel("py/CourseReqsParsed1.xlsx", sheet_name="Gr12")
seniors = seniors['Class'].tolist()[0:90]

final_assignments = [] #takes in tuples in the order (Student, Course, Period, Section)

#indexing data
students = df['Student'].unique().tolist()
courses = df['Course'].unique().tolist()

# setting up requirements

NUM_PERIODS = 8 # 0 - 7
SECTIONS_PER_COURSE = {}
MAX_STUDENTS_PER_SECTION = 20
required_periods = { # Format: {'CourseName_SectionID': required_period (int)}
    # 'Multivar Calc_0': 0,
    'Chorus_0': 7,
    'US String Orchestra_0': 0,
    # 'US Winds_0': 1
}
course_cats = {}

prescheduled_courses = {
    "Multivar Calc": [],
    "Chamber Singers": [],
    "Swing Choir": [],
    "US Chamber Orch": []
}

for _, row in secs.iterrows():
    course = row['Name']
    sections = row["# Sections"]
    cat = row['Category']
    course_cats[course] = cat
    SECTIONS_PER_COURSE[course] = int(sections)
    req_pd = row.get('Period', default=None)
    if req_pd != None:
        required_periods[f"{course}_0"] = req_pd




# assignments, building initial map

student_course_map = {}
priority_map = {}
course_weight_map = {}
for _, row in df.iterrows():
    student = row['Student']
    course = row['Course']
    student_course_map.setdefault(student, []).append(course) #if the course reqs list exists, appends the course; if not, makes a list & appends course
    priority = row.get('Priority', 5)
    # print(student + course + str(priority))
    if course in prescheduled_courses.keys():
        prescheduled_courses.setdefault(course, []).append(student)
        student_course_map[student].remove(course)
        # print("prescheduled course requested")
    else:
        priority_map[(student, course)] = priority
        # for period in range(NUM_PERIODS):
        #     course_weight_map[(student, course, period)] = float(row["Weight"])

# print(student_course_map['Ding, Grace'])
# eliminate nested classes -- STAR add way to actually handle this later....
# for student in students:
#     if "Multivar Calc" in student_course_map[student] and "Chamber Singers" in student_course_map[student]:
#         student_course_map[student].remove("Chamber Singers")
#     if "US Chamber Orch" in student_course_map[student] and "US String Orch" in student_course_map[student]:
#         student_course_map[student].remove("US String Orch")
#     if "Swing Choir" in student_course_map[student] and "US Chorus" in student_course_map[student]:
#         student_course_map[student].remove("US Chorus")


# initialize model
model = cp_model.CpModel()

#assigning periods
stu_course_sec_period = {} #(Student, Course, Section, Period) = True/False
course_section_period = {}


for course in courses:
    for section in range(SECTIONS_PER_COURSE[course]):
        for period in range(NUM_PERIODS):
            key = (course, section, period)
            course_section_period[key] = model.NewBoolVar(f"course_{course}_sec{section}_U{period}") #value is 1 if the section is scheduled in that period

for student in students:
    if len(student_course_map[student]) != 0:
        for course in student_course_map[student]:
            for section in range(SECTIONS_PER_COURSE[course]):
                for period in range(NUM_PERIODS):
                    key = (student, course, section, period)
                    stu_course_sec_period[key] = model.NewBoolVar(f"{student}_{course}_sec{section}_U{period}")



# CONSTRAINTS
# 1. each section is assigned to only one period
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


# start by scheduling math and WL courses
for student in students:

#     # Student must be scheduled in their requested language course
    if any(course_cats[course]=="WL" for course in student_course_map[student]):
        wlcourse = [course for course in student_course_map[student] if "WL" in course[0:3]]
        model.Add(sum(stu_course_sec_period[(student, course, sec, period)]
                  for course in wlcourse
                  for sec in range(SECTIONS_PER_COURSE[course])
                  for period in range(NUM_PERIODS)
                  ) == 1)
    # Student must be scheduled in their requested language course
    if any(course_cats[course]=="MAT" for course in student_course_map[student]):
        wlcourse = [course for course in student_course_map[student] if "MAT" in course[0:3]]
        model.Add(sum(stu_course_sec_period[(student, course, sec, period)]
                  for course in wlcourse
                  for sec in range(SECTIONS_PER_COURSE[course])
                  for period in range(NUM_PERIODS)
                  ) >= 1)

#students cannot be in more than one class at once -- STAR need to figure out how to sum weights to <= 1
for student in students:
    for p in range(NUM_PERIODS):
        model.Add(sum(stu_course_sec_period[(student, course, section, p)]
            for course in student_course_map[student]
            for section in range(SECTIONS_PER_COURSE[course])
        ) <= 1)

# STAR -- have to include a way to prioritize scheduling one of every course over scheduling 2 courses in the same category

# student is in only one section of a course
for student in students:
    for course in student_course_map[student]:
        model.Add(sum(
            stu_course_sec_period[(student, course, section, p)]
            for section in range(SECTIONS_PER_COURSE[course])
            for p in range(NUM_PERIODS)
        ) <= 1)
        for section in range(SECTIONS_PER_COURSE[course]):
            for p in range(NUM_PERIODS):
                # Students can only be assigned if the section is scheduled then
                model.AddImplication(
                    stu_course_sec_period[(student, course, section, p)],
                    course_section_period[(course, section, p)]
                )

# seniors must be in one eng course
# for student in students:
#     if student in seniors:
#         engCourses = [course for course in student_course_map[student] if "Eng" in course]
#         model.Add(sum(
#             stu_course_sec_period[(student, course, section, p)]
#             for p in range(NUM_PERIODS)
#             for course in engCourses
#             for section in range(SECTIONS_PER_COURSE[course])
#         ) == 1)
        
# limits the number of students per course
for course in courses:
    for section in range(SECTIONS_PER_COURSE[course]):
        for p in range(NUM_PERIODS):
            enrolled = [
                stu_course_sec_period[(s, course, section, p)]
                for s in students if course in student_course_map[s]
            ]
            if enrolled and course != "US Chorus" and course != "US String Orch":
                model.Add(sum(enrolled) <= MAX_STUDENTS_PER_SECTION)


# seniors must be in at least 4 courses
# for student in seniors:
#     model.Add(sum(
#         stu_course_sec_period[(student, course, section, p)]
#             for course in student_course_map[student]
#             for section in range(SECTIONS_PER_COURSE[course])
#             for p in range(NUM_PERIODS)
#     ) >= 4)


# STAR circle back to this.... try to figure out how to make this distribute widely
for student in students:
    core_courses = []
    for course in student_course_map[student]:
        if course_cats[course] not in core_courses:
            core_courses.append(course_cats[course])


# solve by maximizing the priority score, not counting english courses
# model.Maximize(sum(
#     (4 if priority_map.get((student, course), 3) == 1 and not "Eng" in course[0:3] else
#      2 if priority_map.get((student, course), 3) == 2 and not "Eng" in course[0:3] else
#      1) * stu_course_sec_period[(student, course, section, period)]
#     for (student, course, section, period) in stu_course_sec_period
# ))

model.Maximize(sum(
    stu_course_sec_period[(student, course, section, p)] * (priority_map[(student, course)]**-1)
    for (student, course, section, p) in stu_course_sec_period
))
solver = cp_model.CpSolver()

solver.parameters.max_time_in_seconds = 600.0
status = solver.Solve(model)

# Step 7: Output results
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    assignments = []
    for (student, course, section, period), var in stu_course_sec_period.items():
        if solver.Value(var):
            assignments.append((student, course, section + 1, period))  # 1-based index

    result_df = pd.DataFrame(assignments, columns=["Student", "Course", "Section", "Period"])
    result_df.to_excel("final_schedule.xlsx", index=False)
    print("Schedule created: final_schedule.xlsx")
else:
    print("No feasible solution found.")



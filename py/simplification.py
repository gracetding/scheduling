import pandas as pd
from ortools.sat.python import cp_model

def run_model(model, priority_num, courses_considered):
    # Load course reqs spreadsheet
    df = pd.read_excel("py/CourseReqsParsed1.xlsx")  # columns: Course, Student, Category, Priority (int)
    # Loads available courses
    secs = pd.read_excel("py/CourseReqsParsed1.xlsx", sheet_name="Classes")

    seniors = pd.read_excel("py/CourseReqsParsed1.xlsx", sheet_name="Gr12")
    seniors = seniors['Class'].tolist()[0:90]

    # final_assignments = [] #takes in tuples in the order (Student, Course, Period, Section)

    #indexing data
    courses = []
    # setting up requirements

    NUM_PERIODS = 8 # 0 - 7
    SECTIONS_PER_COURSE = {}
    MAX_STUDENTS_PER_SECTION = 20
    required_periods = { # Format: {'CourseName_SectionID': required_period (int)}
        # 'Multivar Calc_0': 0,
        'US Chorus_0': 7,
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
            required_periods[f"{course}_0"] = req_pd - 1

    # assignments, building initial map
    student_course_map = {}
    course_student_priority = {}
    for _, row in df.iterrows():
        student = row['Student']
        course = row['Course']
        if course_cats[course] in courses_considered:
            if course not in courses:
                courses.append(course)
            if int(row['Priority']) <= priority_num or "Eng" in course:
                student_course_map.setdefault(student, []).append(course) #if the course reqs list exists, appends the course; if not, makes a list & appends course
                # print(student_course_map[student])
                if course in prescheduled_courses.keys():
                    student_course_map[student].remove(course)
                course_student_priority[(course, student)] = int(row["Priority"])

    # print (course_student_priority)
    # for student, courses in student_course_map.items():
    #     print(student, courses)
    # print(student_course_map["Ding, Grace"])
    # initialize model
    # print(courses)
    #assigning periods
    stu_course_sec_period = {} #(Student, Course, Section, Period) = True/False
    course_section_period = {}
    

    for course in courses:
        for section in range(SECTIONS_PER_COURSE[course]):
            for period in range(NUM_PERIODS):
                key = (course, section, period)
                course_section_period[key] = model.NewBoolVar(f"course_{course}_sec{section}_U{period}") #value is 1 if the section is scheduled in that period

    # print(course_section_period)
    for student in student_course_map.keys():
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

    
    # only one section of a course is scheuduled per period
    for course in courses:
        for period in range(NUM_PERIODS):
            model.Add(sum(course_section_period[(course, section, period)]
                          for section in range(SECTIONS_PER_COURSE[course]))
                          <= 1) 

    #students cannot be in more than one class at once
    for student in student_course_map.keys():
        for p in range(NUM_PERIODS):
            model.Add(sum(stu_course_sec_period[(student, course, section, p)]
                for course in student_course_map[student]
                for section in range(SECTIONS_PER_COURSE[course])
            ) <= 1)

    # student is in only one section of a course
    for student in student_course_map.keys():
        for course in student_course_map[student]:
            model.Add(sum(stu_course_sec_period[(student, course, sec, p)] 
                        for p in range(NUM_PERIODS)
                        for sec in range(SECTIONS_PER_COURSE[course])) <= 1)
            #student is only in course if it is scheduled in that period
            for section in range(SECTIONS_PER_COURSE[course]):
                for p in range(NUM_PERIODS):
                    model.AddImplication(stu_course_sec_period[(student, course, section, p)], course_section_period[(course, section, p)])

    #students must be in one english course
    # for student in student_course_map.keys():
    #     engCourses = [course for course in student_course_map[student] if "Eng" in course]
    #     model.Add(sum(
    #         stu_course_sec_period[(student, course, section, p)]
    #         for p in range(NUM_PERIODS)
    #         for course in engCourses
    #         for section in range(SECTIONS_PER_COURSE[course])
    #     ) == 1)

    # limits the number of students per course
    for course in courses:
        for section in range(SECTIONS_PER_COURSE[course]):
            for p in range(NUM_PERIODS):
                enrolled = [
                    stu_course_sec_period[(s, course, section, p)]
                    for s in student_course_map.keys() if course in student_course_map[s]
                ]
                if enrolled and course != "US Chorus" and course != "US String Orch":
                    model.Add(sum(enrolled) <= MAX_STUDENTS_PER_SECTION)
        
    model.maximize(sum(
        stu_course_sec_period.values() ))
    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = 600.0
    # solver.parameters.enumerate_all_solutions = True
    status = solver.Solve(model)
    
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        assignments = []
        for (student, course, section, period), var in stu_course_sec_period.items():
            if solver.Value(var):
                assignments.append((student, course, section, period+1))  # 1-based index

        result_df = pd.DataFrame(assignments, columns=["Student", "Course", "Section", "Period"])
        result_df.to_excel("py/final_schedule.xlsx", index=False)
        print("Schedule created: final_schedule.xlsx")
        return True
    else:
        print("No feasible solution found.")
        return False


model = cp_model.CpModel()

# run_model(model, 1, ["WL", "MAT"])
run_model(model, 1, ["MAT", "WL", "SCI", "HIS", "CS", "Arts"])
# run_model(model, 2, ["WL", "HIS"])
# run_model(model, 3, ["WL", "HIS"])


# Step 7: Output results


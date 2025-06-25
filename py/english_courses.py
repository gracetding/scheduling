import pandas as pd
from ortools.sat.python import cp_model
import numpy as np

def read_prev_model(model):
    df = pd.read_excel(model)
    assignments = []
    for _, row in df.iterrows():
        student = row['Student']
        course = row['Course']
        section = row['Section']
        period = row['Period']
        assignments.append((student, course, section, period, 0))
    return assignments

def eng_model(prev_model, model): #where prev model is the old spreadsheet
    # Load course reqs spreadsheet
    df = pd.read_excel("CourseReqs2525.xlsx")  # columns: Course, Student, Category, Priority (int)
    # Loads available courses
    secs = pd.read_excel("CourseReqs2525.xlsx", sheet_name="Classes")
    # seniors = pd.read_excel("CourseReqs2525.xlsx", sheet_name="Gr12")
    # seniors = seniors['Class'].unique().tolist()

    #indexing data
    courses = []
    assignments = read_prev_model(prev_model)
    # setting up requirements

    NUM_PERIODS = 8 # 0 - 7
    SECTIONS_PER_COURSE = {}
    MAX_STUDENTS_PER_SECTION = 20
    
    for i, row in secs.iterrows():
        course = row['Name']
        sections = row["# Sections"]
        if not pd.isnull(row['Name']) and "Eng 12" in course:
            courses.append(course)
            if not pd.isnull(row['# Sections']):
                SECTIONS_PER_COURSE[course] = int(sections)
       

    # assignments, building initial map
    student_course_map = {}
    course_student_priority = {}
    for _, row in df.iterrows():
        student = row['Student']
        course = row['Course']
        if "Eng 12" in course:
            if course not in courses:
                courses.append(course)
            student_course_map.setdefault(student, []).append(course) #if the course reqs list exists, appends the course; if not, makes a list & appends course
            course_student_priority[(course, student)] = int(row["Priority #"])


    #assigning periods
    stu_course_sec_period = {} #(Student, Course, Section, Period) = True/False
    course_section_period = {}
    
    ## SETTING UP MODEL ##
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
    for (student, course, section, period, priority) in assignments:
        if period != 0:
            stu_course_sec_period[(student, course, section, period-1)] = model.NewBoolVar(f"{student}_{course}_sec{section}_U{period-1}")
            course_section_period[(course, section, period-1)] = model.NewBoolVar(f"course_{course}_sec{section}_U{period-1}")



    # CONSTRAINTS
    # must meet previous assigned courses
    for (student, course, section, period, priority) in assignments:
        if period != 0:
            model.Add(stu_course_sec_period[(student, course, section, period-1)] == 1)
            model.Add(course_section_period[(course, section, period-1)] == 1)
    # 1. each section is assigned to only one period
    for course in courses:
        for section in range(SECTIONS_PER_COURSE[course]):
            model.Add(sum(course_section_period[(course, section, p)] for p in range(NUM_PERIODS)) == 1)

    # salata's classes are scheduled during 2 and 4
    for period in [1, 3]:
        model.Add(sum(course_section_period[(course, 0, period)]
                      for course in ['Eng 12 Digitopia', "Eng 12 War"]) == 1)
        
    
    # only one section of a course is scheuduled per period
    
    for period in range(NUM_PERIODS):
        model.Add(sum(course_section_period[(course, section, period)]
                    for course in courses
                    for section in range(SECTIONS_PER_COURSE[course])
                    )
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

    #students must be in exactly one english course
    for student in student_course_map.keys():
        engCourses = [course for course in student_course_map[student] if "Eng" in course]
        model.Add(sum(
            stu_course_sec_period[(student, course, section, p)]
            for p in range(NUM_PERIODS)
            for course in engCourses
            for section in range(SECTIONS_PER_COURSE[course])
        ) == 1)

    # limits the number of students per course
    for course in courses:
        for section in range(SECTIONS_PER_COURSE[course]):
            for p in range(NUM_PERIODS):
                enrolled = [
                    stu_course_sec_period[(s, course, section, p)]
                    for s in student_course_map.keys() if course in student_course_map[s]
                ]
                if enrolled:
                    model.Add(sum(enrolled) <= MAX_STUDENTS_PER_SECTION)
        

    model.Maximize(sum(
        stu_course_sec_period[(student, course, section, p)] * (course_student_priority[(course, student)]**-1)
        for student in student_course_map.keys()
        for course in student_course_map[student]
        for section in range(SECTIONS_PER_COURSE[course])
        for p in range(NUM_PERIODS)
    ))
    


    solver = cp_model.CpSolver()
    
    status = solver.Solve(model)
    solver.parameters.max_time_in_seconds = 600.0
    # Step 7: Output results
    
    
    # solver.parameters.enumerate_all_solutions = True
    # status = solver.Solve(model)
    
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        name = prev_model.split('.')[0][-1]
        fname = "25-26 Eng Courses/modified_english_courses" + name + ".xlsx"
        score = 0
        for (student, course, section, period), var in stu_course_sec_period.items():
            # alerts if AALit is not scheduled
            # if course_student_priority[("Eng12 AALit", student)] == 1:
            #     print("hello")
            if "Eng 12" in course:
                priority = course_student_priority[(course, student)]
                if solver.Value(var):
                    assignments.append((student, course, section, period+1, priority))  # 1-based index
                    score += priority
        result_df = pd.DataFrame(assignments, columns=["Student", "Course", "Section", "Period", "Priority"])
        result_df.to_excel(fname, index=False)
        print("Schedule created: " + fname)
        print("Score: "+ str(score))

        return True
    else:
        print("No feasible solution found.")
        return False


model = cp_model.CpModel()

eng_model("25-26 Single Section Courses/final_schedule_solution_4.xlsx", model)
eng_model("25-26 Single Section Courses/final_schedule_solution_5.xlsx", model)
eng_model("25-26 Single Section Courses/final_schedule_solution_6.xlsx", model)
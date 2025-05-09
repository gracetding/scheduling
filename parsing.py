import pandas as pd

requests = pd.read_excel('CourseReqsParsed1.xlsx', sheet_name="Requests")
classes = pd.read_excel('CourseReqsParsed1.xlsx', sheet_name="Classes", header=1)
students = []
with open("sampleseeds.txt", "w") as f:
    classes = classes.fillna(value=0)
    for course in classes.values.tolist():
        print(course)
        # desc = course
        abbrevName = course[0].replace(" ", "")
        abbrevName = abbrevName.replace("&", "")
        if course[2] > 1:
            for x in range(int(course[2])):
                f.write('Section.create(name: "{}", section_num: {})\n'.format(course[0], str(x+1)))
        else:    
            f.write('{} = Section.create(name: "{}", section_num: 1)\n'.format(abbrevName, course[0]))
        if course[1] != 0: #timeslot if possible
            ts = course[1].replace(".", "")
            f.write('SectionTimeslot.create(course_id: {}.id, timeslot_id: {}.id)\n'.format(abbrevName, ts))
        # if desc[2] != "nan": #number of

    for col in requests.values.tolist():
        name = col[3].split(", ")
        fullname = name[0]+name[1]
        fullname = fullname.replace(" ", "")
        fullname = fullname.replace("'", "")
        fullname = fullname.replace("-", "")
        if not fullname in students:
            students.append(fullname)
            f.write('{} = Student.create(name: "{}")\n'.format(fullname, col[3]))
        if col[5] == "First Choice":
            prio = 1
        elif col[5] == "Second Choice":
            prio = 2
        elif col[5] == "Third Choice":
            prio = 3
        
        f.write('Request.create(course_name: "{}", student_id: {}.id, priority: {})\n'.format(col[1], fullname, prio))


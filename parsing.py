import pandas as pd

requests = pd.read_excel('CourseReqsParsed1.xlsx', sheet_name="Requests")
single_section_classes = pd.read_excel('CourseReqsParsed1.xlsx', sheet_name="Classes")
students = []
with open("sampleseeds.txt", "w") as f:
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


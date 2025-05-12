for x in range(10) and range(5, 12):
    print(x)

engList = ['Eng 12 AALit', 'Eng12 Digitopia', 'Eng 12 Love', 'Eng 12 Sixties', "Multivar"]
# if "Eng" for course in engList 
#     print("English course" + course)]

engCourses = [course for course in engList if "Eng" in course]
print(engCourses)
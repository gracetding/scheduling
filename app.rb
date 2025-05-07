require 'sinatra'
require 'sinatra/activerecord'
require './models.rb'
require 'roo'


set :database, {adapter: 'sqlite3', database: 'schedule.sqlite3'}

# File.open('CourseReqsParsed.xlsx') do |file|
#     content = file.readlines
# end

file = Roo::Spreadsheet.open 'CourseReqsParsed1.xlsx'

single_courses = file.sheet(1)
single_section_list = single_courses.column(1).to_a

single_courses.each do |course| #adds single-section courses to database
    sec = Section.create(name: course[0], section_num: 1)
    time = Timeslot.find_by(period: course[1])
    if time != nil #adds timeslot association if possible
        SectionTimeslot.create(course_id: sec.id, timeslot_id: time.id)
    end
    # puts course
end
puts "finished making single-section courses"

# requests = file.sheet(0)
# requests.each do |line|
#     # puts line
#     if line[3] == nil and line[1] == nil
#         puts "nothing here!"
#         break
#     else
#         stu = Student.find_or_create_by(name: line[3])
#         sec = Section.find_or_create_by(name: line[1], section_num: 1)
#         Request.create(course_name: line[1], student_id: stu.id)
#     end
# end

# puts "finished making requests"
single_section_list.each do |course| #schedules people with single-section courses
    sect = Section.find_by(name: course) #goes by courses
    Request.where(course_name: course, priority: 1).each do |req|
        assign = StudentSection.create(student_id: req.student_id, section_id: sect.id)
        ts = SectionTimeslot.find_by(course_id: sect.id)
        if ts != nil
            assign.update(timeslot_id: ts.timeslot_id)
        end
        
    end
end

doc = File.new("assignments.txt", "w")

StudentSection.select(:section_id).distinct.each do |assignment| #prints everyone it's scheduled
    # puts "printing assignments"
    classname = Section.find_by(id: assignment.section_id)
    doc.print(classname.name + " ")
    if SectionTimeslot.find_by(course_id: classname.id) != nil
        time = Timeslot.find_by(id: SectionTimeslot.find_by(course_id: classname.id).timeslot_id)

        doc.print(time.period) 
    end
    if StudentSection.where(section_id: assignment.section_id).count > 20
        doc.print("\n**This should probably be two sections**")
    end
    StudentSection.where(section_id: assignment.section_id).each do |stu|
        student = Student.find_by(id: stu.student_id)
        doc.print("\n" + student.name)
    end
    doc.print("\n\n")
end
puts "done writing!"

doc.close



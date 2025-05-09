require 'sinatra'
require 'sinatra/activerecord'
require './models.rb'
require 'roo'


set :database, {adapter: 'sqlite3', database: 'schedule.sqlite3'}

# File.open('CourseReqsParsed.xlsx') do |file|
#     content = file.readlines
# end



# Request.where(priority: 1, fulfilled: false).find_each(batch_size: 100) do |req| #latest scheduling code
#     sect = Section.find_by(name: req.course_name, section_num: 1)
#     if StudentSection.where(section_id: sect.id).count >= 20 and Section.find_by(name: req.course_name, section_num: 2) != nil
#         sect = Section.find_by(name: req.course_name, section_num: 2)
#     end
#     assign = StudentSection.create(student_id: req.student_id, section_id: sect.id)
#     req.update(fulfilled: true)
# end


# # class_list = File.new("all_classes.txt", "w")
# # Section.all.each do |sect|
# #     class_list.print(sect.name + ", section num. " + sect.section_num.to_s + "\n")

# # end
# # class_list.close 

# doc = File.new("assignments.txt", "w")

# StudentSection.select(:section_id).distinct.each do |assignment| #prints everyone it's scheduled
#     # puts "printing assignments"
#     classname = Section.find_by(id: assignment.section_id)
#     doc.print(classname.name + " " + classname.section_num.to_s)
#     if SectionTimeslot.find_by(course_id: classname.id) != nil
#         time = Timeslot.find_by(id: SectionTimeslot.find_by(course_id: classname.id).timeslot_id)

#         doc.print(time.period) 
#     end
#     if StudentSection.where(section_id: assignment.section_id).count > 20
#         doc.print("\n**This should probably be two sections**")
#     end
#     StudentSection.where(section_id: assignment.section_id).each do |stu|
#         student = Student.find_by(id: stu.student_id)
#         doc.print("\n" + student.name)
#     end
#     doc.print("\n\n")
# end
# puts "done writing!"

# doc.close



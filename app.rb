require 'sinatra'
require 'sinatra/activerecord'
require './models.rb'
require 'roo'


set :database, {adapter: 'sqlite3', database: 'schedule.sqlite3'}

# File.open('CourseReqsParsed.xlsx') do |file|
#     content = file.readlines
# end

file = Roo::Spreadsheet.open '../CourseReqsParsed.xlsx'
sheets = file.sheets
requests = file.sheet(0)
single_courses = file.sheet(0).column(1)

requests.each do |line|
    if line[3] != ""
        puts line[1] 
        puts line[3]
        stu = Student.find_or_create_by(name: line[3])
        puts "CREATING NEW STUDENT"
        sec = Section.find_or_create_by(name: line[1], section_num: 1)
        puts "CREATING NEW SECTION"
        Request.create(course_name: line[1], student_id: stu.id)

    end
end

puts Student.all.name
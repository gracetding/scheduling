class CreateSectionTimeslotsTable < ActiveRecord::Migration[8.0]
  def change
    create_table :section_timeslots do |t|
      t.integer :course_id, :null => false
      t.integer :timeslot_id, :null => false
    end
  end
end

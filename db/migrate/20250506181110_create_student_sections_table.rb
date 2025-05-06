class CreateStudentSectionsTable < ActiveRecord::Migration[8.0]
  def change
    create_table :student_sections do |t|
      t.integer :student_id, :null => false
      t.integer :section_id, :null => false
      t.integer :timeslot_id, :null => false
    end
  end
end

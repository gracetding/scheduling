class CreateRequestsTable < ActiveRecord::Migration[8.0]
  def change
    create_table :requests do |t|
      t.string :course_name, :null => false
      t.integer :student_id, :null => false
      t.integer :priority, :null => false
    end
  end
end

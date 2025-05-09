class CreateStudentsTable < ActiveRecord::Migration[8.0]
  def change
    create_table :students do |t|
      t.string :name, :null => false
    end
  end
end

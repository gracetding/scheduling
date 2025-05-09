class CreateTimeslotsTable < ActiveRecord::Migration[8.0]
  def change
    create_table :timeslots do |t|
      t.string :period, :null => false
    end
  end
end

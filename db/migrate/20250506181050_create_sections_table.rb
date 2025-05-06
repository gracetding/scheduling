class CreateSectionsTable < ActiveRecord::Migration[8.0]
  def change
    create_table :sections do |t|
      t.string :name, :null => false
      t.integer :section_num, :null => false
    end
  end
end

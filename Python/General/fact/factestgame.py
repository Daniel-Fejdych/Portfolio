from factruegame import *

iron = item_directory.get_item_by_name("IronOre")
stack = ItemStack(iron, 10)

assert stack.space_left() == iron.maxStackSize - 10

split_stack = stack.split(5)
assert split_stack.amount == 5
assert stack.amount == 5

stack.merge(split_stack)
assert stack.amount == 10

inventory = [
    ItemStack(iron, 5),
    None
]

recipe = recipe_directory.get_recipe_by_name("SmeltIron")

assert recipe.can_craft(inventory)

template = template_directory.get_template("IronMiner")
producer = Producer(0,0,0, tier=1, template=template)

for _ in range(template.baseProductionTime):
    producer.tick()

assert producer.inventory[0] is not None

template = template_directory.get_template("Furnace")
crafter = Crafter(1,0,0,1,template)

# Insert required inputs manually
# ...
while crafter.get_output_summary() == {}:
    crafter.tick()

assert crafter.get_output_summary() != {}




save_world()
load_world()

assert len(world_grid) > 0

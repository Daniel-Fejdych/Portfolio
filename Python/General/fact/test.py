import unittest
import os

from game import *

class TestGameSystems(unittest.TestCase):

    def setUp(self):
        world_grid.clear()
        availableObjects.clear()

    # =========================
    # RECIPE TEST
    # =========================

    def test_recipe_with_tag(self):
        recipe = recipe_directory.get_recipe_by_name("SciencePackRecipe")
        self.assertIsNotNone(recipe)

        iron_plate = item_directory.get_item_by_name("IronPlate")
        copper_plate = item_directory.get_item_by_name("CopperPlate")

        inventory = [
            ItemStack(iron_plate, 1),
            ItemStack(copper_plate, 1)
        ]

        self.assertTrue(recipe.can_craft(inventory))

        outputs = recipe.craft(inventory)
        self.assertEqual(outputs[0].item.itemName, "SciencePack")
        self.assertEqual(outputs[0].amount, 1)

    # =========================
    # CRAFTER TEST
    # =========================

    def test_crafter_smelting(self):
        furnace_template = template_directory.get_template("Furnace")
        crafter = Crafter(0, 0, 0, 1, furnace_template)

        iron_ore = item_directory.get_item_by_name("IronOre")

        crafter.inventory[0] = ItemStack(iron_ore, 2)

        # Run enough ticks
        for _ in range(10):
            crafter.tick()

        summary = crafter.get_output_summary()
        self.assertIn("IronPlate", summary)
        self.assertEqual(summary["IronPlate"], 1)

    # =========================
    # RESEARCH TEST
    # =========================

    def test_research_unlock(self):
        lab_template = template_directory.get_template("Lab")
        researcher = Researcher(0, 0, 0, 1, lab_template)

        science_pack = item_directory.get_item_by_name("SciencePack")
        researcher.inventory[0] = ItemStack(science_pack, 2)

        # Run enough ticks for BasicAutomation
        for _ in range(20):
            researcher.tick()

        self.assertIn("BasicAutomation", availableObjects)
        self.assertIn("BasicBelt", availableObjects)

    # =========================
    # SAVE / LOAD TEST
    # =========================

    def test_save_and_load(self):
        box_template = template_directory.get_template("SmallBox")
        box = Box(5, 5, 0, 1, box_template)

        iron_ore = item_directory.get_item_by_name("IronOre")
        box.inventory[0] = ItemStack(iron_ore, 10)

        save_world("test_saves.json")

        world_grid.clear()

        load_world(0, "test_saves.json")

        loaded_box = get_object_at(5, 5, 0)
        self.assertIsNotNone(loaded_box)
        self.assertEqual(
            loaded_box.inventory[0].item.itemName,
            "IronOre"
        )
        self.assertEqual(
            loaded_box.inventory[0].amount,
            10
        )

        os.remove("test_saves.json")


if __name__ == "__main__":
    unittest.main()

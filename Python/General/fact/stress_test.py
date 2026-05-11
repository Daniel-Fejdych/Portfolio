import time
import random

from game import *

def spawn_factory_cluster(offset_x, offset_y):
    """
    Creates a full production cluster.
    """

    # Miners
    for i in range(5):
        template = template_directory.get_template("MegaIronMiner")
        Producer(offset_x + i, offset_y, 0, 3, template)

    for i in range(5):
        template = template_directory.get_template("MegaCopperMiner")
        Producer(offset_x + i, offset_y + 1, 0, 3, template)

    # Furnaces
    for i in range(4):
        template = template_directory.get_template("MegaFurnace")
        Crafter(offset_x + i, offset_y + 3, 0, 3, template)

    # Assemblers
    for i in range(3):
        template = template_directory.get_template("MegaAssembler")
        Crafter(offset_x + i, offset_y + 6, 0, 3, template)

    # Lab
    template = template_directory.get_template("MegaLab")
    lab = Researcher(offset_x + 2, offset_y + 9, 0, 3, template)

    science_item = item_directory.get_item_by_name("SciencePack")
    lab.inventory[0] = ItemStack(science_item, 10)


def run_stress_test():

    world_grid.clear()
    availableObjects.clear()

    print("Spawning stress world...")

    # Spawn 10 factory clusters
    for i in range(10):
        spawn_factory_cluster(i * 20, 0)

    total_objects = len(world_grid)
    print(f"Spawned {total_objects} objects")

    TICKS = 5000

    start = time.time()

    for tick in range(TICKS):
        for obj in list(world_grid.values()):
            obj.tick()

        if tick % 500 == 0:
            print(f"Tick {tick}")

    duration = time.time() - start

    print("\n===== STRESS TEST COMPLETE =====")
    print(f"Ticks: {TICKS}")
    print(f"Objects: {total_objects}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Ticks/sec: {TICKS / duration:.2f}")
    print("Unlocked:", availableObjects)


if __name__ == "__main__":
    run_stress_test()

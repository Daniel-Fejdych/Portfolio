"""
Factory Game – A simulation of a factory with belts, producers, crafters, and research.
"""

from typing import List, Optional, Dict, Tuple, Any
import math
import json
import os
from enum import Enum


# =========================
#  Constants & Enums
# =========================
class MachineState(Enum):
    """Possible states of a machine."""
    IDLE = "IDLE"
    WORKING = "WORKING"
    BLOCKED_OUTPUT = "BLOCKED_OUTPUT"
    STARVED_INPUT = "STARVED_INPUT"


# Directions as (dx, dy, dz) for 3D grid.
DIRECTION_OFFSETS = {
    0: (1, 0, 0),    # North (+x)
    1: (0, 1, 0),    # West (+y)
    2: (-1, 0, 0),   # South (-x)
    3: (0, -1, 0),   # East (-y)
    4: (0, 0, 1),    # Up (+z)
    5: (0, 0, -1),   # Down (-z)
}


# =========================
#  Custom Exceptions
# =========================
class GameError(Exception):
    """Base exception for game‑specific errors."""
    pass


class LoadError(GameError):
    """Raised when loading a save fails."""
    pass


# =========================
#  Item System
# =========================
class Item:
    """An item type with a name, stack size, and tags."""
    def __init__(self, item_name: str, max_stack_size: int, tag_array: List[str]):
        if max_stack_size <= 0:
            raise ValueError("max_stack_size must be > 0")
        self.item_name = item_name
        self.max_stack_size = max_stack_size
        self.tag_array = tag_array

    def has_tag(self, tag: str) -> bool:
        return tag in self.tag_array

    def __repr__(self):
        return f"Item({self.item_name}, max={self.max_stack_size})"


class ItemStack:
    """A stack of a specific item."""
    def __init__(self, item: Item, amount: int):
        if amount <= 0:
            raise ValueError("ItemStack amount must be > 0")
        if amount > item.max_stack_size:
            raise ValueError("Amount exceeds max stack size")
        self.item = item
        self.amount = amount

    def can_merge(self, other: "ItemStack") -> bool:
        return self.item.item_name == other.item.item_name

    def space_left(self) -> int:
        return self.item.max_stack_size - self.amount

    def merge(self, other: "ItemStack") -> Optional["ItemStack"]:
        """
        Merge as much as possible from `other` into this stack.
        Returns an overflow stack if not all could fit.
        """
        if not self.can_merge(other):
            raise ValueError("Cannot merge different items")
        total = self.amount + other.amount
        if total <= self.item.max_stack_size:
            self.amount = total
            return None
        else:
            self.amount = self.item.max_stack_size
            overflow_amount = total - self.item.max_stack_size
            return ItemStack(self.item, overflow_amount)

    def split(self, amount: int) -> "ItemStack":
        """Split off a new stack of `amount` items."""
        if amount <= 0 or amount > self.amount:
            raise ValueError("Invalid split amount")
        self.amount -= amount
        return ItemStack(self.item, amount)

    def is_empty(self) -> bool:
        return self.amount == 0

    def __repr__(self):
        return f"ItemStack({self.item.item_name}, {self.amount})"


# =========================
#  Recipe System
# =========================
class RecipeInput:
    """Input requirement for a recipe – either a specific item or a tag."""
    def __init__(self, amount: int, item: Optional[Item] = None, tag: Optional[str] = None):
        if amount <= 0:
            raise ValueError("RecipeInput amount must be > 0")
        if (item is None and tag is None) or (item is not None and tag is not None):
            raise ValueError("RecipeInput must have either item OR tag")
        self.item = item
        self.tag = tag
        self.amount = amount

    def matches(self, stack: ItemStack) -> bool:
        if self.item:
            return stack.item.item_name == self.item.item_name
        if self.tag:
            return self.tag in stack.item.tag_array
        return False

    def __repr__(self):
        if self.item:
            return f"RecipeInput(Item={self.item.item_name}, {self.amount})"
        return f"RecipeInput(Tag={self.tag}, {self.amount})"


class Recipe:
    """A recipe that consumes inputs and produces outputs."""
    def __init__(self, name: str, inputs: List[RecipeInput],
                 outputs: List[ItemStack], base_crafting_time: int):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.base_crafting_time = base_crafting_time

    def can_craft(self, inventory: List[Optional[ItemStack]]) -> bool:
        for inp in self.inputs:
            total = 0
            for stack in inventory:
                if stack and inp.matches(stack):
                    total += stack.amount
            if total < inp.amount:
                return False
        return True

    def craft(self, inventory: List[Optional[ItemStack]]) -> Optional[List[ItemStack]]:
        """
        Consume inputs from inventory and return a list of output stacks.
        Returns None if inputs are insufficient.
        """
        if not self.can_craft(inventory):
            return None

        # Remove inputs
        for inp in self.inputs:
            remaining = inp.amount
            for i, stack in enumerate(inventory):
                if stack and inp.matches(stack):
                    remove = min(stack.amount, remaining)
                    stack.amount -= remove
                    remaining -= remove
                    if stack.amount == 0:
                        inventory[i] = None
                    if remaining == 0:
                        break

        # Return copies of outputs
        return [ItemStack(stack.item, stack.amount) for stack in self.outputs]

    def __repr__(self):
        return f"Recipe({self.name})"


# =========================
#  Directories (load from files)
# =========================
class ItemDirectory:
    """Loads items from a CSV file."""
    def __init__(self, file_path: str = "items.txt"):
        self.items: Dict[str, Item] = {}
        self._load_items(file_path)

    def _load_items(self, file_path: str):
        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) < 2:
                        continue
                    name = parts[0]
                    max_stack = int(parts[1])
                    tags = parts[2:] if len(parts) > 2 else []
                    self.items[name] = Item(name, max_stack, tags)
        except FileNotFoundError:
            print(f"Warning: {file_path} not found. Starting with empty item list.")

    def get_item_by_name(self, name: str) -> Optional[Item]:
        return self.items.get(name)


class RecipeDirectory:
    """Loads recipes from a CSV file."""
    def __init__(self, item_directory: ItemDirectory, file_path: str = "recipes.txt"):
        self.item_directory = item_directory
        self.recipes: Dict[str, Recipe] = {}
        self._load_recipes(file_path)

    def _load_recipes(self, file_path: str):
        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = [p.strip() for p in line.split(",")]
                    if "IN" not in parts or "OUT" not in parts:
                        continue

                    name = parts[0]
                    base_time = int(parts[1])

                    in_idx = parts.index("IN")
                    out_idx = parts.index("OUT")
                    input_parts = parts[in_idx + 1:out_idx]
                    output_parts = parts[out_idx + 1:]

                    # Parse inputs
                    inputs = []
                    valid = True
                    for inp in input_parts:
                        if inp.startswith("tag:"):
                            _, tag, amt = inp.split(":")
                            inputs.append(RecipeInput(int(amt), tag=tag))
                        else:
                            item_name, amt = inp.split(":")
                            item = self.item_directory.get_item_by_name(item_name)
                            if item is None:
                                print(f"Unknown item '{item_name}' in recipe '{name}'")
                                valid = False
                                break
                            inputs.append(RecipeInput(int(amt), item=item))
                    if not valid:
                        continue

                    # Parse outputs
                    outputs = []
                    for out in output_parts:
                        item_name, amt = out.split(":")
                        item = self.item_directory.get_item_by_name(item_name)
                        if item is None:
                            print(f"Unknown item '{item_name}' in recipe '{name}'")
                            valid = False
                            break
                        outputs.append(ItemStack(item, int(amt)))
                    if not valid:
                        continue

                    self.recipes[name] = Recipe(name, inputs, outputs, base_time)

        except FileNotFoundError:
            print(f"Warning: {file_path} not found. Starting with empty recipes.")

    def get_recipe_by_name(self, name: str) -> Optional[Recipe]:
        return self.recipes.get(name)


class Research:
    """A research project that unlocks new templates."""
    def __init__(self, name: str, time: int, inputs: List[RecipeInput],
                 unlocked_template_names: List[str], dependencies: List[str]):
        self.name = name
        self.time = time
        self.inputs = inputs
        self.unlocked_template_names = unlocked_template_names
        self.dependencies = dependencies
        # Will be filled later by ResearchDirectory.resolve_templates()
        self.unlocked_templates: List["WorldObjectTemplate"] = []

    def __repr__(self):
        return f"Research({self.name}, unlocks={self.unlocked_template_names})"


class ResearchDirectory:
    """Loads research projects from a CSV file."""
    def __init__(self, item_directory: ItemDirectory, file_path: str = "researches.txt"):
        self.item_directory = item_directory
        self.researches: Dict[str, Research] = {}
        # This will be set later after WorldObjectTemplateDirectory is created
        self.template_directory = None
        self._load_researches(file_path)

    def _load_researches(self, file_path: str):
        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = [p.strip() for p in line.split(",")]
                    if "IN" not in parts or "OUT" not in parts:
                        continue

                    name = parts[0]
                    time = int(parts[1])

                    in_idx = parts.index("IN")
                    out_idx = parts.index("OUT")
                    requires_idx = parts.index("REQUIRES") if "REQUIRES" in parts else None

                    # Inputs
                    if requires_idx is not None:
                        input_parts = parts[in_idx + 1:requires_idx]
                    else:
                        input_parts = parts[in_idx + 1:out_idx]

                    inputs = []
                    valid = True
                    for inp in input_parts:
                        if inp.startswith("tag:"):
                            _, tag, amt = inp.split(":")
                            inputs.append(RecipeInput(int(amt), tag=tag))
                        else:
                            item_name, amt = inp.split(":")
                            item = self.item_directory.get_item_by_name(item_name)
                            if item is None:
                                print(f"Unknown item '{item_name}' in research '{name}'")
                                valid = False
                                break
                            inputs.append(RecipeInput(int(amt), item=item))
                    if not valid:
                        continue

                    # Dependencies
                    if requires_idx is not None:
                        dependencies = parts[requires_idx + 1:out_idx]
                    else:
                        dependencies = []

                    # Outputs (unlocked template names)
                    output_parts = parts[out_idx + 1:]
                    unlocked_names = output_parts.copy()

                    self.researches[name] = Research(name, time, inputs,
                                                     unlocked_names, dependencies)

        except FileNotFoundError:
            print(f"Warning: {file_path} not found. Starting with empty researches.")

    def get_research_by_name(self, name: str) -> Optional[Research]:
        return self.researches.get(name)

    def resolve_templates(self, template_directory):
        """Link each research to its actual WorldObjectTemplate objects."""
        for research in self.researches.values():
            research.unlocked_templates = []
            for tname in research.unlocked_template_names:
                tpl = template_directory.get_template(tname)
                if tpl:
                    research.unlocked_templates.append(tpl)
                else:
                    print(f"Unknown template '{tname}' in research '{research.name}'")


# =========================
#  World Object Templates
# =========================
class WorldObjectTemplate:
    """Base template for any world object."""
    def __init__(self, name: str, obj_type: str, inventory_size: int, max_tier: int = 1):
        self.name = name
        self.obj_type = obj_type          # "BOX", "BELT", "PRODUCER", "CRAFTER", "RESEARCHER"
        self.inventory_size = inventory_size
        self.max_tier = max_tier

    def __repr__(self):
        return f"{self.obj_type}Template({self.name}, maxTier={self.max_tier})"


class BoxTemplate(WorldObjectTemplate):
    def __init__(self, name: str, inventory_size: int, max_tier: int):
        super().__init__(name, "BOX", inventory_size, max_tier)


class BeltTemplate(WorldObjectTemplate):
    def __init__(self, name: str, base_movement_speed: int, max_tier: int):
        super().__init__(name, "BELT", inventory_size=1, max_tier=max_tier)
        self.base_movement_speed = base_movement_speed


class ProducerTemplate(WorldObjectTemplate):
    def __init__(self, name: str, produced_item: Item, base_production_time: int, max_tier: int):
        super().__init__(name, "PRODUCER", inventory_size=1, max_tier=max_tier)
        self.produced_item = produced_item
        self.base_production_time = base_production_time


class CrafterTemplate(WorldObjectTemplate):
    def __init__(self, name: str, recipes: List[Recipe],
                 base_crafting_delay: int, inventory_size: int,
                 output_inventory_size: int, max_tier: int):
        super().__init__(name, "CRAFTER", inventory_size, max_tier)
        self.recipes = recipes
        self.base_crafting_delay = base_crafting_delay
        self.output_inventory_size = output_inventory_size


class ResearcherTemplate(WorldObjectTemplate):
    def __init__(self, name: str, research_names: List[str],
                 base_research_delay: int, inventory_size: int, max_tier: int):
        super().__init__(name, "RESEARCHER", inventory_size, max_tier)
        self.research_names = research_names
        self.base_research_delay = base_research_delay
        # Resolved later
        self.researches: List[Research] = []


class WorldObjectTemplateDirectory:
    """Loads object templates from a CSV file."""
    def __init__(self, item_directory: ItemDirectory,
                 recipe_directory: RecipeDirectory,
                 research_directory: ResearchDirectory,
                 file_path: str = "objects.txt"):
        self.item_directory = item_directory
        self.recipe_directory = recipe_directory
        self.research_directory = research_directory
        self.templates: Dict[str, WorldObjectTemplate] = {}
        self._load_templates(file_path)

    def _load_templates(self, file_path: str):
        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = [p.strip() for p in line.split(",")]
                    obj_type = parts[0]

                    try:
                        if obj_type == "BOX":
                            # BOX, name, invSize, maxTier
                            _, name, inv_size, max_tier = parts
                            tpl = BoxTemplate(name, int(inv_size), int(max_tier))

                        elif obj_type == "BELT":
                            # BELT, name, speed, maxTier
                            _, name, speed, max_tier = parts
                            tpl = BeltTemplate(name, int(speed), int(max_tier))

                        elif obj_type == "PRODUCER":
                            # PRODUCER, name, itemName, baseTime, maxTier
                            _, name, item_name, base_time, max_tier = parts
                            item = self.item_directory.get_item_by_name(item_name)
                            if not item:
                                print(f"Unknown item '{item_name}' in producer '{name}'")
                                continue
                            tpl = ProducerTemplate(name, item, int(base_time), int(max_tier))

                        elif obj_type == "CRAFTER":
                            # CRAFTER, name, invSize, outSize, recipe1;recipe2, maxTier
                            _, name, inv_size, out_size, recipe_str, max_tier = parts
                            recipe_names = recipe_str.split(";")
                            recipes = []
                            for rn in recipe_names:
                                r = self.recipe_directory.get_recipe_by_name(rn)
                                if r:
                                    recipes.append(r)
                                else:
                                    print(f"Unknown recipe '{rn}' in crafter '{name}'")
                            tpl = CrafterTemplate(name, recipes, 0,  # base_crafting_delay set to 0 (not used)
                                                   int(inv_size), int(out_size), int(max_tier))

                        elif obj_type == "RESEARCHER":
                            # RESEARCHER, name, invSize, research1;research2, baseDelay, maxTier
                            _, name, inv_size, research_str, base_delay, max_tier = parts
                            research_names = research_str.split(";")
                            tpl = ResearcherTemplate(name, research_names,
                                                     int(base_delay), int(inv_size), int(max_tier))
                        else:
                            continue

                        self.templates[name] = tpl

                    except (ValueError, IndexError) as e:
                        print(f"Error parsing line: {line}\n  {e}")

        except FileNotFoundError:
            print("Warning: objects.txt not found. Starting with empty templates.")

    def get_template(self, name: str) -> Optional[WorldObjectTemplate]:
        return self.templates.get(name)

    def resolve_researches(self):
        """Link researcher templates to actual Research objects."""
        for tpl in self.templates.values():
            if isinstance(tpl, ResearcherTemplate):
                tpl.researches = []
                for rname in tpl.research_names:
                    r = self.research_directory.get_research_by_name(rname)
                    if r:
                        tpl.researches.append(r)
                    else:
                        print(f"Unknown research '{rname}' in template '{tpl.name}'")


# =========================
#  World Objects
# =========================
class WorldObject:
    """Base class for any object placed in the world."""
    def __init__(self, x: int, y: int, z: int, tier: int, template: WorldObjectTemplate):
        if tier <= 0 or tier > template.max_tier:
            raise ValueError("Tier exceeds template max tier or below 1.")
        self.x = x
        self.y = y
        self.z = z
        self.tier = tier
        self.template = template

        self.inventory_size = template.inventory_size
        self.inventory = [None] * self.inventory_size

        self.state = MachineState.IDLE
        self.state_reason = None

    @property
    def pos(self) -> Tuple[int, int, int]:
        return (self.x, self.y, self.z)

    def add_itemstack(self, stack: ItemStack) -> bool:
        """Add a stack to this object's inventory, merging when possible."""
        # Try to merge with existing stacks
        for existing in self.inventory:
            if existing and existing.can_merge(stack):
                overflow = existing.merge(stack)
                if overflow is None:
                    return True
                stack = overflow

        # Place in empty slot
        for i in range(self.inventory_size):
            if self.inventory[i] is None:
                self.inventory[i] = stack
                return True

        return False

    def remove_one_stack(self) -> Optional[ItemStack]:
        """Remove the first non‑empty stack from inventory."""
        for i in range(self.inventory_size):
            if self.inventory[i] is not None:
                stack = self.inventory[i]
                self.inventory[i] = None
                return stack
        return None

    def set_state(self, state: MachineState, reason: Optional[str] = None):
        self.state = state
        self.state_reason = reason

    def get_status(self) -> Dict:
        return {
            "type": self.__class__.__name__,
            "position": self.pos,
            "tier": self.tier,
            "state": self.state.value,
            "reason": self.state_reason
        }

    def get_inventory_summary(self) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for stack in self.inventory:
            if stack:
                name = stack.item.item_name
                summary[name] = summary.get(name, 0) + stack.amount
        return summary

    def tick(self):
        """Override in subclasses."""
        pass


class Box(WorldObject):
    """Simple storage box."""
    pass


class Belt(WorldObject):
    """Moves items from input to output direction."""
    def __init__(self, x: int, y: int, z: int, tier: int,
                 template: BeltTemplate,
                 input_direction: int, output_direction: int):
        super().__init__(x, y, z, tier, template)
        self.input_direction = input_direction
        self.output_direction = output_direction

        speed = template.base_movement_speed
        self.input_interval = max(1, speed // tier)
        self.output_interval = max(1, speed // tier)

        self._input_progress = 0
        self._output_progress = 0

    def get_progress(self) -> float:
        return max(self._input_progress / self.input_interval,
                   self._output_progress / self.output_interval)

    def tick(self):
        # Input phase
        in_dx, in_dy, in_dz = DIRECTION_OFFSETS[self.input_direction]
        input_obj = get_object_at(self.x + in_dx, self.y + in_dy, self.z + in_dz)

        if self.inventory[0] is None:
            if input_obj is None:
                self.set_state(MachineState.STARVED_INPUT, "No input object")
                self._input_progress = 0
            else:
                self._input_progress += 1
                self.set_state(MachineState.WORKING, "Pulling item")
                if self._input_progress >= self.input_interval:
                    stack = input_obj.remove_one_stack()
                    if stack:
                        self.inventory[0] = stack
                    self._input_progress = 0
        else:
            self._input_progress = 0

        # Output phase
        out_dx, out_dy, out_dz = DIRECTION_OFFSETS[self.output_direction]
        output_obj = get_object_at(self.x + out_dx, self.y + out_dy, self.z + out_dz)

        if self.inventory[0] is not None:
            if output_obj is None:
                self.set_state(MachineState.BLOCKED_OUTPUT, "No output object")
                self._output_progress = 0
            else:
                self._output_progress += 1
                self.set_state(MachineState.WORKING, "Pushing item")
                if self._output_progress >= self.output_interval:
                    stack = self.inventory[0]
                    if output_obj.add_itemstack(stack):
                        self.inventory[0] = None
                    else:
                        self.set_state(MachineState.BLOCKED_OUTPUT, "Output full")
                    self._output_progress = 0
        else:
            self._output_progress = 0


class Producer(WorldObject):
    """Produces a single item type at a constant rate."""
    def __init__(self, x: int, y: int, z: int, tier: int, template: ProducerTemplate):
        super().__init__(x, y, z, tier, template)
        self._interval = max(1, template.base_production_time // tier)
        self._tick_counter = 0

    def get_progress(self) -> float:
        return self._tick_counter / self._interval

    def tick(self):
        self._tick_counter += 1
        if self._tick_counter < self._interval:
            self.set_state(MachineState.WORKING, "Producing...")
            return

        self._tick_counter = 0
        produced = ItemStack(self.template.produced_item, 1)

        if self.inventory[0] is None:
            self.inventory[0] = produced
            self.set_state(MachineState.WORKING, "Produced item")
            return

        existing = self.inventory[0]
        if existing.can_merge(produced):
            overflow = existing.merge(produced)
            if overflow:
                self.set_state(MachineState.BLOCKED_OUTPUT, "Inventory full")
            else:
                self.set_state(MachineState.WORKING, "Produced item")
        else:
            self.set_state(MachineState.BLOCKED_OUTPUT, "Wrong item in slot")


class Crafter(WorldObject):
    """Crafts recipes using inputs and produces outputs."""
    def __init__(self, x: int, y: int, z: int, tier: int, template: CrafterTemplate):
        super().__init__(x, y, z, tier, template)
        self.output_inventory = [None] * template.output_inventory_size
        self._current_recipe = None
        self._craft_progress = 0
        self.required_time = 0

    def remove_one_stack(self) -> Optional[ItemStack]:
        """Remove from output inventory first (belts pull from output)."""
        for i, stack in enumerate(self.output_inventory):
            if stack is not None:
                self.output_inventory[i] = None
                return stack
        return None

    def add_output_stack(self, stack: ItemStack) -> bool:
        """Add a stack to the output inventory."""
        # Merge
        for existing in self.output_inventory:
            if existing and existing.can_merge(stack):
                overflow = existing.merge(stack)
                if overflow is None:
                    return True
                stack = overflow

        # Empty slot
        for i in range(len(self.output_inventory)):
            if self.output_inventory[i] is None:
                self.output_inventory[i] = stack
                return True
        return False

    def _select_recipe(self) -> Optional[Recipe]:
        for recipe in self.template.recipes:
            if recipe.can_craft(self.inventory):
                return recipe
        return None

    def _can_accept_output(self, stack: ItemStack) -> bool:
        """Check if the output inventory can accept the stack."""
        # Copy for simulation
        temp_inv = [s if s is None else ItemStack(s.item, s.amount)
                    for s in self.output_inventory]
        for existing in temp_inv:
            if existing and existing.can_merge(stack):
                overflow = existing.merge(stack)
                if overflow is None:
                    return True
                stack = overflow
        for s in temp_inv:
            if s is None:
                return True
        return False

    def get_progress(self) -> float:
        if self.required_time == 0:
            return 0.0
        return self._craft_progress / self.required_time

    def get_output_summary(self) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for stack in self.output_inventory:
            if stack:
                name = stack.item.item_name
                summary[name] = summary.get(name, 0) + stack.amount
        return summary

    def tick(self):
        # Select recipe if none
        if self._current_recipe is None:
            recipe = self._select_recipe()
            if recipe:
                self._current_recipe = recipe
                self._craft_progress = 0
                self.required_time = max(1, (recipe.base_crafting_time +
                                             self.template.base_crafting_delay) // self.tier)
            else:
                self.set_state(MachineState.STARVED_INPUT, "Missing recipe inputs")
                return

        self._craft_progress += 1
        self.set_state(MachineState.WORKING,
                       f"Crafting {self._current_recipe.name}")

        if self._craft_progress < self.required_time:
            return

        recipe = self._current_recipe

        # Verify inputs still present
        if not recipe.can_craft(self.inventory):
            self.set_state(MachineState.STARVED_INPUT,
                           "Inputs removed mid‑craft")
            self._reset_crafting()
            return

        # Verify output space
        for stack in recipe.outputs:
            if not self._can_accept_output(stack):
                self.set_state(MachineState.BLOCKED_OUTPUT,
                               "Output inventory full")
                return

        # Perform craft
        recipe.craft(self.inventory)
        for stack in recipe.outputs:
            self.add_output_stack(ItemStack(stack.item, stack.amount))

        self.set_state(MachineState.WORKING,
                       f"Completed {recipe.name}")
        self._reset_crafting()

    def _reset_crafting(self):
        self._current_recipe = None
        self._craft_progress = 0
        self.required_time = 0


class Researcher(WorldObject):
    """Performs research to unlock new templates."""
    def __init__(self, x: int, y: int, z: int, tier: int, template: ResearcherTemplate):
        super().__init__(x, y, z, tier, template)
        self._current_research: Optional[Research] = None
        self._progress = 0
        self.required_time = 0

    def _select_research(self, unlocked_names: List[str]) -> Optional[Research]:
        for research in self.template.researches:
            # Already unlocked?
            if research.name in unlocked_names:
                continue
            # Dependencies met?
            if any(dep not in unlocked_names for dep in research.dependencies):
                continue
            # Inputs available?
            if self._has_inputs(research):
                return research
        return None

    def _has_inputs(self, research: Research) -> bool:
        for inp in research.inputs:
            total = 0
            for stack in self.inventory:
                if stack and inp.matches(stack):
                    total += stack.amount
            if total < inp.amount:
                return False
        return True

    def _consume_inputs(self, research: Research):
        for inp in research.inputs:
            remaining = inp.amount
            for i, stack in enumerate(self.inventory):
                if stack and inp.matches(stack):
                    remove = min(stack.amount, remaining)
                    stack.amount -= remove
                    remaining -= remove
                    if stack.amount == 0:
                        self.inventory[i] = None
                    if remaining == 0:
                        break

    def tick(self, unlocked_names: List[str]):
        if self._current_research is None:
            research = self._select_research(unlocked_names)
            if research:
                self._current_research = research
                self._progress = 0
                self.required_time = max(1, (research.time +
                                             self.template.base_research_delay) // self.tier)
            else:
                self.set_state(MachineState.STARVED_INPUT, "No research available")
                return

        self._progress += 1
        self.set_state(MachineState.WORKING,
                       f"Researching {self._current_research.name}")

        if self._progress < self.required_time:
            return

        research = self._current_research

        # Re‑check inputs
        if not self._has_inputs(research):
            self.set_state(MachineState.STARVED_INPUT,
                           "Inputs removed mid‑research")
            self._reset()
            return

        self._consume_inputs(research)

        # Unlock will be handled by the Game after the tick
        self.set_state(MachineState.WORKING,
                       f"Completed {research.name}")
        self._reset()

    def _reset(self):
        self._current_research = None
        self._progress = 0
        self.required_time = 0


# =========================
#  World & Game Classes
# =========================
class World:
    """Manages the grid of world objects and the game tick."""
    def __init__(self):
        self._grid: Dict[Tuple[int, int, int], WorldObject] = {}

    def add_object(self, obj: WorldObject):
        pos = obj.pos
        if pos in self._grid:
            raise ValueError(f"Position {pos} already occupied")
        self._grid[pos] = obj

    def remove_object(self, obj: WorldObject):
        pos = obj.pos
        if pos in self._grid and self._grid[pos] is obj:
            del self._grid[pos]

    def get_object_at(self, x: int, y: int, z: int) -> Optional[WorldObject]:
        return self._grid.get((x, y, z))

    def tick(self):
        """Advance all objects by one tick."""
        # Iterate over a snapshot to allow modifications during tick
        for obj in list(self._grid.values()):
            obj.tick()

    def get_all_objects(self) -> List[WorldObject]:
        return list(self._grid.values())

    def __len__(self):
        return len(self._grid)


class Game:
    """
    Main game class holding world, directories, and global state
    (e.g., unlocked object names).
    """
    def __init__(self):
        # Directories
        self.item_dir = ItemDirectory("items.txt")
        self.recipe_dir = RecipeDirectory(self.item_dir, "recipes.txt")
        self.research_dir = ResearchDirectory(self.item_dir, "researches.txt")
        self.template_dir = WorldObjectTemplateDirectory(
            self.item_dir, self.recipe_dir, self.research_dir, "objects.txt"
        )

        # Resolve cross‑references
        self.research_dir.template_directory = self.template_dir
        self.research_dir.resolve_templates(self.template_dir)
        self.template_dir.resolve_researches()

        # World
        self.world = World()

        # Global unlock state: names of unlocked object templates and completed research
        self.unlocked_names: List[str] = []

    def create_object(self, template_name: str, x: int, y: int, z: int, tier: int,
                      **kwargs) -> WorldObject:
        """Factory method to create a world object and add it to the world."""
        template = self.template_dir.get_template(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        if tier <= 0 or tier > template.max_tier:
            raise ValueError(f"Tier {tier} invalid for template {template_name}")

        obj_type = template.obj_type
        if obj_type == "BOX":
            obj = Box(x, y, z, tier, template)
        elif obj_type == "BELT":
            if "input_direction" not in kwargs or "output_direction" not in kwargs:
                raise ValueError("Belt requires input_direction and output_direction")
            obj = Belt(x, y, z, tier, template,
                       kwargs["input_direction"], kwargs["output_direction"])
        elif obj_type == "PRODUCER":
            obj = Producer(x, y, z, tier, template)
        elif obj_type == "CRAFTER":
            obj = Crafter(x, y, z, tier, template)
        elif obj_type == "RESEARCHER":
            obj = Researcher(x, y, z, tier, template)
        else:
            raise ValueError(f"Unknown object type: {obj_type}")

        self.world.add_object(obj)
        return obj

    def tick(self):
        """Advance the simulation by one tick."""
        # First, tick all objects normally
        self.world.tick()

        # Then, handle research completions (unlocking)
        for obj in self.world.get_all_objects():
            if isinstance(obj, Researcher) and obj._current_research is not None:
                # If research completed in this tick, unlock its templates
                if obj._progress >= obj.required_time and obj._current_research is not None:
                    for tpl in obj._current_research.unlocked_templates:
                        if tpl.name not in self.unlocked_names:
                            self.unlocked_names.append(tpl.name)
                    # Also mark research itself as completed
                    if obj._current_research.name not in self.unlocked_names:
                        self.unlocked_names.append(obj._current_research.name)

    def save(self, filename: str = "saves.json"):
        """Save the current world state to a file."""
        save_data = {
            "objects": [self._serialize_object(obj) for obj in self.world.get_all_objects()],
            "unlocked_names": self.unlocked_names
        }

        # Load existing saves or create new list
        if os.path.exists(filename):
            with open(filename, "r") as f:
                all_saves = json.load(f)
        else:
            all_saves = []

        all_saves.append(save_data)

        with open(filename, "w") as f:
            json.dump(all_saves, f, indent=4)

        print(f"World saved. Total saves: {len(all_saves)}")

    def load(self, index: Optional[int] = None, filename: str = "saves.json"):
        """Load a world state from a save file."""
        if not os.path.exists(filename):
            raise LoadError("No save file found.")

        with open(filename, "r") as f:
            all_saves = json.load(f)

        if not all_saves:
            raise LoadError("Save file is empty.")

        if index is None:
            index = len(all_saves) - 1  # newest

        if index < 0 or index >= len(all_saves):
            raise IndexError("Invalid save index.")

        save_data = all_saves[index]

        # Clear current world and unlocked state
        self.world = World()
        self.unlocked_names = save_data.get("unlocked_names", [])

        # Rebuild objects
        for obj_data in save_data["objects"]:
            self._deserialize_object(obj_data)

    def _serialize_object(self, obj: WorldObject) -> Dict:
        """Convert a world object to a JSON‑serializable dict."""
        data = {
            "template": obj.template.name,
            "x": obj.x,
            "y": obj.y,
            "z": obj.z,
            "tier": obj.tier,
            "inventory": [self._serialize_itemstack(s) for s in obj.inventory],
            "state": obj.state.value,
            "state_reason": obj.state_reason
        }

        if isinstance(obj, Belt):
            data.update({
                "input_direction": obj.input_direction,
                "output_direction": obj.output_direction,
                "_input_progress": obj._input_progress,
                "_output_progress": obj._output_progress
            })
        elif isinstance(obj, Producer):
            data["_tick_counter"] = obj._tick_counter
        elif isinstance(obj, Crafter):
            data.update({
                "output_inventory": [self._serialize_itemstack(s) for s in obj.output_inventory],
                "_craft_progress": obj._craft_progress,
                "required_time": obj.required_time,
                "_current_recipe": obj._current_recipe.name if obj._current_recipe else None
            })
        elif isinstance(obj, Researcher):
            data.update({
                "_progress": obj._progress,
                "required_time": obj.required_time,
                "_current_research": obj._current_research.name if obj._current_research else None
            })

        return data

    def _deserialize_object(self, data: Dict):
        """Create a world object from saved data and add it to the world."""
        template = self.template_dir.get_template(data["template"])
        if not template:
            raise LoadError(f"Unknown template {data['template']}")

        kwargs = {}
        if template.obj_type == "BELT":
            kwargs["input_direction"] = data["input_direction"]
            kwargs["output_direction"] = data["output_direction"]

        obj = self.create_object(data["template"], data["x"], data["y"], data["z"],
                                 data["tier"], **kwargs)

        # Restore inventory
        obj.inventory = [
            self._deserialize_itemstack(s) for s in data["inventory"]
        ]
        obj.state = MachineState(data.get("state", MachineState.IDLE.value))
        obj.state_reason = data.get("state_reason")

        if isinstance(obj, Belt):
            obj._input_progress = data.get("_input_progress", 0)
            obj._output_progress = data.get("_output_progress", 0)
        elif isinstance(obj, Producer):
            obj._tick_counter = data.get("_tick_counter", 0)
        elif isinstance(obj, Crafter):
            obj.output_inventory = [
                self._deserialize_itemstack(s) for s in data.get("output_inventory", [])
            ]
            # Pad/trim to expected size
            while len(obj.output_inventory) < obj.template.output_inventory_size:
                obj.output_inventory.append(None)
            obj.output_inventory = obj.output_inventory[:obj.template.output_inventory_size]

            obj._craft_progress = data.get("_craft_progress", 0)
            obj.required_time = data.get("required_time", 0)
            recipe_name = data.get("_current_recipe")
            if recipe_name:
                obj._current_recipe = self.recipe_dir.get_recipe_by_name(recipe_name)
        elif isinstance(obj, Researcher):
            obj._progress = data.get("_progress", 0)
            obj.required_time = data.get("required_time", 0)
            research_name = data.get("_current_research")
            if research_name:
                obj._current_research = self.research_dir.get_research_by_name(research_name)

    @staticmethod
    def _serialize_itemstack(stack: Optional[ItemStack]) -> Optional[Dict]:
        if stack is None:
            return None
        return {"item": stack.item.item_name, "amount": stack.amount}

    def _deserialize_itemstack(self, data: Optional[Dict]) -> Optional[ItemStack]:
        if data is None:
            return None
        item = self.item_dir.get_item_by_name(data["item"])
        if not item:
            raise LoadError(f"Unknown item '{data['item']}' in save file")
        return ItemStack(item, data["amount"])


# =========================
#  Helper (for backward compatibility)
# =========================
def get_object_at(x: int, y: int, z: int) -> Optional[WorldObject]:
    """
    Temporary helper to allow existing belt code to work.
    In a full refactor, belts would get the world reference.
    This is a stop‑gap until we can inject the world into belts.
    """
    # This is a hack; ideally belts would receive the world instance.
    # For now, we rely on a global game instance.
    global _current_game
    if _current_game:
        return _current_game.world.get_object_at(x, y, z)
    return None


# Global reference to the active game (needed for belts' get_object_at)
_current_game: Optional[Game] = None


def main():
    """Example main function."""
    global _current_game
    game = Game()
    _current_game = game  # for belt helper

    # Example: create a box and a belt
    box_tpl = "SmallBox"   # assuming such template exists
    belt_tpl = "BasicBelt"
    try:
        game.create_object(box_tpl, 0, 0, 0, 1)
        game.create_object(belt_tpl, 1, 0, 0, 1,
                           input_direction=0, output_direction=2)
    except ValueError as e:
        print(f"Error creating object: {e}")

    # Run a few ticks
    for _ in range(10):
        game.tick()

    # Save
    game.save()

    # Load later
    game.load(index=0)  # load the first save


if __name__ == "__main__":
    main()

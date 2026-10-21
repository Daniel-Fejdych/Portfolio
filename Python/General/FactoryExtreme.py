"""Factory Builder — extended PyGame automation prototype.

Architecture (extended)
-----------------------
* Building *behaviour* lives in Python subclasses of Building. Each subclass
  is registered by the @register decorator, which stores it both in
  BUILDING_CLASSES (name -> class, used by the config loader) and in
  BUILDING_REGISTRY (key -> BuildingTemplate, used by the UI/menu).
* A BuildingTemplate is the UI-facing "menu entry": it holds the class, a
  display name, a colour, a hotkey, and a params dict that is splatted into
  the class constructor. This lets the config file register *variants*
  (Copper Miner, Gear Assembler, ...) without new Python code.
* Recipes are still pure data. The config file can add new recipes at runtime.
* Resources are declared for validation/documentation.
* Simulation is tick-based. Item.moved_tick guards against items moving
  multiple tiles in one frame through a belt chain.
* The build menu (TAB) is a modal overlay that lets the player pick both
  the building type and its orientation. It reads/writes game.selected_type
  and game.build_direction directly.
"""

import os
import sys
from dataclasses import dataclass, field

import pygame
from pygame.locals import *


# ========== Configuration ==========
TILE_SIZE = 48
GRID_WIDTH = 15
GRID_HEIGHT = 12
UI_HEIGHT = 80
SCREEN_WIDTH = TILE_SIZE * GRID_WIDTH
SCREEN_HEIGHT = TILE_SIZE * GRID_HEIGHT + UI_HEIGHT
FPS = 60

CONFIG_PATH = "factory_config.txt"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)
BLUE = (70, 130, 180)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)


# ========== Directions ==========
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRECTIONS = (UP, DOWN, LEFT, RIGHT)
DIR_NAMES = {UP: "Up", DOWN: "Down", LEFT: "Left", RIGHT: "Right"}


def opposite(direction):
    """Return the reverse of a direction vector."""
    return (-direction[0], -direction[1])


def right_of(direction):
    """Direction 90 degrees clockwise (screen coords, y-down)."""
    return (-direction[1], direction[0])


def left_of(direction):
    """Direction 90 degrees counter-clockwise (screen coords, y-down)."""
    return (direction[1], -direction[0])


# ========== Items & Recipes ==========
@dataclass
class Item:
    """A single unit of material travelling through the factory."""
    type: str
    moved_tick: int = -1   # simulation tick when the item last moved


@dataclass
class Recipe:
    """A crafting recipe: consume `inputs` (type -> count) over `craft_time` ticks."""
    output: str
    inputs: dict = field(default_factory=dict)
    craft_time: int = 40


# Default recipes — the config file may add more at runtime. Extending this
# dict (in code or from a file) never requires touching the Assembler class.
RECIPES = {
    "iron_plate": Recipe(output="iron_plate",
                         inputs={"iron_ore": 1},
                         craft_time=40),
}

# Declared resource names. Purely informational/for validation; item types
# are strings throughout the code, so you can use an undeclared resource
# without crashing — it just won't appear in the menu's tooltip.
RESOURCES = {"iron_ore", "iron_plate", "gear", "copper_ore", "copper_plate", "coal"}


# ========== Building registry ==========
# BUILDING_CLASSES maps a Python class *name* ("Belt") to the class itself.
# The config file references classes by this name.
BUILDING_CLASSES = {}

# BUILDING_REGISTRY maps a UI *key* ("belt", "miner_copper", ...) to a
# BuildingTemplate. This is what the menu and placement code iterate over.
BUILDING_REGISTRY = {}


@dataclass
class BuildingTemplate:
    """A menu entry: the behaviour class plus the presentation and params
    needed to instantiate it."""
    key: str
    cls: type
    display_name: str
    hotkey: int
    color: tuple
    params: dict = field(default_factory=dict)

    def create(self, pos, direction):
        """Instantiate the underlying Building with the stored params."""
        return self.cls(pos, direction, **self.params)


def register(cls):
    """Class decorator: register a Building subclass with a default template."""
    BUILDING_CLASSES[cls.__name__] = cls
    BUILDING_REGISTRY[cls.KEY] = BuildingTemplate(
        key=cls.KEY,
        cls=cls,
        display_name=cls.DISPLAY_NAME,
        hotkey=cls.HOTKEY,
        color=cls.COLOR,
        params={},
    )
    return cls


# ========== Drawing helpers ==========
def draw_arrow(surface, center, direction, color, length=None, width=3):
    """Draw a line + arrowhead from `center` pointing along `direction`."""
    if length is None:
        length = TILE_SIZE // 3
    end = (center[0] + direction[0] * length,
           center[1] + direction[1] * length)
    pygame.draw.line(surface, color, center, end, width)

    perp = (-direction[1], direction[0])
    ah = 6
    left = (end[0] - direction[0] * ah + perp[0] * ah,
            end[1] - direction[1] * ah + perp[1] * ah)
    right = (end[0] - direction[0] * ah - perp[0] * ah,
             end[1] - direction[1] * ah - perp[1] * ah)
    pygame.draw.polygon(surface, color, (end, left, right))


# ========== Buildings ==========
class Building:
    """Base class for everything the player can place on the grid."""

    KEY = "building"
    DISPLAY_NAME = "Building"
    HOTKEY = None
    COLOR = WHITE

    def __init__(self, pos, direction):
        self.pos = pos
        self.direction = direction   # primary facing / output direction

    def update(self, grid, tick):
        pass

    def can_accept(self, item, from_dir):
        return False

    def accept(self, item, from_dir):
        pass

    def draw(self, screen, rect):
        pygame.draw.rect(screen, self.COLOR, rect)


@register
class Belt(Building):
    """Carries one item at a time toward `direction`."""

    KEY = "belt"
    DISPLAY_NAME = "Belt"
    HOTKEY = K_1
    COLOR = GRAY

    def __init__(self, pos, direction):
        super().__init__(pos, direction)
        self.item = None

    def update(self, grid, tick):
        # Skip empty belts or items already moved this tick. This prevents an
        # item from being pushed along an entire belt chain in one frame.
        if self.item is None or self.item.moved_tick == tick:
            return
        neighbor = grid.get_neighbor(self.pos, self.direction)
        if neighbor and neighbor.can_accept(self.item, opposite(self.direction)):
            item = self.item
            neighbor.accept(item, opposite(self.direction))
            item.moved_tick = tick
            self.item = None

    def can_accept(self, item, from_dir):
        return self.item is None and from_dir == opposite(self.direction)

    def accept(self, item, from_dir):
        if self.can_accept(item, from_dir):
            self.item = item
            return True
        return False

    def draw(self, screen, rect):
        pygame.draw.rect(screen, self.COLOR, rect)
        draw_arrow(screen, rect.center, self.direction, WHITE)
        if self.item is not None:
            pygame.draw.circle(screen, YELLOW, rect.center, TILE_SIZE // 6)


@register
class Miner(Building):
    """Produces ore on a timer and pushes it out in `direction`."""

    KEY = "miner"
    DISPLAY_NAME = "Miner"
    HOTKEY = K_2
    COLOR = BROWN

    def __init__(self, pos, direction, produce_interval=60,
                 output_type="iron_ore"):
        super().__init__(pos, direction)
        self.produce_interval = produce_interval
        self.output_type = output_type
        self.timer = 0
        self.output_item = None

    def update(self, grid, tick):
        if self.output_item is None:
            if self.timer <= 0:
                self.output_item = Item(self.output_type)
                self.timer = self.produce_interval
            else:
                self.timer -= 1
        else:
            neighbor = grid.get_neighbor(self.pos, self.direction)
            if neighbor and neighbor.can_accept(self.output_item,
                                                opposite(self.direction)):
                item = self.output_item
                neighbor.accept(item, opposite(self.direction))
                item.moved_tick = tick
                self.output_item = None

    def can_accept(self, item, from_dir):
        return False

    def draw(self, screen, rect):
        pygame.draw.rect(screen, self.COLOR, rect)
        draw_arrow(screen, rect.center, self.direction, WHITE)
        pygame.draw.circle(screen, ORANGE, rect.center, TILE_SIZE // 5)
        if self.output_item is not None:
            pygame.draw.circle(screen, YELLOW,
                               (rect.centerx, rect.centery + TILE_SIZE // 4),
                               TILE_SIZE // 10)


@register
class Assembler(Building):
    """Runs a Recipe: accepts inputs from `input_dir`, pushes output `direction`."""

    KEY = "assembler"
    DISPLAY_NAME = "Assembler"
    HOTKEY = K_3
    COLOR = BLUE

    INPUT_CAPACITY = 10

    def __init__(self, pos, direction, recipe_name="iron_plate"):
        super().__init__(pos, direction)
        self.output_dir = direction
        self.input_dir = opposite(direction)
        self.recipe = RECIPES[recipe_name]

        self.input_inventory = {}
        self.output_item = None
        self.craft_timer = 0

    def _has_all_inputs(self):
        return all(self.input_inventory.get(t, 0) >= n
                   for t, n in self.recipe.inputs.items())

    def _consume_inputs(self):
        for t, n in self.recipe.inputs.items():
            self.input_inventory[t] -= n

    def _input_count(self):
        return sum(self.input_inventory.values())

    def update(self, grid, tick):
        # Crafting
        if self.craft_timer > 0:
            self.craft_timer -= 1
            if self.craft_timer == 0:
                self.output_item = Item(self.recipe.output)
        elif self.output_item is None and self._has_all_inputs():
            self._consume_inputs()
            self.craft_timer = self.recipe.craft_time

        # Pushing
        if self.output_item is not None:
            neighbor = grid.get_neighbor(self.pos, self.output_dir)
            if neighbor and neighbor.can_accept(self.output_item,
                                                opposite(self.output_dir)):
                item = self.output_item
                neighbor.accept(item, opposite(self.output_dir))
                item.moved_tick = tick
                self.output_item = None

    def can_accept(self, item, from_dir):
        if from_dir != self.input_dir:
            return False
        if item.type not in self.recipe.inputs:
            return False
        return self._input_count() < self.INPUT_CAPACITY

    def accept(self, item, from_dir):
        if self.can_accept(item, from_dir):
            self.input_inventory[item.type] = \
                self.input_inventory.get(item.type, 0) + 1
            return True
        return False

    def draw(self, screen, rect):
        pygame.draw.rect(screen, self.COLOR, rect)
        draw_arrow(screen, rect.center, self.output_dir, RED)
        draw_arrow(screen, rect.center, self.input_dir, WHITE)
        if self.output_item is not None:
            pygame.draw.circle(screen, YELLOW, rect.center, TILE_SIZE // 6)


# ---------------------------------------------------------------------
# New building types
# ---------------------------------------------------------------------

@register
class Splitter(Building):
    """Accepts from behind, alternates the output between forward and a
    perpendicular side direction (the one 90 degrees to the right)."""

    KEY = "splitter"
    DISPLAY_NAME = "Splitter"
    HOTKEY = K_4
    COLOR = (100, 180, 100)

    def __init__(self, pos, direction):
        super().__init__(pos, direction)
        self.input_dir = opposite(direction)
        self.side_dir = right_of(direction)
        self.output_item = None
        # Alternates on each successful push so half the items go to each
        # output when both are unblocked.
        self.next_is_side = False

    def update(self, grid, tick):
        if self.output_item is None:
            return
        if self.output_item.moved_tick == tick:
            return  # already moved this tick — don't shove it twice
        # Try the scheduled output first, then fall back to the other.
        first = self.side_dir if self.next_is_side else self.direction
        second = self.direction if self.next_is_side else self.side_dir
        for d in (first, second):
            neighbor = grid.get_neighbor(self.pos, d)
            if neighbor and neighbor.can_accept(self.output_item, opposite(d)):
                item = self.output_item
                neighbor.accept(item, opposite(d))
                item.moved_tick = tick
                self.output_item = None
                self.next_is_side = not self.next_is_side
                return

    def can_accept(self, item, from_dir):
        return self.output_item is None and from_dir == self.input_dir

    def accept(self, item, from_dir):
        if self.can_accept(item, from_dir):
            self.output_item = item
            return True
        return False

    def draw(self, screen, rect):
        pygame.draw.rect(screen, self.COLOR, rect)
        # Short input arrow (white) and two output arrows (red).
        draw_arrow(screen, rect.center, self.input_dir, WHITE,
                   length=TILE_SIZE // 5, width=2)
        draw_arrow(screen, rect.center, self.direction, RED,
                   length=TILE_SIZE // 4)
        draw_arrow(screen, rect.center, self.side_dir, RED,
                   length=TILE_SIZE // 4)
        if self.output_item is not None:
            pygame.draw.circle(screen, YELLOW, rect.center, TILE_SIZE // 6)


@register
class Merger(Building):
    """Accepts from three sides (back, left, right) and pushes everything
    forward along `direction`."""

    KEY = "merger"
    DISPLAY_NAME = "Merger"
    HOTKEY = K_5
    COLOR = (140, 100, 180)

    def __init__(self, pos, direction):
        super().__init__(pos, direction)
        self.input_dirs = (
            opposite(direction),
            left_of(direction),
            right_of(direction),
        )
        self.output_item = None

    def update(self, grid, tick):
        if self.output_item is None:
            return
        if self.output_item.moved_tick == tick:
            return
        neighbor = grid.get_neighbor(self.pos, self.direction)
        if neighbor and neighbor.can_accept(self.output_item,
                                            opposite(self.direction)):
            item = self.output_item
            neighbor.accept(item, opposite(self.direction))
            item.moved_tick = tick
            self.output_item = None

    def can_accept(self, item, from_dir):
        return self.output_item is None and from_dir in self.input_dirs

    def accept(self, item, from_dir):
        if self.can_accept(item, from_dir):
            self.output_item = item
            return True
        return False

    def draw(self, screen, rect):
        pygame.draw.rect(screen, self.COLOR, rect)
        # Output arrow (red) forward, short white arrows for each input.
        draw_arrow(screen, rect.center, self.direction, RED)
        for d in self.input_dirs:
            draw_arrow(screen, rect.center, d, WHITE,
                       length=TILE_SIZE // 5, width=2)
        if self.output_item is not None:
            pygame.draw.circle(screen, YELLOW, rect.center, TILE_SIZE // 6)


@register
class Chest(Building):
    """Passive storage. Accepts from any side until `capacity` is reached."""

    KEY = "chest"
    DISPLAY_NAME = "Chest"
    HOTKEY = K_6
    COLOR = (180, 140, 80)

    def __init__(self, pos, direction, capacity=20):
        super().__init__(pos, direction)
        self.capacity = capacity
        self.contents = {}

    def _count(self):
        return sum(self.contents.values())

    def can_accept(self, item, from_dir):
        return self._count() < self.capacity

    def accept(self, item, from_dir):
        if self.can_accept(item, from_dir):
            self.contents[item.type] = self.contents.get(item.type, 0) + 1
            return True
        return False

    def draw(self, screen, rect):
        pygame.draw.rect(screen, self.COLOR, rect)
        # Lid across the top third + a little knob.
        lid_h = TILE_SIZE // 3
        darker = tuple(max(0, c - 40) for c in self.COLOR)
        pygame.draw.rect(screen, darker,
                         (rect.x, rect.y, rect.width, lid_h))
        pygame.draw.line(screen, BLACK,
                         (rect.left, rect.y + lid_h),
                         (rect.right, rect.y + lid_h), 2)
        pygame.draw.circle(screen, YELLOW,
                           (rect.centerx, rect.y + lid_h), 3)


@register
class Sink(Building):
    """Void: destroys any item pushed into it. Useful as a disposal point."""

    KEY = "sink"
    DISPLAY_NAME = "Sink"
    HOTKEY = K_7
    COLOR = (60, 60, 60)

    def can_accept(self, item, from_dir):
        return True   # always hungry

    def accept(self, item, from_dir):
        return True   # item is destroyed here

    def draw(self, screen, rect):
        pygame.draw.rect(screen, self.COLOR, rect)
        # Big white X communicates "destroy".
        pygame.draw.line(screen, WHITE,
                         (rect.left + 8, rect.top + 8),
                         (rect.right - 8, rect.bottom - 8), 3)
        pygame.draw.line(screen, WHITE,
                         (rect.left + 8, rect.bottom - 8),
                         (rect.right - 8, rect.top + 8), 3)


# ========== Grid ==========
class Grid:
    """2-D container of building placements with neighbor lookup."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [[None] * width for _ in range(height)]

    def in_bounds(self, col, row):
        return 0 <= col < self.width and 0 <= row < self.height

    def get(self, col, row):
        return self.cells[row][col] if self.in_bounds(col, row) else None

    def set(self, col, row, building):
        if self.in_bounds(col, row):
            self.cells[row][col] = building

    def get_neighbor(self, pos, direction):
        return self.get(pos[0] + direction[0], pos[1] + direction[1])

    def buildings(self):
        return [b for row in self.cells for b in row if b is not None]


# ========== Configuration file loader ==========
# The default config is written to disk on first run. Editing it lets you
# add resources, recipes, and building variants without touching Python.
DEFAULT_CONFIG = """\
# =====================================================================
# Factory Builder configuration file
# ---------------------------------------------------------------------
# Lines starting with '#' are comments. Blank lines are ignored.
# Sections are marked with [section_name].
# =====================================================================

# ---------------------------------------------------------------------
# RESOURCES
# Each line is a resource/item-type name. Resources are purely
# informational — item types are strings — but declaring them documents
# what your factory handles.
# ---------------------------------------------------------------------
[resources]
iron_ore
iron_plate
gear
copper_ore
copper_plate
coal

# ---------------------------------------------------------------------
# RECIPES
# Format:  <name>: output=<item>, input=<item>:<count>, time=<ticks>
# Multiple 'input=' entries are allowed (one per ingredient).
# ---------------------------------------------------------------------
[recipes]
iron_plate:     output=iron_plate,   input=iron_ore:1,    time=40
gear:           output=gear,         input=iron_plate:2,  time=60
copper_plate:   output=copper_plate, input=copper_ore:1,  time=40

# ---------------------------------------------------------------------
# BUILDINGS
# Format:  <key>: class=<ClassName>, display=<name>, color=<r,g,b>,
#                 hotkey=<key>, <param>=<value>, ...
#
# <ClassName> must be one of: Belt, Miner, Assembler, Splitter,
# Merger, Chest, Sink.
#
# Extra params are passed to the class __init__. Per class:
#   Belt:       (none)
#   Miner:      produce_interval=<ticks>, output_type=<item>
#   Assembler:  recipe_name=<recipe key>
#   Splitter:   (none)
#   Merger:     (none)
#   Chest:      capacity=<n>
#   Sink:       (none)
#
# The <key> identifies the entry in the menu. You can define *multiple*
# entries using the same class to make variants (e.g. copper miner).
# ---------------------------------------------------------------------
[buildings]
belt:           class=Belt,      display=Belt,         color=128,128,128, hotkey=1
miner:          class=Miner,     display=Miner,        color=139,69,19,   hotkey=2, output_type=iron_ore,   produce_interval=60
assembler:      class=Assembler, display=Assembler,    color=70,130,180,  hotkey=3, recipe_name=iron_plate
splitter:       class=Splitter,  display=Splitter,     color=100,180,100, hotkey=4
merger:         class=Merger,    display=Merger,       color=140,100,180, hotkey=5
chest:          class=Chest,     display=Chest,        color=180,140,80,  hotkey=6, capacity=20
sink:           class=Sink,      display=Sink,         color=60,60,60,    hotkey=7

# Variants — same behaviour classes, different parameters.
miner_copper:   class=Miner,     display=Copper Miner, color=200,120,60,  hotkey=8, output_type=copper_ore, produce_interval=80
assembler_gear: class=Assembler, display=Gear Asm,     color=90,150,220,  hotkey=9, recipe_name=gear
"""


def ensure_config_file(path):
    """Create the default config if it does not already exist."""
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG)


def _coerce(value):
    """Best-effort conversion of a config value to bool/int/float/string."""
    v = value.strip()
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


def _parse_hotkey(value):
    """Accept '1', 'a', or 'K_1' and return the pygame keycode."""
    v = value.strip()
    if not v.startswith("K_"):
        v = "K_" + v
    key = getattr(pygame, v, None)
    if key is None:
        raise ValueError(f"Unknown pygame key: {value}")
    return key


def _parse_recipe_line(line):
    """Parse one `[recipes]` line and register the resulting Recipe."""
    name, rest = line.split(":", 1)
    name = name.strip()
    output = None
    inputs = {}
    time = 40
    for part in (p.strip() for p in rest.split(",")):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        k, v = k.strip(), v.strip()
        if k == "output":
            output = v
        elif k == "input":
            itype, count = v.split(":", 1)
            itype = itype.strip()
            inputs[itype] = inputs.get(itype, 0) + int(count.strip())
        elif k == "time":
            time = int(v)
    if output is None:
        raise ValueError(f"Recipe '{name}' is missing an output")
    RECIPES[name] = Recipe(output=output, inputs=inputs, craft_time=time)


def _parse_building_line(line):
    """Parse one `[buildings]` line and register a BuildingTemplate."""
    key, rest = line.split(":", 1)
    key = key.strip()
    class_name = None
    display = None
    color = None
    hotkey = None
    params = {}

    for part in (p.strip() for p in rest.split(",")):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        k, v = k.strip(), v.strip()
        if k == "class":
            class_name = v
        elif k == "display":
            display = v
        elif k == "color":
            color = tuple(int(x) for x in v.split(","))
        elif k == "hotkey":
            hotkey = _parse_hotkey(v)
        else:
            params[k] = _coerce(v)

    if class_name is None:
        raise ValueError(f"Building '{key}' is missing a class=... field")
    if class_name not in BUILDING_CLASSES:
        raise ValueError(
            f"Building '{key}' references unknown class '{class_name}'. "
            f"Known: {sorted(BUILDING_CLASSES)}"
        )
    cls = BUILDING_CLASSES[class_name]
    BUILDING_REGISTRY[key] = BuildingTemplate(
        key=key,
        cls=cls,
        display_name=display if display is not None else cls.DISPLAY_NAME,
        hotkey=hotkey if hotkey is not None else cls.HOTKEY,
        color=color if color is not None else cls.COLOR,
        params=params,
    )


def load_config(path):
    """Load resources, recipes, and building templates from a text file.

    Recipes and buildings that already exist are *replaced*; new ones are
    *added*. This lets a config file extend the default set without having
    to know everything that ships with the game.
    """
    section = None
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip().lower()
                continue
            try:
                if section == "resources":
                    RESOURCES.add(line)
                elif section == "recipes":
                    _parse_recipe_line(line)
                elif section == "buildings":
                    _parse_building_line(line)
            except Exception as exc:
                print(f"[config] skipping line in [{section}]: "
                      f"{line!r} ({exc})")


# ========== Popup build menu ==========
class BuildMenu:
    """Modal overlay that lets the player pick a building type AND an
    orientation. It reads/writes the owning game's `selected_type` and
    `build_direction` directly — no sync code required.
    """

    def __init__(self, font, big_font, game):
        self.font = font
        self.big_font = big_font
        self.game = game
        self.open = False
        self.panel_rect = None
        self.type_buttons = []      # list of (key, rect)
        self.dir_buttons = []       # list of (direction, rect)
        self.close_button = None

    def open_menu(self):
        self.open = True
        self._layout()

    def close_menu(self):
        self.open = False

    def _layout(self):
        """Compute the panel size and all button rects from the current
        BUILDING_REGISTRY (which may have grown since the game started)."""
        entries = list(BUILDING_REGISTRY.items())
        if not entries:
            self.panel_rect = pygame.Rect(0, 0, 200, 100)
            self.type_buttons = []
            self.dir_buttons = []
            self.close_button = pygame.Rect(0, 0, 0, 0)
            return

        # Pick a column count that keeps the panel on-screen.
        cols = max(3, min(4, (len(entries) + 2) // 3))
        rows = (len(entries) + cols - 1) // cols
        btn_w, btn_h = 160, 64
        pad = 10

        title_h = 44
        dir_section_h = 90
        close_h = 50

        content_w = cols * btn_w + (cols - 1) * pad
        panel_w = max(content_w + 2 * pad, 400)
        panel_h = title_h + rows * (btn_h + pad) + dir_section_h + close_h + pad

        px = (SCREEN_WIDTH - panel_w) // 2
        py = (SCREEN_HEIGHT - UI_HEIGHT - panel_h) // 2
        # Clamp so the panel is fully visible even with a long config file.
        py = max(5, min(py, SCREEN_HEIGHT - UI_HEIGHT - panel_h - 5))
        self.panel_rect = pygame.Rect(px, py, panel_w, panel_h)

        # Building-type grid.
        self.type_buttons = []
        start_x = px + pad + (panel_w - 2 * pad - content_w) // 2
        start_y = py + title_h
        for i, (key, _tpl) in enumerate(entries):
            c, r = i % cols, i // cols
            rect = pygame.Rect(start_x + c * (btn_w + pad),
                               start_y + r * (btn_h + pad),
                               btn_w, btn_h)
            self.type_buttons.append((key, rect))

        # Direction row.
        dir_y = start_y + rows * (btn_h + pad) + 15
        dir_size = 46
        total_dirs_w = 4 * dir_size + 3 * pad
        dirs_x = px + (panel_w - total_dirs_w) // 2
        self.dir_buttons = []
        for i, d in enumerate(DIRECTIONS):
            rect = pygame.Rect(dirs_x + i * (dir_size + pad),
                               dir_y, dir_size, dir_size)
            self.dir_buttons.append((d, rect))

        self.close_button = pygame.Rect(px + panel_w - 100,
                                        py + panel_h - 42, 88, 32)

    def handle_event(self, event):
        """Process one event while the menu is open. Always consumes it."""
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                self.close_menu()
                return True
            if event.key in (K_RETURN, K_TAB, K_SPACE):
                self.close_menu()
                return True
            if event.key == K_r:
                self.game.rotate_build_direction()
                return True
            # Hotkeys still work inside the menu — convenient for power users.
            for key, tpl in BUILDING_REGISTRY.items():
                if tpl.hotkey is not None and event.key == tpl.hotkey:
                    self.game.selected_type = key
                    return True
            return True

        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for key, r in self.type_buttons:
                if r.collidepoint(mx, my):
                    self.game.selected_type = key
                    return True
            for d, r in self.dir_buttons:
                if r.collidepoint(mx, my):
                    self.game.build_direction = d
                    return True
            if self.close_button.collidepoint(mx, my):
                self.close_menu()
                return True
            if not self.panel_rect.collidepoint(mx, my):
                # Click outside the panel closes the menu.
                self.close_menu()
                return True
            return True

        return True   # swallow everything else while modal

    def draw(self, screen):
        if not self.open:
            return

        # Dim the world behind the menu.
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        # Panel background + border.
        pygame.draw.rect(screen, (35, 35, 45), self.panel_rect)
        pygame.draw.rect(screen, (220, 220, 220), self.panel_rect, 2)

        # Title.
        title = self.big_font.render("Build Menu", True, WHITE)
        screen.blit(title, (self.panel_rect.x + 15, self.panel_rect.y + 10))

        # Building-type buttons.
        for key, r in self.type_buttons:
            tpl = BUILDING_REGISTRY[key]
            selected = (key == self.game.selected_type)
            bg = (70, 120, 80) if selected else (55, 55, 65)
            pygame.draw.rect(screen, bg, r)
            pygame.draw.rect(screen, WHITE if selected else tpl.color, r, 2)

            swatch = pygame.Rect(r.x + 6, r.y + 6, 22, 22)
            pygame.draw.rect(screen, tpl.color, swatch)
            pygame.draw.rect(screen, WHITE, swatch, 1)

            name_surf = self.font.render(tpl.display_name, True, WHITE)
            screen.blit(name_surf, (r.x + 34, r.y + 8))

            if tpl.hotkey is not None:
                hk = pygame.key.name(tpl.hotkey).upper()
                hk_surf = self.font.render(f"[{hk}]", True, (220, 200, 100))
                screen.blit(hk_surf, (r.x + 34, r.y + 32))

        # Direction label + buttons.
        if self.dir_buttons:
            lbl_y = self.dir_buttons[0][1].y - 22
            lbl = self.font.render("Direction (R cycles):",
                                   True, (200, 200, 200))
            screen.blit(lbl, (self.panel_rect.x + 15, lbl_y))

        for d, r in self.dir_buttons:
            selected = (d == self.game.build_direction)
            bg = (70, 120, 80) if selected else (55, 55, 65)
            pygame.draw.rect(screen, bg, r)
            pygame.draw.rect(screen, WHITE, r, 2)
            draw_arrow(screen, r.center, d, WHITE, length=14, width=3)

        # Close button.
        pygame.draw.rect(screen, (100, 50, 50), self.close_button)
        pygame.draw.rect(screen, WHITE, self.close_button, 1)
        close_txt = self.font.render("Close", True, WHITE)
        screen.blit(close_txt,
                    (self.close_button.centerx - close_txt.get_width() // 2,
                     self.close_button.centery - close_txt.get_height() // 2))


# ========== Game ==========
class FactoryGame:
    """Owns game state, input handling, simulation stepping and rendering."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Factory Builder")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 22)
        self.big_font = pygame.font.SysFont(None, 30)

        self.grid = Grid(GRID_WIDTH, GRID_HEIGHT)
        self.tick = 0

        # Load resources / recipes / buildings from disk. If anything goes
        # wrong, the hard-coded defaults in this module stay in effect.
        try:
            ensure_config_file(CONFIG_PATH)
            load_config(CONFIG_PATH)
            self.status_text = f"Loaded {CONFIG_PATH}"
        except Exception as exc:
            self.status_text = f"Using defaults ({exc})"

        # Default selection — first key in the registry (belt by default).
        first_key = next(iter(BUILDING_REGISTRY), "belt")
        self.selected_type = first_key
        self.build_direction = RIGHT

        # The popup menu mutates selected_type / build_direction directly.
        self.menu = BuildMenu(self.font, self.big_font, self)

    # --- Input helpers ---
    def cell_from_mouse(self):
        mx, my = pygame.mouse.get_pos()
        if my >= SCREEN_HEIGHT - UI_HEIGHT:
            return None
        col, row = mx // TILE_SIZE, my // TILE_SIZE
        return (col, row) if self.grid.in_bounds(col, row) else None

    def place_building(self, col, row):
        if self.grid.get(col, row) is not None:
            return
        tpl = BUILDING_REGISTRY.get(self.selected_type)
        if tpl is None:
            return
        self.grid.set(col, row, tpl.create((col, row), self.build_direction))

    def remove_building(self, col, row):
        if self.grid.get(col, row) is not None:
            self.grid.set(col, row, None)

    def rotate_build_direction(self):
        idx = DIRECTIONS.index(self.build_direction)
        self.build_direction = DIRECTIONS[(idx + 1) % 4]
        self.status_text = f"Direction: {DIR_NAMES[self.build_direction]}"

    # --- Simulation ---
    def step_simulation(self):
        for building in self.grid.buildings():
            building.update(self.grid, self.tick)
        self.tick += 1

    # --- Rendering ---
    def draw_grid(self):
        grid_h = SCREEN_HEIGHT - UI_HEIGHT
        for x in range(0, SCREEN_WIDTH, TILE_SIZE):
            pygame.draw.line(self.screen, BLACK, (x, 0), (x, grid_h))
        for y in range(0, grid_h, TILE_SIZE):
            pygame.draw.line(self.screen, BLACK, (0, y), (SCREEN_WIDTH, y))

    def draw_buildings(self):
        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                b = self.grid.get(col, row)
                if b is not None:
                    b.draw(self.screen,
                           pygame.Rect(col * TILE_SIZE, row * TILE_SIZE,
                                       TILE_SIZE, TILE_SIZE))

    def draw_ui(self):
        ui_y = SCREEN_HEIGHT - UI_HEIGHT
        pygame.draw.rect(self.screen, GRAY,
                         pygame.Rect(0, ui_y, SCREEN_WIDTH, UI_HEIGHT))

        tpl = BUILDING_REGISTRY.get(self.selected_type)
        if tpl is not None:
            info = (f"Selected: {tpl.display_name} | "
                    f"Direction: {DIR_NAMES[self.build_direction]}")
        else:
            info = "No building selected"
        self.screen.blit(self.font.render(info, True, WHITE),
                         (10, ui_y + 10))
        self.screen.blit(self.font.render(self.status_text, True, WHITE),
                         (10, ui_y + 32))

        # Hotkey summary built from the registry — stays in sync automatically.
        entries = " | ".join(
            f"{pygame.key.name(t.hotkey)}:{t.display_name}"
            for t in BUILDING_REGISTRY.values() if t.hotkey is not None
        )
        instr = entries + " | TAB:Menu | R:Rotate | LMB:Place | RMB:Remove | ESC:Exit"
        self.screen.blit(self.font.render(instr, True, WHITE),
                         (10, ui_y + 55))

    # --- Main loop ---
    def handle_events(self):
        """Process all pending events; return False to quit."""
        for event in pygame.event.get():
            if event.type == QUIT:
                return False

            # ESC quits the game, unless the menu is open (it closes first).
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                if self.menu.open:
                    self.menu.close_menu()
                else:
                    return False
                continue

            # TAB toggles the popup menu.
            if event.type == KEYDOWN and event.key == K_TAB:
                if self.menu.open:
                    self.menu.close_menu()
                else:
                    self.menu.open_menu()
                continue

            # While the menu is open, let it consume events.
            if self.menu.open:
                self.menu.handle_event(event)
                continue

            if event.type == KEYDOWN:
                if event.key == K_r:
                    self.rotate_build_direction()
                    continue
                for key, tpl in BUILDING_REGISTRY.items():
                    if tpl.hotkey is not None and event.key == tpl.hotkey:
                        self.selected_type = key
                        self.status_text = f"{tpl.display_name} selected"
                        break

            elif event.type == MOUSEBUTTONDOWN:
                # Clicking anywhere in the UI strip opens the menu.
                if event.pos[1] >= SCREEN_HEIGHT - UI_HEIGHT:
                    if event.button == 1:
                        self.menu.open_menu()
                    continue
                cell = self.cell_from_mouse()
                if cell is None:
                    continue
                col, row = cell
                if event.button == 1:
                    self.place_building(col, row)
                elif event.button == 3:
                    self.remove_building(col, row)

        return True

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.step_simulation()

            self.screen.fill(WHITE)
            self.draw_grid()
            self.draw_buildings()
            self.draw_ui()
            # The menu draws last so it sits on top of everything.
            self.menu.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    FactoryGame().run()
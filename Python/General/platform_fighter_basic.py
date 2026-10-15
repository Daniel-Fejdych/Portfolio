"""A small PyGame platform-fighter prototype.

Controls:
    A / D       Move left / right
    W           Jump
    Space       Quick slash
    Left Shift  Heavy attack
    F1          Toggle hitbox debug overlay

Install PyGame with ``python -m pip install pygame`` before running this file.
"""

from __future__ import annotations

import random
from typing import Iterable, TypedDict

import pygame
from pygame import draw

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TILE_SIZE = 32
GRAVITY = 1_000
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
LIGHT_RED = (255, 100, 100)
BLUE = (0, 0, 200)
LIGHT_BLUE = (100, 100, 255)
BACKGROUND = (30, 30, 30)

# Simple string constants for the game's finite-state machine. Using plain
# strings keeps the prototype readable while still letting us switch on state
# in ``update`` and ``draw``.
STATE_PLAYING = "playing"
STATE_WON = "won"
STATE_LOST = "lost"



# Legend: # = solid tile, P = player, G = ground enemy,
#         F = flying enemy, C = charger, S = shooter, . = empty space.
def load_levels(filename) -> dict:
    """
    Loads any number of levels from a file into a dictionary.

    File format:
        level id
        row of level characters
        row of level characters
        ...
        next level id
        ...

    Returns:
        dict: {level_id: [row1, row2, ...], ...}
    """
    levels = {}
    current_id = None
    current_rows = []

    with open(filename, "r") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n\r")
            stripped = line.strip()

            # Blank lines separate/end levels — skip them
            if stripped == "":
                continue

            # An int signals a new level id
            if stripped.isnumeric():
                # Save the previous level, if any
                if current_id is not None:
                    levels[current_id] = current_rows
                current_id = int(stripped)
                current_rows = []
            else:
                # Otherwise it's a row of level tiles
                if current_id is None:
                    raise ValueError(
                        f"Found level data before any level id: {stripped!r}"
                    )
                current_rows.append(stripped)

    # Save the final level
    if current_id is not None:
        levels[current_id] = current_rows

    return levels

LEVELS = load_levels("levels.txt")

def chance_this_frame(probability_at_60_fps: float, dt: float) -> bool:
    """Roll a probability calibrated for 60 FPS without tying it to frame rate."""
    probability = max(0.0, min(1.0, probability_at_60_fps))
    # If several frames' worth of time pass at once, adjust the chance so the
    # average behaviour remains approximately the same as it is at 60 FPS.
    frame_adjusted_probability = 1.0 - (1.0 - probability) ** (dt * FPS)
    return random.random() < frame_adjusted_probability


class AttackDefinition(TypedDict, total=False):
    """Configuration fields shared by all character attack definitions."""

    offset: tuple[int, int]
    size: tuple[int, int]
    damage: int
    duration: float
    cooldown: float
    # Optional projectile velocity in pixels per second. The x component is
    # multiplied by the owner's facing direction when the attack is created.
    velocity: tuple[float, float]


# ---------------------------------------------------------------------------
# General attack definitions
# ---------------------------------------------------------------------------
PLAYER_ATTACKS: dict[str, AttackDefinition] = {
    "slash": {
        "offset": (30, -10),
        "size": (40, 20),
        "damage": 10,
        "duration": 0.2,
        "cooldown": 0.4,
    },
    "heavy": {
        "offset": (40, -15),
        "size": (50, 30),
        "damage": 20,
        "duration": 0.25,
        "cooldown": 0.8,
    },
}

GROUND_ENEMY_ATTACKS: dict[str, AttackDefinition] = {
    "slash": {
        "offset": (30, -10),
        "size": (40, 40),
        "damage": 10,
        "duration": 0.2,
        "cooldown": 0.4,
    },
}

FLYING_ENEMY_ATTACKS: dict[str, AttackDefinition] = {
    "slash": {
        "offset": (30, -10),
        "size": (40, 40),
        "damage": 10,
        "duration": 0.2,
        "cooldown": 0.4,
    },
}

CHARGER_ENEMY_ATTACKS: dict[str, AttackDefinition] = {
    "charge": {
        "offset": (35, -10),
        "size": (50, 20),
        "damage": 20,
        "duration": 0.2,
        "cooldown": 1.0,
    },
}

SHOOTER_ENEMY_ATTACKS: dict[str, AttackDefinition] = {
    "blast": {
        "offset": (50, -5),
        "size": (30, 10),
        "damage": 10,
        "duration": 3.0,
        "cooldown": 0.7,
        # Move forward in the direction the shooter is facing.
        "velocity": (400.0, 0.0),
    },
}


# ---------------------------------------------------------------------------
# Attacks
# ---------------------------------------------------------------------------
class Attack:
    """A short-lived hitbox that can damage each target at most once."""

    def __init__(
        self,
        owner: Entity,
        offset: tuple[int, int],
        size: tuple[int, int],
        damage: int,
        duration: float,
        velocity: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        self.owner = owner
        self.offset = offset
        self.size = size
        self.damage = damage
        self.remaining = duration
        self.hit_targets: set[Entity] = set()

        # Attacks with zero velocity stay attached to their owner. Attacks with
        # velocity detach immediately and travel as projectiles.
        self.follows_owner = velocity == (0.0, 0.0)
        self.velocity = pygame.Vector2(velocity[0] * owner.facing, velocity[1])
        self.position = self._owner_anchored_position()

    def _owner_anchored_position(self) -> pygame.Vector2:
        """Return the top-left position for a hitbox attached to the owner."""
        x = self.owner.rect.centerx + self.offset[0] * self.owner.facing

        # When facing left, the hitbox must extend to the left of its x anchor,
        # rather than starting at the anchor and extending back across the owner.
        if self.owner.facing < 0:
            x -= self.size[0]

        y = self.owner.rect.centery + self.offset[1]
        return pygame.Vector2(x, y)

    def get_rect(self) -> pygame.Rect:
        """Build a hitbox from the attack's current position."""
        return pygame.Rect(
            round(self.position.x),
            round(self.position.y),
            self.size[0],
            self.size[1],
        )

    def update(self, dt: float, entities: Iterable[Entity]) -> None:
        """Age the hitbox, move projectiles, and apply damage to new targets."""
        self.remaining -= dt
        if self.remaining <= 0:
            return

        if self.follows_owner:
            self.position = self._owner_anchored_position()
        else:
            self.position += self.velocity * dt

        hitbox = self.get_rect()

        for entity in entities:
            # Remember hits so a target does not lose health every frame while
            # standing inside one attack's active hitbox.
            if entity is self.owner or entity in self.hit_targets or entity.health <= 0:
                continue

            if hitbox.colliderect(entity.rect):
                # ``take_damage`` is a no-op when the target is invulnerable,
                # but we still record the hit so this particular hitbox does
                # not keep retrying every frame while it overlaps.
                entity.take_damage(self.damage)
                self.hit_targets.add(entity)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the hitbox outline as a simple visual debugging aid."""
        pygame.draw.rect(surface, WHITE, self.get_rect(), width=2)

    def alive(self) -> bool:
        """Return whether the attack still has active time remaining."""
        return self.remaining > 0


# ---------------------------------------------------------------------------
# World objects and moving entities
# ---------------------------------------------------------------------------
class Tile(pygame.sprite.Sprite):
    """A single solid block in the level."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect(topleft=(x, y))


class Entity(pygame.sprite.Sprite):
    """Shared movement, health, damage, and attack behaviour for characters."""

    # Default invulnerability window after a hit, in seconds. Subclasses (for
    # example, the player) can raise this so they are not shredded by multiple
    # overlapping attacks in a single frame. Enemies default to 0 to preserve
    # the original prototype's "every hit counts" feel.
    invuln_duration: float = 0.0

    def __init__(self, x: int, y: int, color: tuple[int, int, int], health: int) -> None:
        super().__init__()
        self.image = pygame.Surface((28, 28))
        self.color = color
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

        # Keep a floating-point position so slow movement is not lost when a
        # pygame.Rect truncates fractional pixel changes on every frame.
        self.position = pygame.Vector2(self.rect.topleft)
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False

        # Set during ``move`` when a horizontal collision occurs. Enemies use
        # this to detect that they are pressed against a wall and need to jump.
        self.blocked_horizontal = False

        self.health = health
        self.attacks: list[Attack] = []
        self.flash_timer = 0.0
        # Counts down while the entity is immune to further damage.
        self.invuln_timer = 0.0
        self.facing = 1  # 1 = right, -1 = left

        # Each attack definition contains its hitbox, damage, active time, and
        # cooldown. Subclasses fill this dictionary with their own moves.
        self.attack_defs: dict[str, AttackDefinition] = {}
        self.attack_cooldowns: dict[str, float] = {}

    def apply_gravity(self, dt: float) -> None:
        """Accelerate downward; callers can omit this for flying characters."""
        self.vel.y += GRAVITY * dt

    def move(
        self,
        tiles: Iterable[Tile],
        entities: Iterable[Entity],
        dt: float,
    ) -> None:
        """Move on each axis separately and resolve solid-object collisions."""
        tiles = tuple(tiles)
        entities = tuple(entities)

        # Update facing when horizontal movement is requested. Stationary
        # characters (such as the shooter) can set facing directly in update().
        if self.vel.x > 0:
            self.facing = 1
        elif self.vel.x < 0:
            self.facing = -1

        # Horizontal movement and collision resolution.
        self.position.x += self.vel.x * dt
        self.rect.x = round(self.position.x)
        horizontal_collision = False

        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel.x > 0:
                    self.rect.right = tile.rect.left
                    horizontal_collision = True
                elif self.vel.x < 0:
                    self.rect.left = tile.rect.right
                    horizontal_collision = True

        for entity in entities:
            if entity is not self and self.rect.colliderect(entity.rect):
                if self.vel.x > 0:
                    self.rect.right = entity.rect.left
                    horizontal_collision = True
                elif self.vel.x < 0:
                    self.rect.left = entity.rect.right
                    horizontal_collision = True

        # Expose "I hit something while trying to move horizontally" so that
        # ground-based AI (e.g. enemies that walk into walls) can react.
        self.blocked_horizontal = horizontal_collision

        # Preserve fractional movement between frames unless a collision has
        # snapped the rectangle to a whole-pixel boundary.
        if horizontal_collision:
            self.position.x = float(self.rect.x)

        # Vertical movement and collision resolution. Gravity-driven actors
        # land on both tiles and other characters, which sets on_ground.
        self.position.y += self.vel.y * dt
        self.rect.y = round(self.position.y)
        self.on_ground = False
        vertical_collision = False

        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel.y > 0:
                    self.rect.bottom = tile.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                    vertical_collision = True
                elif self.vel.y < 0:
                    self.rect.top = tile.rect.bottom
                    self.vel.y = 0
                    vertical_collision = True

        for entity in entities:
            if entity is not self and self.rect.colliderect(entity.rect):
                if self.vel.y > 0:
                    self.rect.bottom = entity.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                    vertical_collision = True
                elif self.vel.y < 0:
                    self.rect.top = entity.rect.bottom
                    self.vel.y = 0
                    vertical_collision = True

        if vertical_collision:
            self.position.y = float(self.rect.y)

    def try_attack(self, name: str, current_time: float) -> None:
        """Start an attack only if it exists and its cooldown has elapsed."""
        data = self.attack_defs.get(name)
        if data is None:
            return

        cooldown = data["cooldown"]
        last_attack_time = self.attack_cooldowns.get(name, float("-inf"))
        if current_time - last_attack_time < cooldown:
            return

        self.attack_cooldowns[name] = current_time
        self.attacks.append(
            Attack(
                owner=self,
                offset=data["offset"],
                size=data["size"],
                damage=data["damage"],
                duration=data["duration"],
                velocity=data.get("velocity", (0.0, 0.0)),
            )
        )

    def create_attack(self) -> None:
        """Create a simple default attack for callers that need one."""
        self.attacks.append(
            Attack(self, offset=(30, -10), size=(30, 20), damage=1, duration=0.2)
        )

    def take_damage(self, amount: int) -> bool:
        """Apply damage unless the target is dead, shielded, or invulnerable.

        Returns ``True`` only when the hit actually landed, which lets callers
        distinguish a real hit from one soaked by invulnerability frames.
        """
        if amount <= 0 or self.health <= 0 or self.invuln_timer > 0:
            return False
        self.health = max(0, self.health - amount)
        self.flash_timer = 0.1
        # Begin the i-frame window. Entities whose ``invuln_duration`` is 0
        # simply skip the window, preserving the original behaviour.
        self.invuln_timer = self.invuln_duration
        return True

    def update_flash(self, dt: float) -> None:
        """Animate hit flashes and invulnerability flicker, then restore colour."""
        self.flash_timer = max(0.0, self.flash_timer - dt)
        self.invuln_timer = max(0.0, self.invuln_timer - dt)

        if self.flash_timer > 0:
            # Solid white immediately after taking a hit.
            self.image.fill(WHITE)
        elif self.invuln_timer > 0:
            # Flicker between the entity's colour and a dimmed variant so the
            # player can see they are briefly immune to further hits.
            visible = int(self.invuln_timer * 20) % 2 == 0
            self.image.fill(self.color if visible else tuple(c // 2 for c in self.color))
        else:
            self.image.fill(self.color)

    def update_attacks(self, dt: float, entities: Iterable[Entity]) -> None:
        """Update active attacks and discard expired hitboxes."""
        for attack in self.attacks:
            attack.update(dt, entities)
        self.attacks = [attack for attack in self.attacks if attack.alive()]

    def draw_attacks(self, surface: pygame.Surface) -> None:
        """Render active hitboxes on top of the characters."""
        for attack in self.attacks:
            attack.draw(surface)


# ---------------------------------------------------------------------------
# Player character
# ---------------------------------------------------------------------------
class Player(Entity):
    # Give the player a short mercy window so a scrum of enemies cannot
    # dump all of their damage into one frame.
    invuln_duration = 0.5

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, GREEN, health=150)
        self.speed = 300
        self.jump_power = -500
        self.attack_defs = PLAYER_ATTACKS

    def update(
        self,
        tiles: Iterable[Tile],
        dt: float,
        entities: Iterable[Entity],
        current_time: float,
    ) -> None:
        keys = pygame.key.get_pressed()

        # Subtracting the two key states allows left and right to cancel out.
        horizontal_input = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        self.vel.x = horizontal_input * self.speed

        if keys[pygame.K_w] and self.on_ground:
            self.vel.y = self.jump_power

        # Holding an attack key repeats the move when its cooldown permits.
        if keys[pygame.K_SPACE]:
            self.try_attack("slash", current_time)
        if keys[pygame.K_LSHIFT]:
            self.try_attack("heavy", current_time)

        self.apply_gravity(dt)
        self.move(tiles, entities, dt)
        self.update_attacks(dt, entities)
        self.update_flash(dt)


# ---------------------------------------------------------------------------
# Enemy characters
# ---------------------------------------------------------------------------
class GroundEnemy(Entity):
    """A ground enemy that follows the player and occasionally jumps."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, RED, health=100)
        self.speed = 150
        self.attack_defs = GROUND_ENEMY_ATTACKS

    def update(
        self,
        tiles: Iterable[Tile],
        player: Player,
        dt: float,
        entities: Iterable[Entity],
        current_time: float,
    ) -> None:
        self.vel.x = self.speed if player.rect.centerx > self.rect.centerx else -self.speed

        # Jump either randomly or whenever the walk was stopped by a wall so
        # the enemy can hop over small obstacles instead of standing there.
        if self.on_ground and (self.blocked_horizontal or chance_this_frame(0.01, dt)):
            self.vel.y = -400
        if chance_this_frame(0.02, dt):
            self.try_attack("slash", current_time)

        self.apply_gravity(dt)
        self.move(tiles, entities, dt)
        self.update_attacks(dt, entities)
        self.update_flash(dt)


class FlyingEnemy(Entity):
    """A flying enemy that steers directly toward the player's position."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, BLUE, health=60)
        self.speed = 120
        self.attack_defs = FLYING_ENEMY_ATTACKS

    def update(
        self,
        tiles: Iterable[Tile],
        player: Player,
        dt: float,
        entities: Iterable[Entity],
        current_time: float,
    ) -> None:
        direction = pygame.Vector2(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery,
        )

        # A zero-length vector means the enemy is already at the target point.
        # In that case, leave its velocity at zero to avoid normalising it.
        if direction.length_squared() > 0:
            direction = direction.normalize()
        self.vel = direction * self.speed

        if chance_this_frame(0.03, dt):
            self.try_attack("slash", current_time)

        self.move(tiles, entities, dt)
        self.update_attacks(dt, entities)
        self.update_flash(dt)


class ChargerEnemy(Entity):
    """A tougher ground enemy with a stronger, slower charge attack."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, LIGHT_RED, health=120)
        self.speed = 200
        self.attack_defs = CHARGER_ENEMY_ATTACKS

    def update(
        self,
        tiles: Iterable[Tile],
        player: Player,
        dt: float,
        entities: Iterable[Entity],
        current_time: float,
    ) -> None:
        self.vel.x = self.speed if player.rect.centerx > self.rect.centerx else -self.speed

        # Same anti-stuck behaviour as GroundEnemy: if our walk into the player
        # was blocked by geometry, hop over the obstacle rather than pace.
        if self.on_ground and self.blocked_horizontal:
            self.vel.y = -400

        if chance_this_frame(0.02, dt):
            self.try_attack("charge", current_time)

        self.apply_gravity(dt)
        self.move(tiles, entities, dt)
        self.update_attacks(dt, entities)
        self.update_flash(dt)


class ShooterEnemy(Entity):
    """A stationary enemy that faces the player and fires ranged hitboxes."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, LIGHT_BLUE, health=80)
        self.attack_defs = SHOOTER_ENEMY_ATTACKS

    def update(
        self,
        tiles: Iterable[Tile],
        player: Player,
        dt: float,
        entities: Iterable[Entity],
        current_time: float,
    ) -> None:
        # This enemy does not use gravity or horizontal movement.
        self.vel.x = 0
        self.vel.y = 0
        self.facing = -1 if player.rect.centerx < self.rect.centerx else 1

        if chance_this_frame(0.03, dt):
            self.try_attack("blast", current_time)

        self.move(tiles, entities, dt)
        self.update_attacks(dt, entities)
        self.update_flash(dt)


# ---------------------------------------------------------------------------
# Game setup, level loading, and main loop
# ---------------------------------------------------------------------------
class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Platform Fighter")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 60)

        self.tiles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player: Player | None = None
        self.running = True

        # Finite-state machine replaces the old ``game_over`` boolean so we
        # can tell a loss apart from a win and display the right banner.
        self.state = STATE_PLAYING

        # Hitboxes are handy while building the game but visually noisy once
        # it is playable, so we default them on and let F1 toggle them.
        self.show_hitboxes = True

        self.elapsed_time = 0.0

        # Level progression is owned by the instance so reloads cannot leak
        # state through a module-level counter.
        self.current_level_id = 0
        self.next_level_id = 0
        self.transition_timer = 0.0

        self.load_level(LEVELS.get(self.current_level_id))

    def load_level(self, level: list[str]) -> None:
        """Build the tile map and characters from the level's character grid."""
        if not level:
            raise ValueError("The level cannot be empty.")

        # Wipe everything from the previous level. Without this, a reload
        # would stack the new tiles/enemies on top of the old ones.
        self.tiles.empty()
        self.enemies.empty()
        self.player = None
        self.elapsed_time = 0.0

        row_width = len(level[0])
        if any(len(row) != row_width for row in level):
            raise ValueError("Every row in the level must have the same width.")

        player_spawns = 0
        enemy_types = {
            "G": GroundEnemy,
            "F": FlyingEnemy,
            "C": ChargerEnemy,
            "S": ShooterEnemy,
        }

        for tile_y, row in enumerate(level):
            for tile_x, symbol in enumerate(row):
                x = tile_x * TILE_SIZE
                y = tile_y * TILE_SIZE

                if symbol == "#":
                    self.tiles.add(Tile(x, y))
                elif symbol == "P":
                    player_spawns += 1
                    self.player = Player(x, y)
                elif symbol in enemy_types:
                    self.enemies.add(enemy_types[symbol](x, y))
                elif symbol != ".":
                    raise ValueError(f"Unknown level symbol {symbol!r} at ({tile_x}, {tile_y}).")

        # Failing early is clearer than an AttributeError during the game loop.
        if player_spawns != 1:
            raise ValueError(f"The level must contain exactly one player spawn; found {player_spawns}.")

    def update(self, dt: float) -> None:
        """Advance gameplay by one frame unless the round has ended."""
        # After a win or loss, count down a short pause and then swap in the
        # queued level. Doing this in ``update`` (instead of blocking with
        # ``sleep`` inside ``draw``) keeps the window responsive and lets the
        # banner actually be presented before the level changes.
        if self.state in (STATE_WON, STATE_LOST):
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                if self.next_level_id in LEVELS:
                    self.current_level_id = self.next_level_id
                else:
                    # Ran past the last authored level; loop back to the start.
                    self.current_level_id = 0
                self.load_level(LEVELS[self.current_level_id])
                self.state = STATE_PLAYING
            return

        if self.state != STATE_PLAYING or self.player is None:
            return

        self.elapsed_time += dt
        # Use a snapshot so each actor sees the same entity list during this
        # frame, even if an enemy is removed after updates finish.
        entities = [self.player, *self.enemies.sprites()]
        self.player.update(self.tiles, dt, entities, self.elapsed_time)

        for enemy in tuple(self.enemies):
            enemy.update(self.tiles, self.player, dt, entities, self.elapsed_time)

        # Remove defeated enemies after all actors have completed their updates.
        for enemy in tuple(self.enemies):
            if enemy.health <= 0:
                self.enemies.remove(enemy)

        # A loss takes priority over a win in the unlikely case both occur on
        # the same frame (player and last enemy trade lethal blows).
        if self.player.health <= 0:
            self.state = STATE_LOST
            self.transition_timer = 2.0
            self.next_level_id = self.current_level_id  # retry the same level
        elif len(self.enemies) == 0:
            self.state = STATE_WON
            self.transition_timer = 2.0
            self.next_level_id = self.current_level_id + 1

    def draw(self) -> None:
        """Render the level, characters, active hitboxes, and a small HUD."""
        self.screen.fill(BACKGROUND)

        for tile in self.tiles:
            self.screen.blit(tile.image, tile.rect)

        characters: list[Entity] = []
        if self.player is not None:
            characters.append(self.player)
        characters.extend(self.enemies.sprites())

        for entity in characters:
            self.screen.blit(entity.image, entity.rect)
            # Only draw the debug hitboxes when the F1 overlay is enabled.
            if self.show_hitboxes:
                entity.draw_attacks(self.screen)

        if self.player is not None:
            health_text = self.font.render(f"Health: {self.player.health}", True, WHITE)
            enemies_text = self.font.render(f"Enemies: {len(self.enemies)}", True, WHITE)
            self.screen.blit(health_text, (12, 10))
            self.screen.blit(enemies_text, (12, 42))

        # Show the appropriate end-of-round banner. Both messages use the same
        # code path so it is easy to add more states later.
        if self.state == STATE_LOST:
            self._draw_centered_banner("GAME OVER", WHITE)
        elif self.state == STATE_WON:
            self._draw_centered_banner("VICTORY!", GREEN)

        pygame.display.flip()

    def _draw_centered_banner(self, message: str, color: tuple[int, int, int]) -> None:
        """Render a single large message centered on the screen."""
        text = self.large_font.render(message, True, color)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)

    def run(self) -> None:
        """Run the event, update, and render loop until the window is closed."""
        try:
            while self.running:
                dt = self.clock.tick(FPS) / 1000.0

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                        # Debug overlay toggle; handy while tuning hitboxes.
                        self.show_hitboxes = not self.show_hitboxes

                # Exit immediately instead of processing one extra frame after
                # the window-close event.
                if not self.running:
                    break

                self.update(dt)
                self.draw()
        finally:
            # Always release SDL resources, including when an exception occurs.
            pygame.quit()


def main() -> None:
    """Application entry point; importing this module does not launch the game."""
    Game().run()


if __name__ == "__main__":
    main()
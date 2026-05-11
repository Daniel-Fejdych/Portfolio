import pygame
import sys
import random

# ---------------- CONFIG ----------------
TILE_SIZE = 32
GRAVITY = 1000
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200)

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# ---------------- LEVEL ----------------
LEVEL = [
"........................",
"......................S.",
"..............F.........",
".................###....",
"....P...................",
"...........G........C...",
"########.###############",
"........................",
"........#...............",
"FFFFFF#FFCC#CCCCCCFFFFFF",
"...#.............###....",
"#SSSSS..................",
"GGGGGGGGGGGGGGGGGGGGGGGG",
"########################"
]

# ---------------- ATTACK ----------------
class Attack:
    def __init__(self, owner, offset, size, damage, duration):
        self.owner = owner
        self.offset = offset
        self.size = size
        self.damage = damage
        self.timer = duration

    def get_rect(self):
        return pygame.Rect(
            self.owner.rect.centerx + self.offset[0] * self.owner.facing,
            self.owner.rect.centery + self.offset[1],
            self.size[0],
            self.size[1]
        )

    def update(self, dt, entities):
        self.timer -= dt
        rect = self.get_rect()

        for entity in entities:
            if entity != self.owner and rect.colliderect(entity.rect):
                entity.take_damage(self.damage)

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.get_rect(), 2)

    def alive(self):
        return self.timer > 0

# ---------------- TILE ----------------
class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect(topleft=(x, y))

# ---------------- ENTITY ----------------
class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, color, health):
        super().__init__()
        self.image = pygame.Surface((28, 28))
        self.color = color
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False

        self.health = health
        self.attacks = []

        self.flash_timer = 0
        self.facing = 1  # 1 = right, -1 = left

        self.attack_cooldown = 0.5
        self.last_attack_time = 0
        self.attack_defs = {}
        self.attack_cooldowns = {}

    def apply_gravity(self, dt):
        self.vel.y += GRAVITY * dt

    def move(self, tiles, entities, dt):
        # Facing
        if self.vel.x > 0:
            self.facing = 1
        elif self.vel.x < 0:
            self.facing = -1

        # --- Horizontal ---
        self.rect.x += self.vel.x * dt

        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel.x > 0:
                    self.rect.right = tile.rect.left
                elif self.vel.x < 0:
                    self.rect.left = tile.rect.right

        for entity in entities:
            if entity != self and self.rect.colliderect(entity.rect):
                if self.vel.x > 0:
                    self.rect.right = entity.rect.left
                elif self.vel.x < 0:
                    self.rect.left = entity.rect.right

        # --- Vertical ---
        self.rect.y += self.vel.y * dt
        self.on_ground = False

        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if self.vel.y > 0:
                    self.rect.bottom = tile.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                elif self.vel.y < 0:
                    self.rect.top = tile.rect.bottom
                    self.vel.y = 0

        for entity in entities:
            if entity != self and self.rect.colliderect(entity.rect):
                if self.vel.y > 0:
                    self.rect.bottom = entity.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                elif self.vel.y < 0:
                    self.rect.top = entity.rect.bottom
                    self.vel.y = 0

    def try_attack(self, name, current_time):
        if name not in self.attack_defs:
            return

        cooldown = self.attack_defs[name]["cooldown"]

        if name not in self.attack_cooldowns:
            self.attack_cooldowns[name] = 0

        if current_time - self.attack_cooldowns[name] >= cooldown:
            self.attack_cooldowns[name] = current_time
            data = self.attack_defs[name]

            self.attacks.append(
                Attack(
                    self,
                    data["offset"],
                    data["size"],
                    data["damage"],
                    data["duration"]
                )
            )

    def create_attack(self):
        # Default attack (can override)
        offset = 30 * self.facing
        rect = pygame.Rect(
            self.rect.centerx + offset,
            self.rect.centery - 10,
            30, 20
        )
        self.attacks.append(Attack(self, rect, 1, 0.2))

    def take_damage(self, amount):
        self.health -= amount
        self.flash_timer = 0.1

    def update_flash(self, dt):
        if self.flash_timer > 0:
            self.flash_timer -= dt
            self.image.fill(WHITE)
        else:
            self.image.fill(self.color)

    def update_attacks(self, dt, entities):
        for attack in self.attacks:
            attack.update(dt, entities)
        self.attacks = [a for a in self.attacks if a.alive()]

    def draw_attacks(self, screen):
        for attack in self.attacks:
            attack.draw(screen)

# ---------------- PLAYER ----------------
class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, GREEN, 150)
        self.speed = 300
        self.jump_power = -500
        self.attack_defs = {
            "slash": {
                "offset": (30, -10),
                "size": (40, 20),
                "damage": 1,
                "duration": 0.2,
                "cooldown": 0.4
            },
            "heavy": {
                "offset": (40, -15),
                "size": (50, 30),
                "damage": 2,
                "duration": 0.25,
                "cooldown": 0.8
            }
        }

    def update(self, tiles, dt, entities, current_time):
        keys = pygame.key.get_pressed()
        self.vel.x = 0

        if keys[pygame.K_a]:
            self.vel.x = -self.speed
        if keys[pygame.K_d]:
            self.vel.x = self.speed

        if keys[pygame.K_w] and self.on_ground:
            self.vel.y = self.jump_power

        if keys[pygame.K_SPACE]:
            self.try_attack("slash", current_time)

        if keys[pygame.K_LSHIFT]:
            self.try_attack("heavy", current_time)

        self.apply_gravity(dt)
        self.move(tiles, entities, dt)

        self.update_attacks(dt, entities)
        self.update_flash(dt)

# ---------------- GROUND ENEMY ----------------
class GroundEnemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, RED, 100)
        self.speed = 150
        self.attack_defs = {
            "slash": {
                "offset": (30, -10),
                "size": (40, 40),
                "damage": 1,
                "duration": 0.2,
                "cooldown": 0.4
            }
        }

    def update(self, tiles, player, dt, entities, current_time):
        self.vel.x = self.speed if player.rect.centerx > self.rect.centerx else -self.speed

        if self.on_ground and random.random() < 0.01:
            self.vel.y = -400

        if random.random() < 0.02:
            self.try_attack("slash", current_time)

        self.apply_gravity(dt)
        self.move(tiles, entities, dt)

        self.update_attacks(dt, entities)
        self.update_flash(dt)

# ---------------- FLYING ENEMY ----------------
class FlyingEnemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, BLUE, 60)
        self.speed = 120
        self.attack_defs = {
            "slash": {
                "offset": (30, -10),
                "size": (40, 40),
                "damage": 1,
                "duration": 0.2,
                "cooldown": 0.4
            }
        }

    def update(self, tiles, player, dt, entities, current_time):
        direction = pygame.Vector2(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery
        )

        if direction.length() != 0:
            direction = direction.normalize()

        self.vel = direction * self.speed

        if random.random() < 0.03:
            self.try_attack("slash", current_time)

        self.move(tiles, entities, dt)

        self.update_attacks(dt, entities)
        self.update_flash(dt)

class ChargerEnemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, (255, 100, 100), 120)
        self.speed = 200

        self.attack_defs = {
            "charge": {
                "offset": (35, -10),
                "size": (50, 20),
                "damage": 2,
                "duration": 0.2,
                "cooldown": 1.0
            }
        }

    def update(self, tiles, player, dt, entities, time):
        self.vel.x = self.speed if player.rect.centerx > self.rect.centerx else -self.speed

        if random.random() < 0.02:
            self.try_attack("charge", time)

        self.apply_gravity(dt)
        self.move(tiles, entities, dt)

        self.update_attacks(dt, entities)
        self.update_flash(dt)


class ShooterEnemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, (100, 100, 255), 80)

        self.attack_defs = {
            "blast": {
                "offset": (50, -5),
                "size": (30, 10),
                "damage": 1,
                "duration": 0.3,
                "cooldown": 0.7
            }
        }

    def update(self, tiles, player, dt, entities, time):
        # Stay mostly still but face player
        self.vel.x = 0

        if player.rect.centerx < self.rect.centerx:
            self.facing = -1
        else:
            self.facing = 1

        if random.random() < 0.03:
            self.try_attack("blast", time)

        self.move(tiles, entities, dt)

        self.update_attacks(dt, entities)
        self.update_flash(dt)

# ---------------- GAME ----------------
class Game:
    def __init__(self):
        self.tiles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player = None

        self.load_level(LEVEL)

        self.running = True
        self.game_over = False

    def load_level(self, level):
        for y, row in enumerate(level):
            for x, char in enumerate(row):
                px = x * TILE_SIZE
                py = y * TILE_SIZE

                if char == "#":
                    self.tiles.add(Tile(px, py))
                elif char == "P":
                    self.player = Player(px, py)
                elif char == "G":
                    self.enemies.add(GroundEnemy(px, py))
                elif char == "F":
                    self.enemies.add(FlyingEnemy(px, py))
                elif char == "C":
                    self.enemies.add(ChargerEnemy(px, py))
                elif char == "S":
                    self.enemies.add(ShooterEnemy(px, py))

    def run(self):
        while self.running:
            dt = clock.tick(60) / 1000
            current_time = pygame.time.get_ticks() / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            if not self.game_over:
                entities = [self.player] + list(self.enemies)

                self.player.update(self.tiles, dt, entities, current_time)

                for enemy in self.enemies:
                    enemy.update(self.tiles, self.player, dt, entities, current_time)

                # Remove dead enemies
                for enemy in list(self.enemies):
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)

                if self.player.health <= 0:
                    self.game_over = True

            # Draw
            screen.fill((30, 30, 30))

            for tile in self.tiles:
                screen.blit(tile.image, tile.rect)

            for entity in [self.player] + list(self.enemies):
                screen.blit(entity.image, entity.rect)
                entity.draw_attacks(screen)

            if self.game_over:
                font = pygame.font.Font(None, 60)
                text = font.render("GAME OVER", True, WHITE)
                screen.blit(text, (300, 250))

            pygame.display.flip()

        pygame.quit()
        sys.exit()

# ---------------- MAIN ----------------
Game().run()

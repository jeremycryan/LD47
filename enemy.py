import math
import pygame
import random
import constants as c


class Enemy:
    def __init__(self, game, pos):
        self.game = game
        self.x, self.y = pos
        self.velocity = [0, 0]
        self.hp = 1
        self.difficulty_points = 1
        self.game.entities.append(self)
        self.radius = 30
        self.friendly = self.game.entities

    def update(self, dt, events):
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt

        self.check_tile_collisions()
        self.check_bullet_collisions()

        if self.hp <= 0:
            self.game.entities.remove(self)

    def draw(self, surface, offset=(0, 0)):
        x = self.x + offset[0]
        y = self.y + offset[1]
        pygame.draw.circle(surface, (255, 0, 0), (x, y), self.radius)

    def check_bullet_collisions(self):
        for bullet in self.game.bullets:
            if bullet.x < self.x - self.radius - bullet.radius or bullet.x > self.x + self.radius + bullet.radius:
                continue
            if bullet.y < self.y - self.radius - bullet.radius or bullet.y > self.y + self.radius + bullet.radius:
                continue
            if math.sqrt((bullet.x - self.x)**2 + (bullet.y - self.y)**2) < self.radius + bullet.radius:
                if self not in bullet.owner.friendly:
                    self.get_hit_by(bullet)

    def get_hit_by(self, bullet):
        self.hp -= bullet.damage

    def check_tile_collisions(self):
        if self.game.room is None:
            return
        else:
            x, y = self.game.room.world_to_cell(self.x, self.y, discrete=True)
            do_break = False
            for cell_x in [x-1, x, x+1]:
                for cell_y in [y-1, y, y+1]:
                    if self.game.room.cell_is_blocking(cell_x, cell_y):
                        real_x, real_y = self.game.room.cell_to_world(cell_x, cell_y)
                        do_break = self.bump_tile(real_x, real_y)
                    if do_break:
                        break
                if do_break:
                    break

    def bump_tile(self, x, y):
        dx = x - self.x
        dy = y - self.y
        if math.sqrt(dx**2 + dy**2) > 1.5 * c.TILE_SIZE + self.radius:
            return
        else:
            did_something = False
            decel = 0.2
            if hasattr(self, "bounces"):
                decel = 1.0
            if type(self) is BounceEnemy:
                decel = 1
            if -c.TILE_SIZE//2 < dx < c.TILE_SIZE//2:
                if 0 < dy < self.radius + c.TILE_SIZE//2:
                    self.y = y - c.TILE_SIZE//2 - self.radius - 1
                    self.velocity[1] *= -decel
                    did_something = True
                if 0 > dy > -self.radius - c.TILE_SIZE//2:
                    self.y = y + c.TILE_SIZE//2 + self.radius + 1
                    self.velocity[1] *= -decel
                    did_something = True
            if -c.TILE_SIZE//2 < dy < c.TILE_SIZE//2:
                if 0 < dx < self.radius + c.TILE_SIZE//2:
                    self.x = x - c.TILE_SIZE//2 - self.radius - 1
                    self.velocity[0] *= -decel
                    did_something = True
                if 0 > dx > -self.radius - c.TILE_SIZE//2:
                    self.x = x + c.TILE_SIZE//2 + self.radius + 1
                    self.velocity[0] *= -decel
                    did_something = True
            if did_something:
                if hasattr(self, "bounces"):
                    self.bounces += 1
                return True
            for corner in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                cx = x + corner[0] * c.TILE_SIZE//2
                cy = y + corner[1] * c.TILE_SIZE//2
                if math.sqrt((self.x - cx)**2 + (self.y - cy)**2) < self.radius:
                    dcx = cx - self.x
                    dcy = cy - self.y
                    unit_mag = c.mag(dcx, dcy)
                    if not unit_mag:
                        continue
                    self.x = cx - (self.radius+1) * dcx/unit_mag
                    self.y = cy - (self.radius+1) * dcy/unit_mag
                    if abs(dcy) < abs(dcx):
                        self.velocity[0] *= -decel
                    else:
                        self.velocity[1] *= -decel
                    if hasattr(self, "bounces"):
                        self.bounces += 1
                    return True
            return False

class BounceEnemy(Enemy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.speed = 100
        self.surface = pygame.image.load(c.image_path("fly.png"))

    def update(self, dt, events):
        super().update(dt, events)
        if self.velocity == [0, 0]:
            angle = random.random()*math.pi*2
            self.velocity[0] = math.sin(angle) * self.speed
            self.velocity[1] = math.cos(angle) * self.speed
        mag = c.mag(*self.velocity)
        if mag < self.speed:
            self.velocity[0] *= self.speed/mag
            self.velocity[1] *= self.speed/mag

    def draw(self, surface, offset=(0, 0)):
        x = self.x + offset[0] - self.surface.get_width()//2
        y = self.y + offset[1] - self.surface.get_height()//2
        surface.blit(self.surface, (x, y))

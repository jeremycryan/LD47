import pygame
import constants as c
import time
import math
from particle import BulletHit, TrailBit
from enemy import Enemy


class Bullet:
    def __init__(self, game, owner, pos, velocity=(0, 0), damage=100):
        self.game = game
        self.owner = owner

        self.x, self.y = pos
        self.velocity = list(velocity)
        self.radius = 12
        self.damage = damage
        self.surf = self.game.get_static(c.image_path("bullet.png"))
        self.glow = self.game.get_static(c.image_path("glow.png"))
        self.angle = 0
        self.age = 0

        self.bounces = 0

        self.since_spew = 0

        self._bump_tile = Enemy.bump_tile
        self._check_tile_collisions = Enemy.check_tile_collisions

    def bump_tile(self, *args, **kwargs):
        return self._bump_tile(self, *args, **kwargs)

    def check_tile_collisions(self):
        self._check_tile_collisions(self)

    def update(self, dt, events):
        self.since_spew += dt
        while self.since_spew > 0.01:
            TrailBit(self.game, self.owner, position=(self.x, self.y))
            self.since_spew -= 0.01
        self.age += dt
        self.x += self.velocity[0]*dt
        self.y += self.velocity[1]*dt

        self.angle += 120 * dt

        if not self.owner.has_powerup(c.BOUNCY) or self.bounces > 2:
            if self.game.room is not None:
                x, y = self.game.room.world_to_cell(self.x, self.y, discrete=True)
                if self.game.room.cell_is_blocking(x, y):
                    self.game.room.break_if_breakable_at(x, y)
                    self.destroy()
        else:
            if self.game.room is not None:
                self.check_tile_collisions()

    def destroy(self):
        self.destroyed = True
        self.game.bullets.remove(self)
        BulletHit(self.game, position=(self.x, self.y))
        self.game.current_scene.shake(3)
        self.game.bullet_destroyed_noise.play()

    def draw(self, surface, offset=(0, 0)):
        surf = pygame.transform.rotate(self.surf, self.angle)
        x = self.x - surf.get_width()//2 + offset[0]
        y = self.y - surf.get_height()//2 + offset[1]
        vis_rad = self.radius + 2 * math.sin(self.age*40)
        #surface.blit(surf, (x, y))
        pygame.draw.circle(surface, (200, 200, 200), (self.x + offset[0], self.y + offset[1]), vis_rad+2)
        pygame.draw.circle(surface, (255, 255, 255), (self.x + offset[0], self.y + offset[1]), vis_rad)
        x = self.x - self.glow.get_width()//2 + offset[0]
        y = self.y - self.glow.get_height()//2 + offset[1]
        surface.blit(self.glow, (x, y), special_flags=pygame.BLEND_RGBA_ADD)

    def collide_with(self, other):
        if hasattr(other, "friendly"):
            if self.owner in other.friendly:
                return
        self.hit(other)

    def hit(self, other):
        pass

import pygame
import random


from enemy import Enemy
from sprite_tools import SpriteSheet, Sprite
import constants as c

class Particle:

    def __init__(self, game, surface, duration=None, position=(0, 0), velocity=(0, 0), rotation=0, drag = 0.05):
        self.game = game
        self.surf = surface
        self.duration = duration
        self.velocity = list(velocity)
        self.x, self.y = position
        self.rotation = rotation
        self.angle = random.random()*360
        self.game.particles.add(self)
        self.drag = drag
        self.radius = 5
        self.age = 0

        self._bump_tile = Enemy.bump_tile
        self._check_tile_collisions = Enemy.check_tile_collisions

    def update(self, dt, events):
        self.velocity[0] *= self.drag**dt
        self.velocity[1] *= self.drag**dt
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt
        self.angle += self.rotation * dt
        self.rotation *= 0.5**dt
        if self.duration is not None:
            self.duration -= dt
            if self.duration <= 0:
                self.destroy()

        self.age += dt

        self.check_tile_collisions()

    def bump_tile(self, *args, **kwargs):
        self._bump_tile(self, *args, **kwargs)

    def check_tile_collisions(self):
        self._check_tile_collisions(self)

    def destroy(self):
        self.game.particles.remove(self)

    def draw(self, surface, offset=(0, 0)):
        surf = pygame.transform.rotate(self.surf, self.angle)
        x = self.x - surf.get_width()//2 + offset[0]
        y = self.y - surf.get_height()//2 + offset[1]
        surface.blit(surf, (x, y))

class BulletHit(Particle):
    def __init__(self, game, position=(0, 0)):
        super().__init__(game, None, position=position)
        self.sprite = Sprite(16)
        anim = SpriteSheet(c.image_path("bullet_hit.png"), (8, 1), 8)
        self.sprite.add_animation({"Default": anim})
        self.sprite.start_animation("Default")
        self.game.top_particles.add(self)

        surface = pygame.Surface((100, 100))
        surface.fill((0, 0, 0))
        pygame.draw.circle(surface, (255, 255, 255), (50, 50), 50)
        self.boom = surface
        self.boom.set_colorkey((0, 0, 0))
        self.boom_alpha = 200
        self.boom_size = 40

    def update(self, dt, events):
        self.age += dt
        self.boom_alpha -= 1600*dt
        self.boom_size += 600*dt
        self.sprite.update(dt)
        if self.age > 0.4:
            self.destroy()

    def draw(self, surface, offset=(0, 0)):
        x = self.x + offset[0]
        y = self.y + offset[1]
        self.sprite.set_position((x, y))
        self.sprite.draw(surface)

        boom = pygame.transform.scale(self.boom, (int(self.boom_size), int(self.boom_size)))
        boom.set_alpha(self.boom_alpha)
        surface.blit(boom, (x - self.boom_size//2, y - self.boom_size//2))

    def destroy(self):
        super().destroy()
        self.game.top_particles.remove(self)

class TrailBit(Particle):
    def __init__(self, game, owner, **kwargs):
        surface = pygame.Surface((24, 24))
        surface.fill((0, 0, 0))
        self.owner = owner
        color = (255, 255, 255)
        pygame.draw.circle(surface, color, (12, 12), 12)
        surface.set_colorkey((0, 0, 0))
        super().__init__(game, surface, **kwargs)
        self.duration = 1
        self.start_alpha = 50

    def update(self, dt, events):
        super().update(dt, events)
        alpha = (self.duration - self.age)*self.start_alpha
        self.surf.set_alpha(alpha)
        if self.age > self.duration:
            self.destroy()

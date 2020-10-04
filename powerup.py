import pygame
import constants as c
import math


class Powerup:
    def __init__(self, game, surface, pos=(0, 0)):
        self.radius = 24
        self.age = 0
        self.game = game
        self.x, self.y = pos
        self.y_offset = -self.y
        self.surface = surface
        self.shadow = pygame.Surface((self.radius*2, self.radius*2))
        self.shadow.fill((255, 255, 255))
        self.shadow.set_colorkey((255, 255, 255))
        self.shadow.set_alpha(40)
        self.landed = False
        pygame.draw.circle(self.shadow, (0, 0, 0), (self.radius, self.radius), self.radius)
        self.glow = self.game.get_static(c.image_path("glow.png"))

    def update(self, dt, events):
        self.age += dt
        if self.landed:
            self.y_offset = 6 * math.sin(self.age * 6)
        else:
            self.y_offset += 600*dt
            if self.y_offset >= 0:
                self.y_offset = 0
                self.landed = True
                self.game.current_scene.shake(5)
                self.game.powerup_land_noise.play()
        self.check_collisions()

    def draw(self, surface, offset=(0, 0)):

        x = self.x + offset[0] - self.glow.get_width()//2
        y = self.y + offset[1] - self.glow.get_height()//2 + self.y_offset - 30
        surface.blit(self.glow, (x, y), special_flags = pygame.BLEND_RGBA_ADD)

        width = self.shadow.get_width()
        width -= 10
        if (int(width + self.y_offset/2)) > 0:
            shadow = pygame.transform.scale(self.shadow, (int(width + self.y_offset/2), int(width + self.y_offset/2)))
            x = self.x + offset[0] - shadow.get_width()//2
            y = self.y + offset[1] - shadow.get_height()//2
            surface.blit(shadow, (x, y))
        x = self.x + offset[0] - self.surface.get_width()//2
        y = self.y + offset[1] - self.surface.get_height()//2 + self.y_offset - 30
        surface.blit(self.surface, (x, y))

    def check_collisions(self):
        for player in self.game.current_scene.players:
            if c.mag(player.x - self.x, player.y - self.y) < player.radius + self.radius and self.landed:
                self.collected_by(player)
                break

    def collected_by(self, player):
        self.game.powerup_collect_noise.play()
        self.game.powerups.remove(self)


class FastSpinPowerup(Powerup):
    def __init__(self, game, pos=(0, 0)):
        surface = game.get_static(c.image_path("spin.png"))
        super().__init__(game, surface, pos=pos)

    def collected_by(self, player):
        super().collected_by(player)
        FastSpin(player)

class SlipperySocksPowerup(Powerup):
    def __init__(self, game, pos=(0, 0)):
        surface = game.get_static(c.image_path("socks.png"))
        super().__init__(game, surface, pos=pos)

    def collected_by(self, player):
        super().collected_by(player)
        SlipperySocks(player)

class DoubleShotPowerup(Powerup):
    def __init__(self, game, pos=(0, 0)):
        surface = game.get_static(c.image_path("double.png"))
        super().__init__(game, surface, pos=pos)

    def collected_by(self, player):
        super().collected_by(player)
        DoubleShot(player)

class BouncyPowerup(Powerup):
    def __init__(self, game, pos=(0, 0)):
        surface = game.get_static(c.image_path("bouncy.png"))
        super().__init__(game, surface, pos=pos)

    def collected_by(self, player):
        super().collected_by(player)
        Bouncy(player)

class FastShootingPowerup(Powerup):
    def __init__(self, game, pos=(0, 0)):
        surface = game.get_static(c.image_path("mandible.png"))
        super().__init__(game, surface, pos=pos)

    def collected_by(self, player):
        super().collected_by(player)
        FastShooting(player)

class Effect:

    def __init__(self, owner):
        self.age = 0
        self.owner = owner
        found = False
        for item in self.owner.effects:
            if item.id == self.id:
                item.age = 0
                found = True
                break
        if not found:
            self.owner.effects.append(self)

    def update(self, dt, events):
        self.age += dt

        if self.age > self.duration:
            self.end()

    def end(self):
        self.owner.effects.remove(self)

class FastSpin(Effect):

    def __init__(self, owner):
        self.id=c.FAST_SPINNING
        self.duration = 25
        super().__init__(owner)
        self.name = "Caffeine"
        self.description = "Spin to win"
        self.mult = 2
        self.icon = pygame.transform.scale2x(self.owner.game.get_static(c.image_path("spin_icon.png")))

class SlipperySocks(Effect):

    def __init__(self, owner):
        self.id=c.SLIPPERY_SOCKS
        self.name = "Slippery Socks"
        self.description = "There better be a bulk discount"
        self.duration = 18
        super().__init__(owner)
        self.icon = pygame.transform.scale2x(self.owner.game.get_static(c.image_path("socks_icon.png")))

class DoubleShot(Effect):

    def __init__(self, owner):
        self.id=c.DOUBLE_SHOT
        self.name = "Double Shot"
        self.description = "For that special someone you really want to shoot twice"
        self.duration = 18
        super().__init__(owner)
        self.icon = pygame.transform.scale2x(self.owner.game.get_static(c.image_path("double_icon.png")))

class Bouncy(Effect):

    def __init__(self, owner):
        self.id=c.BOUNCY
        self.name = "Bouncy Bullets"
        self.description = "When the collision code works correctly"
        self.duration = 18
        super().__init__(owner)
        self.icon = pygame.transform.scale2x(self.owner.game.get_static(c.image_path("bouncy_icon.png")))

class FastShooting(Effect):

    def __init__(self, owner):
        self.id=c.FAST_SHOOTING
        self.name = "Mandible Lubricant"
        self.description = "Improves regurigation efficiency by 80% or more"
        self.duration = 25
        super().__init__(owner)
        self.icon = pygame.transform.scale2x(self.owner.game.get_static(c.image_path("mandible_icon.png")))

import pygame
import math
import constants as c
import random
from bullet import *
from particle import *

SPIN_SPEED = "spin speed"
CHARGE_TIME = "charge time"
CHARGED_SPEED = "charged speed"
KNOCKBACK = "knockback"
MAX_SHAKE = "max_shake"
BULLET_TYPE = "bullet_type"
BULLET_SPEED = "bullet_speed"
DAMAGE = "damage"

class Player:
    def __init__(self, game, skin=1, player_num=1):
        self.game = game
        self.controller = Player.ButtonController()

        self.effects = []

        self.radius = 26
        self.charged = 0
        self.charging = False
        self.props = {CHARGE_TIME: 1,
                      SPIN_SPEED: 160, # degrees per second
                      CHARGED_SPEED: 60, # degrees per second
                      KNOCKBACK: 800,
                      MAX_SHAKE: 6,
                      BULLET_TYPE: Bullet,
                      BULLET_SPEED: 800,
                      DAMAGE: 70}

        self.friendly = [self]

        self.sailing = False
        self.since_fire = 0
        self.sail_time = 0.1
        self.temp_sail_time = self.sail_time

        self.angle = 0 # degrees CCW from right

        self.x, self.y = self.game.room.spawns[player_num]

        self.velocity = [0, 0]

        self.skin = skin

        self.color_dict = {1: (255, 230, 220),
                            2: (230, 220, 255),
                            3: (0, 255, 0),
                            4: (255, 0, 255),
                            5: (255, 255, 255)}
        self.color = self.color_dict[self.skin]

        self.surf = pygame.image.load(c.image_path(f"player_{skin}.png"))
        self.dead_surf = pygame.image.load(c.image_path(f"player_{skin}_dead.png"))
        self.blink_surf = pygame.mask.from_surface(self.surf).to_surface().convert()
        self.blink_surf.set_colorkey((0, 0, 0))
        self.legs_1 = pygame.image.load(c.image_path(f"legs_1_{skin}.png"))
        self.blink_legs_1 = pygame.mask.from_surface(self.legs_1).to_surface().convert()
        self.blink_legs_1.set_colorkey((0, 0, 0))
        self.legs_2 = pygame.image.load(c.image_path(f"legs_2_{skin}.png"))
        self.blink_legs_2 = pygame.mask.from_surface(self.legs_2).to_surface().convert()
        self.blink_legs_2.set_colorkey((0, 0, 0))
        self.leg_step_amt = 15
        size = 1.35
        self.shadow = pygame.Surface((int(c.TILE_SIZE*size), int(c.TILE_SIZE*size)))
        self.shadow.fill((255, 255, 255))
        self.shadow.set_colorkey((255, 255, 255))
        self.shadow.set_alpha(60)
        pygame.draw.circle(self.shadow, (0, 0, 0), (self.shadow.get_width()//2, self.shadow.get_height()//2), self.shadow.get_width()//2)

        self.one_leg = pygame.Surface((22, 29))
        self.one_leg.fill((255, 255, 0))
        self.one_leg.set_colorkey((255, 255, 0))
        self.one_leg.blit(self.legs_2, (-21, -16))

        self.charge_threshold = 0.7

        self.since_damage = 100
        self.dead = False

        self.hp = 100
        self.arrow = pygame.image.load(c.image_path("arrow.png"))
        self.arrow.set_colorkey((0, 0, 0))

    def draw_arrow(self, surface, offset=(0, 0)):
        post_threshold = min(self.charged/self.get(CHARGE_TIME) - self.charge_threshold, 1-self.charge_threshold)/(1-self.charge_threshold)
        if post_threshold <= 0 or not self.charging:
            return
        else:
            post_threshold = (1 - (1 - post_threshold)**2)
            angle_offsets = [0]
            if self.has_powerup(c.DOUBLE_SHOT):
                angle_offsets = [-15, 15]
            for angle_offset in angle_offsets:
                self.angle += angle_offset
                distance = post_threshold * 100
                x, y = self.get_direction_vector()
                arrow = pygame.transform.rotate(self.arrow, self.angle)
                x = x*distance + self.x - arrow.get_width()//2 + offset[0]
                y = y*distance + self.y - arrow.get_height()//2 + offset[1]
                min_x, min_y, w, h = self.game.room.get_rect()

                if x > min_x and y > min_y and x < min_x + w - arrow.get_width() and y < min_y + h - arrow.get_height():
                    surface.blit(arrow, (x, y))

                along = 0
                while along < distance - 15:
                    x, y = self.get_direction_vector()
                    x = x*along + self.x + offset[0]
                    y = y*along + self.y + offset[1]
                    if x > min_x + 3 and y > min_y + 3 and x < min_x - 3 + w and y < min_y + h - 3:
                        pygame.draw.circle(surface, (255, 255, 255), (x, y), 3)
                    along += 16

                self.angle -= angle_offset

    def bump_vel(self, x, y):
        self.velocity[0] += x
        self.velocity[1] += y
        self.game.bounce_noise.play()
        if self.dead:
            self.props[SPIN_SPEED] = random.random() * 240 - 120

    def check_player_collisions(self):
        for player in self.game.current_scene.players:
            if player is self:
                continue
            else:
                dx = player.x - self.x
                dy = player.y - self.y
                mag = c.mag(dx, dy)
                if mag < self.radius + player.radius - 2:
                    if not mag:
                        continue
                    bump_amt = 200
                    x = dx/mag * bump_amt
                    y = dy/mag * bump_amt
                    self.bump_vel(-x, -y)
                    player.bump_vel(x, y)

                    self.x = player.x - (self.radius + player.radius)*dx/mag
                    self.y = player.y - (self.radius + player.radius)*dy/mag


    def legs_1_angle(self):
        angle = self.angle - (self.angle % (self.leg_step_amt*2))
        if self.angle % (self.leg_step_amt*2) < self.leg_step_amt:
            angle += (self.angle % (self.leg_step_amt*2)) * 2
        else:
            angle += self.leg_step_amt * 2
        return angle

    def legs_2_angle(self):
        angle = self.angle - (self.angle % (self.leg_step_amt*2))
        if self.angle % (self.leg_step_amt*2) < self.leg_step_amt:
            pass
        else:
            angle += ((self.angle % (self.leg_step_amt*2)) - self.leg_step_amt) * 2
        return angle

    def check_tile_collisions(self):
        if self.game.room is None:
            return
        else:
            x, y = self.game.room.world_to_cell(self.x, self.y, discrete=True)
            for cell_x in [x-1, x, x+1]:
                for cell_y in [y-1, y, y+1]:
                    if self.game.room.cell_is_blocking(cell_x, cell_y):
                        real_x, real_y = self.game.room.cell_to_world(cell_x, cell_y)
                        if self.bump_tile(real_x, real_y):
                            if c.mag(*self.velocity) > 5:
                                self.game.bounce_noise.play()
                            return

    def bump_tile(self, x, y):
        dx = x - self.x
        dy = y - self.y
        if math.sqrt(dx**2 + dy**2) > 1.5 * c.TILE_SIZE + self.radius:
            return False
        else:
            did_something = False
            decel = 0.4
            if self.has_powerup(c.SLIPPERY_SOCKS):
                decel = 0.7
            if -c.TILE_SIZE//2 < dx < c.TILE_SIZE//2:
                if 0 < dy < self.radius + c.TILE_SIZE//2:
                    self.y = y - c.TILE_SIZE//2 - self.radius
                    self.velocity[1] *= -decel
                    did_something = True
                if 0 > dy > -self.radius - c.TILE_SIZE//2:
                    self.y = y + c.TILE_SIZE//2 + self.radius
                    self.velocity[1] *= -decel
                    did_something = True
            if -c.TILE_SIZE//2 < dy < c.TILE_SIZE//2:
                if 0 < dx < self.radius + c.TILE_SIZE//2:
                    self.x = x - c.TILE_SIZE//2 - self.radius
                    self.velocity[0] *= -decel
                    did_something = True
                if 0 > dx > -self.radius - c.TILE_SIZE//2:
                    self.x = x + c.TILE_SIZE//2 + self.radius
                    self.velocity[0] *= -decel
                    did_something = True
            if did_something:
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
                    self.x = cx - self.radius * dcx/unit_mag
                    self.y = cy - self.radius * dcy/unit_mag
                    if abs(dcy) < abs(dcx):
                        self.velocity[0] *= -decel
                    else:
                        self.velocity[1] *= -decel
                    return True
            return False

    def check_bullet_collisions(self):
        if self.dead:
            return
        for bullet in list(self.game.bullets):
            if bullet.x < self.x - self.radius - bullet.radius or bullet.x > self.x + self.radius + bullet.radius:
                continue
            if bullet.y < self.y - self.radius - bullet.radius or bullet.y > self.y + self.radius + bullet.radius:
                continue
            if math.sqrt((bullet.x - self.x)**2 + (bullet.y - self.y)**2) < self.radius + bullet.radius:
                if self not in bullet.owner.friendly:
                    self.get_hit_by(bullet)

    def get_hit_by(self, bullet):
        self.game.player_hurt_noise.play()
        self.hp -= bullet.damage
        self.since_damage = 0

        self.game.current_scene.shake(10)

        bump_amt = 0.3
        bx = bullet.velocity[0] * bump_amt
        by = bullet.velocity[1] * bump_amt
        self.bump_vel(bx, by)

        if self.hp <= 0 and not self.dead:
            self.hp = 0
            self.die()
        bullet.destroy()

    def die(self):
        #self.game.current_scene.players.remove(self)
        self.charged = 0
        self.charging = 0
        self.controller.disabled = True
        self.dead = True
        self.effects = []
        for i in range(8):
            angle = i/8 * 2 * math.pi + self.angle*math.pi/180
            speed = random.random()**2*140 + 60
            vx = speed * math.cos(angle) + self.velocity[0]*1
            vy = speed * -math.sin(angle) + self.velocity[1]*1
            Particle(self.game,
                self.one_leg,
                position=(self.x, self.y),
                velocity=(vx, vy),
                rotation=(random.random()*200 - 100))


    def get_direction_vector(self):
        x = math.cos(self.angle/180*math.pi)
        y = -math.sin(self.angle/180*math.pi)
        return x, y

    def get_spin_velocity(self):
        if self.sailing:
            return 0
        dif = self.get(SPIN_SPEED) - self.get(CHARGED_SPEED)
        speed = self.get(CHARGED_SPEED) + dif * (1 - self.charged)**2
        return speed

    def get(self, tag):
        result = self.props[tag]
        if self.has_powerup(c.FAST_SPINNING):
            if tag in (SPIN_SPEED, CHARGED_SPEED):
                result *= 2.5
        if self.has_powerup(c.DOUBLE_SHOT):
            if tag in (KNOCKBACK,):
                result *= 0.6
        if self.has_powerup(c.FAST_SHOOTING):
            if tag in (CHARGE_TIME,):
                result *= 0.5
        return result

    def has_powerup(self, id):
        for effect in self.effects:
            if effect.id == id:
                return True
        return False

    def set(self, tag, value):
        self.props[tag] = value

    def bind_key(self, key):
        self.controller.key = key

    def unbind_key(self):
        self.bind_key(None)

    def update(self, dt, events):
        x, y, w, h = self.game.room.get_rect()
        if self.x > x+w or self.y > y+h or self.x < x or self.y < y:
            self.x, self.y = c.WINDOW_WIDTH//2, c.WINDOW_HEIGHT//2
            pygame.display.set_caption("Spinneret (definitely not riddled with bugs)")
        for effect in self.effects[::-1]:
            effect.update(dt, events)
        self.since_damage += dt
        self.controller.update(dt, events)
        self.since_fire += dt
        if self.since_fire >= self.temp_sail_time:
            self.sailing = False
        if self.controller.is_pressed():
            self.down()
        if self.controller.is_released():
            self.up()

        self.check_bullet_collisions()
        self.check_player_collisions()

        mag = c.mag(self.velocity[0], self.velocity[1])
        if not self.sailing and mag and not self.has_powerup(c.SLIPPERY_SOCKS):
            self.velocity[0] = self.velocity[0] * 0.002**dt
            self.velocity[1] = self.velocity[1] * 0.002**dt
        if self.has_powerup(c.SLIPPERY_SOCKS):
            max_speed = 400
            if mag > max_speed:
                self.velocity[0] *= max_speed/mag
                self.velocity[1] *= max_speed/mag
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt

        self.angle += self.get_spin_velocity()*dt
        if self.charging:
            speed = 1/self.get(CHARGE_TIME)
            self.charged += speed*dt
            if self.charged > 1:
                self.charged = 1

        if self.dead:
            self.props[SPIN_SPEED] *= 0.2**dt

        self.check_tile_collisions()

    def draw(self, surface, offset=(0, 0)):
        rx = (random.random() - 0.5) * self.get(MAX_SHAKE) * self.charged
        ry = (random.random() - 0.5) * self.get(MAX_SHAKE) * self.charged

        xoff, yoff = self.get_direction_vector()
        xoff *= 10
        yoff *= 10

        if not self.dead:
            surf = self.shadow
            x = self.x - surf.get_width()//2 + offset[0] + rx
            y = self.y - surf.get_height()//2 + offset[1] + ry + 10
            surface.blit(surf, (x, y))

            legs = self.legs_1 if not self.blinking() else self.blink_legs_1
            surf = pygame.transform.rotate(legs, self.legs_1_angle())
            x = self.x - surf.get_width()//2 + offset[0] + rx + xoff
            y = self.y - surf.get_height()//2 + offset[1] + ry + yoff
            surface.blit(surf, (x, y))

            legs = self.legs_2 if not self.blinking() else self.blink_legs_2
            surf = pygame.transform.rotate(legs, self.legs_2_angle())
            x = self.x - surf.get_width()//2 + offset[0] + rx + xoff
            y = self.y - surf.get_height()//2 + offset[1] + ry + yoff
            surface.blit(surf, (x, y))

        self.draw_arrow(surface, offset=offset)

        body = self.surf if not self.blinking() else self.blink_surf
        if self.dead and not self.blinking():
            body = self.dead_surf
        surf = pygame.transform.rotate(body, self.angle)
        x = self.x - surf.get_width()//2 + offset[0] + rx
        y = self.y - surf.get_height()//2 + offset[1] + ry
        surface.blit(surf, (x, y))

        effect_spacing = 24
        x = self.x + offset[0] - effect_spacing/2 * (len(self.effects) - 1) - 12
        y = self.y + offset[1] - 52
        for effect in self.effects:
            if (effect.duration - effect.age) > 3.2 or effect.age % 0.4 < 0.2:
                surface.blit(effect.icon, (x, y))
            x += effect_spacing

        #pygame.draw.circle(surface, (255, 255, 100), (self.x + offset[0], self.y + offset[1]), self.radius, width=2)

    def blinking(self):
        return self.since_damage < 0.18

    def down(self):
        self.charging = True

    def up(self):
        self.charging = False
        self.charge_threshold = 0.7 if not self.has_powerup(c.FAST_SHOOTING) else 0.5
        if self.charged > self.charge_threshold:
            self.fire()
        self.charged = 0

    def fire(self):
        offsets = [0]
        if self.has_powerup(c.DOUBLE_SHOT):
            offsets = [-15, 15]

        self.game.shoot_noise.play()
        for offset in offsets:
            self.angle += offset
            x, y = self.get_direction_vector()
            self.velocity[0] += -x * self.get(KNOCKBACK) * self.charged
            self.velocity[1] += -y * self.get(KNOCKBACK) * self.charged
            self.sailing = True
            self.since_fire = 0
            self.temp_sail_time = self.sail_time * self.charged

            xv, yv = self.get_direction_vector()
            xv *= self.get(BULLET_SPEED)
            yv *= self.get(BULLET_SPEED)
            new_bullet = Bullet(self.game, self, (self.x, self.y), (xv, yv), damage=self.get(DAMAGE))
            self.game.bullets.add(new_bullet)
            self.angle -= offset

    class ButtonController:
        def __init__(self, key=None):
            self.key = key
            self.pressed = False # was pressed this frame
            self.released = False # was released this frame
            self.disabled = False

        def update(self, dt, events):
            if self.disabled:
                return
            if self.key is None:
                self.pressed = False
                self.released = False
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == self.key:
                        self.pressed = True
                if event.type == pygame.KEYUP:
                    if event.key == self.key:
                        self.released = True

        def is_pressed(self):
            if self.pressed:
                self.pressed = False
                return True
            return False

        def is_released(self):
            if self.released:
                self.released = False
                return True
            return False

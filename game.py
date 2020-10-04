import pygame
import constants as c
import sys
from player import Player
from room import *
from enemy import *
import math
import time
from button import Button

from powerup import *

class Game:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode(c.WINDOW_SIZE)
        self.next_scene = None
        self.bullets = set()
        self.particles = set()
        self.top_particles = set()
        self.powerups = []
        self.entities = []
        self.static_images = {}
        self.room = None

        master=0.7
        self.button_noise = pygame.mixer.Sound(c.sounds_path("button_raw.wav"))
        self.button_noise.set_volume(0.4*master)
        self.join_noise = pygame.mixer.Sound(c.sounds_path("join.wav"))
        self.join_noise.set_volume(0.6*master)
        self.cut_off_noise = pygame.mixer.Sound(c.sounds_path("start_game.wav"))
        self.cut_off_noise.set_volume(0.8*master)
        self.leave_noise = pygame.mixer.Sound(c.sounds_path("player_leave.wav"))
        self.leave_noise.set_volume(0.35*master)
        self.bullet_destroyed_noise = pygame.mixer.Sound(c.sounds_path("bullet_destroyed.wav"))
        self.bullet_destroyed_noise.set_volume(0.17*master)
        self.player_hurt_noise = pygame.mixer.Sound(c.sounds_path("player_hurt.wav"))
        self.player_hurt_noise.set_volume(0.5*master)
        self.shoot_noise = pygame.mixer.Sound(c.sounds_path("shoot_raw.wav"))
        self.shoot_noise.set_volume(0.20*master)
        self.bounce_noise = pygame.mixer.Sound(c.sounds_path("bounce.wav"))
        self.bounce_noise.set_volume(0.15*master)
        self.powerup_land_noise = pygame.mixer.Sound(c.sounds_path("powerup_land.wav"))
        self.powerup_land_noise.set_volume(0.18*master)
        self.powerup_collect_noise = pygame.mixer.Sound(c.sounds_path("powerup_collect.wav"))
        self.powerup_collect_noise.set_volume(0.32*master)
        pygame.mixer.music.load(c.sounds_path("music_v1.ogg"))
        pygame.mixer.music.play(-1)

        pygame.display.set_caption("Spinnerets")

        self.key_list = []
        self.skin_list = []
        self.win_list = []

        self.current_scene = LD47Scene(self)#RoomScene(self)

    def reset_room(self):
        self.powerups = []
        self.entities = []
        self.bullets = set()
        self.particles = set()
        self.top_particles = set()

    def get_static(self, path):
        if path not in self.static_images:
            self.static_images[path] = pygame.image.load(path)
        return self.static_images[path]

    def main(self):
        while True:
            self.current_scene.main()
            self.current_scene = self.next_scene
            self.clear_scene()

    def clear_scene(self):
        self.bullets = set()

    def update_globals(self):
        dt = self.clock.tick(c.MAX_FPS)/1000
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        if dt > 1/15:
            dt = 1/15
        return dt, events

    def flip(self):
        pygame.display.flip()

class Scene:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.shake_mag = 0

    def shake(self, amt):
        self.shake_mag = max(self.shake_mag, amt)


class RoomSelect(Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = 4
        self.room_previews = [self.get_preview(idx) for idx in range(1, 1+self.count)]
        self.names = ["Starter", "Pips", "Clover"]
        self.level_font = pygame.font.Font(c.fonts_path("yoster.ttf"), 45)

    def get_preview(self, idx):
        room = Room.from_file(self.game, c.rooms_path(f"{idx}.txt"))
        return room.preview()

    def draw_names(self, surface, offset=(0, 0)):
        x = 50
        y = 50
        for item in self.names:
            render = self.level_font.render(item, 1, (255, 255, 255))
            surface.blit(render, (x+offset[0], y+offset[1]))
            y += 55
        pass

    def draw_rooms(self, surface, offset=(0, 0)):
        pass

    def main(self):
        while True:
            dt, events = self.game.update_globals()

            offset = (0, 0)

            self.screen.fill((0, 0, 0))
            self.draw_lines(self.screen)
            self.draw_rooms(self.screen)
            self.draw_names(self.screen, offset)
            pygame.display.flip()

    def draw_lines(self, surface, offset=(0, 0)):
        x = (time.time()*30)%30
        while x < c.WINDOW_WIDTH + c.WINDOW_HEIGHT:
            x_end = x - c.WINDOW_HEIGHT
            pygame.draw.line(surface, (40, 30, 10), (x, c.WINDOW_HEIGHT), (x_end, 0), 6)
            x += 30


class CharacterSelect(Scene):

    def __init__(self, game):
        super().__init__(game)
        self.keys = []
        self.skins = []
        self.xs = []
        self.since_click = []
        self.skin_to_spider_surf = {skin: self.game.get_static(c.image_path(f"spider_{skin}.png")) for skin in range(1, 5)}
        self.key_font = pygame.font.Font(c.fonts_path("yoster.ttf"), 75)
        self.long_key_font = pygame.font.Font(c.fonts_path("yoster.ttf"), 40)
        self.note_font = pygame.font.Font(c.fonts_path("yoster.ttf"), 20)
        self.spider_shadow = pygame.Surface((64, 64))
        self.spider_shadow.fill((255, 255, 255))
        pygame.draw.circle(self.spider_shadow, (0, 0, 0), (32, 32), 32)
        self.spider_shadow.set_alpha(40)
        self.spider_shadow.set_colorkey((255, 255, 255))
        self.player_frame = pygame.transform.scale2x(pygame.image.load(c.image_path("player_frame.png")))

        button_surf = pygame.image.load(c.image_path("button.png"))
        button_hover = pygame.image.load(c.image_path("button_hover.png"))
        button_disabled = pygame.image.load(c.image_path("button_disabled.png"))
        button_clicked = pygame.image.load(c.image_path("button_clicked.png"))

        self.black = pygame.Surface(c.WINDOW_SIZE)
        self.black.fill((0, 0, 0))
        self.black_alpha = 255
        self.black_target_alpha = 0

        self.button = Button(button_surf,
                        (c.WINDOW_WIDTH//2, c.WINDOW_HEIGHT - 135),
                        on_click=self.next_scene,
                        hover_surf=button_hover,
                        click_surf=button_clicked,
                        disabled_surf=button_disabled)
        self.button.disable()
        self.over = False

    def draw_lines(self, surface, offset=(0, 0)):
        x = (time.time()*20)%30
        while x < c.WINDOW_WIDTH + c.WINDOW_HEIGHT:
            x_end = x - c.WINDOW_HEIGHT
            pygame.draw.line(surface, (40, 30, 10), (x, c.WINDOW_HEIGHT), (x_end, 0), 6)
            x += 30

    def next_scene(self):
        self.game.skin_list = self.skins
        self.game.key_list = self.keys
        self.game.cut_off_noise.play()
        self.game.win_list = [0 for _ in self.keys]

        #self.over = True
        self.black_target_alpha = 255

    def pressed(self, key):
        for i, item in enumerate(self.keys):
            if item == key:
                add = 1
                while self.skins[i] + add in self.skins:
                    add += 1
                self.skins[i] += add
                self.since_click[i] = 0
                if self.skins[i] > 4:
                    self.skins.pop(i)
                    self.keys.pop(i)
                    self.since_click.pop(i)
                    self.xs.pop(i)
                    self.game.leave_noise.play()
                else:
                    self.game.button_noise.play()
                return
        if len(self.keys) < 4:
            self.keys.append(key)
            skin = 1
            while skin in self.skins:
                skin += 1
            self.skins.append(skin)
            self.since_click.append(0)
            self.xs.append(len(self.xs))
            self.game.join_noise.play()

    def spider_hop(self, idx):
        x = self.since_click[idx] * 6
        y = -(-x**2 + x)*60
        return min(y, 0)

    def draw_title_line(self, surface, offset=(0, 0)):
        line = self.long_key_font.render("Press any key to join", 1, (255, 255, 255))
        y = 40 + 4 * math.sin(time.time()*3)
        surface.blit(line, (c.WINDOW_WIDTH//2-line.get_width()//2+offset[0], y+offset[1]))

    def draw_player_preview(self, surface, idx, pos, offset=(0, 0)):
        offset = offset[0] + 3*math.sin(time.time()*4+idx), offset[1] - 50 + 4*math.cos(time.time()*5+idx)
        w = 225
        h = 350
        back = self.player_frame
        #back.fill((100, 100, 100))
        skin = self.skins[idx]
        spider_surf = self.skin_to_spider_surf[skin]
        x, y = pos
        key = self.keys[idx]
        surface.blit(back,(x-w//2+offset[0], y-h//2+offset[1]))
        surface.blit(self.spider_shadow,(x-self.spider_shadow.get_width()//2+offset[0], y-150-self.spider_shadow.get_height()//2+offset[1]))
        surface.blit(spider_surf,(x-spider_surf.get_width()//2+offset[0], y-160-spider_surf.get_height()//2+offset[1]+self.spider_hop(idx)))
        key_name = pygame.key.name(key)
        font = self.long_key_font
        if len(key_name) <= 1 or key_name in [f"f{n}" for n in range(1, 13)]:
            key_name = key_name.upper()
            font = self.key_font
        if key_name == "backspace":
            key_name = "back space"
        key_name_surfs = [font.render(word, 1, (255, 255, 255)) for word in key_name.split()]
        yoff = -20*len(key_name_surfs)-1
        for key_name_surf in key_name_surfs:
            surface.blit(key_name_surf,(x-key_name_surf.get_width()//2+offset[0], y+30-key_name_surf.get_height()//2+offset[1]+yoff))
            yoff += 40
        note = [self.note_font.render(word, 1, (200, 200, 220)) for word in ["Press again","to change skin"]]
        yoff= -10
        for line in note:
            surface.blit(line,(x-line.get_width()//2+offset[0],y+90-line.get_height()//2+offset[1]+yoff))
            yoff += 20

    def main(self):
        while not self.over:
            dt, events = self.game.update_globals()

            for event in events:
                if event.type == pygame.KEYDOWN and self.black_target_alpha == 0:
                    self.pressed(event.key)

            self.screen.fill((20, 20, 20))
            self.draw_lines(self.screen)

            da = self.black_target_alpha - self.black_alpha
            if da:
                da = da/abs(da) * 800 * dt
            self.black_alpha = c.approach(self.black_alpha, self.black_target_alpha, da)
            if abs(self.black_alpha) < 2:
                self.black_alpha = 0

            for idx, item in enumerate(self.since_click):
                self.since_click[idx] += dt

            for idx, x in enumerate(self.xs):
                d = idx - x
                self.xs[idx] = c.approach(x, idx, d*dt*12)

            xoff = math.sin(time.time() * 37) * self.shake_mag
            yoff = math.sin(time.time() * 40) * self.shake_mag
            self.shake_mag *= 0.1**dt
            self.shake_mag = c.approach(self.shake_mag, 0, -20*dt)
            offset = xoff, yoff

            if len(self.keys) < 2:
                self.button.disable()
            else:
                self.button.enable()
            self.button.update(dt, events)

            x = c.WINDOW_WIDTH//2 - 750//2
            y = c.WINDOW_HEIGHT//2

            self.draw_title_line(self.screen, offset=offset)
            self.button.draw(self.screen, offset[0], offset[1])

            for idx, item in enumerate(self.keys):
                xoff, yoff = offset
                xoff += self.xs[idx]*250
                if self.black_target_alpha == 255:
                    yoff = offset[1] - ((self.black_alpha/9)**2) + 1.5*self.black_alpha
                self.draw_player_preview(self.screen, idx, (x, y), offset=(xoff, yoff))

            self.black.set_alpha(self.black_alpha)
            if self.black_alpha > 0:
                self.screen.blit(self.black, (0, 0))

            self.game.flip()

            if self.black_target_alpha == 255 and self.black_alpha >= 255:
                self.over=True
                self.game.next_scene = RoomScene(self.game)

class ResultsScreen(Scene):

    def __init__(self, game):
        super().__init__(game)
        self.keys = []
        self.skins = []
        self.xs = []
        self.since_click = []
        self.skin_to_spider_surf = {skin: self.game.get_static(c.image_path(f"spider_{skin}.png")) for skin in range(1, 5)}
        self.over = False

        self.black = pygame.Surface(c.WINDOW_SIZE)
        self.black.fill((0, 0, 0))
        self.black_alpha = 255
        self.black_target_alpha = 0

        self.countdown = 10

        self.key_font = pygame.font.Font(c.fonts_path("yoster.ttf"), 75)
        self.long_key_font = pygame.font.Font(c.fonts_path("yoster.ttf"), 40)
        self.note_font = pygame.font.Font(c.fonts_path("yoster.ttf"), 20)
        self.spider_shadow = pygame.Surface((64, 64))
        self.spider_shadow.fill((255, 255, 255))
        pygame.draw.circle(self.spider_shadow, (0, 0, 0), (32, 32), 32)
        self.spider_shadow.set_alpha(40)
        self.spider_shadow.set_colorkey((255, 255, 255))
        self.player_frame = pygame.transform.scale2x(pygame.image.load(c.image_path("player_frame.png")))

        self.since_click = [0 for _ in self.game.key_list]

        self.crown = self.game.get_static(c.image_path("crown.png"))

    def draw_lines(self, surface, offset=(0, 0)):
        x = (time.time()*20)%30
        while x < c.WINDOW_WIDTH + c.WINDOW_HEIGHT:
            x_end = x - c.WINDOW_HEIGHT
            pygame.draw.line(surface, (40, 30, 10), (x, c.WINDOW_HEIGHT), (x_end, 0), 6)
            x += 30

    def next_scene(self):
        #self.over = True
        self.black_target_alpha = 255

    def spider_hop(self, idx):
        x = self.since_click[idx] * 6
        y = -(-x**2 + x)*60
        return min(y, 0)

    def draw_title_line(self, surface, offset=(0, 0)):
        line = self.long_key_font.render(f"Next stage in {int(self.countdown+1)}", 1, (255, 255, 255))
        y = c.WINDOW_HEIGHT - 80 + 4 * math.sin(time.time()*3)
        surface.blit(line, (c.WINDOW_WIDTH//2-line.get_width()//2+offset[0], y+offset[1]))

    def draw_player_preview(self, surface, idx, pos, offset=(0, 0)):
        offset = offset[0] + 3*math.sin(time.time()*4+idx), offset[1] - 50 + 4*math.cos(time.time()*5+idx)
        w = 225
        h = 350
        back = self.player_frame
        #back.fill((100, 100, 100))
        skin = self.game.skin_list[idx]
        spider_surf = self.skin_to_spider_surf[skin]
        x, y = pos
        key = self.game.key_list[idx]
        surface.blit(back,(x-w//2+offset[0], y-h//2+offset[1]))
        surface.blit(self.spider_shadow,(x-self.spider_shadow.get_width()//2+offset[0], y-150-self.spider_shadow.get_height()//2+offset[1]))
        surface.blit(spider_surf,(x-spider_surf.get_width()//2+offset[0], y-160-spider_surf.get_height()//2+offset[1]+self.spider_hop(idx)))
        if self.game.win_list[idx] == max(self.game.win_list):
            surface.blit(self.crown, (x-self.crown.get_width()//2+offset[0], y-160-spider_surf.get_height()//2+offset[1]+self.spider_hop(idx)-4))
        key_name = pygame.key.name(key)
        font = self.long_key_font
        if len(key_name) <= 1 or key_name in [f"f{n}" for n in range(1, 13)]:
            key_name = key_name.upper()
            font = self.key_font
        if key_name == "backspace":
            key_name = "back space"
        key_name_surfs = [font.render(word, 1, (255, 255, 255)) for word in key_name.split()]
        yoff = -20*len(key_name_surfs)-1
        for key_name_surf in key_name_surfs:
            surface.blit(key_name_surf,(x-key_name_surf.get_width()//2+offset[0], y-20-key_name_surf.get_height()//2+offset[1]+yoff))
            yoff += 40
        note_text = []
        if self.game.win_list[idx] == max(self.game.win_list):
            note_text = ["Current","leader"]
        note = [self.note_font.render(word, 1, (200, 200, 220)) for word in note_text]
        yoff= -10
        for line in note:
            surface.blit(line,(x-line.get_width()//2+offset[0],y+50-line.get_height()//2+offset[1]+yoff))
            yoff += 20

        wins_text = f"{self.game.win_list[idx]} wins"
        render = self.long_key_font.render(wins_text, 1, (255, 255, 255))
        surface.blit(render, (x - render.get_width()//2+offset[0], y+105-render.get_height()//2+offset[1]))

    def main(self):
        while not self.over:
            dt, events = self.game.update_globals()

            self.countdown -= dt

            if self.countdown <= 0and self.black_target_alpha <255:
                self.black_target_alpha = 255
                self.game.cut_off_noise.play()

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key in self.game.key_list:
                        self.countdown = int(self.countdown)
                        self.game.button_noise.play()

            self.screen.fill((20, 20, 20))
            self.draw_lines(self.screen)

            da = self.black_target_alpha - self.black_alpha
            if da:
                da = da/abs(da) * 800 * dt
            self.black_alpha = c.approach(self.black_alpha, self.black_target_alpha, da)
            if abs(self.black_alpha) < 2:
                self.black_alpha = 0

            for idx, item in enumerate(self.since_click):
                self.since_click[idx] += dt

            for idx, x in enumerate(self.xs):
                d = idx - x
                self.xs[idx] = c.approach(x, idx, d*dt*12)

            xoff = math.sin(time.time() * 37) * self.shake_mag
            yoff = math.sin(time.time() * 40) * self.shake_mag
            self.shake_mag *= 0.1**dt
            self.shake_mag = c.approach(self.shake_mag, 0, -20*dt)
            offset = xoff, yoff
            x = c.WINDOW_WIDTH//2 - 750//2
            y = c.WINDOW_HEIGHT//2

            self.draw_title_line(self.screen, offset=offset)

            for idx, item in enumerate(self.game.key_list):
                xoff, yoff = offset
                xoff += idx*250
                if self.black_target_alpha == 255:
                    yoff = offset[1] - ((self.black_alpha/9)**2) + 1.5*self.black_alpha
                self.draw_player_preview(self.screen, idx, (x, y), offset=(xoff, yoff))

            self.black.set_alpha(self.black_alpha)
            if self.black_alpha > 0:
                self.screen.blit(self.black, (0, 0))

            self.game.flip()

            if self.black_target_alpha == 255 and self.black_alpha >= 255:
                self.over=True
                self.game.next_scene = RoomScene(self.game)

class StarFishScene(Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo = pygame.image.load(c.image_path("star_fish.png"))
        self.logo = pygame.transform.scale2x(self.logo)
        self.age = 0
        self.black = pygame.Surface(c.WINDOW_SIZE)
        self.black.fill((0, 0, 0))
        self.duration = 2.5
        self.angle = -self.duration//2 * 8

    def next_scene(self):
        return CharacterSelect(self.game)

    def main(self):
        duration = self.duration
        while True:
            dt, events = self.game.update_globals()
            self.age += dt
            self.screen.fill((0, 0, 0))
            self.angle += dt*10
            logo = pygame.transform.rotate(self.logo, self.angle)
            x = c.WINDOW_WIDTH//2 - logo.get_width()//2
            y = c.WINDOW_HEIGHT//2 - logo.get_height()//2
            self.screen.blit(logo, (x, y))
            fadein = 0.5
            fadeout = 0.7
            if self.age < fadein:
                alpha = 255 - 255*self.age/fadein
            elif self.age < duration - fadeout:
                alpha = 0
            else:
                start = duration - fadeout
                alpha = (self.age - start)/fadeout * 255
            self.black.set_alpha(alpha)
            self.screen.blit(self.black, (0, 0))
            pygame.display.flip()

            if self.age > duration:
                self.game.next_scene = self.next_scene()
                break

class LD47Scene(StarFishScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo = pygame.image.load(c.image_path("ld47.png"))

    def next_scene(self):
        return StarFishScene(self.game)

class RoomScene(Scene):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skin_list = self.game.skin_list
        self.key_list = self.game.key_list
        self.room_num = random.choice([1, 2, 3, 4, 5, 6, 7])
        self.checking_inputs = False
        self.countdown = 3
        self.numbers = [self.game.get_static(c.image_path("1.png")),
                        self.game.get_static(c.image_path("2.png")),
                        self.game.get_static(c.image_path("3.png"))]

    def update_powerup_spawning(self, dt, events):
        self.next_powerup -= dt
        if self.next_powerup <= 0:
            self.random_powerup()
            self.next_powerup = random.random()*20 + 20

    def random_powerup(self):
        weights = [(SlipperySocksPowerup, 10),
                    (FastSpinPowerup, 10),
                    (DoubleShotPowerup, 7),
                    (BouncyPowerup, 7)]
        total = sum([i[1] for i in weights])
        choose = int(random.random() * total)
        pos = random.choice(self.game.room.powerup_spawns)
        if pos in [(item.x, item.y) for item in self.game.powerups]:
            return
        on = 0
        for item in weights:
            on += item[1]
            if on > choose:
                self.game.powerups.append(item[0](self.game, pos=pos))
                break

    def main(self):
        self.game.reset_room()
        self.room = Room.from_file(self.game, c.rooms_path(f"{self.room_num}.txt"))
        self.game.room = self.room
        self.next_powerup = 10
        self.players = []
        for i, skin in enumerate(self.skin_list):
            player = Player(self.game, skin=skin, player_num=i+1)
            self.players.append(player)
            player.bind_key(self.key_list[i])

        self.black = pygame.Surface(c.WINDOW_SIZE)
        self.black.fill((0, 0, 0))
        self.black_target_alpha = 0
        self.black_alpha = 255

        #self.game.powerups.append(BouncyPowerup(self.game, pos=(500,300)))
        #self.players[0].die()
        is_over = False
        self.age = 0

        while True:
            dt, events = self.game.update_globals()
            self.age += dt

            if not self.checking_inputs:
                for player in self.players:
                    player.controller.disabled = True
            else:
                for player in self.players:
                    if not player.dead:
                        player.controller.disabled = False

            alive_count = sum([not player.dead for player in self.players])
            if alive_count <= 1 and not is_over:
                is_over = True
            if is_over:
                self.black_target_alpha = 255

            ba = self.black_target_alpha - self.black_alpha
            if ba < 0:
                self.black_alpha -= dt*1200
            elif ba > 0:
                self.black_alpha += dt * 200
            if self.black_alpha > 255:
                self.black_alpha = 255
            if self.black_alpha <0:
                self.black_alpha = 0


            if self.countdown <= 100:
                self.countdown -= dt
                if self.countdown <= 0.5:
                    self.checking_inputs = True

            self.update_powerup_spawning(dt, events)

            self.room.update(dt, events)
            for particle in list(self.game.particles):
                particle.update(dt, events)
            for bullet in list(self.game.bullets):
                bullet.update(dt, events)
            for entity in self.game.entities[::-1]:
                entity.update(dt, events)
            for player in self.players[::-1]:
                player.update(dt, events)
            for powerup in self.game.powerups[::-1]:
                powerup.update(dt, events)

            xoff = math.sin(time.time() * 37) * self.shake_mag
            yoff = math.sin(time.time() * 40) * self.shake_mag
            self.shake_mag *= 0.1**dt
            self.shake_mag = c.approach(self.shake_mag, 0, -20*dt)
            offset = xoff, yoff

            self.screen.fill((0, 0, 0))
            #if self.player.charging:
            #    self.screen.fill((200, 200, 200))
            self.room.draw(self.screen, offset, layer=0)
            for particle in self.game.particles - self.game.top_particles:
                particle.draw(self.screen, offset)
            for entity in self.game.entities:
                entity.draw(self.screen, offset)
            self.players.sort(key=lambda x:x.y)
            for player in self.players:
                player.draw(self.screen, offset)
            for powerup in self.game.powerups:
                if powerup.landed:
                    powerup.draw(self.screen, offset)
            self.room.draw(self.screen, offset, layer=2)
            for powerup in self.game.powerups:
                if not powerup.landed:
                    powerup.draw(self.screen, offset)
            for bullet in self.game.bullets:
                bullet.draw(self.screen, offset)
            for particle in self.game.top_particles:
                particle.draw(self.screen, offset)

            number = None
            if self.countdown >= 2:
                number = 3
            elif self.countdown >= 1:
                number = 2
            elif self.countdown > 0:
                number = 1
            if self.countdown >10:
                number = None
            if number:
                number_surf = self.numbers[number-1]
                scale = min(1+0.15*math.sin(self.age*math.pi*2), self.countdown*2)
                number_surf = pygame.transform.scale(number_surf, (int(number_surf.get_width()*scale), int(number_surf.get_height()*scale)))
                x = c.WINDOW_WIDTH//2 - number_surf.get_width()//2
                y = c.WINDOW_HEIGHT//2 - number_surf.get_height()//2
                number_surf.set_colorkey((255, 0, 0))
                alpha =None
                number_surf.set_alpha(min(254, self.countdown*500 - 40))
                self.screen.blit(number_surf, (x, y))

            if self.black_alpha > 0:
                self.black.set_alpha(self.black_alpha)
                self.screen.blit(self.black, (0, 0))

            self.game.flip()

            if is_over and self.black_alpha >= 255:
                for idx, player in enumerate(self.players):
                    if not player.dead:
                        actual_idx = self.game.skin_list.index(player.skin)
                        self.game.win_list[actual_idx] += 1
                self.game.next_scene = ResultsScreen(self.game)
                break


if __name__ == '__main__':
    Game().main()

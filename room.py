import pygame
import constants as c
import random

class Tile:
    def __init__(self, game, room, coords):
        self.game = game
        self.surface = pygame.Surface((c.TILE_SIZE, c.TILE_SIZE))
        self.surface.fill((200, 200, 200))
        self.room = room

        self.layer = 0

        self.blocking = False
        self.hazardous = False

        self.x_coord = coords[0]
        self.y_coord = coords[1]
        self.x = (c.WINDOW_WIDTH - c.TILE_SIZE*(room.width-1))//2 + c.TILE_SIZE * coords[0]
        self.y = (c.WINDOW_HEIGHT - c.TILE_SIZE*(room.height-1))//2 + c.TILE_SIZE * coords[1]

    def update(self, dt, events):
        pass

    def draw(self, surface, offset=(0, 0)):
        x = self.x - self.surface.get_width()//2 + offset[0]
        y = self.y - self.surface.get_height()//2 + offset[1]
        surface.blit(self.surface, (x, y))

class EmptyTile(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.surface = self.game.get_static(c.image_path("grass.png"))
        self.surface = pygame.transform.scale2x(self.surface)

class BlockingTile(Tile):
    def __init__(self, game, room, coords):
        super().__init__(game, room, coords)
        self.surfaces = {}
        for i, item in enumerate(["border_left.png",
                                  "border_right.png",
                                  "border_bottom.png",
                                  "border_top.png",
                                  "border_in_bl.png",
                                  "border_in_tl.png",
                                  "border_in_tr.png",
                                  "border_in_br.png",
                                  "border_out_bl.png",
                                  "border_out_tl.png",
                                  "border_out_tr.png",
                                  "border_out_br.png"]):
            self.surfaces[i] = pygame.transform.scale2x(self.game.get_static(c.image_path(item)))
        self.surface = pygame.transform.scale2x(self.surface)
        self.blocking = True
        self.layer = 2
        self.black = pygame.Surface((c.TILE_SIZE, c.TILE_SIZE))
        self.black.fill((0, 0, 0))
        self.black_t = self.black.copy()
        self.black_t.set_alpha(40)
        self.black_t.set_colorkey((255, 255, 255))
        self.has_neighbored = False

    def set_black_t_corner(self, corner = (0, 0)):
        self.black_t.fill((255, 255, 255))
        corner = [1 - c for c in corner]
        cx = self.black_t.get_width()//2
        cy = self.black_t.get_height()//2
        pygame.draw.circle(self.black_t, (0, 0, 0), (cx, cy), self.black_t.get_width()//2)
        if corner[0]:
            self.black_t.blit(self.black, (cx, 0))
        else:
            self.black_t.blit(self.black, (-cx, 0))
        if corner[1]:
            self.black_t.blit(self.black, (0, cy))
        else:
            self.black_t.blit(self.black, (0, -cy))

    def draw(self, surface, offset=(0, 0)):
        old_surf = self.surface
        if not self.has_neighbored:
            self.has_neighbored = True
            neighbors = self.room.neighbors(self.x_coord, self.y_coord)
            if neighbors[1][0] == "X" and neighbors[0][1] == "X" and neighbors[2][1] == "X" and neighbors[1][2] != "X":
                self.surface = self.surfaces[0]
            elif neighbors[1][2] == "X" and neighbors[0][1] == "X" and neighbors[2][1] == "X" and neighbors[1][0] != "X":
                self.surface = self.surfaces[1]
            elif neighbors[1][0] == "X" and neighbors[0][1] == "X" and neighbors[1][2] == "X" and neighbors[2][1] != "X":
                self.surface = self.surfaces[3]
            elif neighbors[2][1] == "X" and neighbors[1][0] == "X" and neighbors[1][2] == "X" and neighbors[0][1] != "X":
                self.surface = self.surfaces[2]
            elif all([all([item=="X" for item in row]) for row in neighbors]):
                self.surface = self.black
            elif self.four_edges(neighbors) and neighbors[0][2] != "X":
                self.surface = self.surfaces[4]
            elif self.four_edges(neighbors) and neighbors[2][2] != "X":
                self.surface = self.surfaces[5]
            elif self.four_edges(neighbors) and neighbors[2][0] != "X":
                self.surface = self.surfaces[6]
            elif self.four_edges(neighbors) and neighbors[0][0] != "X":
                self.surface = self.surfaces[7]
            elif self.only_edges(neighbors) == [1, 0, 0, 1]:
                self.surface = self.surfaces[8]
                if self.surface != old_surf:
                    self.set_black_t_corner((0, 1))
            elif self.only_edges(neighbors) == [0, 0, 1, 1]:
                self.surface = self.surfaces[9]
                if self.surface != old_surf:
                    self.set_black_t_corner((0, 0))
            elif self.only_edges(neighbors) == [0, 1, 1, 0]:
                self.surface = self.surfaces[10]
                if self.surface != old_surf:
                    self.set_black_t_corner((1, 0))
            elif self.only_edges(neighbors) == [1, 1, 0, 0]:
                self.surface = self.surfaces[11]
                if self.surface != old_surf:
                    self.set_black_t_corner((1, 1))
            else:
                self.surface = pygame.Surface((c.TILE_SIZE,c.TILE_SIZE))
                self.surface.fill((50, 50, 50))

        x = self.x - c.TILE_SIZE//2 + offset[0] + 12
        y = self.y - c.TILE_SIZE//2 + offset[1] + 20
        surface.blit(self.black_t, (x, y))
        super().draw(surface, offset=offset)

    def four_edges(self, neighbors):
        if neighbors[0][1] == "X" and neighbors[1][0] == "X" and neighbors[1][2] == "X" and neighbors[2][1] == "X":
            return True

    def only_edges(self, neighbors):
        return [item=="X" for item in (neighbors[0][1], neighbors[1][0], neighbors[2][1], neighbors[1][2])]



class Door(BlockingTile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.open_surface = pygame.Surface((c.TILE_SIZE, c.TILE_SIZE))
        self.open_surface.fill((180, 190, 220))

    def draw(self, surface, offset=(0, 0)):
        if self.blocking:
            super().draw(surface, offset=offset)
        else:
            self.surface, self.open_surface = self.open_surface, self.surface
            super().draw(surface, offset=offset)
            self.surface, self.open_surface = self.open_surface, self.surface

    def lock(self):
        self.blocking = True

    def unlock(self):
        self.blocking = False

class Room:
    @staticmethod
    def from_file(game, path):
        with open(path, "r") as f:
            lines = [line.replace("D","X") for line in f.readlines()]
        width = len(lines[0].strip())
        height = len(lines)
        room = Room(game, width, height, randomize=False)
        room.lines = lines
        room.width, room.height = width, height
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if char == "X" or char=="D":
                    room.objects[y][x].append(BlockingTile(game, room, (x, y)))
                if char in [".", "X", "D", "1", "2", "3", "4", "P"]:
                    room.objects[y][x].append(EmptyTile(game, room, (x, y)))
                    if char in ["1", "2", "3", "4"]:
                        room.spawns[int(char)] = room.cell_to_world(x, y)
                    if char in ["P"]:
                        room.powerup_spawns.append(room.cell_to_world(x, y))
                # if char == "D":
                #     door = Door(game, room, (x, y))
                #     room.objects[y][x].append(door)
                #     room.doors.append(door)
        return room

    def get_rect(self):
        w = self.width * c.TILE_SIZE
        h = self.height * c.TILE_SIZE
        x, y = self.cell_to_world(-0.5, -0.5)
        return (x, y, w, h)

    def neighbors(self, x0, y0):
        array = [[[] for _ in range(3)] for _ in range(3)]
        for x in [x0 - 1, x0, x0 + 1]:
            for y in [y0 - 1, y0, y0+1]:
                if x < 0 or y < 0 or x >= self.width or y >= self.height:
                    array[y-y0+1][x-x0+1] = "X"
                else:
                    array[y-y0+1][x-x0+1] = self.lines[y][x]
        return array

    def preview(self):
        surf = pygame.Surface(c.WINDOW_SIZE)
        self.draw(surf)
        self.draw(surf, layer=2)
        surf = pygame.transform.scale(surf, (surf.get_width()//4, surf.get_height()//4))
        return surf

    def __init__(self, game, width, height, randomize=True):
        self.game = game
        self.width = width
        self.height = height
        self.doors = []
        self.powerup_spawns = []
        self.spawns = {}
        if randomize:
            self.objects = [[[self.random_tile(x, y)] for x in range(width)] for y in range(height)]
        else:
            self.objects = [[[] for x in range(width)] for y in range(height)]

    def some_doors_are_locked(self):
        return any([door.blocking for door in self.doors])

    def lock_doors(self):
        for door in self.doors:
            door.lock()

    def unlock_doors(self):
        for door in self.doors:
            door.unlock()

    def random_tile(self, x, y):
        if random.random() < 0.1:
            return BlockingTile(self.game, self, (x, y))
        else:
            return EmptyTile(self.game, self, (x, y))

    def pop_random(self):
        for cell in self.cell_iter():
            cell.append(self.random_tile())

    def cell_iter(self):
        for row in self.objects:
            for cell in row:
                yield cell

    def item_iter(self):
        for cell in self.cell_iter():
            for item in cell:
                yield item

    def update(self, dt, events):
        for item in self.item_iter():
            item.update(dt, events)

        if not self.game.entities and self.some_doors_are_locked():
            self.unlock_doors()

    def draw(self, surface, offset=(0, 0), layer=None):
        for item in self.item_iter():
            if item.layer == layer or layer is None:
                item.draw(surface, offset=offset)

    def world_to_cell(self, x, y, discrete=False):
        x -= c.WINDOW_WIDTH//2 - (self.width-1)/2 * c.TILE_SIZE
        y -= c.WINDOW_HEIGHT//2 - (self.height-1)/2 * c.TILE_SIZE
        x /= c.TILE_SIZE
        y /= c.TILE_SIZE
        if discrete:
            x = int(x + 0.5)
            y = int(y + 0.5)
        return (x, y)

    def cell_to_world(self, x, y):
        x = (c.WINDOW_WIDTH - c.TILE_SIZE*(self.width-1))//2 + c.TILE_SIZE * x
        y = (c.WINDOW_HEIGHT - c.TILE_SIZE*(self.height-1))//2 + c.TILE_SIZE * y
        return x, y

    def cell_is_blocking(self, x, y):
        if x < 0 or x >= self.width:
            return False
        if y < 0 or y >= self.height:
            return False
        cell = self.objects[y][x]
        for item in cell:
            if item.blocking:
                return True
        return False

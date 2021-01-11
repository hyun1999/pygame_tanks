import os.path
import pygame
from tanks.constants import PIXEL_RATIO
from tanks.grid import cell_to_screen, get_rect
from tanks.time import delta_time
from tanks.directions import *
from tanks.TankControlScheme import TankControlScheme


def load_image(name):
    image = pygame.image.load(os.path.join('data', name))
    rect = image.get_rect()
    return pygame.transform.scale(image, (rect.w * PIXEL_RATIO, rect.h * PIXEL_RATIO))


def cut_sheet(sheet, columns, rows):
    frames = []
    w, h = sheet.get_width() // columns, sheet.get_height() // rows
    for j in range(rows):
        for i in range(columns):
            frames.append(sheet.subsurface(pygame.Rect(w * i, h * j, w, h)))
    return frames


class SpriteBase(pygame.sprite.Sprite):
    sheet = None

    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.image = self.sheet
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(x, y)


class GridSprite(SpriteBase):
    char = None
    destroyable = False
    tank_obstacle = True
    shell_obstacle = True

    def __init__(self, grid_x, grid_y, *groups):
        super().__init__(*cell_to_screen(grid_x, grid_y), *groups)


class ConcreteWall(GridSprite):
    sheet = load_image('concrete.png')
    char = '#'


class BrickWall(GridSprite):
    sheet = load_image('brick.png')
    char = '%'
    destroyable = True


class Bush(GridSprite):
    sheet = load_image('bush.png')
    char = '*'
    tank_obstacle = False
    shell_obstacle = False


class Water(GridSprite):
    sheet = load_image('water.png')
    char = '~'
    shell_obstacle = False


class Shell(SpriteBase):
    sheet = load_image('shell.png')
    speed = 100

    def __init__(self, x, y, direction, *groups):
        rotate = 0
        self.vector_velocity = direction_to_vector(direction, self.speed)
        size = self.sheet.get_size()
        if direction == WEST:
            x -= size[0] * 1.5
            y -= size[1] / 2
            rotate = 90
        if direction == NORTH:
            x -= size[0] / 2
            y -= size[1]
        if direction == SOUTH:
            x -= size[0] / 2
            rotate = 180
        if direction == EAST:
            y -= size[1] / 2
            rotate = -90
        self.pos = pygame.Vector2(x, y)
        super().__init__(x, y, *groups)
        self.image = pygame.transform.rotate(self.image, rotate)

    def update(self):
        self.pos += self.vector_velocity * delta_time()
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y

        field = get_rect()

        if self.pos.x > field.right or self.pos.x < field.left or self.pos.y > field.bottom or self.pos.y < field.top:
            self.kill()
            return

        for group in self.groups():
            for sprite in group:
                if sprite is not self:
                    if self.is_collided_with(sprite):
                        if isinstance(sprite, GridSprite):
                            if sprite.destroyable:
                                sprite.kill()
                                self.kill()
                            elif sprite.shell_obstacle:
                                self.kill()
                        elif isinstance(sprite, Shell):
                            self.kill()
                            sprite.kill()

    def is_collided_with(self, sprite):
        return self.rect.colliderect(sprite.rect)


class Tank(SpriteBase):
    skins = load_image('tanks.png')
    speed = 50
    frames = cut_sheet(skins, 8, 1)

    def __init__(self, x, y, is_default_control_scheme, *groups):
        if is_default_control_scheme:
            self.sheets = self.frames[:4]
        else:
            self.sheets = self.frames[4:]
        self.sheet = self.sheets[0]
        super().__init__(x, y, *groups)
        self.control_scheme = TankControlScheme.default() if is_default_control_scheme else TankControlScheme.alternative()
        self.pos = pygame.Vector2(x, y)
        self.vector_velocity = pygame.Vector2(0, 0)
        self.flag = True

    def update(self):
        for group in self.groups():
            for sprite in group:
                if self.is_collided_with(sprite) and sprite is not self:
                    pass
                else:
                    if self.control_scheme.up_pressed():
                        self.image = self.sheets[0]
                        self._move(pygame.Vector2(0, -self.speed))

                    elif self.control_scheme.down_pressed():
                        self.image = self.sheets[2]
                        self._move(pygame.Vector2(0, self.speed))

                    elif self.control_scheme.right_pressed():
                        self.image = self.sheets[3]
                        self._move(pygame.Vector2(self.speed, 0))

                    elif self.control_scheme.left_pressed():
                        self.image = self.sheets[1]
                        self._move(pygame.Vector2(-self.speed, 0))

    def _move(self, vector):
        self.vector_velocity = vector
        self.pos += self.vector_velocity * delta_time()
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y

    def is_collided_with(self, sprite):
        return self.rect.colliderect(sprite.rect)

from abc import ABC, abstractmethod
from enum import Enum

import pygame as pg
import logging as log

from pygame.surface import Surface

SOFT_GREEN = (186, 254, 202)
BLUE = (0, 0, 248)

log.basicConfig(level=log.DEBUG)
pg.init()

KEN_STAGE_PATHS = [
    'assets/KenStage/frame_0_delay-0.2s.gif',
    'assets/KenStage/frame_1_delay-0.25s.gif',
    'assets/KenStage/frame_2_delay-0.02s.gif',
    'assets/KenStage/frame_3_delay-0.1s.gif',
    'assets/KenStage/frame_4_delay-0.2s.gif',
]

RYU_SPRITES_PATH = 'assets/Ryu.png'


class State(Enum):
    MOVE_RIGHT = 'move_right'
    MOVE_LEFT = 'move_left'
    IDLE = 'idle'
    ATTACK = 'attack'
    GUARD = 'guard'
    JUMP = 'jump'


class SpriteSheet(ABC):
    def __init__(self):
        self.current_num_frames = 0
        self.max_num_frames = 30
        self.index = 0

    @abstractmethod
    def get_sprite(self) -> Surface:
        pass


class BackgroundSprite(SpriteSheet):
    def __init__(self, paths: list[str]):
        super().__init__()
        self.bg_sprites = [pg.image.load(path).convert() for path in paths]

    def get_sprite(self) -> Surface:
        self.current_num_frames += 1
        if self.current_num_frames >= self.max_num_frames:
            self.current_num_frames = 0
            self.index = (self.index + 1) % len(self.bg_sprites)
        return self.bg_sprites[self.index]


class Player(SpriteSheet):
    def __init__(self, path: str, x: int, y: int, flip: bool):
        super().__init__()
        scaler = 2.5
        self.sprite = pg.image.load(path).convert()
        self.state = State.IDLE
        self.velocity = 4
        self.flip = flip

        self.idle_sprites: list[Surface] = [
            self.sprite.subsurface(pg.Rect(0, 0, 70, 110)),
            self.sprite.subsurface(pg.Rect(70, 0, 70, 110)),
            self.sprite.subsurface(pg.Rect(140, 0, 70, 110)),
            self.sprite.subsurface(pg.Rect(205, 0, 70, 110)),
            self.sprite.subsurface(pg.Rect(270, 0, 70, 110)),
        ]
        self.move_right_sprites: list[Surface] = [
            self.sprite.subsurface(pg.Rect(70, 120, 70, 110)),
            self.sprite.subsurface(pg.Rect(145, 120, 70, 110)),
            self.sprite.subsurface(pg.Rect(220, 120, 70, 110)),
        ]
        self.move_left_sprites: list[Surface] = [
            self.sprite.subsurface(pg.Rect(295, 120, 70, 110)),
            self.sprite.subsurface(pg.Rect(365, 120, 65, 110)),
            self.sprite.subsurface(pg.Rect(425, 120, 65, 110)),
            self.sprite.subsurface(pg.Rect(490, 120, 65, 110)),
        ]
        for sprite in self.idle_sprites + self.move_right_sprites + self.move_left_sprites:
            sprite.set_colorkey(BLUE, pg.RLEACCEL)

        self.idle_sprites = self.scale_sprite(self.idle_sprites, scaler)
        self.move_right_sprites = self.scale_sprite(self.move_right_sprites, scaler)
        self.move_left_sprites = self.scale_sprite(self.move_left_sprites, scaler)
        self.current_sprites = self.idle_sprites

        self.y = y - self.idle_sprites[0].get_height()
        self.x = x
        self.w = self.current_sprites[self.index].get_width()
        self.h = self.current_sprites[self.index].get_height()

    @staticmethod
    def scale_sprite(sprites: list[Surface], scaler: float) -> list[Surface]:
        return [
            pg.transform.scale(sprite, (sprite.get_width() * scaler, sprite.get_height() * scaler))
            for sprite in sprites
        ]

    @property
    def direction(self):
        return 0 if self.flip else 1

    def get_sprite(self) -> Surface:
        match self.state:
            case State.IDLE:
                self.current_sprites = self.idle_sprites
            case State.MOVE_RIGHT:
                self.current_sprites = self.move_right_sprites
            case State.MOVE_LEFT:
                self.current_sprites = self.move_left_sprites

        if self.index >= len(self.current_sprites):
            self.index = 0

        self.current_num_frames += 1
        if self.current_num_frames >= self.max_num_frames:
            self.current_num_frames = 0
            self.index = (self.index + 1) % len(self.current_sprites)

        if self.flip:
            return pg.transform.flip(self.current_sprites[self.index], True, False)
        return self.current_sprites[self.index]

    def get_coord(self) -> tuple[int, int]:
        return self.x, self.y

    def handle_input(self):
        key_pressed = pg.key.get_pressed()
        if key_pressed[pg.K_RIGHT] and (key_pressed[pg.K_LSHIFT] or key_pressed[pg.K_RSHIFT]):
            self.flip = False
        elif key_pressed[pg.K_LEFT] and (key_pressed[pg.K_LSHIFT] or key_pressed[pg.K_RSHIFT]):
            self.flip = True
        elif key_pressed[pg.K_RIGHT]:
            self.state = State.MOVE_LEFT if self.direction == 0 else State.MOVE_RIGHT
            self.x += self.velocity
            if self.x > 1280 - self.w:
                self.x = 1280 - self.w
        elif key_pressed[pg.K_LEFT]:
            self.state = State.MOVE_LEFT if self.direction == 1 else State.MOVE_RIGHT
            self.x -= self.velocity
            if self.x < 0:
                self.x = 0
        else:
            self.state = State.IDLE


class GameManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.screen_width = 1280
        self.screen_height = 720
        self.fps = 144
        self.screen = pg.display.set_mode((self.screen_width, self.screen_height))
        self.game_over = False
        self.clock = pg.time.Clock()
        self.timer = 90.0
        self.delta_t = 1 / self.fps
        self.bg_sprite: SpriteSheet = BackgroundSprite(KEN_STAGE_PATHS)
        self.player_idx = 0
        self.players: list[Player] = [
            Player(RYU_SPRITES_PATH, 50, 620, False),
            Player(RYU_SPRITES_PATH, self.screen_width - 230, 620, True),
        ]

    def run(self):
        # main loop
        while not self.game_over:
            # get single input
            self.players[self.player_idx].handle_input()

            for event in pg.event.get():
                match event.type:
                    case pg.QUIT:
                        self.game_over = True

            self.timer -= self.delta_t
            if self.timer <= 0:
                self.game_over = True

            self.clock.tick(self.fps)
            self.update()

        pg.quit()

    def update(self):
        self.screen.blit(
            pg.transform.scale(self.bg_sprite.get_sprite(), (self.screen_width, self.screen_height)),
            (0, 0),
        )
        self.screen.blit(
            self.players[self.player_idx].get_sprite(),
            self.players[self.player_idx].get_coord(),
        )
        self.screen.blit(
            self.players[1 - self.player_idx].get_sprite(),
            self.players[1 - self.player_idx].get_coord(),
        )
        pg.display.update()

    def log(self):
        # logs go here
        if self.debug:
            log.info(f'FPS: {round(self.clock.get_fps(), 2)}')


def main():
    GameManager(True).run()


if __name__ == '__main__':
    main()

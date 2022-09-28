from abc import ABC, abstractmethod

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
    def __init__(self, path: str, flip=False):
        super().__init__()
        scaler = 2.5
        self.sprite = pg.image.load(path).convert()
        self.flip = flip
        self.sprites: [Surface] = [
            self.sprite.subsurface(pg.Rect(0, 0, 70, 120)),
            self.sprite.subsurface(pg.Rect(70, 0, 70, 120)),
            self.sprite.subsurface(pg.Rect(140, 0, 70, 120)),
            self.sprite.subsurface(pg.Rect(205, 0, 70, 120)),
            self.sprite.subsurface(pg.Rect(270, 0, 70, 120)),
        ]
        for sprite in self.sprites:
            sprite.set_colorkey(BLUE, pg.RLEACCEL)

        self.sprites = [
            pg.transform.scale(sprite, (sprite.get_width() * scaler, sprite.get_height() * scaler))
            for sprite in self.sprites
        ]

    def get_sprite(self) -> Surface:
        self.current_num_frames += 1
        if self.current_num_frames >= self.max_num_frames:
            self.current_num_frames = 0
            self.index = (self.index + 1) % len(self.sprites)

        if self.flip:
            return pg.transform.flip(self.sprites[self.index], True, False)

        return self.sprites[self.index]

    def get_init_coord(self, x: int, y: int) -> tuple[int, int]:
        if self.flip:
            return x - self.sprites[0].get_width(), y - self.sprites[0].get_height()
        return x, y - self.sprites[0].get_height()


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
        self.player1 = Player(RYU_SPRITES_PATH)
        self.player2 = Player(RYU_SPRITES_PATH, True)

    def run(self):
        # main loop
        while not self.game_over:
            # get single input
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
            self.player1.get_sprite(),
            self.player1.get_init_coord(50, 630),
        )
        self.screen.blit(
            self.player2.get_sprite(),
            self.player2.get_init_coord(1230, 630),
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

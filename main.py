import pygame as pg
import logging as log

from pygame.sprite import Sprite
from pygame.surface import Surface

log.basicConfig(level=log.DEBUG)
pg.init()

KEN_STAGES = [
    'assets/KenStage/frame_0_delay-0.2s.gif',
    'assets/KenStage/frame_1_delay-0.25s.gif',
    'assets/KenStage/frame_2_delay-0.02s.gif',
    'assets/KenStage/frame_3_delay-0.1s.gif',
    'assets/KenStage/frame_4_delay-0.2s.gif',
]


class SpriteSheet(Sprite):
    def __init__(self, sheet_path: str):
        super().__init__()
        self.sprite_sheet = pg.image.load(sheet_path).convert()
        self.width = self.sprite_sheet.get_width()
        self.height = self.sprite_sheet.get_height()
        self.scaler = 1

    def scale(self, *args):
        assert len(args) in (1, 2), 'args must have 1 or 2 arguments'
        if len(args) == 1:
            self.width *= args[0]
            self.height *= args[0]
        else:
            self.width, self.height = args

        return self

    def get_sprite(self) -> Surface:
        return pg.transform.scale(self.sprite_sheet, (self.width, self.height))


class Player:
    def __init__(self):
        pass


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
        self.bg_sprites = [
            SpriteSheet(path).scale(self.screen_width, self.screen_height).get_sprite() for path in KEN_STAGES
        ]
        self.bg_index = 0
        self.bg_frames_count = 0

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
        self.bg_frames_count += 1
        if self.bg_frames_count >= 30:
            self.bg_frames_count = 0
            self.bg_index = (self.bg_index + 1) % len(self.bg_sprites)
        self.screen.blit(self.bg_sprites[self.bg_index], (0, 0))
        pg.display.flip()
        pg.display.update()

    def log(self):
        # logs go here
        if self.debug:
            log.info(f'FPS: {round(self.clock.get_fps(), 2)}')


def main():
    GameManager(True).run()


if __name__ == '__main__':
    main()

import pygame as pg


class GameManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pg.display.set_mode((self.screen_width, self.screen_height))
        self.game_over = False
        self.clock = pg.time.Clock()
        self.fps = round(self.clock.get_fps())

    def run(self):
        # main loop
        while not self.game_over:

            # get single input
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.game_over = True

            self.clock.tick(self.fps)

        pg.quit()

    def log(self):
        # logs go here
        if self.debug:
            pass


def main():
    GameManager().run()


if __name__ == '__main__':
    main()

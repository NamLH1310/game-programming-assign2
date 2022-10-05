import logging as log
from abc import ABC, abstractmethod
from enum import Enum

import pygame as pg
from pygame.surface import Surface

SOFT_GREEN = (186, 254, 202)
BLUE = (0, 0, 248)
RED = (255, 0, 0)


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


class Direction(Enum):
    LEFT = 0
    RIGHT = 1


class State(Enum):
    MOVE_RIGHT = 'move_right'
    MOVE_LEFT = 'move_left'
    IDLE = 'idle'
    ATTACK = 'attack'
    ATTACK2 = 'attack2'
    GUARD = 'guard'
    JUMP = 'jump'
    MOVE = 'move'
    KICK = 'kick'
    KICK2 = 'kick2'


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
    def __init__(self, path: str, x: int, y: int, direction: Direction):
        super().__init__()
        self.scaler = 2.5
        self.max_num_frames = 20
        self.sprite = pg.image.load(path).convert()
        self.state = State.IDLE
        self.prev_state = self.state
        self. velocity = 4
        self.direction = direction
        self.is_move_right = True
        self.ground_y: float = y
        self.hurt_box: dict[State, tuple[int, ...]] = {
            State.ATTACK: tuple(map(int, (15 * self.scaler, 20 * self.scaler, 40 * self.scaler, 80 * self.scaler))),
            State.GUARD: tuple(map(int, (15 * self.scaler, 20 * self.scaler, 40 * self.scaler, 80 * self.scaler))),
            State.JUMP: tuple(map(int, (15 * self.scaler, 20 * self.scaler, 40 * self.scaler, 80 * self.scaler))),
            State.IDLE: tuple(map(int, (15 * self.scaler, 20 * self.scaler, 40 * self.scaler, 80 * self.scaler))),
        }
        self.jump_height=12
        self.gravity=0.2
        self.jump_speed = self.jump_height
        self.hit_box: tuple = (70 * self.scaler, 20 * self.scaler, 50 * self.scaler, 10 * self.scaler)

        self.idle_sprites: list[Surface] = [
            self.sprite.subsurface(pg.Rect(0, 10, 70, 95)),
            self.sprite.subsurface(pg.Rect(70, 10, 70, 95)),
            self.sprite.subsurface(pg.Rect(140, 10, 70, 95)),
            self.sprite.subsurface(pg.Rect(205, 10, 70, 95)),
            self.sprite.subsurface(pg.Rect(270, 10, 70, 95)),
        ]

        self.move_sprites: list[list[Surface]] = [
            [
                self.sprite.subsurface(pg.Rect(70, 130, 70, 90)),
                self.sprite.subsurface(pg.Rect(145, 130, 70, 90)),
                self.sprite.subsurface(pg.Rect(220, 130, 70, 90)),
            ],
            [
                self.sprite.subsurface(pg.Rect(295, 125, 70, 90)),
                self.sprite.subsurface(pg.Rect(365, 125, 65, 90)),
                self.sprite.subsurface(pg.Rect(425, 125, 65, 90)),
                self.sprite.subsurface(pg.Rect(490, 125, 65, 90)),
            ],
        ]

        self.frame_idx_hit_box: dict[State, list[int]] = {
            State.ATTACK: [2, 8, 9, 12],
            State.KICK: [2, 5],
        }

        self.hit_box: dict[State, list[pg.Rect]] = {
            State.ATTACK: [

            ],
            State.KICK: [

            ],
        }

        self.attack_sprites: list[Surface] = [
            # first animation
            self.sprite.subsurface(pg.Rect(0, 465, 70, 95)),
            self.sprite.subsurface(pg.Rect(80, 465, 70, 95)),
            self.sprite.subsurface(pg.Rect(160, 465, 125, 95)),
            # second animation
            self.sprite.subsurface(pg.Rect(620, 465, 80, 95)),
            self.sprite.subsurface(pg.Rect(710, 465, 80, 95)),
            self.sprite.subsurface(pg.Rect(800, 465, 80, 95)),
            self.sprite.subsurface(pg.Rect(895, 460, 95, 105)),
            self.sprite.subsurface(pg.Rect(1000, 465, 95, 95)),
            self.sprite.subsurface(pg.Rect(1105, 465, 110, 95)),
            self.sprite.subsurface(pg.Rect(1225, 470, 110, 90)),
            # third animation
            self.sprite.subsurface(pg.Rect(290, 680, 70, 95)),
            self.sprite.subsurface(pg.Rect(370, 680, 95, 95)),
            self.sprite.subsurface(pg.Rect(475, 660, 85, 120)),
        ]

        self.guard_sprites: list[Surface] = [
            self.sprite.subsurface(pg.Rect(275, 355, 70, 100)),
        ]

        self.jump_sprites: list[Surface] = [
            self.sprite.subsurface(pg.Rect(0, 250, 65, 110)),
            self.sprite.subsurface(pg.Rect(65, 240, 65, 110)),
            self.sprite.subsurface(pg.Rect(130, 230, 65, 95)),
            self.sprite.subsurface(pg.Rect(190, 230, 65, 85)),
            self.sprite.subsurface(pg.Rect(255, 235, 60, 80)),
            self.sprite.subsurface(pg.Rect(310, 235, 65, 90)),
            self.sprite.subsurface(pg.Rect(370, 250, 65, 105)),
        ]

        self.kick_sprites: list[Surface] = [
            # first animation
            self.sprite.subsurface(pg.Rect(10, 915, 65, 110)),
            self.sprite.subsurface(pg.Rect(85, 920, 70, 100)),
            self.sprite.subsurface(pg.Rect(160, 920, 120, 100)),
            self.sprite.subsurface(pg.Rect(280, 920, 70, 100)),
            # second animation
            self.sprite.subsurface(pg.Rect(350, 920, 60, 100)),
            self.sprite.subsurface(pg.Rect(415, 920, 90, 100)),
            self.sprite.subsurface(pg.Rect(350, 920, 60, 100)),

        ]

        for sprite in \
                self.idle_sprites + self.attack_sprites + \
                self.move_sprites[0] + self.move_sprites[1] + \
                self.jump_sprites + self.kick_sprites + \
                self.guard_sprites:
            sprite.set_colorkey(BLUE, pg.RLEACCEL)

        self.idle_sprites = self.scale_sprite(self.idle_sprites, self.scaler)
        self.attack_sprites = self.scale_sprite(self.attack_sprites, self.scaler)
        self.move_sprites[0] = self.scale_sprite(self.move_sprites[0], self.scaler)
        self.move_sprites[1] = self.scale_sprite(self.move_sprites[1], self.scaler)
        self.jump_sprites = self.scale_sprite(self.jump_sprites, self.scaler)
        self.kick_sprites = self.scale_sprite(self.kick_sprites, self.scaler)
        self.guard_sprites = self.scale_sprite(self.guard_sprites, self.scaler)
        self.current_sprites = self.idle_sprites

        self.cap_y=y-self.idle_sprites[0].get_height()+20
        self.y = y 
        self.x = x
        self.w = self.current_sprites[self.index].get_width()
        self.h = self.current_sprites[self.index].get_height()
        self.prev_x = x
        self.lock = False

    def update_sprite(self, sprites: list[Surface]):
        self.current_sprites = sprites

    def get_direction_idx(self):
        return 1 if self.direction == Direction.LEFT else 0

    @staticmethod
    def scale_sprite(sprites: list[Surface], scaler: float) -> list[Surface]:
        return [
            pg.transform.scale(sprite, (sprite.get_width() * scaler, sprite.get_height() * scaler))
            for sprite in sprites
        ]

    # def get_hit(self, opp):
    #     """
    #     :param opp:
    #     :type opp: Player
    #     :return:
    #     """
    #     if (opp.state != State.ATTACK) or self.state == State.GUARD:
    #         return
    #
    #     x, y = opp.get_coord()
    #
    #     hit_box = opp.hit_box
    #
    #     flip = opp.direction
    #
    #     addon = 0
    #
    #     if self.state == State.ATTACK:
    #         if self.index == 0:
    #             addon = self.hit_box[2]
    #
    #     min = (x + hit_box[0] - opp.w, y + hit_box[1]) if flip else (x + hit_box[0], y + hit_box[1])
    #     max = (min[0] + hit_box[2], min[1] + hit_box[3])
    #     hurt_box_min = (
    #         self.x + self.hurt_box[self.state][0] + addon, self.y + self.hurt_box[self.state][1]) if flip else (
    #         self.x + self.hurt_box[self.state][0], self.y + self.hurt_box[self.state][1])
    #     hurt_box_max = (hurt_box_min[0] + self.hurt_box[self.state][2], hurt_box_min[1] + self.hurt_box[self.state][3])
    #     if (hurt_box_min[0] > max[0] or
    #             hurt_box_min[1] > max[1] or
    #             hurt_box_max[0] < min[0] or
    #             hurt_box_max[1] < min[1]):
    #         return
    #     else:
    #         print('hurt')

    def get_sprite(self) -> Surface:
        match self.state:
            case State.IDLE:
                # self.current_handle_input = self._handle_input_IDLE
                self.current_num_frames += 1
                if self.current_num_frames >= self.max_num_frames:
                    self.current_num_frames = 0
                    self.index = (self.index + 1) % len(self.current_sprites)
            case State.GUARD:
                self.current_num_frames += 1
                if self.current_num_frames >= self.max_num_frames:
                    self.current_num_frames = 0
                    self.index += 1
            case _:
                self.current_num_frames += 1
                if self.current_num_frames >= self.max_num_frames:
                    self.current_num_frames = 0
                    self.index += 1
                if self.index >= len(self.current_sprites):
                    self.state = State.IDLE
                    self.current_sprites = self.idle_sprites
                    self.index = 0
        
        if self.state == State.JUMP:
            self.ground_y-=self.jump_speed
            self.jump_speed-=self.gravity
            if self.jump_speed<-self.jump_height:
                self.jump_speed=self.jump_height
                self.current_num_frames += 1
                self.state = State.IDLE
                self.current_sprites = self.idle_sprites
                self.index = 0
            

        new_idx = self.index % len(self.current_sprites)

        self.w = self.current_sprites[new_idx].get_width()
        self.h = self.current_sprites[new_idx].get_height()

        if self.direction == Direction.LEFT:
            return pg.transform.flip(self.current_sprites[new_idx], True, False)
        return self.current_sprites[new_idx]

    def get_coord(self) -> tuple[int, int]:
        new_idx = self.index % len(self.current_sprites)
        d = self.current_sprites[new_idx].get_width() - self.idle_sprites[0].get_width()
        if self.direction == Direction.LEFT and d > 0:
            return self.x - d,round (self.ground_y) - self.current_sprites[new_idx].get_height()
        return self.x, round(self.ground_y) - self.current_sprites[new_idx].get_height()

    def handle_input(self) -> bool:
        key_pressed = pg.key.get_pressed()
        if self.state == State.JUMP:
            if key_pressed[pg.K_LEFT]:
                if self.direction == Direction.RIGHT:
                    self.direction = Direction.LEFT
                self.x -= self.velocity
                if self.x < 0:
                    self.x = 0
            if key_pressed[pg.K_RIGHT]:
                if self.direction == Direction.LEFT:
                    self.direction = Direction.RIGHT
                self.x += self.velocity
                if self.x > 1280 - self.w:
                    self.x = 1280 - self.w
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return True
            return False

        if key_pressed[pg.K_RIGHT] and (key_pressed[pg.K_LSHIFT] or key_pressed[pg.K_RSHIFT]):
            self.direction = Direction.RIGHT
        elif key_pressed[pg.K_LEFT] and (key_pressed[pg.K_LSHIFT] or key_pressed[pg.K_RSHIFT]):
            self.direction = Direction.LEFT
        elif key_pressed[pg.K_RIGHT]:
            index = self.get_direction_idx()
            self.update_sprite(self.move_sprites[index if self.is_move_right else 1 - index])
            self.state = State.MOVE
            self.is_move_right = True
            self.x += self.velocity
            if self.x > 1280 - self.w:
                self.x = 1280 - self.w
        elif key_pressed[pg.K_LEFT]:
            index = self.get_direction_idx()
            self.update_sprite(self.move_sprites[index if self.is_move_right else 1 - index])
            self.state = State.MOVE
            self.is_move_right = False
            self.x -= self.velocity
            if self.x < 0:
                self.x = 0
        elif key_pressed[pg.K_g]:
            self.update_sprite(self.guard_sprites)
            self.state = State.GUARD
            self.index = 0

        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                match event.key:
                    case pg.K_a:
                        self.update_sprite(self.attack_sprites)
                        self.state = State.ATTACK
                        self.index = 0
                    case pg.K_SPACE:
                        self.update_sprite(self.jump_sprites)
                        self.state = State.JUMP
                        self.index = 0
                    case pg.K_x:
                        self.update_sprite(self.kick_sprites)
                        self.state = State.KICK
                        self.index = 0
                    case _:
                        self.state = State.IDLE
            elif event.type == pg.QUIT:
                return True

        return False

    def get_hurt_box(self) -> pg.Rect | None:
        new_idx = self.index % len(self.current_sprites)
        w = self.current_sprites[new_idx].get_width()
        h = self.current_sprites[new_idx].get_height()
        d = self.current_sprites[new_idx].get_width() - self.idle_sprites[0].get_width()
        if self.direction == Direction.LEFT and d > 0:
            return pg.Rect(self.x - d, self.ground_y - h, w - 50, h - 30).move(25, 25)
        return pg.Rect(self.x, self.ground_y - h, w - 50, h - 30).move(25, 25)

    def get_hit_box(self) -> pg.Rect | None:
        if self.state in (State.ATTACK, State.KICK) and self.index in self.frame_idx_hit_box[self.state]:
            return self.get_hurt_box()

        return None


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
            Player(RYU_SPRITES_PATH, 50, 620, Direction.RIGHT),
            Player(RYU_SPRITES_PATH, self.screen_width - 230, 620, Direction.LEFT),
        ]

    def run(self):
        # main loop
        while not self.game_over:
            # get single input
            # self.players[1 - self.player_idx].get_hit(self.players[self.player_idx])
            self.game_over = self.players[self.player_idx].handle_input()

            self.timer -= self.delta_t
            if self.timer <= 0:
                self.game_over = True

            self.update()
            self.clock.tick(self.fps)

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
        if self.debug:
            # self.log()
            for player in self.players:
                hurt_box = player.get_hurt_box()
                if hurt_box:
                    pg.draw.rect(self.screen, BLUE, hurt_box, 3)
                hit_box = player.get_hit_box()
                if hit_box:
                    pg.draw.rect(self.screen, RED, hit_box, 3)

        pg.display.update()

    def log(self):
        # logs go here
        log.info(f'{self.players[self.player_idx].state}')


def main():
    GameManager(True).run()


if __name__ == '__main__':
    main()

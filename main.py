import logging as log
import random
from abc import ABC, abstractmethod
from enum import Enum

import pygame as pg
from pygame.surface import Surface

SOFT_GREEN = (186, 254, 202)
BLUE = (0, 0, 248)
LIGHT_BLUE = (135, 253, 255)
RED = (255, 0, 0)
P2 = (127, 255, 0)

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


def scale_sprite(sprites: list[Surface], scaler: float) -> list[Surface]:
    return [
        pg.transform.scale(sprite, (sprite.get_width() * scaler, sprite.get_height() * scaler))
        for sprite in sprites
    ]


def set_color_sprites(sprites: list[Surface], color):
    return [
        change_color(sprite, color) for sprite in sprites
    ]


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
    SHOOT_FIREBALL = 'fireball'


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


class FireBall(SpriteSheet):
    def __init__(self, player):
        """
        :type player: Player
        """
        super().__init__()
        self.direction = player.direction
        self.x = player.x
        if self.direction == Direction.LEFT:
            self.x -= 120
        else:
            self.x += player.w - 50
        self.y = player.y - 230
        self.velocity = 5
        self.sprite = player.sprite
        self.sprites: list[Surface] = [
            self.sprite.subsurface(pg.Rect(580, 1425, 45, 65)),
            self.sprite.subsurface(pg.Rect(640, 1425, 50, 65)),
            self.sprite.subsurface(pg.Rect(695, 1425, 60, 65)),
            self.sprite.subsurface(pg.Rect(760, 1425, 60, 65)),
        ]
        self.index = 0

        for sprite in self.sprites:
            sprite.set_colorkey(BLUE, pg.RLEACCEL)

        self.sprites = scale_sprite(self.sprites, 2.5)

    def get_hit_box(self) -> pg.Rect:
        return pg.Rect(self.x, self.y, self.sprites[self.index].get_width(),
                       self.sprites[self.index].get_height() * 0.6) \
            .move(0, 30)

    def collide(self, other_obj) -> bool:
        """
        :type other_obj: FireBall | Player | None
        :return: bool
        """
        if not other_obj and self.x >= 1280 or self.x <= 0:
            return True
        if type(other_obj) is FireBall:
            return True
        elif type(other_obj) is Player:
            if self.get_hit_box().colliderect(other_obj.get_hurt_box()):
                other_obj.health -= 50
                return True
        return False

    def get_coord(self) -> tuple[int, int]:
        if self.direction == Direction.RIGHT:
            self.x += self.velocity
        else:
            self.x -= self.velocity
        return self.x, self.y

    def get_sprite(self) -> Surface:
        if self.direction == Direction.LEFT:
            pass
        self.current_num_frames += 1

        n = len(self.sprites)
        if self.current_num_frames >= self.max_num_frames and self.index < len(self.sprites):
            self.current_num_frames = 0
            if self.index == n - 1:
                self.index = n - 2
            elif self.index == n - 2:
                self.index = n - 1
            else:
                self.index += 1

        if self.direction == Direction.LEFT:
            return pg.transform.flip(self.sprites[self.index], True, False)
        return self.sprites[self.index]


class Player(SpriteSheet):
    def __init__(self, path: str, x: int, y: int, max_health: int, p2: bool, direction: Direction):
        super().__init__()
        self.p2 = p2
        self.punch_sound = pg.mixer.Sound('assets/sound/punch.mp3')
        self.hadouken_sound = pg.mixer.Sound('assets/sound/hadouken.mp3')
        self.scaler = 2.5
        self.max_num_frames = 20
        self.sprite = pg.image.load(path).convert()
        self.state = State.IDLE
        self.fireballs = set[FireBall]()
        self.removed_fireballs: list[FireBall] = []
        self.prev_state = self.state
        self.velocity = 4
        self.direction = direction
        self.is_move_right = True
        self.ground_y: float = y
        self.health = max_health
        self.hurt_box: dict[State, tuple[int, ...]] = {
            State.ATTACK: tuple(map(int, (15 * self.scaler, 20 * self.scaler, 40 * self.scaler, 80 * self.scaler))),
            State.GUARD: tuple(map(int, (15 * self.scaler, 20 * self.scaler, 40 * self.scaler, 80 * self.scaler))),
            State.JUMP: tuple(map(int, (15 * self.scaler, 20 * self.scaler, 40 * self.scaler, 80 * self.scaler))),
            State.IDLE: tuple(map(int, (15 * self.scaler, 20 * self.scaler, 40 * self.scaler, 80 * self.scaler))),
        }
        self.jump_height = 12
        self.gravity = 0.2
        self.jump_speed = self.jump_height
        self.energy = 0

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
            State.ATTACK: [2, 9, 12],
            State.KICK: [2, 5],
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

        self.shoot_fireball_sprites: list[Surface] = [
            self.sprite.subsurface(pg.Rect(15, 1415, 80, 95)),
            self.sprite.subsurface(pg.Rect(110, 1415, 85, 95)),
            self.sprite.subsurface(pg.Rect(205, 1425, 95, 85)),
            self.sprite.subsurface(pg.Rect(310, 1430, 110, 80)),
            self.sprite.subsurface(pg.Rect(430, 1430, 130, 80)),
        ]

        for sprite in \
                self.idle_sprites + self.attack_sprites + \
                self.move_sprites[0] + self.move_sprites[1] + \
                self.jump_sprites + self.kick_sprites + \
                self.guard_sprites + self.shoot_fireball_sprites:
            sprite.set_colorkey(BLUE, pg.RLEACCEL)

        self.idle_sprites = scale_sprite(self.idle_sprites, self.scaler)
        self.attack_sprites = scale_sprite(self.attack_sprites, self.scaler)
        self.move_sprites[0] = scale_sprite(self.move_sprites[0], self.scaler)
        self.move_sprites[1] = scale_sprite(self.move_sprites[1], self.scaler)
        self.jump_sprites = scale_sprite(self.jump_sprites, self.scaler)
        self.kick_sprites = scale_sprite(self.kick_sprites, self.scaler)
        self.guard_sprites = scale_sprite(self.guard_sprites, self.scaler)
        self.shoot_fireball_sprites = scale_sprite(self.shoot_fireball_sprites, self.scaler)
        if self.p2:
            self.idle_sprites = set_color_sprites(self.idle_sprites, P2)
            self.attack_sprites = set_color_sprites(self.attack_sprites, P2)
            self.move_sprites[0] = set_color_sprites(self.move_sprites[0], P2)
            self.move_sprites[1] = set_color_sprites(self.move_sprites[1], P2)
            self.jump_sprites = set_color_sprites(self.jump_sprites, P2)
            self.kick_sprites = set_color_sprites(self.kick_sprites, P2)
            self.guard_sprites = set_color_sprites(self.guard_sprites, P2)
        self.current_sprites = self.idle_sprites
        self.cap_y = y - self.idle_sprites[0].get_height() + 20
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

    def get_health_bar(self):
        return self.health

    def get_hit(self, opponent):
        """
        :param opponent:
        :type opponent: Player
        :return:
        """
        opponent_hit_boxs, damage = opponent.get_hit_boxs_and_damage()
        if not opponent.get_hit_boxs_and_damage():
            return
        for hit_box in opponent_hit_boxs:
            if hit_box.colliderect(self.get_hurt_box()) and self.current_num_frames == 0:
                if self.state == State.GUARD:
                    self.health -= int(damage * 0.2)
                    self.energy += 7
                    if self.energy > 100:
                        self.energy = 100
                else:
                    self.health -= damage
                pg.mixer.Sound.play(self.punch_sound)
                opponent.energy += 10
                if opponent.energy > 100:
                    opponent.energy = 100
                self.prev_x = self.x
                self.x += 100 if self.direction == Direction.LEFT else -100
                if self.x > 1280 - self.w:
                    self.x = 1280 - self.w
                elif self.x < 0:
                    self.x = 0
                print(self.health)
                break

    def get_sprite(self) -> Surface:
        match self.state:
            case State.IDLE:
                # self.current_handle_input = self._handle_input_IDLE
                self.current_num_frames += 1
                if self.current_num_frames >= self.max_num_frames:
                    match self.current_sprites:
                        case self.attack_sprites:
                            self.state = State.ATTACK
                        case self.kick_sprites:
                            self.state = State.KICK
                    self.current_num_frames = 0
                    self.index = (self.index + 1)
                if self.index >= len(self.current_sprites):
                    self.state = State.IDLE
                    self.current_sprites = self.idle_sprites
                    self.index = 0
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
                    if self.state == State.SHOOT_FIREBALL:
                        self.fireballs.add(FireBall(self))
                    self.state = State.IDLE
                    self.current_sprites = self.idle_sprites
                    self.index = 0

        if self.removed_fireballs:
            for fb in self.removed_fireballs:
                self.fireballs.remove(fb)
            self.removed_fireballs = []

        if self.state == State.JUMP:
            self.ground_y -= self.jump_speed
            self.jump_speed -= self.gravity
            if self.jump_speed < -self.jump_height:
                self.jump_speed = self.jump_height
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
            return self.x - d, round(self.ground_y) - self.current_sprites[new_idx].get_height()
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
            self.state = State.IDLE
            self.current_sprites = self.idle_sprites
        elif key_pressed[pg.K_LEFT] and (key_pressed[pg.K_LSHIFT] or key_pressed[pg.K_RSHIFT]):
            self.direction = Direction.LEFT
            self.state = State.IDLE
            self.current_sprites = self.idle_sprites
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
                print(event.key)
                match event.key:
                    case pg.K_a:
                        print(event.key)
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
                    case pg.K_f:
                        if self.energy >= 50:
                            self.update_sprite(self.shoot_fireball_sprites)
                            self.state = State.SHOOT_FIREBALL
                            self.index = 0
                            self.energy -= 50

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
            return pg.Rect(self.x - int(d * 0.4), self.ground_y - h, int(w * 0.6), h - 25).move(0, 25)
        return pg.Rect(self.x, self.ground_y - h, int(w * 0.6), h - 25).move(30, 25)

    def get_hit_boxs_and_damage(self) -> tuple[list[pg.Rect], int]:
        new_idx = self.index % len(self.current_sprites)
        h = self.current_sprites[new_idx].get_height()
        match self.state:
            case State.ATTACK:
                match self.index:
                    case 2:
                        offset_x = 180
                        damage = 10
                        if self.direction == Direction.LEFT:
                            return [
                                       pg
                                       .Rect(-140, 40, self.current_sprites[2].get_width() - offset_x, 25)
                                       .move(self.x, self.ground_y - h)
                                   ], damage
                        return [
                                   pg
                                   .Rect(offset_x, 40, self.current_sprites[2].get_width() - offset_x, 25)
                                   .move(self.x, self.ground_y - h)
                               ], damage
                    case 9:
                        offset_xs = [
                            190,
                            205,
                            230,
                        ]
                        damage = 20
                        if self.direction == Direction.LEFT:
                            return [
                                       pg
                                       .Rect(-55, 30, self.current_sprites[8].get_width() - offset_xs[-3] - 50, 40)
                                       .move(self.x, self.ground_y - h),
                                       pg
                                       .Rect(-70, 70, self.current_sprites[8].get_width() - offset_xs[-2] - 20, 40)
                                       .move(self.x, self.ground_y - h),
                                       pg
                                       .Rect(-95, 110, self.current_sprites[9].get_width() - offset_xs[-1] - 10, 40)
                                       .move(self.x, self.ground_y - h),
                                   ], damage
                        return [
                                   pg
                                   .Rect(offset_xs[-3], 30, self.current_sprites[8].get_width() - offset_xs[-3] - 50,
                                         40)
                                   .move(self.x, self.ground_y - h),
                                   pg
                                   .Rect(offset_xs[-2], 70, self.current_sprites[8].get_width() - offset_xs[-2] - 20,
                                         40)
                                   .move(self.x, self.ground_y - h),
                                   pg
                                   .Rect(offset_xs[-1], 110, self.current_sprites[9].get_width() - offset_xs[-1] - 10,
                                         40)
                                   .move(self.x, self.ground_y - h)
                               ], damage
                    case 12:
                        offset_x = 160
                        if self.direction == Direction.LEFT:
                            return [
                                       pg
                                       .Rect(-30, 0, self.current_sprites[12].get_width() - offset_x - 5, 100)
                                       .move(self.x, self.ground_y - h)
                                   ], 30
                        return [
                                   pg
                                   .Rect(offset_x, 0, self.current_sprites[12].get_width() - offset_x - 5, 100)
                                   .move(self.x, self.ground_y - h)
                               ], 30
            case State.KICK:
                match self.index:
                    case 2:
                        w = self.current_sprites[2].get_width()
                        offset_xs = [
                            150,
                            200,
                            230,
                        ]
                        damage = 10
                        if self.direction == Direction.LEFT:
                            return [
                                       pg
                                       .Rect(-20, 50, offset_xs[-2] - offset_xs[-3], 40)
                                       .move(self.x, self.ground_y - h),
                                       pg
                                       .Rect(-50, 30, offset_xs[-1] - offset_xs[-2], 40)
                                       .move(self.x, self.ground_y - h),
                                       pg
                                       .Rect(-120, 10, w - offset_xs[-1], 30)
                                       .move(self.x, self.ground_y - h),
                                   ], damage
                        return [
                                   pg
                                   .Rect(offset_xs[-3], 50, offset_xs[-2] - offset_xs[-3], 40)
                                   .move(self.x, self.ground_y - h),
                                   pg
                                   .Rect(offset_xs[-2], 30, offset_xs[-1] - offset_xs[-2], 40)
                                   .move(self.x, self.ground_y - h),
                                   pg
                                   .Rect(offset_xs[-1], 10, w - offset_xs[-1], 30)
                                   .move(self.x, self.ground_y - h),
                               ], damage
                    case 5:
                        w = self.current_sprites[5].get_width()
                        offset_xs = [
                            120,
                            150,
                        ]
                        damage = 15
                        if self.direction == Direction.LEFT:
                            return [
                                       pg
                                       .Rect(0, 110, w - offset_xs[-2] - 50, 30)
                                       .move(self.x, self.ground_y - h),
                                       pg
                                       .Rect(-40, 140, w - offset_xs[-1] - 10, 30)
                                       .move(self.x, self.ground_y - h),
                                   ], damage
                        return [
                                   pg
                                   .Rect(offset_xs[-2], 110, w - offset_xs[-2] - 50, 30)
                                   .move(self.x, self.ground_y - h),
                                   pg
                                   .Rect(offset_xs[-1], 140, w - offset_xs[-1] - 10, 30)
                                   .move(self.x, self.ground_y - h),
                               ], damage

        return [], 0


class AIController:
    def __init__(self, max_num_frame: int):
        self.lock_animation = 0
        self.max_num_frame = max_num_frame
        self.random = random.SystemRandom()

    def update_AI_state(self, ai: Player, human: Player) -> None:

        distance = ai.x - human.x

        if ai.state == State.IDLE:
            # In IDLE, it has the tendency to move towards the player
            if distance < -100:
                ai.direction = Direction.RIGHT
                index = ai.get_direction_idx()
                ai.update_sprite(ai.move_sprites[index if ai.is_move_right else 1 - index])
                ai.state = State.MOVE
                ai.is_move_right = True
                ai.x += int(ai.velocity * 1 / 2)
                if ai.x >= human.x:
                    ai.x = human.x
                elif ai.x >= 1280:
                    ai.x = 1280
                ai.state = State.IDLE
            elif distance >= 100:
                ai.direction = Direction.LEFT
                index = ai.get_direction_idx()
                ai.update_sprite(ai.move_sprites[index if ai.is_move_right else 1 - index])
                ai.state = State.MOVE
                ai.is_move_right = False
                ai.x -= int(ai.velocity / 2)
                if ai.x <= human.x:
                    ai.x = human.x
                ai.state = State.IDLE
            elif self.random.randint(0, 143) == 0:
                if human.state == State.ATTACK and abs(distance) <= 100 and ai.state == State.IDLE:
                    self.lock_animation = len(ai.guard_sprites) * self.max_num_frame
                    ai.update_sprite(ai.guard_sprites)
                    ai.state = State.GUARD
                    ai.index = 0
                else:
                    self.lock_animation = len(ai.attack_sprites) * self.max_num_frame
                    ai.update_sprite(ai.attack_sprites)
                    ai.state = State.ATTACK
                    ai.index = 0

        # elif ai.state == State.ATTACK:
        #     if self.lock_animation < 0:
        #         ai.state = State.IDLE
        #     self.lock_animation -= 1
        # elif ai.state == State.GUARD:
        #     if self.lock_animation < 0:
        #         ai.state = State.IDLE
        #     self.lock_animation -= 1
        else:
            if self.lock_animation < 0:
                ai.state = State.IDLE
            self.lock_animation -= 1


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
        self.max_health = 500
        self.menu = True
        self.winner = ""
        self.font_time = pg.font.SysFont("comicsans", 80, True, True)
        self.font_player = pg.font.SysFont("impact", 40, False, False)
        self.font_menu = pg.font.SysFont("consolas", 40, True, False)
        self.font_option = pg.font.SysFont("consolas", 80, True, False)
        self.players: list[Player] = [
            Player(RYU_SPRITES_PATH, 50, 620, self.max_health, False, Direction.RIGHT),
            Player(RYU_SPRITES_PATH, self.screen_width - 230, 620, self.max_health, True, Direction.LEFT),
        ]
        self.ai_controller = AIController(self.fps)

    def reset(self, debug=False):
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
        self.max_health = 500
        self.menu = True
        self.winner = ""
        self.font_time = pg.font.SysFont("comicsans", 80, True, True)
        self.font_player = pg.font.SysFont("impact", 40, False, False)
        self.font_menu = pg.font.SysFont("consolas", 40, True, False)
        self.font_option = pg.font.SysFont("consolas", 80, True, False)
        self.players: list[Player] = [
            Player(RYU_SPRITES_PATH, 50, 620, self.max_health, False, Direction.RIGHT),
            Player(RYU_SPRITES_PATH, self.screen_width - 230, 620, self.max_health, True, Direction.LEFT),
        ]
        self.ai_controller = AIController(self.fps)

    def run(self):
        pg.mixer.music.load('assets/sound/guile-theme.mp3')
        pg.mixer.music.play(-1)
        # main loop
        while not self.game_over:
            if not self.menu:
                # get single input
                self.players[1 - self.player_idx].get_hit(self.players[self.player_idx])

                self.players[self.player_idx].get_hit(self.players[1 - self.player_idx])

                self.game_over = self.players[self.player_idx].handle_input()

                self.ai_controller.update_AI_state(self.players[1 - self.player_idx], self.players[self.player_idx])

                self.timer -= self.delta_t if len(self.winner) == 0 else 0
                if self.timer <= 0:
                    self.winner = "No"

            self.update()
            self.clock.tick(self.fps)

        pg.quit()

    def draw_top_bar(self):
        time_text = self.font_time.render(str(round(self.timer)), True, (0, 0, 0))
        self.screen.blit(time_text, (550 + round(180 - time_text.get_width()) / 2, 50))
        health_1 = self.players[0].health
        health_2 = self.players[1].health
        name_plate_1 = self.font_player.render('Player 1', False, (0, 0, 0))
        name_plate_2 = self.font_player.render('Player 2', False, (0, 0, 0))
        self.screen.blit(name_plate_1, (50, 30))
        self.screen.blit(name_plate_2, (1230 - name_plate_2.get_width(), 30))

        pg.draw.rect(self.screen, RED, (50, 50 + round(time_text.get_height() / 2) - 15, 500, 30))
        pg.draw.rect(self.screen, SOFT_GREEN, (50, 35 + round(time_text.get_height() / 2), 500 - round(
            500 / self.max_health * (self.max_health - health_1)) if health_1 > 0 else 0, 30))
        pg.draw.rect(self.screen, RED, (730, 50 + round(time_text.get_height() / 2) - 15, 500, 30))
        pg.draw.rect(self.screen, SOFT_GREEN, (730, 35 + round(time_text.get_height() / 2), 500 - round(
            500 / self.max_health * (self.max_health - health_2)) if health_2 > 0 else 0, 30))

        pg.draw.rect(self.screen, LIGHT_BLUE, (50, 65 + (time_text.get_height() >> 1), 100, 15))
        pg.draw.rect(self.screen, BLUE,
                     (50, 65 + (time_text.get_height() >> 1), self.players[self.player_idx].energy, 15))

        pg.draw.rect(self.screen, LIGHT_BLUE, (1130, 65 + (time_text.get_height() >> 1), 100, 15))
        pg.draw.rect(self.screen, BLUE,
                     (1130, 65 + (time_text.get_height() >> 1), self.players[1 - self.player_idx].energy, 15))

        if health_1 <= 0:
            self.winner = "PLAYER 2"
        elif health_2 <= 0:
            self.winner = "PLAYER 1"

    @staticmethod
    def inner(point: tuple[int, int], x0, x1, y0, y1) -> bool:
        return not (point[0] > x1 or point[0] < x0 or point[1] > y1 or point[1] < y0)

    def draw_menu_screen(self):
        if not self.menu:
            return
        self.screen.fill((0, 0, 0))
        menu_mouse_pos = pg.mouse.get_pos()
        menu_text = self.font_menu.render("MENU", True, (255, 255, 255))
        quit_text = self.font_menu.render("QUIT", True, (255, 255, 255))
        quit_rect = (quit_text.get_width(), quit_text.get_height())

        player_1_button = self.font_option.render("PLAYER 1", True, (255, 255, 255))
        player_2_button = self.font_option.render("PLAYER 2", True, (255, 255, 255))

        self.screen.blit(menu_text, (round((self.screen_width - menu_text.get_width()) / 2), 70))
        self.screen.blit(quit_text,
                         (round((self.screen_width - menu_text.get_width()) / 2), self.screen_height / 2 + 100))

        self.screen.blit(player_1_button, (200, self.screen_height / 2 - 100))
        self.screen.blit(player_2_button,
                         (self.screen_width - 200 - player_2_button.get_width(), self.screen_height / 2 - 100))
        ev = pg.event.get()
        for event in ev:
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.inner(menu_mouse_pos, (self.screen_width - menu_text.get_width()) / 2,
                              (self.screen_width - menu_text.get_width()) / 2 + quit_rect[0],
                              self.screen_height / 2 + 100, self.screen_height / 2 + 100 + quit_rect[1]):
                    self.game_over = True
                elif self.inner(menu_mouse_pos, 200, 200 + player_1_button.get_width(), self.screen_height / 2 - 100,
                                self.screen_height / 2 - 100 + player_1_button.get_height()):
                    self.player_idx = 0
                    self.menu = False
                elif self.inner(menu_mouse_pos, self.screen_width - 200 - player_2_button.get_width(),
                                self.screen_width - 200, self.screen_height / 2 - 100,
                                self.screen_height / 2 - 100 + player_2_button.get_height()):
                    self.player_idx = 1
                    self.menu = False

    def draw_game_over(self):
        if len(self.winner) == 0:
            return
        self.screen.fill((0, 0, 0))
        retry_text = self.font_menu.render("RETRY", True, (255, 255, 255))
        quit_text = self.font_menu.render("QUIT", True, (255, 255, 255))
        winner_text = self.font_menu.render((self.winner + " WIN!" if self.winner != "No" else "DRAW!!!"), True,
                                            (255, 255, 255))
        quit_rect = (quit_text.get_width(), quit_text.get_height())
        retry_rect = (retry_text.get_width(), retry_text.get_height())
        menu_mouse_pos = pg.mouse.get_pos()

        self.screen.blit(retry_text, (round((self.screen_width - retry_text.get_width()) / 2),
                                      self.screen_height / 2 - round(retry_text.get_height() / 2) + 100))
        self.screen.blit(winner_text, (round((self.screen_width - winner_text.get_width()) / 2),
                                       self.screen_height / 2 - round(winner_text.get_height() / 2) - 100))
        self.screen.blit(quit_text, (round((self.screen_width - quit_text.get_width()) / 2),
                                     self.screen_height / 2 - round(quit_text.get_height() / 2) + 200))
        ev = pg.event.get()
        for event in ev:
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.inner(menu_mouse_pos, (self.screen_width - quit_text.get_width()) / 2,
                              (self.screen_width - quit_text.get_width()) / 2 + quit_rect[0],
                              self.screen_height / 2 - round(quit_text.get_height() / 2) + 200,
                              self.screen_height / 2 - round(quit_text.get_height() / 2) + 200 + quit_rect[1]):
                    self.game_over = True
                elif self.inner(menu_mouse_pos, round((self.screen_width - retry_text.get_width()) / 2),
                                round((self.screen_width - retry_text.get_width()) / 2) + retry_rect[0],
                                self.screen_height / 2 - round(retry_text.get_height() / 2) + 100,
                                self.screen_height / 2 - round(retry_text.get_height() / 2) + 100 + retry_rect[1]):
                    self.reset()

    def update(self):
        self.screen.blit(
            pg.transform.scale(self.bg_sprite.get_sprite(), (self.screen_width, self.screen_height)),
            (0, 0),
        )

        self.draw_top_bar()

        for fb in self.players[self.player_idx].fireballs:
            if fb.collide(None) or fb.collide(self.players[1 - self.player_idx]):
                self.players[self.player_idx].removed_fireballs.append(fb)
            self.screen.blit(fb.get_sprite(), fb.get_coord())

        for fb in self.players[1 - self.player_idx].fireballs:
            if fb.collide(None) or fb.collide(self.players[self.player_idx]):
                self.players[1 - self.player_idx].removed_fireballs.append(fb)
            self.screen.blit(fb.get_sprite(), fb.get_coord())

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
                hit_box, _ = player.get_hit_boxs_and_damage()
                if hit_box:
                    for hb in hit_box:
                        pg.draw.rect(self.screen, RED, hb, 3)

                for fb in player.fireballs:
                    pg.draw.rect(self.screen, RED, fb.get_hit_box(), 3)

        self.draw_menu_screen()
        self.draw_game_over()

        pg.display.update()

    def log(self):
        # logs go here
        log.info(f'{self.players[self.player_idx].state}')


def main():
    GameManager(True).run()


def change_color(image: Surface, color):
    coloured_image = pg.Surface(image.get_size())
    coloured_image.fill(color)

    final_image = image.copy()
    final_image.blit(coloured_image, (0, 0), special_flags=pg.BLEND_MULT)
    final_image.set_colorkey((0, 0, 0), pg.RLEACCEL)

    return final_image


if __name__ == '__main__':
    main()

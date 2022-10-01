from abc import ABC, abstractmethod
from audioop import add
from enum import Enum
from re import S
from tkinter import Y
from turtle import Screen
from typing import Tuple

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
        self.max_num_frames = 20
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
        self.action = False
        self.hurt_box:dict[State,Tuple]={State.ATTACK:(15*scaler,20*scaler,40*scaler,80*scaler),
                                   State.GUARD:(15*scaler,20*scaler,40*scaler,80*scaler),
                                   State.JUMP:(15*scaler,20*scaler,40*scaler,80*scaler),
                                   State.IDLE:(15*scaler,20*scaler,40*scaler,80*scaler)}
        self.hit_box: Tuple = (70*scaler,20*scaler,50*scaler,10*scaler)

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
        
        self.attack_sprites: list[Surface] = [
            self.sprite.subsurface(pg.Rect(160, 460, 125, 110)),
            self.sprite.subsurface(pg.Rect(80, 460, 70, 110)),
            self.sprite.subsurface(pg.Rect(0, 460, 70, 110)),
        ]
         # TODO add
        self.jump_sprite: list[Surface]= [
            self.sprite.subsurface(pg.Rect(0, 340, 70, 110)),
            self.sprite.subsurface(pg.Rect(80, 340, 70, 110)),
            self.sprite.subsurface(pg.Rect(160, 340, 125, 110)),
            self.sprite.subsurface(pg.Rect(0, 460, 70, 110)),
            self.sprite.subsurface(pg.Rect(80, 460, 70, 110)),
            self.sprite.subsurface(pg.Rect(160, 460, 125, 110)),
            self.sprite.subsurface(pg.Rect(0, 460, 70, 110)),
            self.sprite.subsurface(pg.Rect(80, 460, 70, 110)),
            self.sprite.subsurface(pg.Rect(160, 460, 125, 110)),   
        ]
        
        for sprite in self.idle_sprites + self.move_right_sprites + self.move_left_sprites +self.attack_sprites:
            sprite.set_colorkey(BLUE, pg.RLEACCEL)

        self.idle_sprites = self.scale_sprite(self.idle_sprites, scaler)
        self.move_right_sprites = self.scale_sprite(self.move_right_sprites, scaler)
        self.move_left_sprites = self.scale_sprite(self.move_left_sprites, scaler)
        self.attack_sprites = self.scale_sprite(self.attack_sprites,scaler)
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

    def get_hit(self, opp):
        
        if(opp.state !=State.ATTACK) or self.state==State.GUARD:
            return
        
        x,y= opp.get_coord()
        
        hitbox=opp.hit_box
        
        flip=opp.flip
        
        addon=0
        
        if self.state==State.ATTACK:
            if self.index==0:
               addon= self.hit_box[2]
        
        min=(x+hitbox[0]-opp.w,y+hitbox[1]) if flip else (x+hitbox[0],y+hitbox[1]) 
        max=(min[0]+hitbox[2],min[1]+hitbox[3])  
        hurtbox_min=(self.x+self.hurt_box[self.state][0]+addon,self.y+self.hurt_box[self.state][1]) if flip else (self.x+self.hurt_box[self.state][0],self.y+self.hurt_box[self.state][1])
        hurtbox_max=(hurtbox_min[0]+self.hurt_box[self.state][2],hurtbox_min[1]+self.hurt_box[self.state][3])
        if(hurtbox_min[0]>max[0] or 
           hurtbox_min[1]>max[1] or 
           hurtbox_max[0]<min[0] or 
           hurtbox_max[1]<min[1] ):
            return
        else:
            print('hurt')
        

    def get_sprite(self) -> Surface:
        match self.state:
            case State.IDLE:
                self.current_sprites = self.idle_sprites
            case State.MOVE_RIGHT:
                self.current_sprites = self.move_right_sprites
            case State.MOVE_LEFT:
                self.current_sprites = self.move_left_sprites
            case State.ATTACK:
                self.current_sprites = self.attack_sprites
        
        if self.index >= len(self.current_sprites):
            self.action = False
            # if self.state != State.IDLE:
            #     self.state = State .IDLE
            self.index = 0
        else:    

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
        # if self.action:
            # return
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
        elif key_pressed[pg.K_a]:
            self.state = State.ATTACK
            self.action = True
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
            self.players[1-self.player_idx].get_hit(self.players[self.player_idx])
            self.players[self.player_idx].handle_input()

            for event in pg.event.get():
                match event.type:
                    case pg.QUIT:
                        self.game_over = True

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
        if self.players[self.player_idx].state==State.ATTACK:
            if self.players[self.player_idx].flip!=True:
                pg.draw.rect(self.screen,(255,0,0),pg.Rect(
                    self.players[self.player_idx].x+self.players[self.player_idx].hit_box[0],
                    self.players[self.player_idx].y+self.players[self.player_idx].hit_box[1],
                    self.players[self.player_idx].hit_box[2],
                    self.players[self.player_idx].hit_box[3]),3)
            else:
                pg.draw.rect(self.screen,(255,0,0),pg.Rect(
                    self.players[self.player_idx].x+self.players[self.player_idx].hit_box[0]-self.players[self.player_idx].w,
                    self.players[self.player_idx].y+self.players[self.player_idx].hit_box[1],
                    self.players[self.player_idx].hit_box[2],
                    self.players[self.player_idx].hit_box[3]),3)
        if self.players[self.player_idx].flip and self.players[self.player_idx].state==State.ATTACK and self.players[self.player_idx].index==0:
            pg.draw.rect(self.screen,(0,0,255),pg.Rect(
                self.players[self.player_idx].x+15*2.5+self.players[self.player_idx].hit_box[2],
                self.players[self.player_idx].y+20*2.5,
                40*2.5,
                80*2.5),3)
        else:
            pg.draw.rect(self.screen,(0,0,255),pg.Rect(
                self.players[self.player_idx].x+15*2.5,
                self.players[self.player_idx].y+20*2.5,
                40*2.5,
                80*2.5),3)
        pg.draw.rect(self.screen,(0,0,255),pg.Rect(
            self.players[1-self.player_idx].x+15*2.5,
            self.players[1-self.player_idx].y+20*2.5,
            40*2.5,
            80*2.5),3)
        x,y=self.players[self.player_idx].get_coord()
        # x = x+ 
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

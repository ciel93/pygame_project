import pygame
import random
import math
from setting import *

class Item(pygame.sprite.Sprite):
    _image_cache = {}

    def __init__(self, groups, center_pos, item_type='power', initial_velocity=None, collision_cooldown=0):
        super().__init__(groups)
        
        self.item_type = item_type
        
        image_map = {
            'power': 'powerup.png',
            'score': 'score.png',
            'bomb': 'bomb.png'
        }
        filename = image_map.get(self.item_type)
        
        if filename and filename in Item._image_cache:
            self.image = Item._image_cache[filename]
        elif filename:
            try:
                self.image = pygame.image.load(f'assets/img/item/{filename}').convert_alpha()
                Item._image_cache[filename] = self.image
            except Exception:
                filename = None # フォールバックへ

        if not filename:
            # フォールバック描画
            self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
            font = pygame.font.SysFont('sans-serif', 18, bold=True)
            text_color = BLACK

            if self.item_type == 'power':
                pygame.draw.circle(self.image, ITEM_POWER_COLOR, (12, 12), 12)
                text_surface = font.render('P', True, text_color)
            elif self.item_type == 'score':
                pygame.draw.circle(self.image, ITEM_SCORE_COLOR, (12, 12), 12)
                text_surface = font.render('S', True, text_color)
            elif self.item_type == 'bomb':
                pygame.draw.circle(self.image, ITEM_BOMB_COLOR, (12, 12), 12)
                text_surface = font.render('B', True, text_color)
            else:
                pygame.draw.circle(self.image, ITEM_DEFAULT_COLOR, (12, 12), 12)
                text_surface = None

            # レンダリングされたテキストがあれば、円の中央に描画
            if text_surface:
                text_rect = text_surface.get_rect(center=(12, 12))
                self.image.blit(text_surface, text_rect)
        else:
            self.image = self.image.copy() # キャッシュからコピーして使用

        self.image = pygame.transform.scale(self.image, (24, 24))
        self.rect = self.image.get_rect(center=center_pos)
        self.speed = 2

        # 位置と速度を浮動小数点で管理
        self.pos = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(initial_velocity) if initial_velocity else pygame.math.Vector2(0, self.speed)
        self.friction = 0.96 # 速度の減衰係数

        # アイテム吸い込み用のフラグと速度
        self.value = 1000 if item_type == 'score' else 0 # スコアアイテムの価値を1000に増加
        self.is_attracted = False
        self.attraction_speed = 16 # 吸い込み速度を8から16に増加

        # 生成直後の当たり判定を無効化するためのクールダウン
        self.collision_cooldown = collision_cooldown

    def update(self, player_pos=None):
        # プレイヤーに引き寄せられている状態の場合
        if self.is_attracted and player_pos:
            direction = player_pos - self.pos
            if direction.length() > 0:
                direction.normalize_ip()
            # 吸い込み時は速度を直接上書き
            self.velocity = direction * self.attraction_speed
        else:
            # 通常時（重力と摩擦）
            gravity = 0.1
            self.velocity.y += gravity
            self.velocity *= self.friction
            # 落下速度が遅すぎる場合は、最低速度を保証
            if self.velocity.length_squared() < 1 and not self.is_attracted:
                self.velocity.y = max(self.velocity.y, self.speed)

        self.pos += self.velocity
        self.rect.center = self.pos

        # クールダウンタイマーを減らす
        if self.collision_cooldown > 0:
            self.collision_cooldown -= 1

        # 画面外に出たら消える
        if self.rect.top > screen_height:
            self.kill()
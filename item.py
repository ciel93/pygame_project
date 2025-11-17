import pygame
import random
from setting import *

class Item(pygame.sprite.Sprite):
    _image_cache = {}

    def __init__(self, groups, center_pos, item_type='power'):
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

        # 位置を浮動小数点で管理
        self.pos = pygame.math.Vector2(self.rect.center)
        # アイテム吸い込み用のフラグと速度
        self.value = 1000 if item_type == 'score' else 0 # スコアアイテムの価値を1000に増加
        self.is_attracted = False
        self.attraction_speed = 12 # 吸い込み速度を8から12に増加

    def update(self, player_pos=None):
        # プレイヤーに引き寄せられている場合
        if self.is_attracted and player_pos:
            # プレイヤーへの方向ベクトルを計算
            direction = player_pos - self.pos
            if direction.length() > 0:
                direction.normalize_ip()
            # 高速でプレイヤーに向かって移動
            self.pos += direction * self.attraction_speed
            self.rect.center = self.pos
        else:
            # 通常時はゆっくり下に落ちる
            self.pos.y += self.speed
            self.rect.center = self.pos

        # 画面外に出たら消える
        if self.rect.top > screen_height:
            self.kill()
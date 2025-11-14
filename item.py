import pygame
import random
from setting import *

class Item(pygame.sprite.Sprite):
    def __init__(self, groups, center_pos, item_type='power'):
        super().__init__(groups)
        
        self.item_type = item_type
        
        # アイテムの種類によって画像を変える
        if self.item_type == 'power':
            try:
                # 画像ファイルが存在すればロードする
                self.image = pygame.image.load('assets/img/item/powerup.png').convert_alpha()
            except Exception: # pygame.error だけでなく FileNotFoundError なども捕捉
                # なければ図形で代替
                self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(self.image, (255, 100, 100), (12, 12), 12)
                pygame.draw.rect(self.image, WHITE, (8, 4, 8, 16)) # 'P'のような形
        elif self.item_type == 'score':
            try:
                self.image = pygame.image.load('assets/img/item/score.png').convert_alpha()
            except Exception:
                self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(self.image, (255, 215, 0), (12, 12), 12) # 金色
                # ドルマーク'$'のような形を描画
                font = pygame.font.SysFont('arial', 20, bold=True)
                text = font.render('S', True, BLACK)
                self.image.blit(text, (self.image.get_width() // 2 - text.get_width() // 2, self.image.get_height() // 2 - text.get_height() // 2))
        else:
            # 'power' 以外のアイテムタイプの場合のフォールバック
            self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (100, 100, 255), (12, 12), 12) # 別の色で表示
            pygame.draw.rect(self.image, WHITE, (8, 8, 8, 8)) # 'S'のような形

        self.image = pygame.transform.scale(self.image, (24, 24))
        self.rect = self.image.get_rect(center=center_pos)
        self.speed = 2

        # 位置を浮動小数点で管理
        self.pos = pygame.math.Vector2(self.rect.center)
        # アイテム吸い込み用のフラグと速度
        self.value = 500 if item_type == 'score' else 0 # スコアアイテムの価値
        self.is_attracted = False
        self.attraction_speed = 8

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
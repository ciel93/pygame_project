import pygame
from setting import *
import math

class EnemyBullet(pygame.sprite.Sprite):
    """敵の弾（direction プロパティ対応）"""
    def __init__(self, groups, x, y, target_group, speed=1, direction=None, radius=6, color=ENEMY_BULLET_COLOR, length=None, bullet_type='normal'):
        radius=8 # 通常弾の半径を大きくする (6 -> 8)
        super().__init__(groups)
        self.screen = pygame.display.get_surface()

        # 衝突対象（プレイヤーのグループなど）
        self.target_group = target_group

        if direction is None:
            # デフォルトは下方向
            self.direction = pygame.math.Vector2(0, 1)
        else:
            if isinstance(direction, pygame.math.Vector2):
                self.direction = direction
            else:
                self.direction = pygame.math.Vector2(direction)
        # 長さを正規化（ゼロベクトルはそのまま）
        if self.direction.length_squared() != 0:
            self.direction = self.direction.normalize()

        # 画像の読み込み
        try:
            # bullet_type に応じて画像を切り替える
            if bullet_type == 'laser':
                self.original_image = pygame.image.load('assets/img/enemy_bullet/laser.png').convert_alpha()
            elif color == ENEMY_BULLET_SPECIAL_COLOR: # 渦巻き弾などの特殊弾
                self.original_image = pygame.image.load('assets/img/enemy_bullet/1.png').convert_alpha()
            else:
                self.original_image = pygame.image.load('assets/img/enemy_bullet/0.png').convert_alpha()
        except Exception:
            # 画像がない場合の代替処理
            if bullet_type == 'laser':
                # レーザーの場合は細長い矩形を生成
                self.original_image = pygame.Surface((int(radius * 2), int(length if length else radius * 15)), pygame.SRCALPHA)
                self.original_image.fill(color)
            else:
                self.original_image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(self.original_image, color, (radius, radius), radius)

        # lengthが指定されていれば細長い矩形に、なければ円形にサイズ調整
        if length:
            width = int(radius * 2)
            height = int(length)
        else:
            width = height = int(radius * 2)
        self.original_image = pygame.transform.scale(self.original_image, (width, height))

        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        
        # 位置ベクトルと当たり判定半径
        self.pos = pygame.math.Vector2(x, y)
        self.speed = speed
        self.radius = max(self.rect.width, self.rect.height) / 2 * 0.8 # 当たり判定を少し小さめに

    def move(self):
        # direction を使って移動
        self.pos += self.direction * self.speed
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def check_off_screen(self):
        if self.rect.top > screen_height or self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > GAME_AREA_WIDTH:
            self.kill()

    def collision_target(self):
        for target in self.target_group:
            # ターゲット中心取得（pos 優先）
            if hasattr(target, 'pos'):
                target_center = pygame.math.Vector2(target.pos)
            else:
                target_center = pygame.math.Vector2(target.rect.center)

            target_radius = getattr(target, 'radius', 20)

            # 円形当たり判定
            if self.pos.distance_to(target_center) < (self.radius + target_radius):
                # ターゲットに take_damage メソッドがあればそれを呼び出す
                # 無敵状態でない場合のみダメージを与える
                if hasattr(target, 'take_damage') and (not hasattr(target, 'invincible') or not target.invincible):
                    target.take_damage(1) # 1ダメージを与える
                self.kill()
                break

    def update(self):
        self.move()

        # 進行方向に応じて画像を回転
        angle = -self.direction.angle_to(pygame.math.Vector2(0, 1))
        # 毎フレーム回転させると画質が劣化するので、元の画像を保持し、それを回転させる
        # self.original_image はリサイズ済みの画像
        self.image = pygame.transform.rotate(self.original_image, angle) 
        self.rect = self.image.get_rect(center=self.rect.center)

        self.check_off_screen()
        self.collision_target()
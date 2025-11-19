import pygame
from setting import *
import math

class EnemyBullet(pygame.sprite.Sprite):
    """敵の弾（direction プロパティ対応）"""
    # 画像をキャッシュするためのクラス変数
    _image_cache = {}

    def __init__(self, groups, x, y, target_group, speed=1, direction=None, radius=8, color=ENEMY_BULLET_COLOR, length=None, bullet_type='normal', frozen_duration=0, lifetime=None):
        super().__init__(groups)
        self.screen = pygame.display.get_surface()

        self.bullet_type = bullet_type
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

        # 画像の読み込み（キャッシュを利用）
        image_key = (bullet_type, radius, length, tuple(color) if bullet_type in ['laser', 'freeze'] or 'fallback' in bullet_type else None)
        if image_key in EnemyBullet._image_cache:
            self.original_image = EnemyBullet._image_cache[image_key]
        else:
            loaded_image = None
            try:
                # bullet_type に応じて画像を切り替える
                if bullet_type == 'laser':
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/laser.png').convert_alpha()
                elif bullet_type == 'vortex_rev': # 反時計回り渦弾
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/1.png').convert_alpha()
                elif bullet_type == 'vortex':
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/0.png').convert_alpha()
                elif bullet_type == 'homing':
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/2.png').convert_alpha()
                elif bullet_type == 'ice':
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/4.png').convert_alpha()
                elif bullet_type == 'freeze':
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/freeze.png').convert_alpha()
                else:
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/0.png').convert_alpha()
                self.original_image = loaded_image
            except Exception:
                # 画像がない場合の代替処理
                # 画像読み込みに失敗した場合、代替描画を行う
                if bullet_type == 'laser':
                    # レーザーの場合は細長い矩形を生成
                    self.original_image = pygame.Surface((int(radius * 2), int(length if length else radius * 15)), pygame.SRCALPHA)
                    self.original_image.fill(color)
                elif bullet_type == 'freeze':
                    # 氷弾の代替画像（氷の結晶のような形）
                    self.original_image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(self.original_image, (180, 220, 255), (radius, radius), radius)
                    pygame.draw.circle(self.original_image, WHITE, (radius, radius), radius, 2)
                else:
                    self.original_image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(self.original_image, color, (radius, radius), radius)
            
            EnemyBullet._image_cache[image_key] = self.original_image

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
        
        # 凍結状態のパラメータ
        self.is_frozen = frozen_duration > 0
        self.frozen_timer = frozen_duration
        
        # 弾の寿命
        self.lifetime = lifetime
        self.has_lifetime = lifetime is not None

    def reset(self, x, y, target_group, speed=1, direction=None, radius=8, color=ENEMY_BULLET_COLOR, length=None, bullet_type='normal', frozen_duration=0, lifetime=None):
        """オブジェクトプールから再利用される際に状態をリセットする"""
        self.pos = pygame.math.Vector2(x, y)
        self.rect.center = self.pos
        self.speed = speed
        self.target_group = target_group
        self.bullet_type = bullet_type
        self.radius = radius # 半径もリセットできるように追加

        if direction is None:
            self.direction = pygame.math.Vector2(0, 1)
        else:
            if isinstance(direction, pygame.math.Vector2):
                self.direction = direction
            else:
                self.direction = pygame.math.Vector2(direction)
        if self.direction.length_squared() != 0:
            self.direction = self.direction.normalize()

        self.is_frozen = frozen_duration > 0
        self.frozen_timer = frozen_duration

        # 寿命をリセット
        self.lifetime = lifetime
        self.has_lifetime = lifetime is not None

        # 画像の再生成とスケーリング
        image_key = (bullet_type, radius, length, tuple(color) if bullet_type in ['laser', 'freeze'] or 'fallback' in bullet_type else None)
        if image_key in EnemyBullet._image_cache:
            self.original_image = EnemyBullet._image_cache[image_key]
        else:
            loaded_image = None
            try:
                if bullet_type == 'laser':
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/laser.png').convert_alpha()
                elif bullet_type == 'vortex_rev':
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/1.png').convert_alpha()
                elif bullet_type == 'vortex':
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/0.png').convert_alpha()
                elif bullet_type == 'homing':
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/2.png').convert_alpha()
                elif bullet_type == 'ice':
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/4.png').convert_alpha()
                else:
                    loaded_image = pygame.image.load('assets/img/enemy_bullet/0.png').convert_alpha()
                self.original_image = loaded_image
            except Exception:
                # フォールバック処理は __init__ と同様のため省略
                self.original_image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(self.original_image, color, (radius, radius), radius)
            EnemyBullet._image_cache[image_key] = self.original_image

        if length:
            width, height = int(radius * 2), int(length)
        else:
            width = height = int(radius * 2)
        self.original_image = pygame.transform.scale(self.original_image, (width, height))
        self.image = self.original_image.copy()
        # 画像は__init__でキャッシュされているものを利用するため、ここでは変更しない
        # 必要であれば、ここで self.image = self.original_image.copy() などでリセット

    def move(self):
        # 凍結中は移動しない
        if self.is_frozen:
            return
        # direction を使って移動
        self.pos += self.direction * self.speed
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def update_frozen_state(self):
        """凍結状態を更新する"""
        if self.is_frozen:
            self.frozen_timer -= 1
            if self.frozen_timer <= 0:
                self.is_frozen = False

    def check_off_screen(self):
        if self.rect.top > screen_height or self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > GAME_AREA_WIDTH:
            self.kill()

    def collision_target(self):
        # ターゲットグループに take_damage メソッドを持つスプライトが存在する場合のみ判定
        if self.target_group and hasattr(self.target_group.sprite, 'take_damage'):
            target = self.target_group.sprite
            # 無敵状態でない場合のみ衝突判定
            if not getattr(target, 'invincible', False):
                # ターゲット中心取得（pos 優先）
                if hasattr(target, 'pos'):
                    target_center = pygame.math.Vector2(target.pos)
                else:
                    target_center = pygame.math.Vector2(target.rect.center)
    
                target_radius = getattr(target, 'radius', 20)
    
                # 円形当たり判定
                if self.pos.distance_to(target_center) < (self.radius + target_radius):
                    target.take_damage(1) # 1ダメージを与える
                    self.kill()

    def update(self):
        # 凍結状態を先に更新
        self.update_frozen_state()
        if self.is_frozen:
            # 凍結中でも寿命は減らす
            if self.has_lifetime:
                self.lifetime -= 1
                if self.lifetime <= 0:
                    self.kill()
                    return
            return # 凍結中はここで処理を中断
        self.move()

        # 渦巻き弾(vortex)や氷弾(ice)は円形なので、負荷の高い回転処理をスキップする
        if self.bullet_type == 'laser':
            # レーザーの場合：根本を軸に回転させる
            angle = -self.direction.angle_to(pygame.math.Vector2(0, 1))
            self.image = pygame.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(midbottom=self.pos)
        elif not self.bullet_type.startswith('vortex') and self.bullet_type != 'ice':
            # 進行方向に応じて画像を回転
            angle = -self.direction.angle_to(pygame.math.Vector2(0, 1))
            # 毎フレーム回転させると画質が劣化するので、元の画像を保持し、それを回転させる
            self.image = pygame.transform.rotate(self.original_image, angle) 
            self.rect = self.image.get_rect(center=self.pos)

        self.check_off_screen()
        # self.collision_target() # 衝突判定はGameクラスのQuadtreeで行うためコメントアウト

        # 寿命を更新
        if self.has_lifetime:
            self.lifetime -= 1
            if self.lifetime <= 0:
                self.kill()
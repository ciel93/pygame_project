import pygame
from setting import *

class Bullet(pygame.sprite.Sprite):
    _image_cache = {}

    def __init__(self, groups, x, y):
        super().__init__(groups)

        #画像
        self.image_list = []
        for i in range(2):
            path = f'assets/img/bullet/{i}.png'
            if path in Bullet._image_cache:
                image = Bullet._image_cache[path]
            else:
                image = pygame.image.load(path).convert_alpha()
                Bullet._image_cache[path] = image
            self.image_list.append(image)

        self.index = 0
        self.pre_image = self.image_list[self.index]
        self.image = pygame.transform.scale(self.pre_image,(24, 48))
        self.rect = self.image.get_rect(midbottom = (x, y))

        # スレッドでの当たり判定で必要になる属性を追加
        self.pos = pygame.math.Vector2(self.rect.center)
        self.radius = self.rect.width / 2 * 0.8 # 当たり判定を少し小さめに

        #移動
        self.speed = 8
        self.lifetime = 300 # 弾の寿命（フレーム数）。60FPSで5秒
        self.direction = pygame.math.Vector2(0, -1) # 進行方向ベクトル
    def check_off_screen(self):
        # 弾がゲームエリアの上下左右いずれかの外に出たら消去する
        if self.rect.bottom < 0 or self.rect.top > screen_height or \
           self.rect.right < 0 or self.rect.left > GAME_AREA_WIDTH:
            # self.kill() # ここでkillするとプールに戻らないため、コメントアウト
            pass
   
    def reset(self, x, y, lifetime=300):
        """オブジェクトプールから再利用される際に状態をリセットする"""
        self.pos = pygame.math.Vector2(x, y)
        self.rect.midbottom = (x, y)
        self.direction = pygame.math.Vector2(0, -1)
        self.index = 0
        self.animation() # 画像を初期状態に

        self.lifetime = lifetime
    def animation(self):
        self.index += 0.05
        
        if self.index >= len(self.image_list):
            self.index = 0

        self.pre_image = self.image_list[int(self.index)] # アニメーションの元画像
        self.image = pygame.transform.scale(self.pre_image,(24, 48))

    def move(self):
        self.pos += self.direction * self.speed
        self.rect.center = self.pos

    def update(self):
        self.move()
        self.check_off_screen()
        self.animation()

        # 進行方向に応じて画像を回転させる
        angle = -self.direction.angle_to(pygame.math.Vector2(0, -1))
        # アニメーションで更新されたself.imageを回転させる
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)


class HomingBullet(Bullet):
    """敵を追尾する弾"""
    def __init__(self, groups, x, y, enemy_group):
        super().__init__(groups, x, y)
        self.enemy_group = enemy_group
        self.target = None
        self.speed = 6  # ホーミング弾の速度
        self.turn_speed = 5  # 弾が方向転換する速さ

        self.pos = pygame.math.Vector2(self.rect.center)
        self.direction = pygame.math.Vector2(0, -1) # 初期方向は上

        # 最初にターゲットを見つけたら、以降は再探索しない
        self.has_initial_target = False

    def reset(self, x, y, lifetime=480):
        """ホーミング弾用のリセットメソッド"""
        super().reset(x, y, lifetime)
        self.rect.center = (x, y) # HomingBulletは中央から発射される
        self.target = None
        self.has_initial_target = False
        self.lifetime = lifetime # ホーミング弾は少し長めの寿命
        # 発射直後は真上に飛ぶ
        self.direction = pygame.math.Vector2(0, -1)


    def find_target(self):
        # ターゲットがいない、またはターゲットが倒された場合、新しいターゲットを探す
        if not self.target or not self.target.alive:
            min_dist = float('inf')
            closest_enemy = None
            for enemy in self.enemy_group:
                dist = self.pos.distance_to(enemy.rect.center)
                if dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy
            self.target = closest_enemy
            if self.target:
                self.has_initial_target = True

    def move(self):
        # 最初のターゲットを見つけるまで索敵する
        if not self.has_initial_target:
            self.find_target()

        if self.target and self.target.alive:
            # ターゲットへの方向ベクトルを計算し、滑らかに追尾
            if (self.target.rect.center - self.pos).length_squared() > 0:
                target_direction = (pygame.math.Vector2(self.target.rect.center) - self.pos)
                if target_direction.length_squared() > 0:
                    target_direction.normalize_ip()

                    # 2つのベクトルがほぼ180度反対向きの場合、slerpは未定義になるためエラーを回避
                    if self.direction.dot(target_direction) < -0.999:
                        # 代わりに線形補間(lerp)を使用して方向を少しだけ変える
                        self.direction = self.direction.lerp(target_direction, self.turn_speed * 0.02)
                    else:
                        self.direction = self.direction.slerp(target_direction, self.turn_speed * 0.02)
                else:
                    # ターゲットが弾の位置と完全に一致した場合、移動を停止しないように現在の方向を維持
                    pass
        
        self.pos += self.direction * self.speed
        self.rect.center = self.pos

    def update(self):
        # 親クラスのアニメーションも呼び出す
        self.move()
        self.check_off_screen()
        
        # 親クラスのアニメーションを呼び出して、self.image を更新
        self.animation()

        # 進行方向ベクトルから角度を計算 (as_polar()を使い、90度オフセットを引く)
        angle = -self.direction.as_polar()[1] - 90

        # 毎回、画質が劣化していないアニメーション用の元画像(self.pre_image)を
        # スケールしてから回転させることで、画質の劣化を防ぐ
        scaled_image = pygame.transform.scale(self.pre_image, (24, 48))
        self.image = pygame.transform.rotate(scaled_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)
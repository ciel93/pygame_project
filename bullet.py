import pygame
from setting import *

class Bullet(pygame.sprite.Sprite):
    def __init__(self, groups, x, y):
        super().__init__(groups)

        #画像
        self.image_list = []
        for i in range(2):
            image = pygame.image.load(f'assets/img/bullet/{i}.png').convert_alpha()
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
    def check_off_screen(self):
        # 弾がゲームエリアの上下左右いずれかの外に出たら消去する
        if self.rect.bottom < 0 or self.rect.top > screen_height or \
           self.rect.right < 0 or self.rect.left > GAME_AREA_WIDTH:
            self.kill()
   
    def animation(self):
        self.index += 0.05
        
        if self.index >= len(self.image_list):
            self.index = 0

        self.pre_image = self.image_list[int(self.index)] # アニメーションの元画像
        self.image = pygame.transform.scale(self.pre_image,(24, 48))

    def move(self):
        self.rect.y -= self.speed

    def update(self):
        self.move()
        self.check_off_screen()
        self.animation()

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
        # 最初にターゲットを見つけるまで、またはターゲットが生存している間のみ追尾
        if not self.has_initial_target:
            self.find_target()

        if self.target and self.target.alive:
            # ターゲットへの方向ベクトルを計算し、滑らかに追尾
            target_direction = (pygame.math.Vector2(self.target.rect.center) - self.pos).normalize()
            self.direction = self.direction.slerp(target_direction, self.turn_speed * 0.02)
        
        self.pos += self.direction * self.speed
        self.rect.center = self.pos

    def update(self):
        # 親クラスのアニメーションも呼び出す
        self.move()
        self.check_off_screen()
        
        # 親クラスのアニメーションを呼び出して、self.image を更新
        self.animation()

        # 進行方向ベクトルから角度を計算
        # self.direction は (0, -1) が上（0度）なので、そこからの角度を計算
        # Pygameのrotateは反時計回りが正なので、-1を掛けて向きを合わせる
        angle = -self.direction.angle_to(pygame.math.Vector2(0, -1))

        # 毎フレームリサイズするのではなく、アニメーションで更新されたself.imageを直接回転させる
        # これにより transform.scale の負荷が減る
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)
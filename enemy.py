import pygame
from setting import *
import random
from explosion import Explosion
from item import Item
from enemy_bullet import EnemyBullet

class Enemy(pygame.sprite.Sprite):
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None):
        super().__init__(groups)

        self.screen = pygame.display.get_surface()

        #グループ
        self.bullet_group = bullet_group
        self.explosion_group = pygame.sprite.Group()
        self.item_group = item_group

        # プレイヤーのスプライトグループ（弾の当たり判定用）
        self.player_group = player_group

        # 敵が発射する弾のグループ（共有グループを受け取る）
        # enemy_bullets_group が渡されていればそれを使い、なければローカルグループを作る
        self.enemy_bullets = enemy_bullets_group if enemy_bullets_group is not None else pygame.sprite.Group()
        self.fire_timer = 0

        #画像
        self.pre_image = pygame.image.load('assets/img/enemy/0.png')
        self.image = pygame.transform.scale(self.pre_image,(50, 50))
        self.rect = self.image.get_rect(center = (x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.radius = 30

        #移動
        move_list = [1, -1]
        self.direction = pygame.math.Vector2((random.choice(move_list), 1))
        self.speed = 1
        self.timer = 0

        #体力
        self.health = 3
        self.score_value = 10 # この敵を倒したときのスコア
        self.alive = True

        #爆発
        self.explosion = False

    def move(self):
        self.timer += 1
        if self.timer > 80:
            self.direction.x *= -1
            self.timer = 0

        # posを基準に移動し、rectに反映
        self.pos += self.direction * self.speed
        self.rect.center = self.pos
    
    def create_random_fire(self):
        """ランダムに弾を発射する（下方向に単発〜3連など）"""
        # player_group が渡されていない場合は発射しない
        if self.player_group is None:
            return

        self.fire_timer += 1
        # 発射判定は一定間隔ごとにランダムで行う
        if self.fire_timer >= 18:
            # 発射確率（0.0〜1.0）を調整
            if random.random() < 0.1:
                # 1〜3発ランダムに発射、若干の横ばらつき
                count = random.randint(1, 3)
                for i in range(count):
                    ox = random.randint(-12, 12)
                    x = self.rect.centerx + ox
                    y = self.rect.bottom + 6
                    speed = random.uniform(1.5, 3.0) # 弾速を遅くする
                    # 弾は self.enemy_bullets（共有グループ）に追加される
                    EnemyBullet(self.enemy_bullets, x, y, self.player_group, speed)
            self.fire_timer = 0

    def check_off_screen(self):
        if self.rect.top > screen_height :
            self.kill()

    def collision_bullet(self):
        # 当たり判定を行う範囲を敵周辺に限定するための矩形を定義
        check_area_size = 150 # 敵を中心とした150x150の範囲
        check_rect = pygame.Rect(0, 0, check_area_size, check_area_size)
        check_rect.center = self.rect.center

        for bullet in [b for b in self.bullet_group if b.rect.colliderect(check_rect)]:
            if self.rect.colliderect(bullet.rect):
                bullet.kill()
                self.health -= 1
            
            if self.health <= 0:
                self.should_award_score = True # スコア加算フラグ
                self.alive = False

    def check_death(self):
        if not self.alive and not self.explosion:
            self.speed = 0
            self.image.set_alpha(0)
            # アイテムドロップ判定
            if self.item_group is not None:
                drop_chance = random.random()
                if drop_chance < 0.05: # 5%の確率でボム (変更なし)
                    item_type = 'bomb'
                elif drop_chance < 0.25: # 20%の確率でスコア (5%～25%)
                    item_type = 'score'
                elif drop_chance < 0.70: # 45%の確率でパワー (25%～70%)
                    item_type = 'power'
                else:
                    item_type = None
                if item_type:
                    Item(self.item_group, self.rect.center, item_type)
            explosion = Explosion(self.explosion_group, self.rect.centerx, self.rect.centery)
            self.explosion = True
        elif self.explosion == True:
            self.kill()
    
    def take_damage(self, damage_amount=1):
        """弾やボムからダメージを受ける"""
        self.health -= damage_amount
        if self.health <= 0 and self.alive:
            self.should_award_score = True
            self.alive = False

    def update(self, move_override=False):
        if not move_override:
            self.move()
        self.collision_bullet()
        self.check_off_screen()
        self.check_death()

         # 敵弾の生成はここで行うが、共有グループの update/draw は Game 側で行う
        self.create_random_fire()

        #グループの描画と更新
        self.explosion_group.draw(self.screen)
        self.explosion_group.update()
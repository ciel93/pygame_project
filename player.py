import pygame
from setting import *
from bullet import Bullet, HomingBullet
from boss import BossEnemy

class Player(pygame.sprite.Sprite):
    def __init__(self, groups, x, y, enemy_group, enemy_bullets_group=None, item_group=None):
        super().__init__(groups)

        self.screen = pygame.display.get_surface()

        #グループ
        self.bullet_group = pygame.sprite.Group()
        self.item_group = item_group
        self.enemy_group = enemy_group
        # 共有の敵弾グループ（Game で作成したグループを受け取る）
        self.enemy_bullets = enemy_bullets_group

        #画像
        self.image_list = []
        for i in range(3):
            image = pygame.image.load(f'assets/img/player/{i}.png').convert_alpha()
            self.image_list.append(pygame.transform.scale(image, (50, 50)))
        self.index = 0
        self.image = self.image_list[self.index]
       # 当たり判定用の円の半径
        self.radius = 5  # プレイヤーの当たり判定サイズ
        self.pos = pygame.math.Vector2(x, y)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)  # 位置ベクトル

        # 当たり判定オーバーレイ表示フラグ（デバッグ用）
        self.show_hitbox = True

        #移動
        self.direction = pygame.math.Vector2()
        self.base_speed = 5           # 基本速度を定義
        self.slow_factor = 0.5        # シフト押下時の速度比（0.5 = 半速）
        self.slow = False             # シフト押下フラグ
        self.speed = self.base_speed  # 現在の速度を base_speed で初期化

        #弾
        self.fire = False
        self.timer = 0
        self.power_level = 1 # 弾のパワーレベル
        # ホーミング弾専用のタイマーとクールダウン
        self.homing_timer = 0
        self.homing_cooldown = 20 # 通常弾の2倍の間隔
        self.max_power = 5   # 最大パワーレベル

        #体力
        self.health = 3
        self.alive = True

        # 無敵時間
        self.invincible = False
        self.invincible_duration = 2000  # 2秒（ミリ秒）
        self.invincible_timer = 0
        self.original_image = self.image.copy() # 点滅用に元の画像を保持

    def input(self):
        key = pygame.key.get_pressed()
        
        # 左シフトまたは右シフトで低速移動
        self.slow = key[pygame.K_LSHIFT] or key[pygame.K_RSHIFT]
        # speed は move() で反映するためここでは direction のみ設定
        if key[pygame.K_UP]:
            self.direction.y = -1
        elif key[pygame.K_DOWN]:
            self.direction.y = 1
        else:
            self.direction.y = 0
        
        if key[pygame.K_LEFT]:
            self.direction.x = -1
            if self.index != 1:
                self.index = 1
                self.image = self.image_list[self.index]
        elif key[pygame.K_RIGHT]:
            self.direction.x = 1
            if self.index != 2:
                self.index = 2
                self.image = self.image_list[self.index]
        else:
            self.direction.x = 0
            if self.index != 0:
                self.index = 0
                self.image = self.image_list[self.index]

        if key[pygame.K_z] and self.fire == False:
            # パワーレベルに応じて弾を発射
            if self.power_level == 1:
                # レベル1: 中央に1発
                Bullet(self.bullet_group, self.rect.centerx, self.rect.top)
            elif self.power_level == 2:
                # レベル2: 少し開いた2発
                Bullet(self.bullet_group, self.rect.centerx - 10, self.rect.centery)
                Bullet(self.bullet_group, self.rect.centerx + 10, self.rect.centery)
            elif self.power_level == 3:
                # レベル3: 3-way弾
                Bullet(self.bullet_group, self.rect.centerx, self.rect.top)
                Bullet(self.bullet_group, self.rect.centerx - 20, self.rect.centery)
                Bullet(self.bullet_group, self.rect.centerx + 20, self.rect.centery)
            elif self.power_level == 4:
                # レベル4: 前方2連射 + 広めの2-way弾
                Bullet(self.bullet_group, self.rect.centerx - 8, self.rect.top)
                Bullet(self.bullet_group, self.rect.centerx + 8, self.rect.top)
                Bullet(self.bullet_group, self.rect.centerx - 25, self.rect.centery)
                Bullet(self.bullet_group, self.rect.centerx + 25, self.rect.centery)
            elif self.power_level >= 5:
                # レベル5: 前方3-way弾 + 両サイドからホーミング弾
                Bullet(self.bullet_group, self.rect.centerx, self.rect.top)
                Bullet(self.bullet_group, self.rect.centerx - 20, self.rect.centery)
                Bullet(self.bullet_group, self.rect.centerx + 20, self.rect.centery)

            self.fire = True

    def cooldown_bullet(self):
        if self.fire:
            self.timer += 1
        if self.timer > 10:
            self.fire = False
            self.timer = 0

    def fire_homing_bullets(self):
        """ホーミング弾を専用のクールダウンで発射する"""
        key = pygame.key.get_pressed()
        # パワーレベルが5以上で、Zキーが押されている場合
        if self.power_level >= 5 and key[pygame.K_z]:
            # ホーミング弾のクールダウンが終わっていれば発射
            if self.homing_timer == 0:
                HomingBullet(self.bullet_group, self.rect.left, self.rect.centery, self.enemy_group)
                HomingBullet(self.bullet_group, self.rect.right, self.rect.centery, self.enemy_group)
                self.homing_timer = self.homing_cooldown # タイマーをリセット

        if self.homing_timer > 0:
            self.homing_timer -= 1

    def move(self):
         # スロー状態を反映した速度を計算
        self.speed = int(self.base_speed * (self.slow_factor if self.slow else 1.0))
        if self.direction.magnitude() != 0:
            self.direction.normalize_ip()
        self.rect.x += self.direction.x*self.speed
        self.check_off_screen('horizontal')
        self.rect.y += self.direction.y*self.speed
        self.check_off_screen('vertical')
        # 位置ベクトルを更新
        self.pos = pygame.math.Vector2(self.rect.center)
    
    def check_off_screen(self, direction):
        if direction == 'horizontal':
            if self.rect.left < 0:
                self.rect.left = 0
            if self.rect.right > GAME_AREA_WIDTH:
                self.rect.right = GAME_AREA_WIDTH
        
        if direction == 'vertical':
            if self.rect.top < 0:
                self.rect.top = 0
            if self.rect.bottom > screen_height:
                self.rect.bottom = screen_height

    def collision_enemy(self):
        # 当たり判定を行う範囲を自機周辺に限定するための矩形を定義
        check_area_size = 250  # 自機を中心とした250x250の範囲
        check_rect = pygame.Rect(0, 0, check_area_size, check_area_size)
        check_rect.center = self.rect.center

        #敵本体との当たり判定
        if not self.invincible:
            # check_rectと衝突する可能性のある敵のみをリストアップ
            nearby_enemies = [e for e in self.enemy_group if e.rect.colliderect(check_rect)]
            for enemy in nearby_enemies:
                if self.rect.colliderect(enemy.rect):
                    # ボス以外の敵と衝突した場合
                    if not isinstance(enemy, BossEnemy):
                        self.take_damage()
                        enemy.kill() # 敵を消滅させる
                        break # 複数の敵と同時に当たらないようにループを抜ける
            
            # 共有の敵弾グループとの円形当たり判定
            if self.enemy_bullets is not None:
                # 同様に、check_rectと衝突する可能性のある敵弾のみをリストアップ
                nearby_bullets = [b for b in self.enemy_bullets if b.rect.colliderect(check_rect)]
                for bullet in nearby_bullets:
                    bullet_pos = pygame.math.Vector2(bullet.rect.center)
                    if self.pos.distance_to(bullet_pos) < self.radius + getattr(bullet, 'radius', 4):
                        self.take_damage()
                        bullet.kill()
                        break # 複数の弾と同時に当たらないようにループを抜ける

    def take_damage(self):
        """ダメージを受けて無敵状態を開始する"""
        self.health -= 1
        # パワーレベルを1に戻す
        self.power_level = 1
        self.invincible = True
        self.invincible_timer = pygame.time.get_ticks()
        if self.health <= 0:
            self.alive = False

    def collision_item(self):
        """アイテムとの当たり判定と取得処理"""
        if self.item_group is not None:
            for item in self.item_group:
                if self.rect.colliderect(item.rect):
                    if item.item_type == 'power':
                        if self.power_level < self.max_power:
                            self.power_level += 1
                    item.kill() # アイテムを消去

    def attract_items(self):
        """画面上部でアイテムを吸い込む"""
        # プレイヤーが画面の上端から30ピクセル以内にいる場合
        if self.rect.top < 30:
            if self.item_group is not None:
                for item in self.item_group:
                    # アイテムの吸い込みフラグを立てる
                    item.is_attracted = True

    
    def check_death(self):
        if self.alive == False:
            self.kill()

    def update_invincibility(self):
        """無敵状態の更新と点滅処理"""
        if self.invincible:
            now = pygame.time.get_ticks()
            # 無敵時間が終了したら
            if now - self.invincible_timer > self.invincible_duration:
                self.invincible = False
                # 現在の画像だけでなく、すべての画像リストの透明度をリセットする
                for img in self.image_list:
                    img.set_alpha(255)
            else:
                # 点滅処理
                alpha = 255 if (now // 100) % 2 == 0 else 128
                self.image.set_alpha(alpha)

    def update(self):
        self.input()
        self.move()
        self.cooldown_bullet()
        self.fire_homing_bullets()
        self.collision_enemy()
        self.collision_item()
        self.attract_items()
        self.update_invincibility()
        self.check_death()

         # 当たり判定オーバーレイ表示（デバッグ表示）
        if self.show_hitbox:
            # 緑の円でヒットボックス、赤い点で中心を表示
            pygame.draw.circle(self.screen, GREEN, (int(self.pos.x), int(self.pos.y)), self.radius, 1)
            pygame.draw.circle(self.screen, RED, (int(self.pos.x), int(self.pos.y)), 2)

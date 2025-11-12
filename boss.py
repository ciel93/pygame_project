import pygame
import random
import math
from enemy import Enemy
from enemy_bullet import EnemyBullet
from setting import *

class BossEnemy(Enemy):
    """ボス：HP大・パターン切替え・視覚的に目立つ"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group)
        self.speed = 1.0
        self.health = 80
        self.max_health = 80
        self.pattern_timer = 0
        self.score_value = 100 # ボスのスコア
        self.pattern = 0
        self.angle = 0.0
        self.vortex_angle = 0.0 # うずまき用の角度
        # レーザー薙ぎ払い用のパラメータ
        self.laser_angle = 90.0 # 開始角度（真下）
        self.laser_sweep_dir = 1 # 薙ぎ払う方向 (1:時計回り, -1:反時計回り)
        # レーヴァテイン用のパラメータ
        self.laevateinn_dir = random.choice([-1, 1])
        try:
            pre = pygame.image.load('assets/img/enemy/boss.png').convert_alpha()
            # 横幅を基準に、元のアスペクト比を維持してリサイズ
            new_width = 120
            aspect_ratio = pre.get_height() / pre.get_width()
            new_height = int(new_width * aspect_ratio)
            self.image = pygame.transform.scale(pre, (new_width, new_height))
        except Exception:
            # 画像がない場合のフォールバック
            surf = pygame.Surface((120,120), pygame.SRCALPHA)
            surf.fill(BOSS_ENEMY_COLOR)
            self.image = surf
        self.rect = self.image.get_rect(center=self.rect.center)
        self.radius = self.rect.width / 2 * 0.9 # 当たり判定を画像の半径に合わせる

        # 撃破時に弾をスコアに変換するためのフラグ
        self.just_defeated = False

        # レーヴァテインの予備動作で元の画像を保持するための変数
        self.original_image = self.image.copy()
        
        # レーヴァテイン用の移動フラグ
        self.is_laevateinn_moving = False
        self.laevateinn_move_dir = 1

    def move(self):
        # 上に現れて、少し下がったら左右に往復する
        target_y = 90
        if self.rect.y < target_y:
            self.pos.y += self.speed
        else:
            # レーヴァテイン薙ぎ払い後の特殊移動
            if self.is_laevateinn_moving:
                self.pos.x += 3.0 * self.laevateinn_move_dir # 少し速めに移動
                if not (self.rect.width / 2 < self.pos.x < GAME_AREA_WIDTH - self.rect.width / 2):
                    self.laevateinn_move_dir *= -1
                self.rect.center = self.pos
                return
            # 水平往復
            self.pos.x += math.sin(pygame.time.get_ticks() * 0.001) * 2

            # 画面内に制限
            if self.pos.x - self.rect.width / 2 < 0:
                self.pos.x = self.rect.width / 2
            if self.pos.x + self.rect.width / 2 > GAME_AREA_WIDTH:
                self.pos.x = GAME_AREA_WIDTH - self.rect.width / 2
        self.rect.center = self.pos

    def create_pattern(self):
        # パターンを周期的に切り替えて弾を生成
        # パターン8（待機）の場合は、短い時間で次のパターンへ移行
        pattern_change_time = 120 if self.pattern == 8 else 240

        self.pattern_timer += 1
        if self.pattern_timer > pattern_change_time:
            self.pattern_timer = 0
            # 現在のパターンが待機(8)でなければ、次は待機パターンへ移行
            if self.pattern != 8:
                self.pattern = 8
            else:
                # 待機が終わったら、次の攻撃パターンへ
                # (self.pattern + 1) % 7 で 0-6 の攻撃パターンをループさせる
                self.pattern = (self.pattern + 1) % 7

        if self.pattern == 0:
            self._wave_spread()
        elif self.pattern == 1:
            self._burst_ring()
        elif self.pattern == 2:
            self._scatter_shot()
        elif self.pattern == 3:
            self._homing_shot()
        elif self.pattern == 4:
            self._double_helix()
        elif self.pattern == 5:
            self._radial_vortex()
        elif self.pattern == 6: # レーザー薙ぎ払いパターン
            self._laser_sweep()
        elif self.pattern == 8: # 何もせずに待機するパターン
            pass # 何も実行しない

    def _wave_spread(self):
        # 横に波打つように縦列で弾を連続発射（少しずつ横ずれ）
        if self.pattern_timer % 15 == 0: # 発射間隔を広げて「まばらに」
            offset = math.sin(self.angle) * 80 # 横の揺れ幅を大きくして「広く」
            for i in range(-2,3):
                x = int(self.rect.centerx + offset + i*20) # 弾同士の間隔も広げる
                y = self.rect.bottom + 6
                speed = 1.5 + i*0.1 # 弾速を「遅く」する
                EnemyBullet(self.enemy_bullets, x, y, self.player_group, speed=speed)
            self.angle += 0.18

    def _burst_ring(self):
        # 横方向に広がるバースト（ボス直下に複数の弾）
        if self.pattern_timer % 50 == 0:
            for i in range(-6,7):
                x = int(self.rect.centerx + i*14)
                y = self.rect.centery + 10
                speed = 1.8 + abs(i)*0.08
                EnemyBullet(self.enemy_bullets, x, y, self.player_group, speed=speed)

    def _scatter_shot(self):
        """n-way弾を扇状にばらまく"""
        if self.pattern_timer % 35 == 0: # 発射間隔を調整
            n = 7  # 発射する弾の数
            spread_angle_deg = 80  # 弾が広がる全体の角度
            
            # 扇の中心を真下（90度）に向ける
            center_angle_rad = math.radians(90)
            spread_angle_rad = math.radians(spread_angle_deg)
            
            for i in range(n):
                # 各弾の角度を計算
                angle = center_angle_rad - spread_angle_rad / 2 + (spread_angle_rad / max(1, n - 1)) * i
                direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
                EnemyBullet(self.enemy_bullets, self.rect.centerx, self.rect.bottom, self.player_group, speed=2.8, direction=direction)
    
    def _homing_shot(self):
        """プレイヤーを狙う弾を定期的に発射する新しいパターン"""
        if self.pattern_timer % 45 == 0:  # 45フレーム毎に発射
            if self.player_group and len(self.player_group) > 0:
                player = list(self.player_group)[0]
                # プレイヤーへの方向ベクトルを計算
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                if dx == 0 and dy == 0:
                    direction = pygame.math.Vector2(0, 1)
                else:
                    direction = pygame.math.Vector2(dx, dy).normalize()

                bullet_speed = 3.0
                # 弾を生成（プレイヤーを狙う）
                EnemyBullet(self.enemy_bullets,
                            self.rect.centerx,
                            self.rect.bottom,
                            self.player_group,
                            speed=bullet_speed,
                            direction=direction)

    def _double_helix(self):
        """二重螺旋状に弾を発射する"""
        if self.pattern_timer % 5 == 0: # 5フレーム毎に発射して滑らかな螺旋に
            amplitude = 90  # 螺旋の幅を少し広げる
            # 螺旋の中心をゆっくりと左右に揺らし、安全地帯をなくす
            center_x = self.rect.centerx + math.cos(self.angle * 0.5) * 40
            
            # 螺旋1
            x1 = center_x + amplitude * math.sin(self.angle)
            EnemyBullet(self.enemy_bullets, x1, self.rect.bottom, self.player_group, speed=2.5)

            # 螺旋2（位相を180度ずらす）
            x2 = center_x + amplitude * math.sin(self.angle + math.pi)
            EnemyBullet(self.enemy_bullets, x2, self.rect.bottom, self.player_group, speed=2.5)

            self.angle += 0.15 # 角度を更新して螺旋を描く

    def _radial_vortex(self):
        """中心から放射状に回転しながら弾を発射する"""
        if self.pattern_timer % 12 == 0: # 弾の発射頻度を下げてまばらに
            num_arms = 6 # 同時に発射する弾の方向（腕の数）
            rotation_speed = 0.07 # 渦全体の回転速度

            # 渦弾の発射と同時に、一定間隔で自機狙い弾を追加
            if self.pattern_timer % 60 == 0:
                if self.player_group and len(self.player_group) > 0:
                    player = list(self.player_group)[0]
                    dx = player.rect.centerx - self.rect.centerx
                    dy = player.rect.centery - self.rect.centery
                    if dx == 0 and dy == 0:
                        direction = pygame.math.Vector2(0, 1)
                    else:
                        direction = pygame.math.Vector2(dx, dy).normalize()
                    
                    # 自機狙い弾は少し速くする
                    EnemyBullet(self.enemy_bullets, self.rect.centerx, self.rect.centery, self.player_group, speed=2.5, direction=direction, radius=16, color=ENEMY_BULLET_SPECIAL_COLOR)

            for i in range(num_arms):
                angle_offset = (2 * math.pi / num_arms) * i

                # 時計回りの渦
                current_angle = self.vortex_angle + angle_offset
                direction = pygame.math.Vector2(math.cos(current_angle), math.sin(current_angle))
                EnemyBullet(self.enemy_bullets, self.rect.centerx, self.rect.centery, self.player_group, speed=1.5, direction=direction)

                # 反時計回りの渦
                current_angle_rev = -self.vortex_angle + angle_offset
                direction_rev = pygame.math.Vector2(math.cos(current_angle_rev), math.sin(current_angle_rev))
                EnemyBullet(self.enemy_bullets, self.rect.centerx, self.rect.centery, self.player_group, speed=1.0, direction=direction_rev)

            self.vortex_angle += rotation_speed # 角度を更新して渦全体を回転させる

    def _laser_sweep(self):
        """レーザーのように弾を薙ぎ払う新しいパターン"""
        # 弾の生成を12フレームに1回に調整（密度をさらに減らすため）
        if self.pattern_timer % 12 == 0:
            speed = 2.0 # 弾速を遅くする
            
            # レーザーの角度を計算（度数法からラジアンに変換）
            angle_rad = math.radians(self.laser_angle)
            direction = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))
            
            # 細長いレーザー弾を生成
            # radiusを大きくしてレーザーをさらに太くする
            EnemyBullet(self.enemy_bullets, self.rect.centerx, self.rect.centery, self.player_group, speed=speed, direction=direction, radius=32, length=150, color=(255, 50, 255), bullet_type='laser')

        # 角度を更新して薙ぎ払い
        self.laser_angle += 0.6 * self.laser_sweep_dir # 薙ぎ払う速度をさらに遅くする
        # 左右の端（20度～160度）で反射するように動く
        if not (20 < self.laser_angle < 160):
            self.laser_sweep_dir *= -1

    def _laevateinn_sweep(self):
        """東方風のレーヴァテイン薙ぎ払い"""
        # パターン開始時の初期化
        if self.pattern_timer == 1:
            self.laevateinn_dir *= -1 # 前のスイングと逆方向から開始
            self.is_laevateinn_moving = False # 移動フラグをリセット

        pre_action_duration = 60 # 予備動作の時間（60フレーム = 1秒）

        # フェーズ1: 予備動作
        if self.pattern_timer < pre_action_duration:
            # ボスの色を赤く点滅させて力を溜める演出
            self.image = self.original_image.copy() # 毎回、元の画像からコピーして使用する
            if self.pattern_timer % 10 < 5:
                self.image.fill((255, 100, 100, 150), special_flags=pygame.BLEND_RGBA_ADD)

        # フェーズ2: 薙ぎ払い
        elif self.pattern_timer < pre_action_duration + (self.pattern_change_time * 0.6):
            self.image = self.original_image.copy() # 色を元に戻す
            if (self.pattern_timer - pre_action_duration) % 8 == 0:
                progress = (self.pattern_timer - pre_action_duration) / (self.pattern_change_time * 0.6)
                angle_deg = 90 - (80 * progress * self.laevateinn_dir)
                angle_rad = math.radians(angle_deg)
                direction = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))

                sword_length = 18
                for i in range(sword_length):
                    dist = i * 28
                    pos = pygame.math.Vector2(self.rect.center) + direction * dist
                    speed = 2.0 + (i / sword_length) * 3.0
                    radius = 10 + (i / sword_length) * 12
                    red_val = 150 + (i / sword_length) * 105
                    EnemyBullet(self.enemy_bullets, pos.x, pos.y, self.player_group, speed=speed, direction=direction, radius=radius, color=(red_val, 50, 20))
        # フェーズ3: 横移動しながら剣を突き出す
        else:
            self.image = self.original_image.copy() # 色を元に戻す
            self.is_laevateinn_moving = True
            self.laevateinn_move_dir = self.laevateinn_dir
            if self.pattern_timer % 12 == 0:
                angle_deg = 90
                angle_rad = math.radians(angle_deg)
                direction = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))

                sword_length = 18
                for i in range(sword_length):
                    dist = i * 28
                    pos = pygame.math.Vector2(self.rect.center) + direction * dist
                    speed = 2.0 + (i / sword_length) * 3.0
                    radius = 10 + (i / sword_length) * 12
                    red_val = 150 + (i / sword_length) * 105
                    EnemyBullet(self.enemy_bullets, pos.x, pos.y, self.player_group, speed=speed, direction=direction, radius=radius, color=(red_val, 50, 20))

    def check_death(self):
        # 倒された最初のフレームでフラグを立てる
        if self.alive == False and self.explosion == False and not self.just_defeated:
            self.just_defeated = True
        super().check_death()

    def update(self):
        # Boss は敵基底 update を参考にして動作させる
        # うずまき弾(pattern 5)発射中は移動を停止する
        if self.pattern != 5:
            self.move()
        self.create_pattern()
        super().update(move_override=True)
        # 爆発などは親に従う
        self.explosion_group.draw(self.screen)
        self.explosion_group.update()

class GrandBossEnemy(BossEnemy):
    """ゲームの最終ボス（大ボス）"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group)
        
        # 大ボス専用のパラメータで上書き
        self.health = 300  # HPを大幅に増やす
        self.score_value = 500 # 大ボスのスコア
        self.max_health = 300
        self.speed = 0.8   # 少しゆっくり動かす
        
        try:
            pre = pygame.image.load('assets/img/enemy/grand_boss.png').convert_alpha()
            # 横幅を基準に、元のアスペクト比を維持してリサイズ
            new_width = 180
            aspect_ratio = pre.get_height() / pre.get_width()
            new_height = int(new_width * aspect_ratio)
            self.image = pygame.transform.scale(pre, (new_width, new_height))
        except Exception:
            # 画像がない場合のフォールバック
            surf = pygame.Surface((180, 180), pygame.SRCALPHA)
            surf.fill(GRAND_BOSS_COLOR)
            self.image = surf
        self.rect = self.image.get_rect(center=self.rect.center)
        self.radius = self.rect.width / 2 * 0.9 # 当たり判定を画像の半径に合わせる

        # パターン切替時間を短くして、より頻繁に攻撃させる
        self.pattern_change_time = 180 # 3秒

        # 親クラスと同様にoriginal_imageを初期化
        self.original_image = self.image.copy()
        
        # HPによる発狂モードのフラグ
        self.enrage_mode = False

    def create_pattern(self):
        # HPが半分以下になったら発狂モードに移行
        if not self.enrage_mode and self.health <= self.max_health / 2:
            self.enrage_mode = True
            self.pattern_change_time = 120 # パターン切替をさらに高速化

        # パターン切替
        self.pattern_timer += 1
        if self.pattern_timer > self.pattern_change_time:
            # 発狂モードでは、より激しい攻撃(4, 5)の頻度が上がる
            if self.enrage_mode:
                self.pattern = random.choice([0, 1, 2, 3, 4, 5, 6, 6, 7, 7]) # パターン7(レーヴァテイン)を追加
            else:
                self.pattern = random.randint(0, 6) # 通常時はレーザーまで
            self.pattern_timer = 0
        
        # 選択されたパターンを実行（親クラスのメソッドを呼び出す）
        if self.pattern == 0:
            self._wave_spread()
        elif self.pattern == 1:
            self._burst_ring()
        elif self.pattern == 2:
            self._scatter_shot()
        elif self.pattern == 3:
            self._homing_shot()
        elif self.pattern == 4:
            self._double_helix()
        elif self.pattern == 5:
            self._radial_vortex()
        elif self.pattern == 6:
            self._laser_sweep()
        else: # パターン7
            self._laevateinn_sweep()

    def update(self):
        # BossEnemyのupdateメソッドを呼び出す
        # これにより、move, create_pattern, 各種チェックが実行される
        # GrandBossEnemyはBossEnemyの攻撃パターンをそのまま利用する
        super().update()
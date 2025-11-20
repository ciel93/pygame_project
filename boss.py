import pygame
import random
import math
from enemy import Enemy
from enemy_bullet import EnemyBullet
from setting import *

class BossEnemy(Enemy):
    """ボス：HP大・パターン切替え・視覚的に目立つ"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool)
        self.speed = 1.0
        self.health = 250
        self.max_health = 250
        self.pattern_timer = 0
        self.pattern_change_time = 300 # パターン切替時間（フレーム数）
        self.score_value = 100 # ボスのスコア
        self.pattern = 0
        self.angle = 0.0
        self.vortex_angle = 0.0 # うずまき用の角度
        self.last_attack_pattern = 0 # 攻撃ローテーションの記憶用
        self.scatter_shot_column_counter = 0 # 扇状弾の偶数列ずらし用カウンター
        # レーザー薙ぎ払い用のパラメータ
        self.laser_angle = 90.0 # 開始角度（真下）
        self.laser_sweep_dir = 1 # 薙ぎ払う方向 (1:時計回り, -1:反時計回り)
        # レーヴァテイン用のパラメータ
        self.laevateinn_dir = random.choice([-1, 1])
        
        image_path = 'assets/img/enemy/boss.png'
        if image_path in Enemy._image_cache:
            pre = Enemy._image_cache[image_path]
        else:
            try:
                pre = pygame.image.load(image_path).convert_alpha()
                Enemy._image_cache[image_path] = pre
            except Exception:
                pre = None
        
        new_width = 120
        aspect_ratio = pre.get_height() / pre.get_width() if pre else 1
        new_height = int(new_width * aspect_ratio)
        self.image = pygame.transform.scale(pre, (new_width, new_height)) if pre else pygame.Surface((new_width, new_height), pygame.SRCALPHA)
        if not pre: self.image.fill(BOSS_ENEMY_COLOR)

        self.rect = self.image.get_rect(center=self.rect.center)
        self.radius = self.rect.width / 2 * 0.9 # 当たり判定を画像の半径に合わせる

        # 撃破時に弾をスコアに変換するためのフラグ
        self.just_defeated = False

        # レーヴァテインの予備動作で元の画像を保持するための変数
        self.original_image = self.image.copy()
        
        # レーヴァテイン用の移動フラグ
        self.is_laevateinn_moving = False
        self.laevateinn_move_dir = 1
        
        # 発狂モードのフラグ
        self.enrage_mode = False
        
        # 攻撃パターンのディスパッチテーブル
        self.attack_patterns = {
            0: self._wave_spread,
            1: self._burst_ring,
            2: self._scatter_shot,
            3: self._homing_shot,
            4: self._double_helix,
            5: self._radial_vortex,
            6: self._laser_sweep,
            7: self._icicle_fall,
            8: self._laevateinn_sweep,
            9: self._perfect_freeze, # 待機(9)を新しい攻撃で上書き
            10: self._scatter_shot_staggered, # 新しいパターンを追加
            11: self._all_around_shot, # 新しい全周囲弾幕パターン
        }

    def move(self):
        # レーヴァテイン薙ぎ払い後の特殊移動
        if self.is_laevateinn_moving:
            self.pos.x += 3.0 * self.laevateinn_move_dir # 少し速めに移動
            if not (self.rect.width / 2 < self.pos.x < GAME_AREA_WIDTH - self.rect.width / 2):
                self.laevateinn_move_dir *= -1
            self.rect.center = self.pos
            return

        # 上に現れて、少し下がったら左右に往復する
        target_y = 90
        if self.rect.y < target_y:
            self.pos.y += self.speed
        else:
            # 通常の水平往復移動
            self.pos.x += math.sin(pygame.time.get_ticks() * 0.001) * 2

            # 画面内に制限
            if self.pos.x - self.rect.width / 2 < 0:
                self.pos.x = self.rect.width / 2
            if self.pos.x + self.rect.width / 2 > GAME_AREA_WIDTH:
                self.pos.x = GAME_AREA_WIDTH - self.rect.width / 2
        self.rect.center = self.pos

    def create_pattern(self):
        # ボスが倒されたら弾の生成を停止
        if not self.alive:
            return

        # HPが半分以下になったら発狂モードに移行
        if not self.enrage_mode and self.health <= self.max_health / 2:
            self.enrage_mode = True
            self.pattern_change_time = 240 # パターン切替を高速化

        # パターンを周期的に切り替えて弾を生成
        # パターン9（待機）の場合は、短い時間で次のパターンへ移行
        if self.pattern == 0: # wave_spread
            pattern_change_time = 360 # wave_spreadの時間を長くする
        elif self.pattern == 12: # 新しい待機パターン番号
            pattern_change_time = 120
        else:
            pattern_change_time = self.pattern_change_time

        self.pattern_timer += 1
        if self.pattern_timer > pattern_change_time:
            # all_around_shot (11) の実行中はパターンを切り替えない
            if self.pattern == 11:
                self.pattern_timer = 0 # タイマーのみリセットして継続
                return

            self.pattern_timer = 0 # タイマーリセットは共通
            if self.enrage_mode:
                # 発狂モード: 激しい攻撃をランダムに選択
                self.pattern = random.choice([4, 5, 6, 7]) # レーヴァテイン(8)を削除
            else:
                # 通常モード: パターンを順番に実行し、間に待機を挟む
                if self.pattern != 12: # 待機パターンへ
                    self.pattern = 12
                else:
                    # 待機が終わったら、次の攻撃パターンへ (0, 1, 2, 10, 11をループ)
                    attack_rotation = [0, 1, 2, 10, 11]
                    current_pattern_index = attack_rotation.index(self.last_attack_pattern) if self.last_attack_pattern in attack_rotation else -1
                    self.last_attack_pattern = attack_rotation[(current_pattern_index + 1) % len(attack_rotation)]
                    self.pattern = self.last_attack_pattern

        # ディスパッチテーブルを使って攻撃パターンを実行
        if self.pattern in self.attack_patterns: # パターンが存在すれば実行
            self.attack_patterns[self.pattern]()
    def _wave_spread(self):
        # 横に波打つように縦列で弾を連続発射（少しずつ横ずれ）
        if self.pattern_timer % 25 == 0: # 発射間隔を少し戻す
            offset = math.sin(self.angle) * 80 # 横の揺れ幅を大きくして「広く」
            for i in range(-4,5): # 発射数9発
                x = int(self.rect.centerx + offset + i*20) # 弾同士の間隔も広げる
                y = self.rect.bottom + 6
                speed = 2.0 # 弾速を少し上げる
                # V字に広がるように、各弾に少しだけ横方向のベクトルを与える
                direction_x = i * 0.08
                direction = pygame.math.Vector2(direction_x, 1).normalize()
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(x, y, self.player_group, speed=speed, direction=direction)
            self.angle += 0.18

    def _burst_ring(self):
        # 横方向に広がるバースト（ボス直下に複数の弾）
        if self.pattern_timer % 50 == 0:
            for i in range(-8, 9): # さらに拡散する弾の数を増やす
                x = int(self.rect.centerx + i * 25) # 弾同士の間隔をさらに広げる
                y = self.rect.centery + 10
                speed = 1.8 + abs(i) * 0.08
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(x, y, self.player_group, speed=speed)

    def _scatter_shot(self):
        """n-way弾を扇状にばらまく"""
        if self.pattern_timer % 35 == 0: # 発射間隔を調整
            n = 5  # 発射する弾の数
            spread_angle_deg = 60  # 弾が広がる全体の角度
            # 扇の中心を真下（90度）に向ける
            center_angle_rad = math.radians(90)
            spread_angle_rad = math.radians(spread_angle_deg)
            
            for i in range(n):
                # 各弾の角度を計算
                angle = center_angle_rad - spread_angle_rad / 2 + (spread_angle_rad / max(1, n - 1)) * i
                direction = pygame.math.Vector2(math.cos(angle), math.sin(angle)) # directionを定義
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(self.rect.centerx, self.rect.bottom, self.player_group, speed=2.8, direction=direction)
    
    def _scatter_shot_staggered(self):
        """n-way弾を扇状に発射し、偶数列の角度をずらす"""
        if self.pattern_timer % 35 == 0:
            n = 7
            spread_angle_deg = 80
            angle_shift_for_column = math.radians(10) if self.scatter_shot_column_counter % 2 == 0 else 0
            center_angle_rad = math.radians(90)
            spread_angle_rad = math.radians(spread_angle_deg)
            for i in range(n):
                angle = center_angle_rad - spread_angle_rad / 2 + (spread_angle_rad / max(1, n - 1)) * i + angle_shift_for_column
                direction = pygame.math.Vector2(math.cos(angle), math.sin(angle)) # directionを定義
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(self.rect.centerx, self.rect.bottom, self.player_group, speed=2.8, direction=direction)
            self.scatter_shot_column_counter += 1 # カウンターをインクリメント
    
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
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(self.rect.centerx,
                             self.rect.bottom,
                             self.player_group,
                             speed=bullet_speed,
                             direction=direction)

    def _double_helix(self):
        """二重螺旋状に弾を発射する"""
        if self.pattern_timer % 12 == 0: # 12フレーム毎に発射して、隙間をさらに粗くする
            amplitude = 120  # 螺旋の幅を長くする
            # 螺旋の中心をゆっくりと左右に揺らし、安全地帯をなくす
            center_x = self.rect.centerx + math.cos(self.angle * 0.5) * 40
            
            # 螺旋1
            x1 = center_x + amplitude * math.sin(self.angle) # x1を定義
            bullet1 = self.enemy_bullet_pool.get()
            bullet1.reset(x1, self.rect.bottom, self.player_group, speed=3.5)

            # 螺旋2（位相を180度ずらす）
            x2 = center_x + amplitude * math.sin(self.angle + math.pi) # x2を定義
            bullet2 = self.enemy_bullet_pool.get()
            bullet2.reset(x2, self.rect.bottom, self.player_group, speed=3.5)

            self.angle += 0.12 # 角度の更新を緩やかにして、縦に引き伸ばす

    def _radial_vortex(self):
        """中心から放射状に回転しながら弾を発射する"""
        if self.pattern_timer % 25 == 0: # 弾の発射頻度をさらに下げる (20 -> 25)
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
                    
                    bullet = self.enemy_bullet_pool.get()
                    bullet.reset(self.rect.centerx, self.rect.centery, self.player_group, speed=2.5, direction=direction, radius=16, bullet_type='homing')

            for i in range(num_arms):
                angle_offset = (2 * math.pi / num_arms) * i

                # 時計回りの渦
                current_angle = self.vortex_angle + angle_offset
                direction = pygame.math.Vector2(math.cos(current_angle), math.sin(current_angle)) # directionを定義
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(self.rect.centerx, self.rect.centery, self.player_group, speed=1.5, direction=direction, bullet_type='vortex')


                # 反時計回りの渦
                current_angle_rev = -self.vortex_angle + angle_offset
                direction_rev = pygame.math.Vector2(math.cos(current_angle_rev), math.sin(current_angle_rev))
                EnemyBullet(self.enemy_bullets, self.rect.centerx, self.rect.centery, self.player_group, speed=1.0, direction=direction_rev, bullet_type='vortex_rev')

            self.vortex_angle += rotation_speed # 角度を更新して渦全体を回転させる

    def _laser_sweep(self):
        """レーザーのように弾を薙ぎ払う新しいパターン"""
        # 弾の生成を32フレームに1回に調整（密度をさらに減らすため）
        if self.pattern_timer % 32 == 0: 
            speed = 2.0 # 弾速を遅くする
            
            # レーザーの角度を計算（度数法からラジアンに変換）
            angle_rad = math.radians(self.laser_angle)
            direction = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))
            
            # 細長いレーザー弾を生成
            # radiusを大きくしてレーザーをさらに太くする
            bullet = self.enemy_bullet_pool.get()
            bullet.reset(self.rect.centerx, self.rect.centery, self.player_group, speed=speed, direction=direction, radius=32, length=150, color=(255, 50, 255), bullet_type='laser')

        # 角度を更新して薙ぎ払い
        self.laser_angle += 0.6 * self.laser_sweep_dir # 薙ぎ払う速度をさらに遅くする
        # 左右の端（20度～160度）で反射するように動く
        if not (20 < self.laser_angle < 160):
            self.laser_sweep_dir *= -1

    def _icicle_fall(self):
        """画面上部からつららのように弾が降り注ぐパターン"""
        if self.pattern_timer % 10 == 0: # 10フレームごとに弾を生成
            x = random.randint(0, GAME_AREA_WIDTH)
            speed = random.uniform(2.5, 5.0)
            # 弾の色を青みがかった色にする
            bullet = self.enemy_bullet_pool.get()
            bullet.reset(x, 0, self.player_group, speed=speed, bullet_type='ice')

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
            self.image = self.original_image.copy()  # 色を元に戻す
            progress = (self.pattern_timer - pre_action_duration) / (self.pattern_change_time * 0.6)
            angle_deg = 90 - (80 * progress * self.laevateinn_dir)
            angle_rad = math.radians(angle_deg)
            direction = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))

            # 剣のような形で弾を生成
            if (self.pattern_timer - pre_action_duration) % 8 == 0:
                sword_length = 24  # 弾数
                for i in range(sword_length):
                    dist = i * 18  # 弾の間隔
                    pos = pygame.math.Vector2(self.rect.center) + direction * dist
                    speed = 1.8 + (i / sword_length) * 2.5
                    radius = 6 + (i / sword_length) * 8
                    red_val = 150 + (i / sword_length) * 105
                    bullet = self.enemy_bullet_pool.get()
                    bullet.reset(pos.x, pos.y, self.player_group, speed=speed, direction=direction, radius=radius, color=(red_val, 50, 20), frozen_duration=4)
        # フェーズ3: 横移動しながら剣を突き出す
        else:
            self.image = self.original_image.copy() # 色を元に戻す
            self.is_laevateinn_moving = True # 特殊移動フラグを立てる
            self.laevateinn_move_dir = self.laevateinn_dir            

            if self.pattern_timer % 14 == 0: # 間隔を広げる
                angle_deg = 90
                angle_rad = math.radians(angle_deg)
                direction = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))

                sword_length = 18
                for i in range(sword_length):
                    dist = i * 28
                    pos = pygame.math.Vector2(self.rect.center) + direction * dist
                    speed = 2.0 + (i / sword_length) * 3.0                    
                    radius = 10 + (i / sword_length) * 12
                    red_val = 150 + (i / sword_length) * 105 # red_valを定義
                    bullet = self.enemy_bullet_pool.get()
                    bullet.reset(pos.x, pos.y, self.player_group, speed=speed, direction=direction, radius=radius, color=(red_val, 50, 20))

    def _perfect_freeze(self):
        """パーフェクトフリーズ風弾幕: 弾を生成し、一定時間後に一斉に動き出す"""
        # パターン開始時に一度だけ大量の弾を生成
        if self.pattern_timer == 1:
            num_bullets = 48 # 生成する弾の数
            radius = 150 # ボスからの距離
            base_frozen_duration = 60 # 基本の凍結時間（フレーム）
            delay_per_bullet = 2 # 弾ごとの追加凍結時間（フレーム）

            for i in range(num_bullets):
                angle = (360 / num_bullets) * i
                angle_rad = math.radians(angle)
                # 弾の生成位置
                pos_offset = pygame.math.Vector2(radius, 0).rotate(angle)
                pos = pygame.math.Vector2(self.rect.center) + pos_offset
                # 弾の発射方向（中心から外側へ）
                direction_outward = pos_offset.normalize()
                current_frozen_duration = base_frozen_duration + (i * delay_per_bullet) # current_frozen_durationを定義
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(pos.x, pos.y, self.player_group, speed=2.5, direction=direction_outward, bullet_type='ice', frozen_duration=current_frozen_duration)

    def _all_around_shot(self):
        """全方位に弾を発射する通常弾幕"""
        if self.pattern_timer % 20 == 0: # 20フレームごとに発射
            num_bullets = 12 # 12方向

            # 毎回少し角度をずらして、螺旋状に見せる
            angle_offset = math.radians(self.pattern_timer) # 緩やかな回転
            
            for i in range(num_bullets):
                angle = (2 * math.pi / num_bullets) * i + angle_offset
                direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(self.rect.centerx, self.rect.centery, self.player_group, speed=0.8, direction=direction)

    def check_death(self):
        # 倒された最初のフレームでフラグを立てる
        if self.alive == False and self.explosion == False and not self.just_defeated:
            self.just_defeated = True
        super().check_death()

    def update(self):
        # Boss は敵基底 update を参考にして動作させる
        # 特定の弾幕発射中の移動制御
        if self.pattern == 11: # all_around_shot
            # X軸の中央に移動して静止
            target_x = GAME_AREA_WIDTH // 2
            dx = target_x - self.pos.x
            # 十分に近づいたら移動を停止
            if abs(dx) > 1:
                self.pos.x += dx * 0.05 # スムーズに移動
            self.rect.centerx = int(self.pos.x)
        elif self.pattern != 5: # うずまき弾(pattern 5)発射中は移動を停止
            self.move()
        self.create_pattern()
        super().update(move_override=True)
        # 爆発などは親に従う
        self.explosion_group.draw(self.screen)
        self.explosion_group.update()
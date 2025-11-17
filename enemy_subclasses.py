import pygame
import random
import math
from enemy import Enemy
from enemy_bullet import EnemyBullet
from setting import *

class FastEnemy(Enemy):
    """素早く動いて少ないHPの敵、スポーン時に停止して自機狙い弾を発射"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool)
        self.speed = 3          # 速く移動
        self.health = 1         # 低HP
        self.score_value = 20   # FastEnemyのスコア
        
        image_path = 'assets/img/enemy/fast.png'
        if image_path in Enemy._image_cache:
            pre = Enemy._image_cache[image_path]
        else:
            try:
                pre = pygame.image.load(image_path).convert_alpha()
                Enemy._image_cache[image_path] = pre
            except Exception:
                pre = None
        
        if pre:
            self.image = pygame.transform.scale(pre, (40, 40))
        else:
            self.image = pygame.Surface((40,40), pygame.SRCALPHA)
            self.image.fill(FAST_ENEMY_COLOR)
        self.rect = self.image.get_rect(center=self.rect.center)
        
        # 位置を浮動小数点で管理
        self.pos = pygame.math.Vector2(self.rect.center)
        
         # 行動パターン用のパラメータ
        self.state = 'spawn'          # spawn -> aim -> move
        self.spawn_time = pygame.time.get_ticks()  # スポーン時刻（ms）
        self.pause_ms = 2000           # スポーン後停止時間（ms）
        self.fire_timer = 0
        self.aim_shots = 0            # 発射した弾数
        self.max_shots = 5            # 発射する弾数
        self.shot_interval = 300      # 弾の発射間隔（ms）

        # 横移動用
        self.move_direction = random.choice([-1, 1])  # 左か右にランダム

    def move(self):
        now = pygame.time.get_ticks()

        if self.state == 'spawn':
                # スポーン直後は pause_ms 経過まで停止
                if now - self.spawn_time >= self.pause_ms:
                    self.state = 'aim'
                    self.last_shot_time = now
                    
        elif self.state == 'aim':
                # プレイヤーを狙って弾を発射（shot_interval 毎）
                if self.player_group and len(self.player_group) > 0:
                    if now - self.last_shot_time >= self.shot_interval:
                        player = list(self.player_group)[0]
                        # プレイヤーへの方向ベクトルを計算
                        dx = player.rect.centerx - self.rect.centerx
                        dy = player.rect.centery - self.rect.centery
                        if dx == 0 and dy == 0:
                            direction = pygame.math.Vector2(0, 1)
                        else:
                            direction = pygame.math.Vector2(dx, dy).normalize()

                        bullet_speed = 3.0 # 弾速を遅くする
                        # 弾を生成（direction を直接渡す）
                        bullet = self.enemy_bullet_pool.get()
                        bullet.reset(self.rect.centerx,
                                     self.rect.bottom,
                                     self.player_group,
                                     speed=bullet_speed,
                                     direction=direction)
                        
                        self.aim_shots += 1
                        self.last_shot_time = now

                        if self.aim_shots >= self.max_shots:
                            self.state = 'move'

        elif self.state == 'move':
                # プレイヤーを追尾する
                if self.player_group and len(self.player_group) > 0:
                    player = list(self.player_group)[0]
                    direction = pygame.math.Vector2(player.rect.centerx - self.pos.x,
                                                    player.rect.centery - self.pos.y)
                    if direction.length() > 0:
                        direction.normalize_ip()
                    self.pos += direction * self.speed

            # pos を rect に反映
        self.rect.centerx = int(self.pos.x)
        self.rect.centery = int(self.pos.y)

    def update(self):
        # FastEnemy 独自の移動ロジックを呼び出す
        self.move()
        # 親クラスの update を呼び出すが、move は上書きしない
        # 弾の衝突判定、死亡処理、画面外チェックなどを実行
        super().update(move_override=True)

class TankEnemy(Enemy):
    """遅いが耐久力のある敵、サイン波移動＋ランダム突進（バースト）"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool)
        self.speed = 0.5       # 基本の縦速度
        self.health = 6        # 高HP
        self.score_value = 30  # TankEnemyのスコア

        image_path = 'assets/img/enemy/tank.png'
        if image_path in Enemy._image_cache:
            pre = Enemy._image_cache[image_path]
        else:
            try:
                pre = pygame.image.load(image_path).convert_alpha()
                Enemy._image_cache[image_path] = pre
            except Exception:
                pre = None
        if pre:
            self.image = pygame.transform.scale(pre, (60, 60))
        else:
            self.image = pygame.Surface((60,60), pygame.SRCALPHA)
            self.image.fill(TANK_ENEMY_COLOR)
        # rect は親が作っているが再取得して中心を維持
        self.rect = self.image.get_rect(center=self.rect.center)

        # 位置を浮動小数点で管理（Y軸が小数増分でも反映されるように）
        self.pos = pygame.math.Vector2(self.rect.centerx, self.rect.centery)

        # サイン波移動のパラメータ
        self.spawn_x = float(self.rect.centerx)
        self.osc_amplitude = 60          # 横振幅（px）
        self.osc_speed = 0.0025          # 角速度（ms 単位）
        self.phase_offset = random.random() * math.tau

        # 突進（バースト）パラメータ
        self.burst_cooldown = random.randint(120, 300)  # 次のバーストまでの待機フレーム
        self.burst_timer = 0
        self.burst_duration = 0
        self.burst_dir = 0
        self.burst_speed = 0

    def move(self):
        # pos を基準に移動（まず現在の rect から pos を同期しておく安全策）
        # self.pos = pygame.math.Vector2(self.rect.centerx, self.rect.centery)  # 不要ならコメントアウト可

        # 基本の縦移動（浮動小数点で加算）
        self.pos.y += self.speed

        # サイン波で横方向を滑らかに移動（float 演算）
        t = pygame.time.get_ticks()
        target_x = self.spawn_x + math.sin(t * self.osc_speed + self.phase_offset) * self.osc_amplitude

        # 突進中なら強制的に横移動を行う（float）
        if self.burst_duration > 0:
            self.pos.x += self.burst_dir * self.burst_speed
            self.burst_duration -= 1
        else:
            # 通常時はスムーズに補間して移動（浮動小数点で保持）
            dx = target_x - self.pos.x
            self.pos.x += dx * 0.08

            # クールダウンカウントダウン、ランダムでバースト開始
            if self.burst_cooldown > 0:
                self.burst_cooldown -= 1
            else:
                if random.random() < 0.25:
                    # バースト開始
                    self.burst_dir = random.choice([-1, 1])
                    self.burst_speed = random.uniform(3.0, 5.0)
                    self.burst_duration = random.randint(18, 36)
                # 次回クールダウンをリセット
                self.burst_cooldown = random.randint(160, 360)

        # pos を rect に反映（整数へ）
        self.rect.centerx = int(self.pos.x)
        self.rect.centery = int(self.pos.y)

        # 画面外に出ないようクリップ（微調整）
        if self.rect.left < 0:
            self.rect.left = 0
            self.pos.x = self.rect.centerx
            self.spawn_x = float(self.rect.centerx)
        if self.rect.right > screen_width:
            self.rect.right = screen_width
            self.pos.x = self.rect.centerx
            self.spawn_x = float(self.rect.centerx)

    def create_random_fire(self):
        # TankEnemy 固有の火力は既存実装のまま（省略せず保持）
        if self.player_group is None:
            return
        self.fire_timer += 1
        if self.fire_timer >= 40:
            # 中～広範囲にばら撒く（3〜5発）
            if random.random() < 0.5:
                cnt = random.randint(3,5)
                for i in range(cnt):
                    ox = -30 + i * (60/(max(1,cnt-1)))  # 横に広げる
                    x = int(self.rect.centerx + ox + random.uniform(-4,4))
                    y = self.rect.bottom + 6 + random.randint(0,6)
                    speed = random.uniform(1.2, 2.5) # 弾速を遅くする
                    bullet = self.enemy_bullet_pool.get()
                    bullet.reset(x, y, self.player_group, speed=speed)
            self.fire_timer = 0

    def update(self):
        self.move()
        self.create_random_fire()
        super().update(move_override=True)
        # 爆発などは親に従う
        self.explosion_group.draw(self.screen)
        self.explosion_group.update()

class WaveEnemy(Enemy):
    """波のように上下に揺れながら横に移動する敵"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool)
        self.speed = 2.5  # 横方向の基本速度
        self.health = 2
        self.score_value = 25 # WaveEnemyのスコア

        image_path = 'assets/img/enemy/wave.png'
        if image_path in Enemy._image_cache:
            pre = Enemy._image_cache[image_path]
        else:
            try:
                pre = pygame.image.load(image_path).convert_alpha()
                Enemy._image_cache[image_path] = pre
            except Exception:
                pre = None
        if pre:
            self.image = pygame.transform.scale(pre, (45, 45))
        else:
            self.image = pygame.Surface((45, 45), pygame.SRCALPHA)
            self.image.fill(WAVE_ENEMY_COLOR)
        self.rect = self.image.get_rect(center=self.rect.center)

        # 位置を浮動小数点で管理
        self.pos = pygame.math.Vector2(self.rect.center)
        
        # 左右どちらから出現したかに応じて移動方向を決定
        self.direction_x = 1 if x < GAME_AREA_WIDTH / 2 else -1

        # サイン波移動のパラメータ
        self.angle = 0
        self.amplitude = 3  # 上下の揺れ幅

    def move(self):
        # 横方向に移動
        self.pos.x += self.direction_x * self.speed
        # サイン波で上下に揺れる
        # self.pos.y += math.sin(self.angle) * self.amplitude # この加算は不要。中心Y座標からの揺れで計算
        self.rect.centery = self.pos.y + math.sin(self.angle) * self.amplitude
        self.angle += 0.1
        self.rect.centerx = self.pos.x

    def create_random_fire(self):
        """一定間隔で真下に弾を発射する"""
        if self.player_group is None:
            return
        
        self.fire_timer += 1
        # 60フレーム（1秒）ごとに発射
        if self.fire_timer > 60:
            self.fire_timer = 0
            # 真下に弾を発射
            bullet = self.enemy_bullet_pool.get()
            bullet.reset(self.rect.centerx, self.rect.bottom, self.player_group, speed=2.5)

    def update(self):
        self.move()
        self.create_random_fire()
        # 親クラスの移動以外の処理（当たり判定、死亡処理など）を呼び出す
        super().update(move_override=True)

class HunterEnemy(Enemy):
    """プレイヤーを追いかけ、狙い撃ちしてくる強化された敵"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool)
        self.speed = 2.0       # 追尾速度
        self.health = 4        # 少し高めのHP
        self.score_value = 40  # HunterEnemyのスコア

        image_path = 'assets/img/enemy/hunter.png'
        if image_path in Enemy._image_cache:
            pre = Enemy._image_cache[image_path]
        else:
            try:
                pre = pygame.image.load(image_path).convert_alpha()
                Enemy._image_cache[image_path] = pre
            except Exception:
                pre = None
        if pre:
            self.image = pygame.transform.scale(pre, (55, 55))
        else:
            self.image = pygame.Surface((55, 55), pygame.SRCALPHA)
            self.image.fill(HUNTER_ENEMY_COLOR)
        self.rect = self.image.get_rect(center=self.rect.center)

        self.pos = pygame.math.Vector2(self.rect.center)
        
        self.fire_cooldown = 120 # 弾の発射間隔 (フレーム)
        self.fire_timer = random.randint(0, self.fire_cooldown) # タイマーをランダムに初期化

    def move(self):
        """プレイヤーを追尾する動き"""
        if self.player_group and len(self.player_group) > 0:
            player = self.player_group.sprite
            direction = player.pos - self.pos
            if direction.length() > 0:
                direction.normalize_ip()
            self.pos += direction * self.speed
            self.rect.center = self.pos

    def create_random_fire(self):
        """一定間隔でプレイヤーを狙って弾を発射する"""
        if self.player_group and len(self.player_group) > 0:
            self.fire_timer += 1
            if self.fire_timer >= self.fire_cooldown:
                self.fire_timer = 0
                player = self.player_group.sprite
                direction = player.pos - self.pos
                if direction.length_squared() > 0:
                    direction.normalize_ip()
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(self.rect.centerx, self.rect.bottom, self.player_group, speed=3.0, direction=direction)

    def update(self):
        self.move()
        self.create_random_fire()
        super().update(move_override=True)
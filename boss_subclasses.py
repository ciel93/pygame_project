import pygame
import random
import math
from enemy import Enemy
from setting import *
from boss import BossEnemy

class GrandBossEnemy(BossEnemy):
    """ゲームの最終ボス（大ボス）"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool)
        
        # 大ボス専用のパラメータで上書き
        self.health = 600  # HPを大幅に増やす
        self.score_value = 1000 # 大ボスのスコア
        self.max_health = 600
        self.speed = 0.8   # 少しゆっくり動かす
        
        image_path = 'assets/img/enemy/grand_boss.png'
        if image_path in GrandBossEnemy._image_cache:
            pre = GrandBossEnemy._image_cache[image_path]
        else:
            try:
                pre = pygame.image.load(image_path).convert_alpha()
                GrandBossEnemy._image_cache[image_path] = pre
            except Exception:
                pre = None
        new_width = 180
        aspect_ratio = pre.get_height() / pre.get_width() if pre else 1
        new_height = int(new_width * aspect_ratio)
        self.image = pygame.transform.scale(pre, (new_width, new_height)) if pre else pygame.Surface((new_width, new_height), pygame.SRCALPHA)
        if not pre: self.image.fill(GRAND_BOSS_COLOR)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.radius = self.rect.width / 2 * 0.9 # 当たり判定を画像の半径に合わせる

        # パターン切替時間を短くして、より頻繁に攻撃させる
        self.pattern_change_time = 240 # 4秒

        # 親クラスと同様にoriginal_imageを初期化
        self.original_image = self.image.copy()
        
        # HPによる発狂モードのフラグ
        self.enrage_mode = False

    def create_pattern(self):
        # HPが半分以下になったら発狂モードに移行
        if not self.enrage_mode and self.health <= self.max_health / 2:
            self.enrage_mode = True
            self.pattern_change_time = 200 # パターン切替を少し高速化

        self.pattern_timer += 1
        if self.pattern_timer > self.pattern_change_time:
            self.pattern_timer = 0
            if self.enrage_mode:
                # 発狂モード: 激しい攻撃の頻度を上げる
                self.pattern = random.choice([4, 5, 6, 8]) # アイシクルフォール (7) を削除
            else:
                # 通常モード: 比較的避けやすい攻撃
                self.pattern = random.randint(0, 3)

        # ディスパッチテーブルを使って攻撃パターンを実行
        if self.pattern in self.attack_patterns:
            self.attack_patterns[self.pattern]()

    def update(self):
        # BossEnemyのupdateメソッドを呼び出す
        super().update()

class SecretBoss(GrandBossEnemy):
    """ノーミス時に出現する隠しボス"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool)

        # 隠しボス専用のパラメータ
        self.health = 800
        self.max_health = 800
        self.score_value = 5000 # 高スコア
        self.pattern_change_time = 220 # パターン切替をさらに高速化

        # 画像を紫色に変更
        image_path = 'assets/img/enemy/grand_boss.png'
        if image_path in GrandBossEnemy._image_cache:
            pre = GrandBossEnemy._image_cache[image_path]
        else:
            try:
                pre = pygame.image.load(image_path).convert_alpha()
                GrandBossEnemy._image_cache[image_path] = pre
            except Exception:
                pre = None
        
        new_width = 180
        aspect_ratio = pre.get_height() / pre.get_width() if pre else 1
        new_height = int(new_width * aspect_ratio)
        self.image = pygame.transform.scale(pre, (new_width, new_height)) if pre else pygame.Surface((new_width, new_height), pygame.SRCALPHA)
        
        # 紫色のオーバーレイをかける
        kanako_overlay = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        kanako_overlay.fill((100, 80, 200, 150)) # 半透明の青紫色に変更
        self.image.blit(kanako_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.original_image = self.image.copy()
        
        # 隠しボス専用の攻撃パターンのみを設定
        self.attack_patterns = {
            16: self._kanako_onbashira_rising,
            17: self._kanako_onbashira_expanded,
            18: self._kanako_mountain_of_faith,
            19: self._kanako_normal_shot, # 通常弾幕を追加
        }

        self.last_attack_pattern = 19 # 最初はスペルカードから始めるように設定

    def create_pattern(self):
        """隠しボス専用の強化された攻撃パターン"""
        # HPが半分以下になったら発狂モードに移行
        if not self.enrage_mode and self.health <= self.max_health / 2:
            self.enrage_mode = True
            self.pattern_change_time = 180 # パターン切替を極限まで高速化

        self.pattern_timer += 1
        if self.pattern_timer > self.pattern_change_time:
            self.pattern_timer = 0
            # 通常弾幕(19)とスペルカード(16,17,18)を交互に実行
            if self.last_attack_pattern == 19:
                # 前回が通常弾幕なら、次はスペルカード
                self.pattern = random.choice([16, 17, 18])
            else:
                # 前回がスペルカードなら、次は通常弾幕
                self.pattern = 19
            self.last_attack_pattern = self.pattern

        # ディスパッチテーブルを使って攻撃パターンを実行
        if self.pattern in self.attack_patterns:
            self.attack_patterns[self.pattern]()

    def _kanako_onbashira_rising(self):
        """【神奈子パターン】御柱「ライジングオンバシラ」"""
        if self.pattern_timer % 20 == 0:
            num_pillars = 2
            for _ in range(num_pillars):
                x = random.randint(50, GAME_AREA_WIDTH - 50)
                direction = pygame.math.Vector2(0, -1)
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(x, screen_height, self.player_group, speed=5.0, direction=direction, radius=25, length=180, color=(120, 80, 200), bullet_type='laser')

    def _kanako_onbashira_expanded(self):
        """【神奈子パターン】神祭「エクスパンデッド・オンバシラ」"""
        if self.pattern_timer % 90 == 0:
            num_directions = 8
            angle_offset = random.uniform(0, 360 / num_directions)
            for i in range(num_directions):
                angle = math.radians((360 / num_directions) * i + angle_offset)
                direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(self.rect.centerx, self.rect.centery, self.player_group, speed=3.0, direction=direction, radius=20, length=150, color=(150, 100, 220), bullet_type='laser')

    def _kanako_mountain_of_faith(self):
        """【神奈子パターン】「マウンテン・オブ・フェイス」"""
        if self.pattern_timer < 120:
            if self.pattern_timer % 8 == 0:
                x = random.randint(0, GAME_AREA_WIDTH)
                y = random.randint(0, 100)
                direction = (self.pos - pygame.math.Vector2(x, y)).normalize()
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(x, y, self.player_group, speed=6.0, direction=direction, radius=6, color=(255, 255, 150), lifetime=60)
        else:
            if (self.pattern_timer - 120) % 25 == 0:
                num_directions = 12
                angle_offset = (self.pattern_timer - 120) * 0.5
                for i in range(num_directions):
                    angle = math.radians((360 / num_directions) * i + angle_offset)
                    direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
                    bullet = self.enemy_bullet_pool.get()
                    bullet.reset(self.rect.centerx, self.rect.centery, self.player_group, speed=2.5, direction=direction, radius=10, color=(100, 100, 255))

    def _kanako_normal_shot(self):
        """【神奈子パターン】通常弾幕"""
        # リング状の弾を発射
        if self.pattern_timer % 25 == 0:
            num_bullets = 10
            angle_offset = self.pattern_timer * 0.7
            for i in range(num_bullets):
                angle = math.radians((360 / num_bullets) * i + angle_offset)
                direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
                bullet = self.enemy_bullet_pool.get()
                bullet.reset(self.rect.centerx, self.rect.centery, self.player_group, speed=2.8, direction=direction, radius=9, color=(120, 120, 255))

        # 自機狙い弾を追加
        if self.pattern_timer % 70 == 0 and self.player_group.sprite:
            player = self.player_group.sprite
            direction_to_player = (player.pos - self.pos).normalize()
            bullet = self.enemy_bullet_pool.get()
            bullet.reset(self.rect.centerx, self.rect.centery, self.player_group, speed=3.5, direction=direction_to_player, radius=12, color=(200, 180, 255))


class Stage1Boss(BossEnemy):
    """ステージ1専用のボス"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool)
        
        # ステージ1ボス専用のパラメータで上書き
        self.health = 250
        self.max_health = 250
        self.score_value = 150
        
        try:
            pre = pygame.image.load('assets/img/enemy/stage1_boss.png').convert_alpha()
            new_width = 100
            aspect_ratio = pre.get_height() / pre.get_width()
            new_height = int(new_width * aspect_ratio)
            self.image = pygame.transform.scale(pre, (new_width, new_height))
        except Exception:
            # 画像がない場合のフォールバック
            surf = pygame.Surface((100, 100), pygame.SRCALPHA)
            surf.fill(STAGE1_BOSS_COLOR) # 青みがかった色
            self.image = surf
        self.rect = self.image.get_rect(center=self.rect.center)
        self.radius = self.rect.width / 2 * 0.9

        # パターン切替時間を設定
        self.pattern_change_time = 240 # 4秒

    def _simple_alternating_shot(self):
        """【専用弾幕】左右から交互に弾を発射する"""
        fire_interval = 15 # 発射間隔を短くして連射感を出す
        if self.pattern_timer % fire_interval == 0:
            # 左右どちらから発射するかを決定
            if (self.pattern_timer // fire_interval) % 2 == 0:
                spawn_pos = self.rect.midleft
            else:
                spawn_pos = self.rect.midright
            
            # 少し広がるように角度をつけて発射
            direction = pygame.math.Vector2(0, 1).rotate(random.uniform(-10, 10))
            bullet = self.enemy_bullet_pool.get()
            bullet.reset(spawn_pos[0], spawn_pos[1], self.player_group, speed=3.5, direction=direction)

    def create_pattern(self):
        """ステージ1ボス用のシンプルな攻撃パターン"""
        self.pattern_timer += 1
        self._simple_alternating_shot() # 常に専用弾幕を実行
        if self.pattern_timer % 90 == 0: # たまに自機狙い弾を追加
            self._homing_shot()

class Stage2MidBoss(BossEnemy):
    """ステージ2の中ボス"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool)
        
        # ステージ2中ボス専用のパラメータ
        self.health = 450
        self.max_health = 450
        self.score_value = 250
        
        try:
            # 画像をロード（なければフォールバック）
            pre = pygame.image.load('assets/img/enemy/stage2_mid_boss.png').convert_alpha()
            new_width = 130
            aspect_ratio = pre.get_height() / pre.get_width()
            new_height = int(new_width * aspect_ratio)
            self.image = pygame.transform.scale(pre, (new_width, new_height))
        except Exception:
            # 画像がない場合のフォールバック
            surf = pygame.Surface((130, 130), pygame.SRCALPHA)
            surf.fill(STAGE2_MID_BOSS_COLOR) # 新しい色
            self.image = surf
        self.rect = self.image.get_rect(center=self.rect.center)
        self.radius = self.rect.width / 2 * 0.9

        # パターン切替時間
        self.pattern_change_time = 260

    def create_pattern(self):
        """ステージ2中ボス用の攻撃パターン"""
        self.pattern_timer += 1
        if self.pattern_timer > self.pattern_change_time:
            self.pattern_timer = 0
            # 待機を挟みつつ、いくつかのパターンをループ
            if self.pattern != 11: # 待機パターンを11に変更
                self.pattern = 11
            else:
                # 待機が終わったら、次の攻撃パターンへ (ホーミング、放射状、波状攻撃)
                self.pattern = random.choice([0, 3, 5])

        # ディスパッチテーブルを使って攻撃パターンを実行
        if self.pattern in self.attack_patterns:
            self.attack_patterns[self.pattern]()
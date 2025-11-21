import pygame
import random
import math
from enemy import Enemy
from setting import *
from boss import BossEnemy

class GrandBossEnemy(BossEnemy):
    """ゲームの最終ボス（大ボス）"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None, enemy_bullet_sound=None, explosion_sound=None, laevateinn_sound=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool, enemy_bullet_sound, explosion_sound, laevateinn_sound)
        
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

class Stage1Boss(BossEnemy):
    """ステージ1専用のボス"""
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None, enemy_bullet_sound=None, explosion_sound=None, laevateinn_sound=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool, enemy_bullet_sound, explosion_sound, laevateinn_sound)
        
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
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None, enemy_bullet_pool=None, enemy_bullet_sound=None, explosion_sound=None, laevateinn_sound=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group, enemy_bullet_pool, enemy_bullet_sound, explosion_sound, laevateinn_sound)
        
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
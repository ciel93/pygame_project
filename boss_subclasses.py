import pygame
import random
from setting import *
from boss import BossEnemy

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

    def move(self):
        # レーヴァテイン薙ぎ払い後の特殊移動
        if self.is_laevateinn_moving:
            self.pos.x += 3.0 * self.laevateinn_move_dir # 少し速めに移動
            if not (self.rect.width / 2 < self.pos.x < GAME_AREA_WIDTH - self.rect.width / 2):
                self.laevateinn_move_dir *= -1
            self.rect.center = self.pos
            return
        
        # それ以外は親クラスの移動ロジックに従う
        super().move()

    def create_pattern(self):
        # HPが半分以下になったら発狂モードに移行
        if not self.enrage_mode and self.health <= self.max_health / 2:
            self.enrage_mode = True
            self.pattern_change_time = 160 # パターン切替を少し高速化（120から変更）

        self.pattern_timer += 1
        if self.pattern_timer > self.pattern_change_time:
            self.pattern_timer = 0
            if self.enrage_mode:
                # 発狂モード: 激しい攻撃の頻度を上げる
                self.pattern = random.choice([4, 5, 6, 8])
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
    def __init__(self, groups, x, y, bullet_group, player_group=None, enemy_bullets_group=None, item_group=None):
        super().__init__(groups, x, y, bullet_group, player_group, enemy_bullets_group, item_group)
        
        # ステージ1ボス専用のパラメータで上書き
        self.health = 100
        self.max_health = 100
        self.score_value = 80
        
        try:
            pre = pygame.image.load('assets/img/enemy/stage1_boss.png').convert_alpha()
            new_width = 100
            aspect_ratio = pre.get_height() / pre.get_width()
            new_height = int(new_width * aspect_ratio)
            self.image = pygame.transform.scale(pre, (new_width, new_height))
        except Exception:
            # 画像がない場合のフォールバック
            surf = pygame.Surface((100, 100), pygame.SRCALPHA)
            surf.fill((100, 100, 255)) # 青みがかった色
            self.image = surf
        self.rect = self.image.get_rect(center=self.rect.center)
        self.radius = self.rect.width / 2 * 0.9

        # パターン切替時間を設定
        self.pattern_change_time = 180 # 3秒

    def create_pattern(self):
        """ステージ1ボス用のシンプルな攻撃パターン"""
        self.pattern_timer += 1
        if self.pattern_timer > self.pattern_change_time:
            self.pattern_timer = 0
            # 現在のパターンが待機(8)でなければ、次は待機パターンへ移行
            if self.pattern != 9:
                self.pattern = 9
            else:
                # 待機が終わったら、次の攻撃パターンへ (0, 1, 2をループ)
                self.pattern = (self.pattern + 1) % 3

        # 選択されたパターンを実行
        if self.pattern == 0:
            # 5-way弾を扇状にばらまく
            if self.pattern_timer % 40 == 0:
                self._scatter_shot()
        elif self.pattern == 1:
            # プレイヤーを狙う弾を発射
            if self.pattern_timer % 50 == 0:
                self._homing_shot()
        elif self.pattern == 2:
            # 横に波打つように弾を発射
            self._wave_spread()
import pygame
from setting import *

class MasterSpark(pygame.sprite.Sprite):
    """プレイヤーのボム（マスタースパーク）を表現するクラス"""
    def __init__(self, groups, player):
        super().__init__(groups)
        self.player = player
        self.screen = pygame.display.get_surface()

        # レーザーの基本設定
        self.duration = 180  # 3秒間持続
        self.timer = self.duration
        self.damage = 0.5  # 1フレームあたりのダメージ

        # プレイヤーが持つ敵グループへの参照を取得
        self.enemy_group = self.player.enemy_group

        # レーザーの画像読み込み
        try:
            self.laser_image_base = pygame.image.load('assets/img/bomb/master_spark.png').convert_alpha()
        except pygame.error:
            self.laser_image_base = None # 画像がない場合はNone

        # レーザー全体の描画領域と当たり判定用のRect
        # 幅は画像の最大幅に合わせる
        self.image = pygame.Surface((412, screen_height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=self.player.rect.midtop)

        # 当たり判定用のマスク
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            return

        # プレイヤーに追従
        self.rect.midbottom = self.player.rect.midtop

        # レーザーの描画
        self.draw_laser()

        # 敵との当たり判定
        self.check_collision()

    def draw_laser(self):
        # 描画前にクリア
        self.image.fill((0, 0, 0, 0))

        # レーザーの幅をタイマーに応じて変化させる（発射時と収束時）
        current_width_ratio = 1.0
        if self.timer > self.duration - 20: # 開始時
            current_width_ratio = (self.duration - self.timer) / 20.0
        elif self.timer < 20: # 終了時
            current_width_ratio = self.timer / 20.0

        # 画像がある場合
        if self.laser_image_base:
            # 元画像の高さを維持しつつ、幅をアニメーションさせる
            new_width = int(self.laser_image_base.get_width() * current_width_ratio)
            if new_width > 0:
                # スケーリングした画像を作成
                scaled_laser = pygame.transform.scale(self.laser_image_base, (new_width, self.rect.height))
                # 中央に配置
                x_pos = (self.rect.width - new_width) // 2
                self.image.blit(scaled_laser, (x_pos, 0))
        # 画像がない場合（フォールバック）
        else:
            outer_width = self.rect.width * current_width_ratio
            inner_width = outer_width * 0.5
            # 外側のレーザー
            pygame.draw.rect(self.image, BOMB_LASER_OUTER_COLOR, (self.rect.width/2 - outer_width/2, 0, outer_width, self.rect.height))
            # 内側のレーザー
            pygame.draw.rect(self.image, BOMB_LASER_INNER_COLOR, (self.rect.width/2 - inner_width/2, 0, inner_width, self.rect.height))

        # 毎フレームマスクを更新
        self.mask = pygame.mask.from_surface(self.image)

    def check_collision(self):
        # レーザーと衝突した敵に継続的にダメージを与える
        for enemy in self.enemy_group:
            # マスクを使ったピクセルパーフェクトな衝突判定
            if pygame.sprite.collide_mask(self, enemy) and hasattr(enemy, 'take_damage'):
                # 敵のtake_damageメソッドを呼び出してダメージを与える
                enemy.take_damage(self.damage)
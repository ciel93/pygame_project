import pygame
from setting import *
from player import Player
from boss import BossEnemy, GrandBossEnemy, Stage1Boss
from stage_manager import StageManager
from support import draw_text

class Game:

    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.score = 0
        # UI表示用のフォントを準備
        self.font_ui = pygame.font.Font(None, 30)

        #グループの作成
        self.create_group()

        #自機
        self.player = Player(self.player_group, 300, 500, self.enemy_group, self.enemy_bullets, self.item_group)
        
        #背景
        self.bg_images = []
        try:
            # ステージごとの背景画像をロード
            self.bg_images.append(pygame.transform.scale(pygame.image.load('assets/img/background/bg.png'),(screen_width,screen_height)))
            self.bg_images.append(pygame.transform.scale(pygame.image.load('assets/img/background/bg2.png'),(screen_width,screen_height)))
        except pygame.error:
            # 画像がない場合のフォールバック
            fallback_bg = pygame.Surface((screen_width, screen_height))
            fallback_bg.fill((20, 0, 40))
            self.bg_images.append(fallback_bg)
            self.bg_images.append(fallback_bg)

        self.bg_img = self.bg_images[0] # 初期背景
        self.bg_y = 0

        # ステージ管理
        self.stage_manager = StageManager(self.enemy_group, self.player_group, self.item_group)

        #ゲームオーバー
        self.game_over = False
        self.game_clear = False
        self.grand_boss_defeated = False # 大ボスを倒したかどうかのフラグ

    def create_group(self):
        self.player_group = pygame.sprite.GroupSingle()
        self.enemy_group = pygame.sprite.Group()
        # 共有の敵弾グループを追加（敵が消えても弾が残る）
        self.enemy_bullets = pygame.sprite.Group()
        self.item_group = pygame.sprite.Group()

    def player_death(self):
        if len(self.player_group) == 0:
            self.game_over = True
            draw_text(self.screen, 'game over', GAME_AREA_WIDTH // 2, screen_height //2 ,75 , RED)
            self.stage_manager.spawn_active = False # 敵の出現を停止
            draw_text(self.screen, 'press SPACE KEY to reset', GAME_AREA_WIDTH // 2, screen_height //2 + 100 ,50 , RED)

    def grand_boss_death(self):
        # 大ボスを倒したらクリア
        if self.grand_boss_defeated:
            self.game_clear = True

    def reset(self):
        key = pygame.key.get_pressed()
        if (self.game_over or self.game_clear) and key[pygame.K_SPACE]:
            # プレイヤーを再生成（敵弾グループも渡す）
            self.player = Player(self.player_group, 300, 500, self.enemy_group, self.enemy_bullets, self.item_group)
            
            # 既存の敵と弾をすべて削除
            self.enemy_group.empty()
            self.enemy_bullets.empty()
            self.item_group.empty()
            self.score = 0 # スコアをリセット
            self.game_clear = False
            self.game_over = False

            # ステージマネージャーをリセットしてステージ1から再開
            self.stage_manager.reset()
            self.grand_boss_defeated = False # フラグをリセット
    
    def scroll_bg(self):
        self.bg_y = (self.bg_y + 1)% screen_height
        # 背景画像をゲームエリアの幅に合わせて描画
        self.screen.blit(self.bg_img,(0, self.bg_y - screen_height))
        self.screen.blit(self.bg_img,(0, self.bg_y))

    def draw_ui(self):
        """ゲームエリア右側のスコア表示画面を描画する"""
        # スコアパネルの背景
        pygame.draw.rect(self.screen, BLACK, (GAME_AREA_WIDTH, 0, SCORE_PANEL_WIDTH, screen_height))
        # ゲームエリアとの境界線
        pygame.draw.line(self.screen, WHITE, (GAME_AREA_WIDTH, 0), (GAME_AREA_WIDTH, screen_height), 1)

        # ステージ表示
        stage_text = f"STAGE: {self.stage_manager.stage}"
        stage_surface = self.font_ui.render(stage_text, True, WHITE)
        self.screen.blit(stage_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - stage_surface.get_width()) // 2, 20))

        # スコア表示
        score_title_surface = self.font_ui.render("SCORE", True, SCORE_TEXT_COLOR)
        self.screen.blit(score_title_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - score_title_surface.get_width()) // 2, 50))
        score_value_surface = self.font_ui.render(f"{self.score:07d}", True, SCORE_TEXT_COLOR) # 7桁表示
        self.screen.blit(score_value_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - score_value_surface.get_width()) // 2, 90))

        # ライフ表示 (既存のものを移動)
        if len(self.player_group) > 0:
            lives_text = f"LIVES: {self.player.health}"
            lives_surface = self.font_ui.render(lives_text, True, WHITE)
            self.screen.blit(lives_surface, (GAME_AREA_WIDTH + 20, screen_height - 40))

        # パワーレベル表示
        if len(self.player_group) > 0:
            power_title_surface = self.font_ui.render("POWER", True, WHITE)
            self.screen.blit(power_title_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - power_title_surface.get_width()) // 2, 130))
            power_level_text = f"{self.player.power_level} / {self.player.max_power}"
            power_level_surface = self.font_ui.render(power_level_text, True, WHITE)
            self.screen.blit(power_level_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - power_level_surface.get_width()) // 2, 160))

    def check_score_award(self):
        """敵が倒されたかチェックし、スコアを加算する"""
        for enemy in self.enemy_group:
            if getattr(enemy, 'should_award_score', False):
                self.score += getattr(enemy, 'score_value', 0)
                enemy.should_award_score = False # スコアの二重加算を防ぐ

    def draw_boss_hp_bar(self, boss):
        """ボスのHPバーを画面上部に描画する"""
        # HPバーの位置とサイズ
        bar_width = GAME_AREA_WIDTH - 200   # 画面幅より少し短く
        bar_height = 25                     # 少し高さを出す
        bar_x = (GAME_AREA_WIDTH - bar_width) // 2
        bar_y = 40 # 表示位置を下に下げる

        # HPの割合を計算
        hp_ratio = max(0, boss.health / boss.max_health)

        # 背景バー (非常に暗い灰色)
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (20, 20, 20), bg_rect)

        # 前景HPバー
        fg_width = bar_width * hp_ratio
        fg_rect = pygame.Rect(bar_x, bar_y, fg_width, bar_height)
        
        # HP残量に応じて色を変える (より鮮やかな色)
        if hp_ratio < 0.2:
            color = (255, 50, 50)  # 非常に低いHPで鮮やかな赤
        elif hp_ratio < 0.5:
            color = (255, 200, 0)  # 中程度のHPで鮮やかなオレンジ
        else:
            color = (50, 255, 50)  # 高いHPで鮮やかな緑
        pygame.draw.rect(self.screen, color, fg_rect)

        # 枠線 (太くする)
        pygame.draw.rect(self.screen, WHITE, bg_rect, 3)

        # 「BOSS HP」テキストを追加
        draw_text(self.screen, "BOSS HP", GAME_AREA_WIDTH // 2, bar_y - 15, 30, WHITE)

    def check_boss_defeat_and_convert_bullets(self):
        """ボスが倒されたかチェックし、残った敵弾をスコアに変換する"""
        for enemy in self.enemy_group:
            # BossEnemy またはそのサブクラス（GrandBossEnemy）が対象
            if isinstance(enemy, BossEnemy) and getattr(enemy, 'just_defeated', False):
                score_per_bullet = 100  # 弾1つあたりのスコア
                # 大ボスが倒されたことを記録
                if isinstance(enemy, GrandBossEnemy):
                    self.grand_boss_defeated = True
                bullet_count = len(self.enemy_bullets)
                self.score += bullet_count * score_per_bullet
                self.enemy_bullets.empty()  # 全ての敵弾を消去

                enemy.just_defeated = False # フラグをリセットして二重処理を防ぐ

    def run(self):
        self.scroll_bg()
        
        # ステージ管理と敵生成
        result = self.stage_manager.update(self.game_over, self.grand_boss_defeated)
        if result == "game_clear":
            self.game_clear = True
        elif isinstance(result, int): # ステージ移行
            self.bg_img = self.bg_images[result - 1]
        
        #グループの描画と更新
        self.player_group.draw(self.screen)
        self.player_group.update()

        # プレイヤーの弾を描画・更新
        if self.player:
            self.player.bullet_group.draw(self.screen)
            self.player.bullet_group.update()

        self.enemy_group.draw(self.screen)
        self.enemy_group.update()

        # ボスがいればHPバーを描画
        for enemy in self.enemy_group:
            if isinstance(enemy, BossEnemy):
                self.draw_boss_hp_bar(enemy)
                break # ボスは1体しかいないはずなのでループを抜ける

        # スコア加算のチェック
        self.check_score_award()

        # ボス撃破時の弾消し＆スコア加算
        self.check_boss_defeat_and_convert_bullets()

        # 共有の敵弾を更新・描画（Enemy を destroy しても弾は残る）
        self.enemy_bullets.update()
        self.enemy_bullets.draw(self.screen)

        # アイテムの更新と描画（プレイヤーが生きている場合、位置を渡す）
        if len(self.player_group) > 0:
            self.item_group.update(self.player.pos)
        else:
            self.item_group.update()
        self.item_group.draw(self.screen)
        
        # UI（スコア、ライフなど）を描画
        self.draw_ui()

        # ステージクリア時のメッセージ表示
        if self.stage_manager.stage_clear_timer > 0 and not self.game_clear:
            draw_text(self.screen, f'STAGE {self.stage_manager.stage} CLEAR', GAME_AREA_WIDTH // 2, screen_height // 2, 75, GREEN)

        # ゲームクリアの判定と描画
        self.grand_boss_death()
        if self.game_clear:
            draw_text(self.screen, 'GAME CLEAR', GAME_AREA_WIDTH // 2, screen_height //2 ,75 , GREEN)
            draw_text(self.screen, 'press SPACE KEY to reset', GAME_AREA_WIDTH // 2, screen_height //2 + 100 ,50 , RED)

        # ゲームオーバーの判定と描画、およびリセット処理
        self.player_death()
        self.reset()
import pygame
from setting import *
from player import Player
from enemy import Enemy
from enemy_subclasses import FastEnemy, TankEnemy, WaveEnemy
from boss import BossEnemy, GrandBossEnemy
import random, pygame, math
from item import Item
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
        self.pre_bg_img = pygame.image.load('assets/img/background/bg.png')
        self.bg_img = pygame.transform.scale(self.pre_bg_img,(screen_width,screen_height))
        self.bg_y = 0

        #敵
        self.timer = 0
        # 敵生成の開始時刻（ミリ秒）と生成を許可するフラグ
        self.spawn_start_time = pygame.time.get_ticks()
        self.spawn_active = True

         # ウェーブスケジュール（時間経過で順次切り替える）
        # start: ウェーブ開始時刻（ミリ秒経過）、
        # type: 敵種別、count: 生成数、interval: 同ウェーブ内の生成間隔（ms）
        self.spawn_schedule = [
            {'start': 0,      'type': 'normal', 'count': 8,  'interval': 800},
            {'start': 5000,   'type': 'fast',   'count': 5, 'interval': 600},
            {'start': 10000,  'type': 'wave',   'count': 7,  'interval': 900}, # WaveEnemyのウェーブを追加
            {'start': 16000,  'type': 'tank',   'count': 6,  'interval': 1000},
            {'start': 23000,  'type': 'normal', 'count': 12, 'interval': 500}, # 追加した通常敵ウェーブ1
            {'start': 30000,  'type': 'normal', 'count': 15, 'interval': 400}, # 追加した通常敵ウェーブ2
            {'start': 38000,  'type': 'boss',   'count': 1,  'interval': 0},
            {'start': 48000,  'type': 'normal', 'count': 20, 'interval': 300}, # 中ボスと大ボスの間のウェーブ
            {'start': 55000,  'type': 'fast',   'count': 8, 'interval': 400}, # FastEnemyのウェーブを追加
            {'start': 65000,  'type': 'grand_boss', 'count': 1, 'interval': 0}, # 大ボスのウェーブを追加
        ]
        self.current_wave = 0
        self.wave_spawned = 0
        self.next_spawn_time = self.spawn_start_time + self.spawn_schedule[0]['interval']

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

    def create_enemy(self):
        # spawn が無効なら何もしない
        if not self.spawn_active:
            return

        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_start_time

        # ボスが存在するかチェック
        is_boss_alive = any(isinstance(enemy, BossEnemy) for enemy in self.enemy_group)

        # ウェーブを進める（経過時間が次ウェーブ開始を超えていれば進行）
        # ただし、ボスが生きている間は次のウェーブに進まない
        if not is_boss_alive:
            while (self.current_wave + 1) < len(self.spawn_schedule) and \
                  elapsed >= self.spawn_schedule[self.current_wave + 1]['start']:
                self.current_wave += 1
                self.wave_spawned = 0
                # 次ウェーブの最初のスポーン時間を now + interval（interval が 0 のときは即時）
                interval = self.spawn_schedule[self.current_wave]['interval']
                self.next_spawn_time = now + (interval if interval > 0 else 0)
        elif is_boss_alive:
            # ボスがいる場合、次のウェーブの開始時間を現在の時間で更新し続ける（遅延させる）
            if (self.current_wave + 1) < len(self.spawn_schedule):
                self.spawn_schedule[self.current_wave + 1]['start'] = elapsed + 100 # 100ms後に再チェック

        # 現在ウェーブの情報
        wave = self.spawn_schedule[self.current_wave]
        # 指定数を生成し終えたら、最終ウェーブ以外は待機（次ウェーブ時間で進む）
        if self.wave_spawned >= wave['count']:
            # 最後のウェーブに達していて全員生成済みなら spawn を停止
            if self.current_wave == len(self.spawn_schedule) - 1:
                self.spawn_active = False
            return
        
        # スポーンタイミングの判定
        if now >= self.next_spawn_time:
            # ゲームオーバー時や自機が存在しないときは生成しないがタイマーは進める
            if self.game_over or len(self.player_group) == 0:
                # 次の spawn を遅らせる
                self.next_spawn_time = now + wave['interval']
                return

            # 同時出現上限（任意）を超えないようにする
            max_simultaneous = 20
            if len(self.enemy_group) < max_simultaneous:
                spawn_type = wave['type']
                
                # WaveEnemyは画面の左右から出現させる
                if spawn_type == 'wave':
                    x = random.choice([-30, GAME_AREA_WIDTH + 30])
                    y = random.randint(80, 150)
                else:
                    x = random.randint(50, GAME_AREA_WIDTH - 50)
                    y = 10 # ゲームエリア上端より少し下にスポーン

                if spawn_type == 'normal':
                    Enemy(self.enemy_group, x, y, self.player.bullet_group, self.player_group, self.enemy_bullets, self.item_group)
                elif spawn_type == 'fast':
                    FastEnemy(self.enemy_group, x, y, self.player.bullet_group, self.player_group, self.enemy_bullets, self.item_group)
                elif spawn_type == 'tank':
                    TankEnemy(self.enemy_group, x, y, self.player.bullet_group, self.player_group, self.enemy_bullets, self.item_group)
                elif spawn_type == 'wave':
                    WaveEnemy(self.enemy_group, x, y, self.player.bullet_group, self.player_group, self.enemy_bullets, self.item_group)
                elif spawn_type == 'boss':
                    BossEnemy(self.enemy_group, GAME_AREA_WIDTH // 2, -80, self.player.bullet_group, self.player_group, self.enemy_bullets, self.item_group)
                elif spawn_type == 'grand_boss':
                    GrandBossEnemy(self.enemy_group, GAME_AREA_WIDTH // 2, -120, self.player.bullet_group, self.player_group, self.enemy_bullets, self.item_group)
                else:
                    # fallback
                    Enemy(self.enemy_group, x, y, self.player.bullet_group, self.player_group, self.enemy_bullets, self.item_group)

                self.wave_spawned += 1

                 # 次のスポーン時間を設定（interval が 0 の場合は即時に複数生成される）
            if wave['interval'] > 0:
                self.next_spawn_time = now + wave['interval']
            else:
                # 即時生成の場合、次は現在時刻（ループで続けて生成される）
                self.next_spawn_time = now

    def player_death(self):
        if len(self.player_group) == 0:
            self.game_over = True
            draw_text(self.screen, 'game over', GAME_AREA_WIDTH // 2, screen_height //2 ,75 , RED)
            self.spawn_active = False # 敵の出現を停止
            draw_text(self.screen, 'press SPACE KEY to reset', GAME_AREA_WIDTH // 2, screen_height //2 + 100 ,50 , RED)

    def grand_boss_death(self):
        # 大ボスを倒し、かつ全ての敵がいなくなったらクリア
        if self.grand_boss_defeated and not self.spawn_active and len(self.enemy_group) == 0:
            self.game_clear = True
            draw_text(self.screen, 'press SPACE KEY to reset', GAME_AREA_WIDTH // 2, screen_height //2 + 100 ,50 , RED)

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

            # 敵の出現タイミングをリセット
            self.spawn_start_time = pygame.time.get_ticks()
            self.spawn_active = True
            self.current_wave = 0
            self.wave_spawned = 0
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

        # スコア表示
        score_title_surface = self.font_ui.render("SCORE", True, SCORE_TEXT_COLOR)
        self.screen.blit(score_title_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - score_title_surface.get_width()) // 2, 50))
        score_value_surface = self.font_ui.render(f"{self.score:07d}", True, SCORE_TEXT_COLOR) # 7桁表示
        self.screen.blit(score_value_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - score_value_surface.get_width()) // 2, 90))

        # ライフ表示 (既存のものを移動)
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

        self.create_enemy()

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

        # ゲームクリアの判定と描画
        self.grand_boss_death()
        if self.game_clear:
            draw_text(self.screen, 'GAME CLEAR', GAME_AREA_WIDTH // 2, screen_height //2 ,75 , GREEN)
            draw_text(self.screen, 'press SPACE KEY to reset', GAME_AREA_WIDTH // 2, screen_height //2 + 100 ,50 , RED)

        # ゲームオーバーの判定と描画、およびリセット処理
        self.player_death()
        self.reset()
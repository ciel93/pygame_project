import pygame
from setting import *
from player import Player
from bullet import Bullet, HomingBullet
from enemy import Enemy
from boss import BossEnemy
from boss_subclasses import GrandBossEnemy, Stage1Boss
from enemy_bullet import EnemyBullet
from stage_manager import StageManager
from support import draw_text
from quadtree import Quadtree
from pooling import BulletPool

class Game:

    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.score = 0
        # UI表示用のフォントを準備
        self.font_ui = pygame.font.Font(None, 30)

        #グループの作成
        self.create_group()

        # 衝突判定用のQuadtreeを種類別に作成
        boundary = pygame.Rect(0, 0, GAME_AREA_WIDTH, screen_height)
        self.enemy_quadtree = Quadtree(0, boundary)
        self.enemy_bullet_quadtree = Quadtree(0, boundary)
        self.player_bullet_quadtree = Quadtree(0, boundary)

        # 弾のオブジェクトプールを作成
        self.bullet_pool = BulletPool(
            bullet_factory=lambda: Bullet(pygame.sprite.Group(), 0, 0),
            initial_size=100,
            add_to_group_func=lambda bullet: self.player.bullet_group.add(bullet)
        )
        self.homing_bullet_pool = BulletPool(
            bullet_factory=lambda: HomingBullet(pygame.sprite.Group(), 0, 0, self.enemy_group),
            initial_size=80,
            add_to_group_func=lambda bullet: self.player.bullet_group.add(bullet)
        )
        self.enemy_bullet_pool = BulletPool(
            bullet_factory=lambda: EnemyBullet(pygame.sprite.Group(), 0, 0, self.player_group), # 敵弾はプレイヤーをターゲットにする
            initial_size=800, # 敵弾は数が多いので多めに
            add_to_group_func=lambda bullet: self.enemy_bullets.add(bullet)
        )

        #自機
        self.player = Player(self.player_group, GAME_AREA_WIDTH // 2, 500, self, self.enemy_group, self.enemy_bullets, self.item_group, self.bullet_pool, self.homing_bullet_pool)
        
        #背景
        self.bg_images = []
        try:
            self.bg_images.append(pygame.transform.scale(pygame.image.load('assets/img/background/bg.png'),(GAME_AREA_WIDTH,screen_height)))
            self.bg_images.append(pygame.transform.scale(pygame.image.load('assets/img/background/bg2.jpg'),(GAME_AREA_WIDTH,screen_height)))

        except pygame.error:
            # 画像がない場合のフォールバック
            fallback_bg = pygame.Surface((screen_width, screen_height))
            fallback_bg.fill((20, 0, 40))
            self.bg_images.append(fallback_bg)
            self.bg_images.append(fallback_bg)

        self.bg_img = self.bg_images[0] # 初期背景
        self.bg_y = 0

        # ステージ管理
        self.stage_manager = StageManager(self.enemy_group, self.player_group, self.item_group, self.enemy_bullet_pool)

        #ゲームオーバー
        self.game_over = False
        self.game_clear = False
        self.grand_boss_defeated = False # 大ボスを倒したかどうかのフラグ
        self.paused = False # ポーズ状態のフラグ
        self.show_quadtree = False # Quadtreeの表示フラグ
        self.show_enemy_hitbox = False # 敵弾の当たり判定表示フラグ
        self.show_pool_debug = False # オブジェクトプールのデバッグ表示フラグ

    def create_group(self):
        self.player_group = pygame.sprite.GroupSingle()
        self.enemy_group = pygame.sprite.Group()
        # 共有の敵弾グループを追加（敵が消えても弾が残る）
        self.enemy_bullets = pygame.sprite.Group()
        self.item_group = pygame.sprite.Group()

    def player_death(self):
        if len(self.player_group) == 0 and not self.game_over: # game_overフラグが既にTrueでない場合のみ実行
            self.game_over = True
            draw_text(self.screen, 'game over', GAME_AREA_WIDTH // 2, screen_height //2 ,75 , RED)
            self.player = None # プレイヤーオブジェクトへの参照を削除
            self.stage_manager.spawn_active = False # 敵の出現を停止
            draw_text(self.screen, 'press SPACE KEY to reset', GAME_AREA_WIDTH // 2, screen_height //2 + 100 ,50 , RED)
    def grand_boss_death(self):
        # 大ボスを倒したらクリア
        if self.grand_boss_defeated:
            self.game_clear = True

    def reset_game(self):
        """ゲームの状態を完全に初期化する"""
        # プレイヤーを再生成
        self.player = Player(self.player_group, GAME_AREA_WIDTH // 2, 500, self, self.enemy_group, self.enemy_bullets, self.item_group, self.bullet_pool, self.homing_bullet_pool)
        
        # プールとグループをクリア
        self.bullet_pool.pool.clear()
        self.homing_bullet_pool.pool.clear()
        self.enemy_bullet_pool.pool.clear()
        self.enemy_group.empty()
        self.enemy_bullets.empty()
        self.item_group.empty()
        
        # 各種フラグとスコアをリセット
        self.score = 0
        self.game_clear = False
        self.game_over = False
        self.paused = False # ポーズ状態も解除
        self.grand_boss_defeated = False
        
        # ステージマネージャーをリセットしてステージ1から再開
        self.stage_manager.reset()
        # 背景画像をステージ1のものに戻す
        self.bg_img = self.bg_images[0]

    def scroll_bg(self):
        # 全ステージで共通のシンプルなスクロール処理を使用
        bg_height = self.bg_img.get_height()
        self.bg_y = (self.bg_y + 1) % bg_height
        self.screen.blit(self.bg_img, (0, self.bg_y - bg_height))
        self.screen.blit(self.bg_img, (0, self.bg_y))

    def draw_ui(self, clock):
        """ゲームエリア右側のスコア表示画面を描画する"""
        # スコアパネルの背景
        pygame.draw.rect(self.screen, BLACK, (GAME_AREA_WIDTH, 0, SCORE_PANEL_WIDTH, screen_height))
        # ゲームエリアとの境界線
        pygame.draw.line(self.screen, WHITE, (GAME_AREA_WIDTH, 0), (GAME_AREA_WIDTH, screen_height), 2)

        # ステージ表示
        stage_text = f"STAGE: {self.stage_manager.stage}"
        stage_surface = self.font_ui.render(stage_text, True, WHITE)
        self.screen.blit(stage_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - stage_surface.get_width()) // 2, 50))

        # スコア表示
        score_title_surface = self.font_ui.render("SCORE", True, WHITE)
        self.screen.blit(score_title_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - score_title_surface.get_width()) // 2, 90))
        score_value_surface = self.font_ui.render(f"{self.score:07d}", True, SCORE_TEXT_COLOR) # 7桁表示
        self.screen.blit(score_value_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - score_value_surface.get_width()) // 2, 125))

        # ライフ表示 (既存のものを移動)
        if len(self.player_group) > 0:
            lives_text = f"LIVES: {self.player.health}"
            lives_surface = self.font_ui.render(lives_text, True, WHITE)
            self.screen.blit(lives_surface, (GAME_AREA_WIDTH + 20, screen_height - 50))

        # ボム表示
        if len(self.player_group) > 0:
            bomb_text = f"BOMB: {self.player.bombs}"
            bomb_surface = self.font_ui.render(bomb_text, True, WHITE)
            self.screen.blit(bomb_surface, (GAME_AREA_WIDTH + 20, screen_height - 80))

        # パワーレベル表示
        if len(self.player_group) > 0:
            power_title_surface = self.font_ui.render("POWER", True, SCORE_TEXT_COLOR)
            self.screen.blit(power_title_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - power_title_surface.get_width()) // 2, 165))
            power_level_text = f"{self.player.power_level} / {self.player.max_power}"
            power_level_surface = self.font_ui.render(power_level_text, True, WHITE)
            self.screen.blit(power_level_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - power_level_surface.get_width()) // 2, 200))

        # FPS表示
        fps = clock.get_fps()
        fps_text = f"FPS: {fps:.2f}"
        fps_surface = self.font_ui.render(fps_text, True, WHITE)
        # UIパネルの上部に中央揃えで表示
        self.screen.blit(fps_surface, (GAME_AREA_WIDTH + (SCORE_PANEL_WIDTH - fps_surface.get_width()) // 2, 20))

        # オブジェクトプールのデバッグ情報を表示 (フラグがTrueの場合のみ)
        if self.show_pool_debug:
            pool_debug_y = 240  # デバッグ情報の表示開始Y座標
            pool_info = [
                ("Normal Bullets", len(self.bullet_pool.pool), 100),
                ("Homing Bullets", len(self.homing_bullet_pool.pool), 80),
                ("Enemy Bullets", len(self.enemy_bullet_pool.pool), 800),
            ]

            for name, size, initial_size in pool_info:
                pool_text = f"{name}: {size}/{initial_size}"
                pool_surface = self.font_ui.render(pool_text, True, WHITE)
                self.screen.blit(pool_surface, (GAME_AREA_WIDTH + 20, pool_debug_y))
                pool_debug_y += 30  # 次の行へ



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
        pygame.draw.rect(self.screen, BOSS_HP_BAR_BG_COLOR, bg_rect)

        # 前景HPバー
        fg_width = bar_width * hp_ratio
        fg_rect = pygame.Rect(bar_x, bar_y, fg_width, bar_height)
        
        # HP残量に応じて色を変える (より鮮やかな色)
        if hp_ratio < 0.2:
            color = BOSS_HP_LOW_COLOR
        elif hp_ratio < 0.5:
            color = BOSS_HP_MID_COLOR
        else:
            color = BOSS_HP_HIGH_COLOR
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
                # 大ボスが倒されたことを記録
                if isinstance(enemy, GrandBossEnemy):
                    self.grand_boss_defeated = True
                score_per_bullet = 100  # 弾1つあたりのスコア
                bullet_count = len(self.enemy_bullets)

                self.score += bullet_count * score_per_bullet
                self.enemy_bullets.empty()  # 全ての敵弾を消去

                enemy.just_defeated = False # フラグをリセットして二重処理を防ぐ

    def scroll_bg(self):
        # 全ステージで共通のシンプルなスクロール処理を使用
        bg_height = self.bg_img.get_height()
        self.bg_y = (self.bg_y + 1) % bg_height
        self.screen.blit(self.bg_img, (0, self.bg_y - bg_height))
        self.screen.blit(self.bg_img, (0, self.bg_y))

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
        pygame.draw.rect(self.screen, BOSS_HP_BAR_BG_COLOR, bg_rect)

        # 前景HPバー
        fg_width = bar_width * hp_ratio
        fg_rect = pygame.Rect(bar_x, bar_y, fg_width, bar_height)
        
        # HP残量に応じて色を変える (より鮮やかな色)
        if hp_ratio < 0.2:
            color = BOSS_HP_LOW_COLOR
        elif hp_ratio < 0.5:
            color = BOSS_HP_MID_COLOR
        else:
            color = BOSS_HP_HIGH_COLOR
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
                # 大ボスが倒されたことを記録
                if isinstance(enemy, GrandBossEnemy):
                    self.grand_boss_defeated = True
                score_per_bullet = 100  # 弾1つあたりのスコア
                bullet_count = len(self.enemy_bullets)

                self.score += bullet_count * score_per_bullet
                self.enemy_bullets.empty()  # 全ての敵弾を消去

                enemy.just_defeated = False # フラグをリセットして二重処理を防ぐ

    def run(self, clock):
        self.scroll_bg()
        
        if self.game_over:
            # ゲームオーバー画面の描画
            draw_text(self.screen, 'GAME OVER', GAME_AREA_WIDTH // 2, screen_height // 2, 75, RED)
            draw_text(self.screen, 'press SPACE KEY to reset', GAME_AREA_WIDTH // 2, screen_height // 2 + 100, 50, RED)
        elif self.paused:
            # ポーズ中は描画のみ行い、更新処理をスキップ
            draw_text(self.screen, 'PAUSED', GAME_AREA_WIDTH // 2, screen_height // 2, 75, WHITE)
            draw_text(self.screen, 'Press R to Reset', GAME_AREA_WIDTH // 2, screen_height // 2 + 60, 40, WHITE)
        else:
            # --- 通常のゲームループ ---
            # ステージ管理と敵生成
            result = self.stage_manager.update(self.game_over, self.grand_boss_defeated)
            if result == "game_clear":
                self.game_clear = True # ゲームクリア
            elif isinstance(result, int): # ステージ移行
                 self.bg_img = self.bg_images[result - 1]
            
            # グループの更新
            self.player_group.update()
            if self.player:
                self.player.bomb_group.update()
                self.player.bullet_group.update()
            self.enemy_group.update() # 敵のupdate
            self.enemy_bullets.update()

            # アイテムの更新（プレイヤーが生きている場合、位置を渡す）
            if len(self.player_group) > 0:
                self.item_group.update(self.player.pos)
                self.check_item_collision()
            else:
                self.item_group.update()

            # スコア加算のチェック
            self.check_score_award()

            # ボス撃破時の弾消し＆スコア加算
            self.check_boss_defeat_and_convert_bullets()

            # --- Quadtreeを使った衝突判定 ---
            # 1. 各Quadtreeをクリア
            self.enemy_quadtree.clear()
            self.enemy_bullet_quadtree.clear()
            self.player_bullet_quadtree.clear()
            
            # 2. 衝突判定の対象となるオブジェクトをすべて挿入
            for enemy in self.enemy_group: self.enemy_quadtree.insert(enemy)
            for bullet in self.enemy_bullets: self.enemy_bullet_quadtree.insert(bullet)
            if self.player:
                for bullet in self.player.bullet_group: self.player_bullet_quadtree.insert(bullet)

            # 3. 衝突判定の実行
            self.check_collisions_with_quadtree()

            # 4. 画面外のプレイヤー弾をプールに戻す
            self.check_player_bullets_off_screen()

            # 5. 画面外の敵弾をプールに戻す
            self.check_enemy_bullets_off_screen()

            # ボム発動の瞬間に画面上の敵弾を一掃し、スコアを加算
            if self.player and self.player.bomb_active and getattr(self.player, 'bomb_just_activated', False):
                bullets_cleared = len(self.enemy_bullets)
                score_per_bullet = 50  # 弾1つあたりのスコア
                self.score += bullets_cleared * score_per_bullet
                # 画面上のすべての敵弾をプールに戻す
                for bullet in list(self.enemy_bullets):
                    self.enemy_bullet_pool.put(bullet)
                self.player.bomb_just_activated = False # フラグをリセット

        # Quadtreeの描画（デバッグ用）
        if self.show_quadtree:
            self.enemy_quadtree.draw(self.screen)
            self.enemy_bullet_quadtree.draw(self.screen)

        # --- 以下はポーズ中も実行される描画処理 ---

        # グループの描画
        self.player_group.draw(self.screen)
        if self.player:
            self.player.bomb_group.draw(self.screen)
            self.player.bullet_group.draw(self.screen)
        self.enemy_group.draw(self.screen)
        self.enemy_bullets.draw(self.screen)
        self.item_group.draw(self.screen)
        
        # プレイヤーの当たり判定を描画 (デバッグ用)
        if self.player and self.player.show_hitbox:
            # 緑の円でヒットボックス、赤い点で中心を表示
            pygame.draw.circle(self.screen, GREEN, (int(self.player.pos.x), int(self.player.pos.y)), self.player.radius, 1)
            pygame.draw.circle(self.screen, RED, (int(self.player.pos.x), int(self.player.pos.y)), 2)

        # 敵弾の当たり判定を描画 (デバッグ用)
        if self.show_enemy_hitbox:
            for bullet in self.enemy_bullets:
                pygame.draw.circle(self.screen, RED, (int(bullet.pos.x), int(bullet.pos.y)), bullet.radius, 1)


        # ボスがいればHPバーを描画
        for enemy in self.enemy_group:
            if isinstance(enemy, BossEnemy):
                self.draw_boss_hp_bar(enemy)
                break # ボスは1体しかいないはずなのでループを抜ける

        # UI（スコア、ライフなど）を描画
        self.draw_ui(clock)

        # ステージクリア時のメッセージ表示
        if self.stage_manager.stage_clear_timer > 0 and not self.game_clear:
            draw_text(self.screen, f'STAGE {self.stage_manager.stage} CLEAR', GAME_AREA_WIDTH // 2, screen_height // 2, 75, GREEN)
        
        # ゲームクリアの判定と描画
        self.grand_boss_death()
        if self.game_clear:
            draw_text(self.screen, 'GAME CLEAR', GAME_AREA_WIDTH // 2, screen_height //2 ,75 , GREEN)
            draw_text(self.screen, 'press SPACE KEY to reset', GAME_AREA_WIDTH // 2, screen_height //2 + 100 ,50 , RED)

        # プレイヤーの死亡判定とリセット処理
        self.player_death()

    def check_collisions_with_quadtree(self):
        """Quadtreeを使用して衝突判定を行う"""
        if not self.player or self.player.invincible or self.player.bomb_active:
            return

        # プレイヤー vs 敵弾/敵本体
        possible_enemies = set()
        self.enemy_quadtree.query(self.player.rect, possible_enemies)
        for enemy in possible_enemies:
            if not isinstance(enemy, BossEnemy) and self.player.pos.distance_to(enemy.pos) < self.player.radius + enemy.radius:
                self.player.take_damage()
                enemy.kill()
                return

        possible_enemy_bullets = set()
        self.enemy_bullet_quadtree.query(self.player.rect, possible_enemy_bullets)
        for bullet in possible_enemy_bullets:
            # レーザー弾はマスクで、それ以外は円で判定
            if getattr(bullet, 'bullet_type', 'normal') == 'laser':
                if pygame.sprite.collide_mask(self.player, bullet):
                    self.player.take_damage()
                    self.enemy_bullet_pool.put(bullet)
                    return
            elif self.player.pos.distance_to(bullet.pos) < self.player.radius + bullet.radius:
                self.player.take_damage()
                self.enemy_bullet_pool.put(bullet)
                return

        # プレイヤーの弾 vs 敵
        for bullet in self.player.bullet_group if self.player else []:
            possible_enemies = set()
            query_rect = bullet.rect.inflate(20, 20)
            self.enemy_quadtree.query(query_rect, possible_enemies)
            for enemy in possible_enemies:
                if bullet.pos.distance_to(enemy.pos) < bullet.radius + enemy.radius:
                    enemy.take_damage(1)
                    self.score += 10 # 弾が命中するたびに10点加算
                    # bullet.kill() の代わりにプールに戻す
                    if isinstance(bullet, HomingBullet):
                        self.homing_bullet_pool.put(bullet)
                    else:
                        self.bullet_pool.put(bullet)
                    break

    def check_item_collision(self):
        """プレイヤーとアイテムの衝突をチェックし、効果を適用する"""
        if self.player:
            # spritecollideは衝突したスプライトのリストを返す。第三引数Trueでアイテムは自動で消える。
            collided_items = pygame.sprite.spritecollide(self.player, self.item_group, True)
            for item in collided_items:
                # アイテムにクールダウンが設定されていれば、取得せずに再度グループに戻す
                if getattr(item, 'collision_cooldown', 0) > 0:
                    self.item_group.add(item) # グループに戻す
                    continue # 次のアイテムへ
                if item.item_type == 'power':
                    if self.player.power_level < self.player.max_power:
                        self.player.power_level += 1
                elif item.item_type == 'bomb':
                    if self.player.bombs < self.player.max_bombs:
                        self.player.bombs += 1
                elif item.item_type == 'score':
                    self.score += item.value

    def check_player_bullets_off_screen(self):
        """画面外に出たプレイヤーの弾をプールに戻す"""
        if not self.player:
            return
        # forループ内でリストを変更すると問題が起きるため、リストのコピーをイテレートする
        for bullet in list(self.player.bullet_group):
            is_off_screen = bullet.rect.bottom < 0 or bullet.rect.top > screen_height or \
                            bullet.rect.right < 0 or bullet.rect.left > GAME_AREA_WIDTH
            if is_off_screen or bullet.lifetime <= 0:
                if isinstance(bullet, HomingBullet):
                    self.homing_bullet_pool.put(bullet)
                else:
                    self.bullet_pool.put(bullet)

    def check_enemy_bullets_off_screen(self):
        """画面外に出た敵弾をプールに戻す"""
        # forループ内でリストを変更すると問題が起きるため、リストのコピーをイテレートする
        for bullet in list(self.enemy_bullets):
            is_off_screen = bullet.rect.top > screen_height or bullet.rect.bottom < 0 or \
                            bullet.rect.right < 0 or bullet.rect.left > GAME_AREA_WIDTH
            if is_off_screen or (hasattr(bullet, 'lifetime') and bullet.lifetime is not None and bullet.lifetime <= 0):
                self.enemy_bullet_pool.put(bullet)
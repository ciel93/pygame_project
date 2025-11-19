import pygame
from setting import *
from game import Game

pygame.init()

#ウィンドウの作成
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("shooting game")

#FPSの設定
clock = pygame.time.Clock()

# フォントを準備
font = pygame.font.Font(None, 30) # FPS表示用
score_font = pygame.font.Font(None, 50) # スコア表示用

#ゲーム
game = Game()

#メインループ##########################################################################################
run = True
while run:
    #背景の塗りつぶし
    screen.fill(BLACK)

    # スコア表示
    score_text = score_font.render(f"Score: {game.score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # FPS表示
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
    screen.blit(fps_text, (screen_width - 100, 10))

    # ゲームの実行
    game.run(clock)

    #イベントの取得
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                run = False
            # Pキーでポーズ状態を切り替える
            if event.key == pygame.K_p:
                game.paused = not game.paused
            # Hキーで当たり判定の表示を切り替える
            if event.key == pygame.K_h and game.player:
                game.player.toggle_hitbox()
            # QキーでQuadtreeの表示を切り替える
            if event.key == pygame.K_q:
                game.show_quadtree = not game.show_quadtree
            # Jキーで敵弾の当たり判定表示を切り替える
            if event.key == pygame.K_j:
                game.show_enemy_hitbox = not game.show_enemy_hitbox
            # ゲームオーバーまたはクリア時にスペースキーでリセット
            if (game.game_over or game.game_clear) and event.key == pygame.K_SPACE:
                game.reset_game()
            # ポーズ中にRキーでリセット
            if game.paused and event.key == pygame.K_r:
                game.reset_game()
    #画面の更新
    pygame.display.flip()
    clock.tick(FPS)

######################################################################################################

pygame.quit()

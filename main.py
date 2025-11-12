import pygame
from setting import *
from game import Game

pygame.init()

#ウィンドウの作成
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("shooting game")

#FPSの設定
clock = pygame.time.Clock()

# FPS表示用のフォントを準備
font = pygame.font.Font(None, 30)

#ゲーム
game = Game()

#メインループ##########################################################################################
run = True
while run:
    #背景の塗りつぶし
    screen.fill(BLACK)

    #ゲームの実行
    game.run()

    # FPSを画面右上に表示
    fps = clock.get_fps()
    fps_text = f"FPS: {fps:.2f}"
    fps_surface = font.render(fps_text, True, WHITE)
    screen.blit(fps_surface, (screen_width - fps_surface.get_width() - 10, 10))

    #イベントの取得
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                run = False
    #画面の更新
    pygame.display.flip()
    clock.tick(FPS)

######################################################################################################

pygame.quit()

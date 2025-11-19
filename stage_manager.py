import pygame
import random
from setting import *
from enemy import Enemy
from enemy_subclasses import FastEnemy, TankEnemy, WaveEnemy, HunterEnemy # boss_subclassesはStageManager内で直接インポート
from boss import BossEnemy
from boss_subclasses import GrandBossEnemy, Stage1Boss, Stage2MidBoss

class StageManager:
    """ステージ進行と敵の出現を管理するクラス"""
    def __init__(self, enemy_group, player_group, item_group, enemy_bullet_pool=None):
        self.enemy_group = enemy_group
        self.player_group = player_group
        self.item_group = item_group
        self.enemy_bullet_pool = enemy_bullet_pool

        self.stage_schedules = {
            1: [ # ステージ1
                {'start': 0,      'type': 'normal', 'count': 8,  'interval': 800},
                {'start': 5000,   'type': 'fast',   'count': 5, 'interval': 600},
                {'start': 10000,  'type': 'wave',   'count': 7,  'interval': 900},
                {'start': 16000,  'type': 'tank',   'count': 6,  'interval': 1000},
                {'start': 23000,  'type': 'normal', 'count': 12, 'interval': 500},
                {'start': 30000,  'type': 'stage1_boss', 'count': 1, 'interval': 0}, # ステージ1の最初のボス
                {'start': 38000,  'type': 'normal', 'count': 15, 'interval': 400}, # ボス間のザコ敵
                {'start': 45000,  'type': 'boss',   'count': 1,  'interval': 0},   # ステージ1の最終ボス
            ],
            2: [ # ステージ2
                {'start': 0,      'type': 'normal', 'count': 15, 'interval': 400},
                {'start': 7000,   'type': 'fast',   'count': 8,  'interval': 400},
                {'start': 13000,  'type': 'hunter', 'count': 6,  'interval': 1200}, # 新しい敵を追加
                {'start': 20000,  'type': 'stage2_mid_boss', 'count': 1, 'interval': 0},  # ステージ2の中ボス
                {'start': 26000,  'type': 'hunter', 'count': 4,  'interval': 1000}, # 中ボス後の追撃
                {'start': 27000,  'type': 'fast',   'count': 6,  'interval': 500},  # hunterと同時に出現
                {'start': 32000,  'type': 'tank',   'count': 8,  'interval': 800},
                {'start': 38000,  'type': 'wave',   'count': 10, 'interval': 600},
                {'start': 44000,  'type': 'grand_boss', 'count': 1, 'interval': 0},
            ]
        }
        self.stage = 1
        self.spawn_schedule = self.stage_schedules[self.stage]
        self.spawn_active = True
        self.spawn_start_time = pygame.time.get_ticks()
        self.current_wave = 0
        self.wave_spawned = 0
        self.next_spawn_time = self.spawn_start_time + self.spawn_schedule[0]['interval']

        self.stage_clear_timer = 0
        self.stage_clear_wait_time = 3000 # 3秒待機

    def start_stage(self, stage_number):
        """指定されたステージを開始する"""
        self.stage = stage_number
        if stage_number > len(self.stage_schedules):
            return "game_clear"

        self.spawn_schedule = self.stage_schedules[self.stage]
        self.spawn_start_time = pygame.time.get_ticks()
        self.current_wave = 0
        self.wave_spawned = 0
        interval = self.spawn_schedule[0]['interval']
        self.next_spawn_time = self.spawn_start_time + (interval if interval > 0 else 0)
        self.spawn_active = True
        self.stage_clear_timer = 0
        return self.stage

    def update(self, game_over, grand_boss_defeated):
        """敵の生成とステージ進行を管理する"""
        # ステージクリア待機中
        if self.stage_clear_timer > 0:
            if pygame.time.get_ticks() - self.stage_clear_timer > self.stage_clear_wait_time:
                # 最終ボスが倒され、かつ現在のステージが最後のステージであればゲームクリアを通知
                if grand_boss_defeated and self.stage == len(self.stage_schedules):
                    self.spawn_active = False # 敵の出現を停止
                    return "game_clear" # ゲームクリアをGameクラスに通知
                # ボスが倒された直後のフレームで grand_boss_defeated がまだFalseの場合があるため、ここで再チェック
                is_boss_alive = any(isinstance(enemy, BossEnemy) for enemy in self.enemy_group)
                if not is_boss_alive and self.stage == len(self.stage_schedules):
                    return "game_clear"
                self.stage_clear_timer = 0 # タイマーをリセットして再実行を防ぐ
                return self.start_stage(self.stage + 1) # 次のステージへ移行
            return None

        if not self.spawn_active:
            return None

        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_start_time
        is_boss_alive = any(isinstance(enemy, BossEnemy) for enemy in self.enemy_group)

        # ボス戦中は後続ウェーブの開始時間を現在時刻で更新し続け、進行を止める
        if is_boss_alive:
            if (self.current_wave + 1) < len(self.spawn_schedule):
                self.spawn_schedule[self.current_wave + 1]['start'] = elapsed + 100 # 100ms先に設定し続ける

        # 時間経過によるウェーブ進行の判定（ボスがいない場合のみ）
        if not is_boss_alive:
            # 次のウェーブが存在し、かつ開始時刻を過ぎていたら
            if (self.current_wave + 1) < len(self.spawn_schedule) and \
               elapsed >= self.spawn_schedule[self.current_wave + 1]['start']:
                self.current_wave += 1
                self.wave_spawned = 0
                self.next_spawn_time = now

        wave = self.spawn_schedule[self.current_wave]
        
        # 現在のウェーブの敵をすべて生成し終えたか
        if self.wave_spawned >= wave['count']:
            # 現在のウェーブがボスウェーブで、そのボスが倒された場合
            if 'boss' in wave['type'] and not is_boss_alive:
                # これがステージの最終ウェーブの場合
                if self.current_wave == len(self.spawn_schedule) - 1:
                    self.spawn_active = False
                    # ステージクリアタイマーを開始
                    self.stage_clear_timer = pygame.time.get_ticks()
                    return None # 待機状態に入る
                # まだ次のウェーブがある場合
                else:
                    # 即座に次のウェーブへ移行
                    self.current_wave += 1
                    self.wave_spawned = 0
                    next_wave = self.spawn_schedule[self.current_wave]
                    self.spawn_start_time = pygame.time.get_ticks() - next_wave['start'] # 経過時間をリセット
                    self.next_spawn_time = now
            return None # 通常のウェーブ完了後、またはボス生存中は次のウェーブ開始時刻まで待機

        # 敵の生成
        if now >= self.next_spawn_time:
            if game_over or len(self.player_group) == 0:
                self.next_spawn_time = now + wave['interval']
                return None

            if len(self.enemy_group) < 20:
                self.create_enemy(wave)
                self.wave_spawned += 1

            if wave['interval'] > 0:
                self.next_spawn_time = now + wave['interval']
            else:
                self.next_spawn_time = now
        return None

    def create_enemy(self, wave):
        """指定されたウェーブの敵を1体生成する"""
        spawn_type = wave['type']
        # プレイヤーが存在しない場合は敵を生成しない
        if not self.player_group.sprite:
            return
        player = self.player_group.sprite # プレイヤーの存在をチェックした後に参照
        enemy_bullets = player.enemy_bullets # Playerが持つ共有グループ

        if spawn_type == 'wave':
            x = random.choice([-30, GAME_AREA_WIDTH + 30])
            y = random.randint(80, 150)
        else:
            x = random.randint(50, GAME_AREA_WIDTH - 50)
            y = 10

        enemy_map = { # enemy_bullet_pool を渡すように変更
            'normal': Enemy,
            'fast': FastEnemy,
            'tank': TankEnemy,
            'wave': WaveEnemy,
            'hunter': HunterEnemy, # マップに追加
            'boss': BossEnemy,
            'stage1_boss': Stage1Boss,
            'stage2_mid_boss': Stage2MidBoss,
            'grand_boss': GrandBossEnemy
        }

        enemy_class = enemy_map.get(spawn_type, Enemy)
        
        if 'boss' in spawn_type:
            y = -80 if spawn_type != 'grand_boss' else -120
            x = GAME_AREA_WIDTH // 2

        enemy_class(self.enemy_group, x, y, player.bullet_group, self.player_group, enemy_bullets, self.item_group, enemy_bullet_pool=self.enemy_bullet_pool)

    def reset(self):
        """ステージマネージャーの状態をリセットする"""
        self.start_stage(1)
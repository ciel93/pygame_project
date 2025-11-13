import pygame
import random
from setting import *
from enemy import Enemy
from enemy_subclasses import FastEnemy, TankEnemy, WaveEnemy
from boss import BossEnemy
from boss_subclasses import GrandBossEnemy, Stage1Boss

class StageManager:
    """ステージ進行と敵の出現を管理するクラス"""
    def __init__(self, enemy_group, player_group, item_group):
        self.enemy_group = enemy_group
        self.player_group = player_group
        self.item_group = item_group

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
                {'start': 8000,   'type': 'fast',   'count': 8,  'interval': 400},
                {'start': 15000,  'type': 'tank',   'count': 8,  'interval': 800},
                {'start': 23000,  'type': 'wave',   'count': 10, 'interval': 600},
                {'start': 32000,  'type': 'grand_boss', 'count': 1, 'interval': 0},
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
                return self.start_stage(self.stage + 1)
            return None

        if not self.spawn_active:
            return None

        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_start_time
        is_boss_alive = any(isinstance(enemy, BossEnemy) for enemy in self.enemy_group)

        # ウェーブ進行
        if not is_boss_alive:
            if (self.current_wave + 1) < len(self.spawn_schedule) and \
                  elapsed >= self.spawn_schedule[self.current_wave + 1]['start']:
                self.current_wave += 1
                self.wave_spawned = 0
                interval = self.spawn_schedule[self.current_wave]['interval']
                self.next_spawn_time = now + (interval if interval > 0 else 0)
        elif is_boss_alive:
            # ボス戦中は次のウェーブの開始時間を遅延させる
            if (self.current_wave + 1) < len(self.spawn_schedule):
                self.spawn_schedule[self.current_wave + 1]['start'] = elapsed + 100

        wave = self.spawn_schedule[self.current_wave]
        if self.wave_spawned >= wave['count']:
            # ボスが出現するウェーブで、ボスがまだ生きている場合は、ここで処理を中断して待機
            if 'boss' in wave['type'] and is_boss_alive:
                return None
            if self.current_wave == len(self.spawn_schedule) - 1 and len(self.enemy_group) == 0:
                self.spawn_active = False
                if not grand_boss_defeated:
                    self.stage_clear_timer = pygame.time.get_ticks()
            return None

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
        player = self.player_group.sprite
        enemy_bullets = player.enemy_bullets # Playerが持つ共有グループ

        if spawn_type == 'wave':
            x = random.choice([-30, GAME_AREA_WIDTH + 30])
            y = random.randint(80, 150)
        else:
            x = random.randint(50, GAME_AREA_WIDTH - 50)
            y = 10

        enemy_map = {
            'normal': Enemy,
            'fast': FastEnemy,
            'tank': TankEnemy,
            'wave': WaveEnemy,
            'boss': BossEnemy,
            'stage1_boss': Stage1Boss,
            'grand_boss': GrandBossEnemy
        }

        enemy_class = enemy_map.get(spawn_type, Enemy)
        
        if 'boss' in spawn_type:
            y = -80 if spawn_type != 'grand_boss' else -120
            x = GAME_AREA_WIDTH // 2

        enemy_class(self.enemy_group, x, y, player.bullet_group, self.player_group, enemy_bullets, self.item_group)

    def reset(self):
        """ステージマネージャーの状態をリセットする"""
        self.start_stage(1)
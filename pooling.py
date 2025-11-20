import pygame

class BulletPool:
    """弾のオブジェクトプールを管理するクラス"""

    def __init__(self, bullet_factory, initial_size, add_to_group_func):
        """
        bullet_factory: 弾オブジェクトを生成する関数 (例: lambda: Bullet(groups, x, y))
        initial_size: プールの初期サイズ
        add_to_group_func: 弾をアクティブなグループに追加する関数
        """
        self.pool = []
        self.factory = bullet_factory
        self.max_size = initial_size
        self.add_to_group = add_to_group_func

        # プールをあらかじめ生成しておく
        for _ in range(initial_size):
            self.pool.append(self.factory())

    def get(self):
        """プールから弾を取得する。プールが空なら新しい弾を生成する。"""
        if len(self.pool) > 0:
            bullet = self.pool.pop()
        else:
            bullet = self.factory() # フォールバック
        
        self.add_to_group(bullet) # 弾をアクティブなグループに追加
        return bullet

    def put(self, bullet):
        """使用済みの弾をプールに戻す。"""
        if len(self.pool) < self.max_size:
            bullet.kill() # 全てのグループから削除して非アクティブにする
            self.pool.append(bullet)
import pygame

class Quadtree:
    """
    衝突判定を効率化するためのQuadtreeクラス。
    各フレームで再構築して使用することを想定しています。
    """
    def __init__(self, level, boundary):
        """
        level: ツリーの階層の深さ
        boundary: このノードが担当する矩形領域 (pygame.Rect)
        """
        self.level = level
        self.boundary = boundary
        self.capacity = 4  # 各ノードが分割される前に保持できるオブジェクトの最大数
        self.max_level = 8 # ツリーの最大深度

        self.objects = []  # このノードに含まれるオブジェクト
        self.nodes = []    # 4つの子ノード

    def clear(self):
        """ツリーをクリアして再利用可能にする"""
        self.objects.clear()
        for node in self.nodes:
            node.clear()
        self.nodes.clear()

    def _subdivide(self):
        """領域を4つの子ノードに分割する"""
        x, y, w, h = self.boundary
        half_w, half_h = w / 2, h / 2

        # 北西、北東、南西、南東の順で子ノードを作成
        nw = pygame.Rect(x, y, half_w, half_h)
        ne = pygame.Rect(x + half_w, y, half_w, half_h)
        sw = pygame.Rect(x, y + half_h, half_w, half_h)
        se = pygame.Rect(x + half_w, y + half_h, half_w, half_h)

        self.nodes.append(Quadtree(self.level + 1, nw))
        self.nodes.append(Quadtree(self.level + 1, ne))
        self.nodes.append(Quadtree(self.level + 1, sw))
        self.nodes.append(Quadtree(self.level + 1, se))

    def insert(self, obj):
        """オブジェクトをツリーに挿入する"""
        # 子ノードがある場合は、適切な子ノードに挿入を試みる
        if self.nodes:
            for node in self.nodes:
                if node.boundary.colliderect(obj.rect):
                    node.insert(obj)
            return

        # このノードにオブジェクトを追加
        self.objects.append(obj)

        # 容量を超え、かつ最大深度に達していない場合、分割してオブジェクトを子に移動
        if len(self.objects) > self.capacity and self.level < self.max_level:
            self._subdivide()
            for o in self.objects:
                for node in self.nodes:
                    if node.boundary.colliderect(o.rect):
                        node.insert(o)
            self.objects.clear()
            
    def draw(self, screen):
        """Quadtreeの矩形領域を再帰的に描画する（デバッグ用）"""
        # 半透明の描画用にSurfaceを作成
        s = pygame.Surface((self.boundary.width, self.boundary.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 255, 0, 50), s.get_rect(), 1) # 4番目の値(50)がアルファ値
        screen.blit(s, self.boundary.topleft)
        for node in self.nodes:
            node.draw(screen)

    def query(self, range_rect, found_objects):
        """指定された範囲(range_rect)内のオブジェクトを検索する"""
        if not self.boundary.colliderect(range_rect):
            return

        if self.nodes:
            for node in self.nodes:
                node.query(range_rect, found_objects)
        else:
            for obj in self.objects:
                if range_rect.colliderect(obj.rect):
                    found_objects.add(obj) # setを使用して重複を避ける
        return found_objects
import sys
import time
from typing import List, Optional
import random
from PIL import Image, ImageDraw

class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __eq__(self, other: 'Point') -> bool:
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))

class Map2D:
    def __init__(self, height: int, width: int) -> None:
        self.height = height
        self.width = width
        self.data = [["⬜" for _ in range(width)] for _ in range(height)]
        self.create_shelves()
        self.create_assembly_line()

    def create_shelves(self) -> None:
        shelf_coords = [
            (5, 10), (12, 10), (19, 10), (26, 10), (33, 10), (40, 10)
        ]
        for start_x, start_y in shelf_coords:
            for row in range(start_x, start_x + 4):
                for col in range(start_y, start_y + 65):
                    if row < self.height and col < self.width:
                        self.data[row][col] = "⬛"

    def create_assembly_line(self) -> None:
        start_x, start_y = 47, 7
        for row in range(start_x, start_x + 2):
            for col in range(start_y, start_y + 85):
                if row < self.height and col < self.width:
                    self.data[row][col] = "⬛"

    def show(self, file_name: str = "output.txt") -> None:
        with open(file_name, 'w', encoding='utf-8') as file:
            for row in self.data:
                file.write(" ".join(row) + '\n')

    def export_image(self, file_name: str = "map.png") -> None:
        cell_size = 10
        image = Image.new("RGB", (self.width * cell_size, self.height * cell_size), "white")
        draw = ImageDraw.Draw(image)

        # 绘制网格背景
        for x in range(self.width):
            for y in range(self.height):
                draw.rectangle([x * cell_size, y * cell_size, (x + 1) * cell_size, (y + 1) * cell_size], outline="lightgrey")

        for x in range(self.height):
            for y in range(self.width):
                color = "white"
                if self.data[x][y] == "⬛":
                    color = "black"
                elif self.data[x][y] == "🟥":
                    color = "red"
                elif self.data[x][y] == "🟩":
                    color = "green"
                elif self.data[x][y] == "🟦":
                    color = "blue"
                elif self.data[x][y] == "🟧":
                    color = "orange"
                elif self.data[x][y] == "🟨":
                    color = "yellow"
                draw.rectangle([(y * cell_size, x * cell_size), ((y + 1) * cell_size, (x + 1) * cell_size)], fill=color, outline="lightgrey")
        image.save(file_name)

    def set_obstacle(self, x: int, y: int) -> None:
        self.data[x][y] = "⬛"

    def set_start_end(self, start: Point, end: Point) -> None:
        self.data[start.x][start.y] = "🟥"
        self.data[end.x][end.y] = "🟥"

class Node:
    def __init__(self, point: Point, endpoint: Point, g: float) -> None:
        self.point = point
        self.endpoint = endpoint
        self.father: Optional[Node] = None
        self.g = g
        self.h = (abs(endpoint.x - point.x) + abs(endpoint.y - point.y)) * 10
        self.f = self.g + self.h

    def get_near(self, ud: int, rl: int) -> 'Node':
        near_point = Point(self.point.x + rl, self.point.y + ud)
        near_node = Node(near_point, self.endpoint, self.g + (10 if ud == 0 or rl == 0 else 14))
        return near_node

class AStar:
    def __init__(self, start: Point, end: Point, map2d: Map2D) -> None:
        self.path: List[Point] = []
        self.closed_list = set()
        self.open_list: List[Node] = []
        self.start = start
        self.end = end
        self.map2d = map2d

    def select_current(self) -> Optional[Node]:
        min_f = sys.maxsize
        node_temp = None
        for node in self.open_list:
            if node.f < min_f:
                min_f = node.f
                node_temp = node
        return node_temp

    def is_in_open_list(self, node: Node) -> bool:
        return any(open_node.point == node.point for open_node in self.open_list)

    def is_obstacle(self, node: Node) -> bool:
        return self.map2d.data[node.point.x][node.point.y] == "⬛"

    def explore_neighbors(self, current_node: Node) -> bool:
        directions = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (-1, 1), (1, -1), (-1, -1)
        ]
        for ud, rl in directions:
            current_neighbor = current_node.get_near(ud, rl)
            if not (0 <= current_neighbor.point.x < self.map2d.height and 0 <= current_neighbor.point.y < self.map2d.width):
                continue
            if current_neighbor.point == self.end:
                return True
            if current_neighbor.point in self.closed_list or self.is_obstacle(current_neighbor):
                continue
            if self.is_in_open_list(current_neighbor):
                previous_current_neighbor = next(
                    open_node for open_node in self.open_list if open_node.point == current_neighbor.point)
                if current_neighbor.f < previous_current_neighbor.f:
                    previous_current_neighbor.father = current_node
                    previous_current_neighbor.g = current_neighbor.g
            else:
                current_neighbor.father = current_node
                self.open_list.append(current_neighbor)
        return False

    def find_path(self) -> Optional[List[Point]]:
        start_node = Node(point=self.start, endpoint=self.end, g=0)
        self.open_list.append(start_node)
        while self.open_list:
            current_node = self.select_current()
            if current_node is None:
                return None
            self.open_list.remove(current_node)
            self.closed_list.add(current_node.point)
            if current_node.point == self.end or self.explore_neighbors(current_node):
                while current_node.father is not None:
                    self.path.insert(0, current_node.point)
                    current_node = current_node.father
                return self.path
        return None

def get_user_point(prompt: str, height: int, width: int, map2d: Map2D) -> Point:
    while True:
        try:
            x = int(input(f"请输入{prompt}x坐标 (0-{height-1}): "))
            y = int(input(f"请输入{prompt}y坐标 (0-{width-1}): "))
            if 0 <= x < height and 0 <= y < width:
                if map2d.data[x][y] == "⬛":
                    print(f"{prompt}坐标位于障碍物上，请重新输入。")
                else:
                    return Point(x, y)
            else:
                print(f"{prompt}坐标超出范围，请重新输入。")
        except ValueError:
            print("请输入有效的整数坐标。")

if __name__ == "__main__":
    random.seed(42)

    height = 50
    width = 100
    map2d = Map2D(height, width)

    start_point = get_user_point("起点", height, width, map2d)
    end_point = get_user_point("终点", height, width, map2d)
    middle_points = [get_user_point(f"中间点{i+1}", height, width, map2d) for i in range(3)]

    map2d.set_start_end(start_point, end_point)
    for point in middle_points:
        map2d.data[point.x][point.y] = "🟦"

    points = [start_point] + middle_points + [end_point]
    total_path = []
    start_time = time.time()
    colors = ["🟧", "🟨", "🟩", "🟦"]  # 橙色，黄色，绿色，青色
    for i in range(len(points) - 1):
        a_star = AStar(points[i], points[i+1], map2d)
        path_segment = a_star.find_path()
        if path_segment:
            total_path.extend(path_segment)
            for point in path_segment:
                if i < len(colors):
                    map2d.data[point.x][point.y] = colors[i]
                else:
                    map2d.data[point.x][point.y] = "🟩"  # Default to green if out of colors
        else:
            print("未找到路径！")
            break
    end_time = time.time()

    if total_path:
        print("找到最佳路径：")
        for point in total_path:
            print(f"({point.x}, {point.y})")
    else:
        print("未找到路径！")

    map2d.export_image("result.png")
    print("程序运行时间：", end_time - start_time, "秒")

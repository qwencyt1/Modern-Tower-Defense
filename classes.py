import pygame
import math
import random


class EnvironmentObject:
    """Класс для декоративных объектов на карте (деревья, камни, кусты)"""

    def __init__(self, x, y, obj_type):
        self.x = x
        self.y = y
        self.obj_type = obj_type
        self.anim_phase = random.uniform(0, math.pi * 2)
        self.size_modifier = random.uniform(0.8, 1.2)

        if obj_type == "tree_pine":
            self.color = (random.randint(20, 40), random.randint(100, 140), random.randint(40, 70))
        elif obj_type == "tree_oak":
            self.color = (random.randint(40, 70), random.randint(130, 170), random.randint(30, 60))
        elif obj_type == "bush":
            self.color = (random.randint(50, 90), random.randint(150, 190), random.randint(40, 70))
        else:  # stone
            c = random.randint(100, 130)
            self.color = (c, c, c + random.randint(0, 10))

    def draw(self, surface, current_time):
        wind = math.sin(current_time * 0.002 + self.anim_phase) * 2

        if self.obj_type in ["tree_pine", "tree_oak"]:
            pygame.draw.rect(surface, (100, 65, 30), (self.x - 3, self.y, 6, 18))
            if self.obj_type == "tree_pine":
                base_w = 24 * self.size_modifier
                for i in range(3):
                    layer_y = self.y - i * 8
                    p1 = (self.x - base_w + i * 4 + wind, layer_y)
                    p2 = (self.x + base_w - i * 4 + wind, layer_y)
                    p3 = (self.x + wind, layer_y - 16)
                    pygame.draw.polygon(surface, self.color, [p1, p2, p3])
            else:
                r = 14 * self.size_modifier
                pygame.draw.circle(surface, self.color, (int(self.x + wind), int(self.y - 4)), int(r))
                pygame.draw.circle(surface, (self.color[0] + 15, self.color[1] + 15, self.color[2]),
                                   (int(self.x - 4 + wind), int(self.y - 8)), int(r * 0.7))
        elif self.obj_type == "bush":
            r = 10 * self.size_modifier
            pygame.draw.circle(surface, self.color, (int(self.x + wind), int(self.y)), int(r))
            pygame.draw.circle(surface, self.color, (int(self.x - 6 + wind), int(self.y + 2)), int(r * 0.8))
            pygame.draw.circle(surface, self.color, (int(self.x + 6 + wind), int(self.y + 2)), int(r * 0.8))
        elif self.obj_type == "stone":
            r = 12 * self.size_modifier
            rect = pygame.Rect(self.x - r, self.y - r * 0.7, r * 2, r * 1.4)
            pygame.draw.ellipse(surface, self.color, rect)
            pygame.draw.ellipse(surface,
                                (max(0, self.color[0] - 30), max(0, self.color[1] - 30), max(0, self.color[2] - 30)),
                                (rect.x + 2, rect.y + rect.height // 2, rect.width - 4, rect.height // 2 - 1))
            pygame.draw.ellipse(surface, (
            min(255, self.color[0] + 30), min(255, self.color[1] + 30), min(255, self.color[2] + 30)),
                                (rect.x + 4, rect.y + 2, rect.width * 0.4, rect.height * 0.3))


class Enemy(pygame.sprite.Sprite):
    def __init__(self, waypoints, health_modifier=1.0, enemy_type="normal"):
        super().__init__()

        self.enemy_type = enemy_type
        # Босс имеет увеличенный размер спрайта
        self.size = 64 if enemy_type == "boss" else 40
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

        self.waypoints = waypoints
        self.current_point_idx = 0
        self.rect.center = self.waypoints[self.current_point_idx]

        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)

        self.max_shield = 0
        self.base_damage_to_base = 1  # Урон, наносимый базе при прорыве

        # Настройка уникальных характеристик под каждый тип врага
        if enemy_type == "fast":
            self.speed = 5
            self.max_hp = int(55 * health_modifier)
            self.color_body = (30, 144, 255)  # Голубой
            self.reward = 8
        elif enemy_type == "shield":
            self.speed = 2.5
            self.max_hp = int(80 * health_modifier)
            self.max_shield = int(60 * health_modifier)  # Силовой щит
            self.color_body = (155, 48, 255)  # Фиолетовый
            self.reward = 12
        elif enemy_type == "kamikaze":
            self.speed = 5.5
            self.max_hp = int(45 * health_modifier)
            self.color_body = (255, 30, 30)  # Ярко-красный
            self.reward = 10
            self.base_damage_to_base = 3  # Смертельно опасен для базы
        elif enemy_type == "boss":
            self.speed = 1.2
            self.max_hp = int(650 * health_modifier)
            self.color_body = (35, 35, 35)  # Тяжелый темный металл
            self.reward = 100
            self.base_damage_to_base = 5
        else:  # normal
            self.speed = 3
            self.max_hp = int(90 * health_modifier)
            self.color_body = (90, 100, 110)  # Серый
            self.reward = 5

        self.hp = self.max_hp
        self.shield = self.max_shield
        self.hp_font = pygame.font.SysFont("Arial", 14, bold=True)

    def take_damage(self, amount):
        if self.shield > 0:
            self.shield -= amount
            if self.shield < 0:
                self.hp += self.shield  # Перенос избыточного урона на здоровье
                self.shield = 0
        else:
            self.hp -= amount

    def update(self):
        if self.hp <= 0:
            self.kill()
            return True

        if self.current_point_idx >= len(self.waypoints) - 1:
            self.kill()
            return False

        target_x, target_y = self.waypoints[self.current_point_idx + 1]
        dx = target_x - self.x # Используем float координату
        dy = target_y - self.y # Используем float координату
        distance = math.hypot(dx, dy)

        # Проверку на близость оставляем, 3 пикселей вполне достаточно
        if distance <= max(self.speed, 3.0):
            self.x = float(target_x)
            self.y = float(target_y)
            self.rect.center = (target_x, target_y)
            self.current_point_idx += 1
        else:
            # Изменяем float переменные без принудительного отбрасывания дробной части int()
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed
            # Переносим результат в rect игры (автоматически приведется к int внутренностями Pygame)
            self.rect.centerx = int(self.x)
            self.rect.centery = int(self.y)

        self.draw_drone_sprite()
        return False

    def draw_drone_sprite(self):
        self.image.fill((0, 0, 0, 0))
        time_ms = pygame.time.get_ticks()
        angle = (time_ms // 10) % 360
        rad = math.radians(angle)

        center = self.size // 2

        blade_dist = center - 6
        blade_offsets = [0, math.pi / 2, math.pi, 3 * math.pi / 2]

        for offset in blade_offsets:
            bx = center + int(math.cos(rad + offset) * blade_dist)
            by = center + int(math.sin(rad + offset) * blade_dist)
            pygame.draw.circle(self.image, (40, 45, 50), (bx, by), 6 if self.enemy_type == "boss" else 5)
            pygame.draw.circle(self.image, (70, 75, 80), (bx, by), 3)

        body_radius = center - 8 if self.enemy_type == "boss" else 12
        pygame.draw.circle(self.image, self.color_body, (center, center), body_radius)
        pygame.draw.circle(self.image, (50, 55, 60), (center, center), body_radius, 2)

        hp_ratio = max(0.0, min(1.0, self.hp / self.max_hp))
        eye_color = (int(255 * (1 - hp_ratio)), int(255 * hp_ratio), 0) if hp_ratio > 0.5 else (
        255, int(255 * hp_ratio * 2), 0)

        if self.enemy_type == "kamikaze":
            pulse = int(abs(math.sin(time_ms * 0.01)) * 100)
            eye_color = (155 + pulse, 0, 0)

        pygame.draw.circle(self.image, eye_color, (center, center), body_radius // 2)
        pygame.draw.circle(self.image, (255, 255, 255), (center - 1, center - 1), 2)

        if self.shield > 0:
            shield_alpha = int((self.shield / self.max_shield) * 110) + 40
            shield_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (0, 191, 255, shield_alpha), (center, center), body_radius + 6, 3)
            pygame.draw.circle(shield_surf, (0, 191, 255, shield_alpha // 3), (center, center), body_radius + 4)
            self.image.blit(shield_surf, (0, 0))

    def draw_hover_hp(self, surface, mouse_pos):
        if self.rect.collidepoint(mouse_pos) and self.enemy_type != "boss":
            shield_str = f" | SHD: {self.shield}" if self.max_shield > 0 else ""
            text_surf = self.hp_font.render(f"HP: {self.hp}/{self.max_hp}{shield_str}", True, (255, 255, 255))
            padding = 6
            box_width = text_surf.get_width() + padding * 2
            box_height = text_surf.get_height() + padding * 2

            mx, my = mouse_pos
            box_x = mx + 15
            box_y = my - box_height - 5

            pygame.draw.rect(surface, (30, 30, 35), (box_x, box_y, box_width, box_height), border_radius=4)
            pygame.draw.rect(surface, (0, 0, 0), (box_x, box_y, box_width, box_height), 1, border_radius=4)
            surface.blit(text_surf, (box_x + padding, box_y + padding))


class Particle(pygame.sprite.Sprite):

    def __init__(self, x, y):
        super().__init__()
        self.x = float(x)
        self.y = float(y)

        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 6)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed

        self.size = random.randint(2, 5)
        self.lifetime = random.randint(20, 40)
        self.color = random.choice([(255, 69, 0), (255, 215, 0), (100, 105, 110), (40, 45, 50)])

        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
            return

        self.x += self.dx
        self.y += self.dy
        self.rect.center = (int(self.x), int(self.y))
        self.dx *= 0.95
        self.dy *= 0.95

    def draw_custom(self, surface):
        alpha = max(0, min(255, int((self.lifetime / 40) * 255)))
        surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (self.size, self.size), self.size)
        surface.blit(surf, (self.rect.x, self.rect.y))


class Tower(pygame.sprite.Sprite):
    def __init__(self, x, y, tower_type="laser"):
        super().__init__()
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.tower_type = tower_type
        self.level = 1
        self.last_shot_time = 0
        self.target_line = None
        self.angle = 0
        self.recoil_offset = 0

        self.max_ammo = 15 if tower_type == "laser" else 45
        self.ammo = self.max_ammo
        self.ammo_requested = False

        if tower_type == "laser":
            self.base_range = 150
            self.base_damage = 38
            self.cooldown = 900
            self.laser_color = (255, 0, 0)
            self.BASE_COLOR = (140, 140, 140)
        else:  # gun
            self.base_range = 220
            self.base_damage = 16
            self.cooldown = 150
            self.laser_color = (0, 191, 255)
            self.BASE_COLOR = (110, 130, 140)

        self.range = self.base_range
        self.damage = self.base_damage
        self.GUN_COLOR = (80, 80, 80)
        self.DETAIL_COLOR = (110, 110, 110)

    def get_upgrade_cost(self):
        if self.level == 1: return 40
        if self.level == 2: return 80
        return None

    def upgrade(self):
        if self.level < 3:
            self.level += 1
            self.damage = int(self.base_damage * (1 + (self.level - 1) * 0.45))
            self.range = int(self.base_range * (1 + (self.level - 1) * 0.2))
            self.max_ammo = int(self.max_ammo * 1.3)
            self.ammo = self.max_ammo

    def attack(self, enemies_group, current_time):
        self.target_line = None
        if self.ammo <= 0: return

        nearest_enemy = None
        min_dist = self.range

        for enemy in enemies_group:
            dist = math.hypot(enemy.rect.centerx - self.rect.centerx, enemy.rect.centery - self.rect.centery)
            if dist < min_dist:
                min_dist = dist
                nearest_enemy = enemy

        if nearest_enemy:
            dx = nearest_enemy.rect.centerx - self.rect.centerx
            dy = nearest_enemy.rect.centery - self.rect.centery
            self.angle = math.atan2(-dy, dx)

            if current_time - self.last_shot_time >= self.cooldown:
                nearest_enemy.take_damage(self.damage)
                self.last_shot_time = current_time
                self.target_line = (self.rect.center, nearest_enemy.rect.center)
                self.recoil_offset = 8
                self.ammo -= 1
            elif current_time - self.last_shot_time < 100:
                self.target_line = (self.rect.center, nearest_enemy.rect.center)

    def draw_custom(self, surface, x=None, y=None, alpha=255, current_time=0):
        pos_x = x if x is not None else self.rect.centerx
        pos_y = y if y is not None else self.rect.centery

        if self.recoil_offset > 0:
            self.recoil_offset *= 0.85
            if self.recoil_offset < 0.2: self.recoil_offset = 0

        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.rect(surf, (*self.BASE_COLOR, alpha), (5, 5, 40, 40), border_radius=4)
        pygame.draw.circle(surf, (*self.DETAIL_COLOR, alpha), (25, 25), 14)

        gun_length = 22 - int(self.recoil_offset)
        gun_end_x = 25 + int(math.cos(self.angle) * gun_length)
        gun_end_y = 25 - int(math.sin(self.angle) * gun_length)

        pygame.draw.line(surf, (*self.GUN_COLOR, alpha), (25, 25), (gun_end_x, gun_end_y), 7)
        pygame.draw.circle(surf, (*self.GUN_COLOR, alpha), (25, 25), 8)

        for i in range(self.level):
            pygame.draw.circle(surf, (255, 215, 0, alpha), (10 + i * 8, 12), 3)

        surface.blit(surf, (pos_x - 25, pos_y - 25))

        if x is None and y is None:
            ammo_ratio = max(0.0, self.ammo / self.max_ammo)
            bar_w = 32
            bar_h = 4
            bx = self.rect.centerx - bar_w // 2
            by = self.rect.top - 8
            pygame.draw.rect(surface, (20, 20, 20), (bx, by, bar_w, bar_h))
            color = (255, 69, 0) if self.ammo <= 3 else (218, 165, 32)
            pygame.draw.rect(surface, color, (bx, by, int(bar_w * ammo_ratio), bar_h))

    def draw_laser(self, surface):
        if self.target_line and self.ammo >= 0:
            pygame.draw.line(surface, self.laser_color, self.target_line[0], self.target_line[1], 4)


class SupplyDrone(pygame.sprite.Sprite):
    """Дрон-доставщик боеприпасов от здания станции к пушкам"""

    def __init__(self, station):
        super().__init__()
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.station = station
        self.rect.center = station.rect.center
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)
        self.speed = 5
        self.target_tower = None
        self.state = "IDLE"

    def update(self, towers_group):
        if self.station.level == 1:
            self.speed = 5
        elif self.station.level == 2:
            self.speed = 8
        elif self.station.level == 3:
            self.speed = 12

        if self.state == "IDLE":
            for tower in towers_group:
                if isinstance(tower, Tower) and tower.ammo <= 3 and not tower.ammo_requested:
                    self.target_tower = tower
                    tower.ammo_requested = True
                    self.state = "DELIVERING"
                    break
            self.x = float(self.station.rect.centerx)
            self.y = float(self.station.rect.centery)

        elif self.state == "DELIVERING":
            if not self.target_tower or not self.target_tower.alive():
                self.state = "RETURNING"
                return
            tx, ty = self.target_tower.rect.center
            dx = tx - self.x
            dy = ty - self.y
            dist = math.hypot(dx, dy)

            if dist <= self.speed:
                self.target_tower.ammo = self.target_tower.max_ammo
                self.target_tower.ammo_requested = False
                self.target_tower = None
                self.state = "RETURNING"
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed

        elif self.state == "RETURNING":
            tx, ty = self.station.rect.center
            dx = tx - self.x
            dy = ty - self.y
            dist = math.hypot(dx, dy)

            if dist <= self.speed:
                self.state = "IDLE"
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed

        self.rect.center = (int(self.x), int(self.y))
        self.draw_drone_sprite()

    def draw_drone_sprite(self):
        self.image.fill((0, 0, 0, 0))
        cx, cy = 20, 20
        drone_color = (25, 25, 25)
        frame_color = (45, 45, 45)
        pygame.draw.line(self.image, frame_color, (7, 7), (33, 33), 4)
        pygame.draw.line(self.image, frame_color, (7, 33), (33, 7), 4)

        time_ms = pygame.time.get_ticks()
        rad = (time_ms // 4) % 360
        offset_x = int(math.cos(rad) * 5)
        offset_y = int(math.sin(rad) * 5)

        rotors = [(7, 7), (33, 7), (7, 33), (33, 33)]
        for rx, ry in rotors:
            pygame.draw.circle(self.image, drone_color, (rx, ry), 4)
            pygame.draw.line(self.image, (170, 170, 170), (rx - offset_x, ry - offset_y),
                             (rx + offset_x, ry + offset_y), 2)

        pygame.draw.circle(self.image, drone_color, (cx, cy), 8)
        indicator_color = (0, 255, 255) if self.state == "IDLE" else (255, 69, 0)
        pygame.draw.circle(self.image, indicator_color, (cx, cy), 3)

        if self.state == "DELIVERING":
            pygame.draw.rect(self.image, (255, 215, 0), (15, 23, 10, 6))


class DroneStation(pygame.sprite.Sprite):
    """Здание-аэродром, к которому привязан снабжающий дрон"""

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.tower_type = "drone_station"
        self.level = 1
        self.range = 0

    def get_upgrade_cost(self):
        if self.level == 1: return 60
        if self.level == 2: return 120
        return None

    def upgrade(self):
        if self.level < 3: self.level += 1

    def attack(self, enemies_group, current_time):
        pass

    def draw_laser(self, surface):
        pass

    def draw_custom(self, surface, x=None, y=None, alpha=255, current_time=0):
        pos_x = x if x is not None else self.rect.centerx
        pos_y = y if y is not None else self.rect.centery
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.rect(surf, (20, 20, 25, alpha), (4, 4, 42, 42), border_radius=8)
        pygame.draw.rect(surf, (50, 50, 55, alpha), (4, 4, 42, 42), 2, border_radius=8)
        pygame.draw.circle(surf, (255, 120, 0, alpha), (25, 25), 15, 2)

        font = pygame.font.SysFont("Arial", 16, bold=True)
        text = font.render("H", True, (255, 120, 0, alpha))
        surf.blit(text, (25 - text.get_width() // 2, 25 - text.get_height() // 2))

        for i in range(self.level):
            pygame.draw.circle(surf, (255, 215, 0, alpha), (10 + i * 8, 12), 3)
        surface.blit(surf, (pos_x - 25, pos_y - 25))


class Road:
    def __init__(self, waypoints):
        self.waypoints = waypoints
        self.thickness = 50
        self.color = (90, 95, 100)
        self.border_color = (195, 160, 115)

    def draw(self, surface):
        if len(self.waypoints) > 1:
            border_radius = (self.thickness + 12) // 2
            for point in self.waypoints:
                pygame.draw.circle(surface, self.border_color, point, border_radius)
            pygame.draw.lines(surface, self.border_color, False, self.waypoints, self.thickness + 12)

            radius = self.thickness // 2
            for point in self.waypoints:
                pygame.draw.circle(surface, self.color, point, radius)
            pygame.draw.lines(surface, self.color, False, self.waypoints, self.thickness)

    def get_distance_to_pos(self, pos):
        x, y = pos
        min_dist = float('inf')
        for i in range(len(self.waypoints) - 1):
            x1, y1 = self.waypoints[i]
            x2, y2 = self.waypoints[i + 1]
            px = x2 - x1
            py = y2 - y1
            something = px * px + py * py
            if something == 0: continue
            u = ((x - x1) * px + (y - y1) * py) / float(something)
            if u > 1:
                u = 1
            elif u < 0:
                u = 0
            closest_x = x1 + u * px
            closest_y = y1 + u * py
            dist = math.hypot(x - closest_x, y - closest_y)
            if dist < min_dist: min_dist = dist
        return min_dist

    def is_near_road(self, pos):
        min_dist_to_center = self.get_distance_to_pos(pos)
        road_radius = self.thickness // 2
        tower_safety_margin = 25
        min_placement_dist = road_radius + tower_safety_margin
        return min_placement_dist <= min_dist_to_center <= min_placement_dist + 40


class Base:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 10
        self.max_hp = 10
        self.width = 100
        self.height = 100
        self.rect = pygame.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)

    def draw(self, surface):
        pygame.draw.rect(surface, (60, 65, 70), self.rect, border_radius=10)
        pygame.draw.rect(surface, (40, 45, 50), self.rect, 4, border_radius=10)
        pygame.draw.circle(surface, (0, 191, 255), (self.x, self.y), 20)
        pygame.draw.circle(surface, (255, 255, 255), (self.x, self.y), 10)


class BuildMenu:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.height = 120
        self.color = (40, 40, 45)
        self.rect = pygame.Rect(0, screen_h - self.height, screen_w, self.height)

        self.btn_laser_rect = pygame.Rect(30, screen_h - self.height + 15, 60, 60)
        self.btn_gun_rect = pygame.Rect(120, screen_h - self.height + 15, 60, 60)
        self.btn_drone_rect = pygame.Rect(210, screen_h - self.height + 15, 60, 60)
        self.upgrade_btn_rect = pygame.Rect(screen_w - 220, screen_h - self.height + 15, 190, 60)
        self.top_panel_rect = pygame.Rect(0, 0, screen_w, 50)

        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.price_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.stat_font = pygame.font.SysFont("Arial", 15, bold=False)
        self.game_over_font = pygame.font.SysFont("Arial", 60, bold=True)
        self.boss_font = pygame.font.SysFont("Impact", 22, bold=False)

    def draw_boss_bar(self, surface, boss_enemy):
        """Отрисовка верхней интерфейсной панели здоровья босса"""
        if not boss_enemy or not boss_enemy.alive():
            return

        bar_w = 450
        bar_h = 20
        bar_x = (self.screen_w - bar_w) // 2
        bar_y = 65  # Расположение сразу под верхней панелью ресурсов

        # Задняя рамка под шкалу здоровья босса
        pygame.draw.rect(surface, (20, 20, 20), (bar_x - 5, bar_y - 25, bar_w + 10, bar_h + 32), border_radius=4)
        pygame.draw.rect(surface, (255, 30, 30), (bar_x - 5, bar_y - 25, bar_w + 10, bar_h + 32), 1, border_radius=4)

        # Название босса
        name_text = self.boss_font.render("КРИТИЧЕСКАЯ УГРОЗА: ДРОН-РАЗРУШИТЕЛЬ", True, (255, 50, 50))
        surface.blit(name_text, (self.screen_w // 2 - name_text.get_width() // 2, bar_y - 24))

        # Сама полоска здоровья
        ratio = max(0.0, boss_enemy.hp / boss_enemy.max_hp)
        pygame.draw.rect(surface, (60, 10, 10), (bar_x, bar_y, bar_w, bar_h))  # Темный фон шкалы
        pygame.draw.rect(surface, (230, 0, 0), (bar_x, bar_y, int(bar_w * ratio), bar_h))  # Красное заполнение HP

        # Отображение точного числа единиц HP поверх шкалы
        hp_str = f"{boss_enemy.hp} / {boss_enemy.max_hp}"
        hp_text = self.price_font.render(hp_str, True, (255, 255, 255))
        surface.blit(hp_text, (self.screen_w // 2 - hp_text.get_width() // 2, bar_y + 1))

    def draw_range_preview(self, surface, pos, radius, is_valid):
        if radius <= 0: return
        color = (255, 0, 0, 40) if not is_valid else (255, 255, 255, 30)
        border_color = (255, 0, 0, 150) if not is_valid else (255, 255, 255, 100)
        mx, my = pos
        overlay = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(overlay, color, (radius, radius), radius)
        pygame.draw.circle(overlay, border_color, (radius, radius), radius, 2)
        surface.blit(overlay, (mx - radius, my - radius))

    def draw(self, surface, selected_type, current_money, wave, enemies_left, base_hp, selected_tower=None):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.line(surface, (70, 70, 75), (0, self.rect.top), (self.rect.width, self.rect.top), 3)

        # Лазерная пушка
        b1_color = (180, 180, 180) if selected_type == "laser" else (100, 100, 100)
        pygame.draw.rect(surface, b1_color, self.btn_laser_rect, border_radius=5)
        pygame.draw.rect(surface, (140, 140, 140), (self.btn_laser_rect.x + 15, self.btn_laser_rect.y + 15, 30, 30),
                         border_radius=3)
        pygame.draw.line(surface, (255, 0, 0), (self.btn_laser_rect.centerx, self.btn_laser_rect.centery),
                         (self.btn_laser_rect.centerx + 12, self.btn_laser_rect.centery - 12), 5)
        price1 = self.price_font.render("30 $", True, (255, 215, 0))
        surface.blit(price1, (self.btn_laser_rect.centerx - price1.get_width() // 2, self.btn_laser_rect.bottom + 5))

        # Скорострельный пулемет
        b2_color = (180, 180, 180) if selected_type == "gun" else (100, 100, 100)
        pygame.draw.rect(surface, b2_color, self.btn_gun_rect, border_radius=5)
        pygame.draw.rect(surface, (110, 130, 140), (self.btn_gun_rect.x + 15, self.btn_gun_rect.y + 15, 30, 30),
                         border_radius=3)
        pygame.draw.line(surface, (0, 191, 255), (self.btn_gun_rect.centerx, self.btn_gun_rect.centery),
                         (self.btn_gun_rect.centerx + 12, self.btn_gun_rect.centery - 12), 5)
        price2 = self.price_font.render("50 $", True, (255, 215, 0))
        surface.blit(price2, (self.btn_gun_rect.centerx - price2.get_width() // 2, self.btn_gun_rect.bottom + 5))

        # Станция дронов
        b3_color = (180, 180, 180) if selected_type == "drone_station" else (100, 100, 100)
        pygame.draw.rect(surface, b3_color, self.btn_drone_rect, border_radius=5)
        bx, by = self.btn_drone_rect.center
        pygame.draw.rect(surface, (20, 20, 25), (bx - 16, by - 16, 32, 32), border_radius=4)
        pygame.draw.circle(surface, (255, 120, 0), (bx, by), 10, 2)
        btn_h_font = pygame.font.SysFont("Arial", 12, bold=True)
        btn_h_text = btn_h_font.render("H", True, (255, 120, 0))
        surface.blit(btn_h_text, (bx - btn_h_text.get_width() // 2, by - btn_h_text.get_height() // 2))
        price3 = self.price_font.render("60 $", True, (255, 215, 0))
        surface.blit(price3, (self.btn_drone_rect.centerx - price3.get_width() // 2, self.btn_drone_rect.bottom + 5))

        if selected_type == "laser":
            pygame.draw.rect(surface, (255, 255, 255), self.btn_laser_rect, 2, border_radius=5)
        elif selected_type == "gun":
            pygame.draw.rect(surface, (255, 255, 255), self.btn_gun_rect, 2, border_radius=5)
        elif selected_type == "drone_station":
            pygame.draw.rect(surface, (255, 255, 255), self.btn_drone_rect, 2, border_radius=5)

        # Вывод статистики выделенной башни
        if selected_tower and selected_tower.alive():
            if selected_tower.tower_type == "drone_station":
                info_name = self.font.render(f"СТАНЦИЯ ДРОНОВ [Ур. {selected_tower.level}]", True, (240, 240, 240))
                current_speed = 5 if selected_tower.level == 1 else (8 if selected_tower.level == 2 else 12)
                info_stats = self.stat_font.render(f"Доставка патронов  |  Скорость дрона: {current_speed}", True,
                                                   (200, 200, 200))
                surface.blit(info_name, (self.screen_w // 2 - 150, self.rect.top + 25))
                surface.blit(info_stats, (self.screen_w // 2 - 150, self.rect.top + 55))

                cost = selected_tower.get_upgrade_cost()
                if cost:
                    pygame.draw.rect(surface, (230, 126, 34), self.upgrade_btn_rect, border_radius=6)
                    up_text = self.price_font.render("АПГРЕЙД", True, (255, 255, 255))
                    cost_text = self.price_font.render(f"Цена: {cost} $", True, (255, 215, 0))
                    next_speed = 8 if selected_tower.level == 1 else 12
                    buff_text = self.price_font.render(
                        f"Будет -> Ур.{selected_tower.level + 1} (Скорость дрона: {next_speed})", True, (46, 204, 113))
                    surface.blit(up_text, (
                    self.upgrade_btn_rect.centerx - up_text.get_width() // 2, self.upgrade_btn_rect.y + 12))
                    surface.blit(cost_text, (
                    self.upgrade_btn_rect.centerx - cost_text.get_width() // 2, self.upgrade_btn_rect.y + 34))
                    surface.blit(buff_text, (self.screen_w // 2 - 150, self.rect.top + 80))
                else:
                    max_text = self.font.render("МАКС. УРОВЕНЬ ДОСТИГНУТ", True, (46, 204, 113))
                    surface.blit(max_text, (self.screen_w - max_text.get_width() - 40, self.rect.top + 45))
            else:
                t_name = "ЛАЗЕРНАЯ ПУШКА" if selected_tower.tower_type == "laser" else "СКОРОСТРЕЛЬНЫЙ ПУЛЕМЕТ"
                info_name = self.font.render(f"{t_name} [Ур. {selected_tower.level}]", True, (240, 240, 240))
                info_stats = self.stat_font.render(
                    f"Урон: {selected_tower.damage}  |  Радиус: {selected_tower.range}  |  Патроны: {selected_tower.ammo}/{selected_tower.max_ammo}",
                    True, (200, 200, 200))
                surface.blit(info_name, (self.screen_w // 2 - 150, self.rect.top + 25))
                surface.blit(info_stats, (self.screen_w // 2 - 150, self.rect.top + 55))

                cost = selected_tower.get_upgrade_cost()
                if cost:
                    pygame.draw.rect(surface, (230, 126, 34), self.upgrade_btn_rect, border_radius=6)
                    up_text = self.price_font.render("АПГРЕЙД", True, (255, 255, 255))
                    cost_text = self.price_font.render(f"Цена: {cost} $", True, (255, 215, 0))
                    next_dmg = int(selected_tower.base_damage * (1 + selected_tower.level * 0.45))
                    next_rng = int(selected_tower.base_range * (1 + selected_tower.level * 0.2))
                    buff_text = self.price_font.render(
                        f"Будет -> Ур.{selected_tower.level + 1} (Урон: {next_dmg} / Рад: {next_rng})", True,
                        (46, 204, 113))
                    surface.blit(up_text, (
                    self.upgrade_btn_rect.centerx - up_text.get_width() // 2, self.upgrade_btn_rect.y + 12))
                    surface.blit(cost_text, (
                    self.upgrade_btn_rect.centerx - cost_text.get_width() // 2, self.upgrade_btn_rect.y + 34))
                    surface.blit(buff_text, (self.screen_w // 2 - 150, self.rect.top + 80))
                else:
                    max_text = self.font.render("МАКС. УРОВЕНЬ ДОСТИГНУТ", True, (46, 204, 113))
                    surface.blit(max_text, (self.screen_w - max_text.get_width() - 40, self.rect.top + 45))

        # Верхняя панель ресурсов
        pygame.draw.rect(surface, (30, 30, 35), self.top_panel_rect)
        pygame.draw.line(surface, (60, 60, 65), (0, 50), (self.screen_w, 50), 2)

        is_boss_wave = (wave % 5 == 0)
        w_color = (255, 50, 50) if is_boss_wave else (240, 240, 240)
        w_lbl = f"ВОЛНА: {wave} (БОСС)" if is_boss_wave else f"Волна: {wave}"

        money_text = self.font.render(f"Золото: {current_money} $", True, (255, 215, 0))
        surface.blit(money_text, (20, 13))

        wave_text = self.font.render(f"{w_lbl}   |   Врагов осталось: {enemies_left}", True, w_color)
        surface.blit(wave_text, (self.screen_w // 2 - wave_text.get_width() // 2, 13))

        base_text = self.font.render(f"Прочность Базы: {base_hp}/10", True, (255, 69, 0))
        surface.blit(base_text, (self.screen_w - base_text.get_width() - 20, 13))

    def draw_game_over(self, surface):
        overlay = pygame.Surface((self.screen_w, self.rect.bottom), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        go_text = self.game_over_font.render("ИГРА ОКОНЧЕНА", True, (255, 0, 0))
        sub_text = self.font.render("Нажмите ESC для выхода", True, (200, 200, 200))
        surface.blit(go_text, (self.screen_w // 2 - go_text.get_width() // 2, surface.get_height() // 2 - 50))
        surface.blit(sub_text, (self.screen_w // 2 - sub_text.get_width() // 2, surface.get_height() // 2 + 20))

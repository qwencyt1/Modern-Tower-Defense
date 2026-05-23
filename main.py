import pygame
import sys
import math
import random
from classes import Enemy, Road, Tower, BuildMenu, Base, Particle, SupplyDrone, DroneStation, EnvironmentObject

# Инициализация Pygame
pygame.init()

screen_info = pygame.display.Info()
WIDTH = screen_info.current_w
HEIGHT = screen_info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Tower Defence - Bosses & Variety")

BG_COLOR = (34, 120, 45)

BASE_X = WIDTH - 80
BASE_Y = int(HEIGHT * 0.45)

WAYPOINTS = [
    (-50, int(HEIGHT * 0.25)),
    (int(WIDTH * 0.4), int(HEIGHT * 0.25)),
    (int(WIDTH * 0.4), int(HEIGHT * 0.65)),
    (int(WIDTH * 0.75), int(HEIGHT * 0.65)),
    (BASE_X, BASE_Y),
    (WIDTH + 100, BASE_Y)
]

road = Road(WAYPOINTS)
menu = BuildMenu(WIDTH, HEIGHT)
player_base = Base(BASE_X, BASE_Y)

enemies_group = pygame.sprite.Group()
towers_group = pygame.sprite.Group()
particles_group = pygame.sprite.Group()
drones_group = pygame.sprite.Group()

# --- ГЕНЕРАЦИЯ ДЕКОРАТИВНОЙ КАРТЫ ---
environment_objects = []
object_types = ["tree_pine", "tree_oak", "bush", "stone"]

grass_texture = pygame.Surface((WIDTH, HEIGHT))
grass_texture.fill(BG_COLOR)
for _ in range(int(WIDTH * HEIGHT * 0.003)):
    tx = random.randint(0, WIDTH - 1)
    ty = random.randint(0, HEIGHT - 1)
    if 50 < ty < HEIGHT - 120:
        g_color = (random.randint(28, 40), random.randint(110, 135), random.randint(35, 55))
        pygame.draw.rect(grass_texture, g_color, (tx, ty, random.randint(1, 3), random.randint(2, 5)))

attempts = 0
while len(environment_objects) < 65 and attempts < 1000:
    attempts += 1
    rx = random.randint(40, WIDTH - 40)
    ry = random.randint(80, HEIGHT - 160)
    if road.get_distance_to_pos((rx, ry)) < 45: continue
    if player_base.rect.inflate(40, 40).collidepoint(rx, ry): continue

    obj_type = random.choice(object_types)
    environment_objects.append(EnvironmentObject(rx, ry, obj_type))

environment_objects.sort(key=lambda o: o.y)

# Экономика и Волны
money = 120
COSTS = {"laser": 30, "gun": 50, "drone_station": 60}

current_wave = 1
enemies_in_current_wave = 5
enemies_spawned_in_wave = 0
total_enemies_left = enemies_in_current_wave
enemy_health_modifier = 1.0

# Ссылка на текущего живого босса для BossBar UI
active_boss = None

wave_break = False
break_timer = 0

selected_tower_type = None
selected_tower_object = None
game_over = False
is_paused = False

SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, 2200)  # Чуть ускорим темп спавна

clock = pygame.time.Clock()
running = True

pause_font = pygame.font.SysFont("Arial", 60, bold=True)
pause_sub_font = pygame.font.SysFont("Arial", 24, bold=False)

while running:
    current_time = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if event.key == pygame.K_h and not game_over: is_paused = not is_paused

        if game_over or is_paused: continue

        if event.type == SPAWN_EVENT:
            if not wave_break and enemies_spawned_in_wave < enemies_in_current_wave:
                # ЛОГИКА ТИПОВЫХ ВОЛН
                if current_wave % 5 == 0:
                    # Каждая 5-я волна — это БОСС. Спавнится только 1 гигантский враг.
                    enemy_type = "boss"
                else:
                    # На обычных волнах расширяем разнообразие по мере роста сложности
                    pool = ["normal"]
                    if current_wave >= 2: pool.append("fast")
                    if current_wave >= 3: pool.append("shield")
                    if current_wave >= 4: pool.append("kamikaze")
                    enemy_type = random.choice(pool)

                new_enemy = Enemy(WAYPOINTS, enemy_health_modifier, enemy_type)
                enemies_group.add(new_enemy)
                enemies_spawned_in_wave += 1

                if enemy_type == "boss":
                    active_boss = new_enemy

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if menu.rect.collidepoint(mouse_pos):
                if menu.btn_laser_rect.collidepoint(mouse_pos):
                    selected_tower_type = None if selected_tower_type == "laser" else "laser"
                    selected_tower_object = None
                elif menu.btn_gun_rect.collidepoint(mouse_pos):
                    selected_tower_type = None if selected_tower_type == "gun" else "gun"
                    selected_tower_object = None
                elif menu.btn_drone_rect.collidepoint(mouse_pos):
                    selected_tower_type = None if selected_tower_type == "drone_station" else "drone_station"
                    selected_tower_object = None
                elif selected_tower_object and menu.upgrade_btn_rect and menu.upgrade_btn_rect.collidepoint(mouse_pos):
                    upgrade_cost = selected_tower_object.get_upgrade_cost()
                    if upgrade_cost and money >= upgrade_cost:
                        money -= upgrade_cost
                        selected_tower_object.upgrade()
            elif selected_tower_type is not None:
                current_cost = COSTS[selected_tower_type]
                if selected_tower_type == "drone_station":
                    allowed_by_road = not player_base.rect.collidepoint(mouse_pos)
                else:
                    allowed_by_road = road.is_near_road(mouse_pos) and not player_base.rect.collidepoint(mouse_pos)

                if money >= current_cost and allowed_by_road:
                    can_place = True
                    for tower in towers_group:
                        if math.hypot(mouse_pos[0] - tower.rect.centerx, mouse_pos[1] - tower.rect.centery) < 45:
                            can_place = False
                            break
                    if can_place:
                        if selected_tower_type == "drone_station":
                            new_tower = DroneStation(mouse_pos[0], mouse_pos[1])
                            new_drone = SupplyDrone(new_tower)
                            drones_group.add(new_drone)
                        else:
                            new_tower = Tower(mouse_pos[0], mouse_pos[1], selected_tower_type)
                        towers_group.add(new_tower)
                        money -= current_cost
                        selected_tower_type = None
            else:
                clicked_tower = None
                for tower in towers_group:
                    if tower.rect.collidepoint(mouse_pos):
                        clicked_tower = tower
                        break
                selected_tower_object = clicked_tower

    if player_base.hp <= 0:
        game_over = True

    if not game_over and not is_paused:
        for enemy in list(enemies_group):
            old_len = len(enemies_group)
            enemy_pos_x = enemy.rect.centerx
            enemy_pos_y = enemy.rect.centery
            enemy_reward = enemy.reward
            damage_to_inflict = enemy.base_damage_to_base

            was_killed = enemy.update()
            new_len = len(enemies_group)

            if new_len < old_len:
                total_enemies_left -= 1
                if was_killed:
                    money += enemy_reward
                    # Боссу нужно больше взрывных частиц!
                    p_count = 50 if enemy.enemy_type == "boss" else 15
                    for _ in range(p_count):
                        particles_group.add(Particle(enemy_pos_x, enemy_pos_y))
                else:
                    player_base.hp -= damage_to_inflict

        particles_group.update()
        drones_group.update(towers_group)

        if total_enemies_left <= 0 and not wave_break:
            wave_break = True
            break_timer = current_time + 4000

        if wave_break and current_time >= break_timer:
            wave_break = False
            current_wave += 1

            # Настройка модификатора здоровья на следующую волну
            if current_wave % 5 == 0:
                # Перед волной с боссом
                enemies_in_current_wave = 1
                enemy_health_modifier *= 1.4
            else:
                if (current_wave - 1) % 5 == 0:
                    # Возврат к нормальному количеству врагов после босса
                    enemies_in_current_wave = math.ceil(5 * (1.2 ** (current_wave // 2)))
                else:
                    enemies_in_current_wave = math.ceil(enemies_in_current_wave * 1.2)

                enemy_health_modifier *= 1.15

            enemies_spawned_in_wave = 0
            total_enemies_left = enemies_in_current_wave
            active_boss = None

        for tower in towers_group:
            tower.attack(enemies_group, current_time)

    # --- ОТРИСОВКА ИГРЫ ---
    screen.blit(grass_texture, (0, 0))
    road.draw(screen)

    for obj in environment_objects:
        obj.draw(screen, current_time)

    player_base.draw(screen)

    for tower in towers_group:
        tower.draw_custom(screen, current_time=current_time)

    for tower in towers_group:
        tower.draw_laser(screen)

    enemies_group.draw(screen)
    drones_group.draw(screen)

    for p in particles_group:
        p.draw_custom(screen)

    if not game_over and selected_tower_object and selected_tower_object.alive():
        menu.draw_range_preview(screen, selected_tower_object.rect.center, selected_tower_object.range, True)

    if not game_over and not is_paused and not menu.rect.collidepoint(
            mouse_pos) and not menu.top_panel_rect.collidepoint(mouse_pos):
        for enemy in enemies_group:
            enemy.draw_hover_hp(screen, mouse_pos)

    if not game_over and not is_paused and selected_tower_type is not None and not menu.rect.collidepoint(
            mouse_pos) and not menu.top_panel_rect.collidepoint(mouse_pos):
        current_cost = COSTS[selected_tower_type]
        if selected_tower_type == "drone_station":
            is_valid_spot = (money >= current_cost) and not player_base.rect.collidepoint(mouse_pos)
        else:
            is_valid_spot = road.is_near_road(mouse_pos) and (
                        money >= current_cost) and not player_base.rect.collidepoint(mouse_pos)

        if is_valid_spot:
            for tower in towers_group:
                if math.hypot(mouse_pos[0] - tower.rect.centerx, mouse_pos[1] - tower.rect.centery) < 45:
                    is_valid_spot = False
                    break

        current_range = 150 if selected_tower_type == "laser" else (220 if selected_tower_type == "gun" else 0)
        menu.draw_range_preview(screen, mouse_pos, current_range, is_valid_spot)

        if selected_tower_type == "drone_station":
            temp_tower = DroneStation(mouse_pos[0], mouse_pos[1])
        else:
            temp_tower = Tower(mouse_pos[0], mouse_pos[1], selected_tower_type)
        temp_tower.draw_custom(screen, mouse_pos[0], mouse_pos[1], alpha=140, current_time=current_time)

    # Отрисовка основного интерфейса меню
    menu.draw(screen, selected_tower_type, money, current_wave, total_enemies_left, max(0, player_base.hp),
              selected_tower_object)

    # Отрисовка Здоровья Босса (BossBar UI сверху), если он на экране
    if active_boss and active_boss.alive():
        menu.draw_boss_bar(screen, active_boss)

    if is_paused and not game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))
        p_text = pause_font.render("ПАУЗА", True, (255, 120, 0))
        ps_text = pause_sub_font.render("Нажмите H, чтобы продолжить", True, (255, 255, 255))
        screen.blit(p_text, (WIDTH // 2 - p_text.get_width() // 2, HEIGHT // 2 - 40))
        screen.blit(ps_text, (WIDTH // 2 - ps_text.get_width() // 2, HEIGHT // 2 + 30))

    if game_over:
        menu.draw_game_over(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

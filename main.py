
import pygame
import random
import sys
import os

# ==================================================
# 1. INITIAL SETUP
# ==================================================

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bike Racing Game")
clock = pygame.time.Clock()

# ==================================================
# 2. SOUND SETUP
# ==================================================

# Handle systems where audio is unavailable
try:
    pygame.mixer.init()
    SOUND_ENABLED = True
except pygame.error:
    SOUND_ENABLED = False

def load_sound(filename):
    if not SOUND_ENABLED:
        return None

    path = os.path.join("assets", "sounds", filename)

    try:
        return pygame.mixer.Sound(path)
    except (pygame.error, FileNotFoundError):
        print("Could not load sound:", filename)
        return None

engine_sound = load_sound("engine.wav")
crash_sound = load_sound("crash.wav")
start_sound = load_sound("start.wav")
acceleration_sound = load_sound("acceleration.wav")
gameover_sound = load_sound("gameover.wav")
pause_sound = load_sound("pause.wav")
restart_sound = load_sound("restart.wav")

engine_channel = None

# Background music
if SOUND_ENABLED:
    try:
        pygame.mixer.music.load(
            os.path.join("assets", "sounds", "background_music.mp3")
        )
        pygame.mixer.music.set_volume(0.35)
    except pygame.error:
        print("Could not load background music.")

def play_effect(sound, volume=1.0):
    if SOUND_ENABLED and sound is not None:
        sound.set_volume(volume)
        sound.play()

def start_engine():
    global engine_channel

    if SOUND_ENABLED and engine_sound is not None:
        if engine_channel is None or not engine_channel.get_busy():
            engine_channel = engine_sound.play(-1)
            if engine_channel:
                engine_channel.set_volume(0.3)

def stop_engine():
    global engine_channel

    if engine_channel is not None:
        engine_channel.stop()
        engine_channel = None

def start_background_music():
    if SOUND_ENABLED:
        try:
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

def stop_all_game_sounds():
    stop_engine()

    if SOUND_ENABLED:
        pygame.mixer.music.stop()

# ==================================================
# 3. COLOURS AND FONTS
# ==================================================

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 220, 0)
GREEN = (30, 180, 70)
BLUE = (40, 160, 230)
RED = (220, 55, 55)
GREY = (150, 150, 150)
DARK = (25, 30, 35)

title_font = pygame.font.Font(None, 75)
font = pygame.font.Font(None, 38)
small_font = pygame.font.Font(None, 27)

# ==================================================
# 4. IMAGE LOADING
# ==================================================

def load_image(filename, size):
    path = os.path.join("assets", "images", filename)
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(image, size)

grass_img = load_image("grass.png", (64, 64))
road_img = load_image("road.png", (360, 64))

player_img = load_image("player_bike.png", (65, 100))

enemy_images = [
    load_image("enemy_bike.png", (65, 100)),
    load_image("enemy_bike2.png", (65, 100))
]

player_bikes = [player_img, enemy_images[0], enemy_images[1]]
bike_names = ["Blue Bike", "Red Bike", "Green Bike"]
selected_bike = 0

cone_img = load_image("cone.png", (40, 55))
barrier_img = load_image("barrier.png", (60, 40))
oil_img = load_image("oil.png", (60, 35))

# ==================================================
# 5. HIGH SCORE
# ==================================================

HIGH_SCORE_FILE = "highscore.txt"

def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, "r") as file:
            return int(file.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_high_score(value):
    with open(HIGH_SCORE_FILE, "w") as file:
        file.write(str(value))

high_score = load_high_score()

# ==================================================
# 6. GAME SETTINGS
# ==================================================

road_width = 360
road_x = (WIDTH - road_width) // 2

lanes = [
    road_x + 30,
    road_x + 147,
    road_x + 265
]

road_y = 0

background_options = ["Classic", "Desert", "Snow"]
selected_background = 0

difficulty_options = ["Easy", "Medium", "Hard"]
selected_difficulty = 1

difficulty_settings = {
    "Easy": {"speed": 0.8, "spawn": 1.3},
    "Medium": {"speed": 1.0, "spawn": 1.0},
    "Hard": {"speed": 1.25, "spawn": 0.8}
}

show_speedometer = True

# ==================================================
# 7. PLAYER AND GAME VARIABLES
# ==================================================

bike_x = road_x + (road_width - 65) // 2
bike_y = 440

player_speed = 6

enemies = []
obstacles = []

score = 0
game_state = "menu"

last_enemy_spawn = 0
last_obstacle_spawn = 0

oil_until = 0

nitro_energy = 100
nitro_active = False
previous_nitro_active = False

# ==================================================
# 8. BUTTONS
# ==================================================

play_button = pygame.Rect(300, 175, 200, 55)
bike_button = pygame.Rect(300, 245, 200, 45)
background_button = pygame.Rect(300, 300, 200, 45)
difficulty_button = pygame.Rect(300, 355, 200, 45)
settings_button = pygame.Rect(300, 410, 200, 45)

back_button = pygame.Rect(300, 490, 200, 50)

left_button = pygame.Rect(220, 310, 70, 55)
right_button = pygame.Rect(510, 310, 70, 55)

settings_toggle = pygame.Rect(320, 315, 160, 55)

# ==================================================
# 9. DRAWING FUNCTIONS
# ==================================================

def draw_text(text, font_style, color, x, y):
    image = font_style.render(text, True, color)
    rect = image.get_rect(center=(x, y))
    screen.blit(image, rect)

def draw_panel(x, y, width, height):
    pygame.draw.rect(
        screen, DARK, (x, y, width, height), border_radius=12
    )
    pygame.draw.rect(
        screen, GREY, (x, y, width, height), 2, border_radius=12
    )

def draw_button(rect, text, color=GREEN):
    pygame.draw.rect(screen, color, rect, border_radius=10)
    draw_text(text, small_font, WHITE, rect.centerx, rect.centery)

# ==================================================
# 10. BACKGROUND
# ==================================================

def draw_background():

    if background_options[selected_background] == "Classic":
        for x in range(0, WIDTH, 64):
            for y in range(0, HEIGHT, 64):
                screen.blit(grass_img, (x, y))

    elif background_options[selected_background] == "Desert":
        screen.fill((205, 165, 100))

        for x in range(20, WIDTH, 75):
            for y in range(20, HEIGHT, 75):
                pygame.draw.circle(screen, (185, 140, 80), (x, y), 4)

    elif background_options[selected_background] == "Snow":
        screen.fill((190, 220, 235))

        for x in range(20, WIDTH, 70):
            for y in range(20, HEIGHT, 70):
                pygame.draw.circle(screen, WHITE, (x, y), 4)

    for y in range(-64 + road_y, HEIGHT, 64):
        screen.blit(road_img, (road_x, y))

    pygame.draw.line(
        screen, WHITE, (road_x + 5, 0),
        (road_x + 5, HEIGHT), 4
    )

    pygame.draw.line(
        screen, WHITE, (road_x + road_width - 5, 0),
        (road_x + road_width - 5, HEIGHT), 4
    )

# ==================================================
# 11. GAME RESET AND START
# ==================================================

def reset_game():
    global bike_x, bike_y, road_y, enemies, obstacles, score
    global last_enemy_spawn, last_obstacle_spawn
    global oil_until, nitro_energy, nitro_active
    global previous_nitro_active, high_score

    bike_x = road_x + (road_width - 65) // 2
    bike_y = 440

    road_y = 0

    enemies = []
    obstacles = []

    score = 0
    oil_until = 0

    nitro_energy = 100
    nitro_active = False
    previous_nitro_active = False

    now = pygame.time.get_ticks()

    last_enemy_spawn = now
    last_obstacle_spawn = now

    high_score = load_high_score()

def start_game(restarting=False):
    global game_state

    reset_game()
    game_state = "playing"

    stop_all_game_sounds()

    if restarting:
        play_effect(restart_sound)
    else:
        play_effect(start_sound)

    start_background_music()

def end_game():
    global game_state

    if game_state != "gameover":
        game_state = "gameover"

        stop_engine()

        if SOUND_ENABLED:
            pygame.mixer.music.stop()

        play_effect(crash_sound)
        play_effect(gameover_sound)

def update_high_score():
    global high_score

    if score > high_score:
        high_score = score
        save_high_score(high_score)

# ==================================================
# 12. MENU SCREEN
# ==================================================

def draw_menu():
    draw_background()

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    draw_panel(180, 65, 440, 480)

    draw_text("BIKE RACING", title_font, YELLOW, WIDTH // 2, 115)

    draw_button(play_button, "PLAY")
    draw_button(bike_button, "SELECT BIKE", BLUE)
    draw_button(background_button, "BACKGROUND", BLUE)
    draw_button(difficulty_button, "DIFFICULTY", BLUE)
    draw_button(settings_button, "SETTINGS", BLUE)

    draw_text(
        "BEST SCORE: " + str(high_score),
        small_font, YELLOW, WIDTH // 2, 475
    )

    draw_text(
        "Choose your racing experience!",
        small_font, WHITE, WIDTH // 2, 520
    )

# ==================================================
# 13. BIKE SELECTION
# ==================================================

def draw_bike_selection():
    draw_background()

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(170)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    draw_panel(160, 100, 480, 420)

    draw_text(
        "SELECT YOUR BIKE", title_font,
        YELLOW, WIDTH // 2, 180
    )

    preview = pygame.transform.scale(
        player_bikes[selected_bike], (100, 150)
    )

    screen.blit(preview, (WIDTH // 2 - 50, 235))

    draw_button(left_button, "<", BLUE)
    draw_button(right_button, ">", BLUE)

    draw_text(
        bike_names[selected_bike],
        font, WHITE, WIDTH // 2, 415
    )

    draw_button(back_button, "BACK")

# ==================================================
# 14. BACKGROUND SELECTION
# ==================================================

def draw_background_selection():
    draw_background()

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(170)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    draw_panel(160, 120, 480, 360)

    draw_text(
        "SELECT BACKGROUND", title_font,
        YELLOW, WIDTH // 2, 195
    )

    draw_button(left_button, "<", BLUE)
    draw_button(right_button, ">", BLUE)

    draw_text(
        background_options[selected_background],
        font, WHITE, WIDTH // 2, 340
    )

    draw_button(back_button, "BACK")

# ==================================================
# 15. DIFFICULTY SELECTION
# ==================================================

def draw_difficulty_selection():
    draw_background()

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(170)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    draw_panel(160, 120, 480, 360)

    draw_text(
        "SELECT DIFFICULTY", title_font,
        YELLOW, WIDTH // 2, 195
    )

    draw_button(left_button, "<", BLUE)
    draw_button(right_button, ">", BLUE)

    draw_text(
        difficulty_options[selected_difficulty],
        font, WHITE, WIDTH // 2, 340
    )

    draw_text(
        "Choose your challenge",
        small_font, WHITE, WIDTH // 2, 390
    )

    draw_button(back_button, "BACK")

# ==================================================
# 16. SETTINGS
# ==================================================

def draw_settings():
    draw_background()

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(170)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    draw_panel(140, 100, 520, 420)

    draw_text("SETTINGS", title_font, YELLOW, WIDTH // 2, 175)

    if show_speedometer:
        toggle_text = "ON"
        toggle_color = GREEN
    else:
        toggle_text = "OFF"
        toggle_color = RED

    draw_text("Speedometer", font, WHITE, WIDTH // 2, 270)

    draw_button(settings_toggle, toggle_text, toggle_color)

    draw_text(
        "Arrow Keys - Move",
        small_font, WHITE, WIDTH // 2, 395
    )

    draw_text(
        "SPACE - Nitro | P - Pause",
        small_font, WHITE, WIDTH // 2, 430
    )

    draw_button(back_button, "BACK")

# ==================================================
# 17. PAUSE SCREEN
# ==================================================

def draw_pause():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(190)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    draw_panel(220, 200, 360, 220)

    draw_text("PAUSED", title_font, YELLOW, WIDTH // 2, 270)
    draw_text("P - Resume", font, WHITE, WIDTH // 2, 340)

    draw_text(
        "M - Main Menu",
        small_font, WHITE, WIDTH // 2, 390
    )

# ==================================================
# 18. GAME OVER SCREEN
# ==================================================

def draw_game_over():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    draw_panel(180, 140, 440, 330)

    draw_text("GAME OVER", title_font, RED, WIDTH // 2, 210)

    draw_text(
        "FINAL SCORE: " + str(score),
        font, WHITE, WIDTH // 2, 290
    )

    draw_text(
        "BEST SCORE: " + str(high_score),
        font, YELLOW, WIDTH // 2, 340
    )

    draw_text(
        "R - Restart",
        small_font, WHITE, WIDTH // 2, 405
    )

    draw_text(
        "M - Menu | Q - Quit",
        small_font, WHITE, WIDTH // 2, 440
    )

# ==================================================
# 19. SPEEDOMETER
# ==================================================

def draw_speedometer(speed):
    if not show_speedometer:
        return

    draw_panel(610, 15, 170, 85)

    draw_text("SPEED", small_font, WHITE, 695, 35)

    draw_text(
        str(int(speed)) + " km/h",
        font, YELLOW, 695, 70
    )

# ==================================================
# 20. NITRO METER
# ==================================================

def draw_nitro_meter():
    draw_panel(15, 105, 230, 75)

    draw_text(
        "NITRO BOOST",
        small_font, WHITE, 130, 123
    )

    pygame.draw.rect(
        screen, GREY, (35, 140, 190, 18),
        border_radius=8
    )

    fill_width = int(190 * nitro_energy / 100)

    if fill_width > 0:
        meter_color = BLUE if nitro_active else GREEN

        pygame.draw.rect(
            screen, meter_color,
            (35, 140, fill_width, 18),
            border_radius=8
        )

    draw_text(
        str(int(nitro_energy)) + "%",
        small_font, WHITE, 130, 165
    )

# ==================================================
# 21. MAIN GAME LOOP
# ==================================================

running = True

while running:

    dt = clock.tick(60) / 1000
    now = pygame.time.get_ticks()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # ------------------------------------------
        # MOUSE CONTROLS
        # ------------------------------------------

        if event.type == pygame.MOUSEBUTTONDOWN:

            mouse = event.pos

            if game_state == "menu":

                if play_button.collidepoint(mouse):
                    start_game()

                elif bike_button.collidepoint(mouse):
                    game_state = "bikes"

                elif background_button.collidepoint(mouse):
                    game_state = "background"

                elif difficulty_button.collidepoint(mouse):
                    game_state = "difficulty"

                elif settings_button.collidepoint(mouse):
                    game_state = "settings"

            elif game_state == "bikes":

                if left_button.collidepoint(mouse):
                    selected_bike = (
                        selected_bike - 1
                    ) % len(player_bikes)

                elif right_button.collidepoint(mouse):
                    selected_bike = (
                        selected_bike + 1
                    ) % len(player_bikes)

                elif back_button.collidepoint(mouse):
                    game_state = "menu"

            elif game_state == "background":

                if left_button.collidepoint(mouse):
                    selected_background = (
                        selected_background - 1
                    ) % len(background_options)

                elif right_button.collidepoint(mouse):
                    selected_background = (
                        selected_background + 1
                    ) % len(background_options)

                elif back_button.collidepoint(mouse):
                    game_state = "menu"

            elif game_state == "difficulty":

                if left_button.collidepoint(mouse):
                    selected_difficulty = (
                        selected_difficulty - 1
                    ) % len(difficulty_options)

                elif right_button.collidepoint(mouse):
                    selected_difficulty = (
                        selected_difficulty + 1
                    ) % len(difficulty_options)

                elif back_button.collidepoint(mouse):
                    game_state = "menu"

            elif game_state == "settings":

                if settings_toggle.collidepoint(mouse):
                    show_speedometer = not show_speedometer

                elif back_button.collidepoint(mouse):
                    game_state = "menu"

        # ------------------------------------------
        # KEYBOARD CONTROLS
        # ------------------------------------------

        if event.type == pygame.KEYDOWN:

            if game_state == "menu":

                if event.key == pygame.K_RETURN:
                    start_game()

                elif event.key == pygame.K_q:
                    running = False

            elif game_state in (
                "bikes", "background", "difficulty", "settings"
            ):

                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"

                elif game_state == "bikes":

                    if event.key == pygame.K_LEFT:
                        selected_bike = (
                            selected_bike - 1
                        ) % len(player_bikes)

                    elif event.key == pygame.K_RIGHT:
                        selected_bike = (
                            selected_bike + 1
                        ) % len(player_bikes)

                elif game_state == "background":

                    if event.key == pygame.K_LEFT:
                        selected_background = (
                            selected_background - 1
                        ) % len(background_options)

                    elif event.key == pygame.K_RIGHT:
                        selected_background = (
                            selected_background + 1
                        ) % len(background_options)

                elif game_state == "difficulty":

                    if event.key == pygame.K_LEFT:
                        selected_difficulty = (
                            selected_difficulty - 1
                        ) % len(difficulty_options)

                    elif event.key == pygame.K_RIGHT:
                        selected_difficulty = (
                            selected_difficulty + 1
                        ) % len(difficulty_options)

                elif game_state == "settings":

                    if event.key == pygame.K_SPACE:
                        show_speedometer = not show_speedometer

            elif game_state == "playing":

                if event.key == pygame.K_p:

                    game_state = "paused"

                    stop_engine()

                    if SOUND_ENABLED:
                        pygame.mixer.music.pause()

                    play_effect(pause_sound)

            elif game_state == "paused":

                if event.key == pygame.K_p:

                    game_state = "playing"

                    if SOUND_ENABLED:
                        pygame.mixer.music.unpause()

                elif event.key == pygame.K_m:

                    game_state = "menu"
                    stop_all_game_sounds()

            elif game_state == "gameover":

                if event.key == pygame.K_r:
                    start_game(restarting=True)

                elif event.key == pygame.K_m:
                    game_state = "menu"
                    stop_all_game_sounds()

                elif event.key == pygame.K_q:
                    running = False

    # ==================================================
    # 22. SCREEN SELECTION
    # ==================================================

    if game_state == "menu":

        stop_engine()
        draw_menu()

    elif game_state == "bikes":

        draw_bike_selection()

    elif game_state == "background":

        draw_background_selection()

    elif game_state == "difficulty":

        draw_difficulty_selection()

    elif game_state == "settings":

        draw_settings()

    elif game_state in ("playing", "paused", "gameover"):

        # ==============================================
        # 23. PLAYING LOGIC
        # ==============================================

        if game_state == "playing":

            start_engine()

            difficulty_name = difficulty_options[selected_difficulty]
            settings = difficulty_settings[difficulty_name]

            difficulty_speed = settings["speed"]
            spawn_multiplier = settings["spawn"]

            enemy_speed = min(
                (5 + score * 0.15) * difficulty_speed, 14
            )

            road_speed = min(
                (5 + score * 0.08) * difficulty_speed, 11
            )

            enemy_delay = max(
                int((1500 - score * 15) / spawn_multiplier), 650
            )

            obstacle_delay = max(
                int((1900 - score * 12) / spawn_multiplier), 850
            )

            keys = pygame.key.get_pressed()

            # NITRO
            nitro_active = (
                keys[pygame.K_SPACE] and nitro_energy > 0
            )

            # Play acceleration sound only when nitro starts
            if nitro_active and not previous_nitro_active:
                play_effect(acceleration_sound)

            previous_nitro_active = nitro_active

            if nitro_active:
                nitro_energy -= 45 * dt
            else:
                nitro_energy += 22 * dt

            nitro_energy = max(0, min(100, nitro_energy))

            if nitro_active:
                current_player_speed = 8
                current_road_speed = road_speed + 3
                current_enemy_speed = enemy_speed + 3

            else:
                current_player_speed = player_speed
                current_road_speed = road_speed
                current_enemy_speed = enemy_speed

            # OIL EFFECT
            if now < oil_until:
                current_player_speed = min(current_player_speed, 3)

            # PLAYER MOVEMENT
            if keys[pygame.K_LEFT]:
                bike_x -= current_player_speed

            if keys[pygame.K_RIGHT]:
                bike_x += current_player_speed

            if keys[pygame.K_UP]:
                bike_y -= current_player_speed

            if keys[pygame.K_DOWN]:
                bike_y += current_player_speed

            bike_x = max(road_x + 5, bike_x)
            bike_x = min(road_x + road_width - 70, bike_x)

            bike_y = max(0, min(HEIGHT - 100, bike_y))

            # ROAD MOVEMENT
            road_y = (road_y + int(current_road_speed)) % 64

            # ENEMY SPAWNING
            if now - last_enemy_spawn >= enemy_delay:

                enemy_x = random.choice(lanes)
                enemy_img = random.choice(enemy_images)

                enemies.append({
                    "image": enemy_img,
                    "rect": pygame.Rect(enemy_x, -110, 60, 95)
                })

                last_enemy_spawn = now

            # OBSTACLE SPAWNING
            if now - last_obstacle_spawn >= obstacle_delay:

                obstacle_type = random.choice(
                    ["cone", "barrier", "oil"]
                )

                if obstacle_type == "cone":
                    image = cone_img
                    width, height = 40, 55

                elif obstacle_type == "barrier":
                    image = barrier_img
                    width, height = 60, 40

                else:
                    image = oil_img
                    width, height = 60, 35

                lane_x = random.choice(lanes)

                obstacles.append({
                    "image": image,
                    "rect": pygame.Rect(
                        lane_x + (65 - width) // 2,
                        -70, width, height
                    ),
                    "type": obstacle_type
                })

                last_obstacle_spawn = now

            # MOVE ENEMIES
            for enemy in enemies[:]:

                enemy["rect"].y += int(current_enemy_speed)

                if enemy["rect"].top > HEIGHT:
                    enemies.remove(enemy)
                    score += 1

            # MOVE OBSTACLES
            for obstacle in obstacles[:]:

                obstacle["rect"].y += int(current_road_speed)

                if obstacle["rect"].top > HEIGHT:
                    obstacles.remove(obstacle)
                    score += 1

            # COLLISION CHECK
            player_rect = pygame.Rect(
                bike_x, bike_y, 65, 100
            )

            for enemy in enemies:

                if player_rect.colliderect(enemy["rect"]):
                    end_game()
                    break

            if game_state == "playing":

                for obstacle in obstacles[:]:

                    if player_rect.colliderect(obstacle["rect"]):

                        if obstacle["type"] == "oil":

                            oil_until = now + 1500
                            obstacles.remove(obstacle)

                        else:
                            end_game()
                            break

            update_high_score()

        # ==============================================
        # 24. DRAW GAME
        # ==============================================

        draw_background()

        for enemy in enemies:
            screen.blit(enemy["image"], enemy["rect"])

        for obstacle in obstacles:
            screen.blit(obstacle["image"], obstacle["rect"])

        screen.blit(
            player_bikes[selected_bike],
            (bike_x, bike_y)
        )

        draw_panel(15, 15, 210, 75)

        draw_text(
            "SCORE: " + str(score),
            font, WHITE, 120, 40
        )

        draw_text(
            "BEST: " + str(high_score),
            small_font, YELLOW, 120, 70
        )

        if nitro_active:
            displayed_speed = (road_speed + 3) * 20
        else:
            displayed_speed = road_speed * 20

        draw_speedometer(displayed_speed)
        draw_nitro_meter()

        if game_state == "playing":

            draw_text(
                "P - PAUSE",
                small_font, WHITE, 695, 125
            )

            if nitro_active:
                draw_text(
                    "NITRO ACTIVE!",
                    font, BLUE, WIDTH // 2, 45
                )

            if now < oil_until:
                draw_text(
                    "SLOW DOWN!",
                    font, YELLOW, WIDTH // 2, 105
                )

        if game_state == "paused":
            draw_pause()

        elif game_state == "gameover":
            draw_game_over()

    pygame.display.update()

# ==================================================
# 25. QUIT GAME
# ==================================================

stop_all_game_sounds()
pygame.quit()
sys.exit()

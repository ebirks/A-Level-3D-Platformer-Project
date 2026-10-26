import math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import time
import math
import sqlite3
from datetime import datetime

# Constants
WINDOW_WIDTH = 1536
WINDOW_HEIGHT = 864
PLAYER_START_POS = [0, 2, 0]
GROUND_SIZE = 7
GRAVITY = -0.02
PLAYER_SPEED = 0.1
JUMP_POWER = 0.2
BOOST_POWER = 0.4
FINISH_COLOR = (1.0, 0.843, 0.0)  # Gold color for finish platform
LEVEL_COMPLETED = False  # Track if level is completed
MAX_CHECKPOINT_RESETS = 3
PLATFORMS = [
    {'pos': [2, 1, -2], 'size': [2, 0.2, 2], 'trap': False, 'boost': False, 'checkpoint': False},    # First platform
    {'pos': [-2, 2, -3], 'size': [2, 0.2, 2], 'trap': True, 'boost': False, 'checkpoint': False},     # Trap platform
    {'pos': [2, 3, -4], 'size': [2, 0.2, 2], 'trap': False, 'boost': True, 'checkpoint': False},      # Boost platform
    {'pos': [2, 7, -3], 'size': [2, 0.2, 2], 'trap': False, 'boost': False, 'checkpoint': False},     # Fourth platform
    {'pos': [3, 8, -1], 'size': [2, 0.2, 2], 'trap': False, 'boost': False, 'checkpoint': False},     # Fifth platform
    {'pos': [1, 9, 1], 'size': [2, 0.2, 2], 'trap': False, 'boost': False, 'checkpoint': True},      # Checkpoint platform
    {'pos': [-1, 10, 2], 'size': [2, 0.2, 2], 'trap': True, 'boost': False, 'checkpoint': False},      # Trap platform
    {'pos': [1, 11, -1], 'size': [2, 0.2, 2], 'trap': False, 'boost': False, 'checkpoint': False},      # Sixth platform
    {'pos': [-2, 12, -1], 'size': [2, 0.2, 2], 'trap': False, 'boost': False, 'checkpoint': False},      # Seventh platform
    {'pos': [-4, 13, 2], 'size': [2, 0.2, 2], 'trap': False, 'boost': True, 'checkpoint': False},      # Boost platform
    {'pos': [0, 16, 3], 'size': [2, 0.2, 2], 'trap': True, 'boost': False, 'checkpoint': False},      # Trap platform
    {'pos': [-2, 17, 0], 'size': [2, 0.2, 2], 'trap': False, 'boost': False, 'checkpoint': True},      # Checkpoint platform
    {'pos': [-5, 18, 1], 'size': [2, 0.2, 2], 'trap': False, 'boost': False, 'checkpoint': False},      # Eighth platform
    {'pos': [-3, 19, 2], 'size': [2, 0.2, 2], 'trap': False, 'boost': False, 'checkpoint': False},      # Ninth platform
    {'pos': [-1, 20, 4], 'size': [2, 0.2, 2], 'trap': False, 'boost': True, 'checkpoint': False},      # Boost platform
    {'pos': [-1, 24, 3], 'size': [2, 0.2, 2], 'trap': True, 'boost': False, 'checkpoint': False},      # Trap platform
    {'pos': [0, 25, 0], 'size': [2, 0.2, 2], 'trap': False, 'boost': False, 'checkpoint': False, 'finish': True},  # Finish platform
]
SCORE_SAVED = False

# Setup pygame and OpenGL
pygame.init()
display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF | OPENGL)
glEnable(GL_DEPTH_TEST)
glEnable(GL_TEXTURE_2D)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glClearColor(0.5, 0.5, 1.0, 1.0)  # This is your blue background
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(45, (WINDOW_WIDTH / WINDOW_HEIGHT), 0.1, 50.0)
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()
glTranslatef(0.0, 0.0, -5)

# Set up movement and physics
player_pos = [0, 2, 0]  # Start position of the player
player_velocity = [0, 0, 0]
player_speed = 0.1
jump_power = 0.2
gravity = -0.02
is_jumping = False
is_paused = False
start_time = time.time()
elapsed_time = 0
stored_time = 0
pause_start_time = 0

# Ground settings
ground_texture = None

#trap settings
trap_timers = {}  # Dictionary to store trap activation times
TRAP_DURATION = 1.5  # Seconds before trap disappears

#camera settings
camera_angle_x = 0  # Camera rotation around Y axis (left/right)
camera_angle_y = 0  # Camera rotation around X axis (up/down)
camera_sensitivity = 0.003  # Adjust this to change mouse sensitivity
player_rotation = 0 # Track player cube rotation

# Checkpoint settings
CHECKPOINT_COLOR = (0.2, 0.8, 0.8)  # Cyan-ish color for checkpoint platforms
current_checkpoint = None  # Store the last touched checkpoint position
checkpoint_resets_remaining = MAX_CHECKPOINT_RESETS


def load_texture(filename):
    try:
        # Print current working directory to help with debugging
        import os
        print(f"Current working directory: {os.getcwd()}")
        print(f"Attempting to load texture: {filename}")

        texture = glGenTextures(1)
        img = pygame.image.load(filename)

        # Print texture information
        print(f"Image size: {img.get_size()}")
        print(f"Image format: {img.get_bitsize()}-bit")

        img = pygame.transform.flip(img, False, True)
        img_data = pygame.image.tostring(img, "RGBA", 1)

        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.get_width(), img.get_height(),
                     0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

        print(f"Successfully loaded texture: {texture}")
        return texture
    except pygame.error as e:
        print(f"Couldn't load texture {filename}: {e}")
        print("Make sure the image file exists and is in the correct format")
        return None
    except Exception as e:
        print(f"Unexpected error loading texture: {e}")
        return None


def draw_ground():
    if ground_texture is None:
        # Fallback color if texture isn't loaded
        glDisable(GL_TEXTURE_2D)
        glColor3f(0.0, 0.8, 0.0)  # Green ground
    else:
        glEnable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)  # White color to not tint texture
        glBindTexture(GL_TEXTURE_2D, ground_texture)

    glBegin(GL_QUADS)
    # Ground plane with texture coordinates
    glTexCoord2f(0.0, 0.0)
    glVertex3f(-7, 0, 7)  # Near left
    glTexCoord2f(5.0, 0.0)
    glVertex3f(7, 0, 7)   # Near right
    glTexCoord2f(5.0, 5.0)
    glVertex3f(7, 0, -7)  # Far right
    glTexCoord2f(0.0, 5.0)
    glVertex3f(-7, 0, -7) # Far left
    glEnd()

    glDisable(GL_TEXTURE_2D)


def draw_platforms():
    current_time = time.time()
    for platform in PLATFORMS:
        platform_pos = tuple(platform['pos'])  # Convert list to tuple
        # Skip drawing if it's a triggered trap that has expired
        if platform.get('trap') and platform_pos in trap_timers:
            if current_time - trap_timers[platform_pos] > TRAP_DURATION:
                continue
        glPushMatrix()
        glTranslatef(*platform['pos'])
        glScalef(*platform['size'])
        glBegin(GL_QUADS)

        # Set color based on platform type
        if platform.get('trap'):
            glColor3f(0.8, 0.2, 0.2)  # Red for trap platforms
        elif platform.get('boost'):
            glColor3f(0.2, 0.8, 0.2)  # Green for boost platforms
        elif platform.get('checkpoint'):
            glColor3f(*CHECKPOINT_COLOR)  # Cyan for checkpoint platforms
        elif platform.get('finish'):
            glColor3f(*FINISH_COLOR)  # Gold for finish platform
        else:
            glColor3f(2.0, 0.5, 1.0)  # Gray for regular platforms

        # Top face
        glVertex3f(-0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5, 0.5)

        # Bottom face
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, 0.5)
        glVertex3f(-0.5, -0.5, 0.5)

        # Front face
        glVertex3f(-0.5, -0.5, 0.5)
        glVertex3f(0.5, -0.5, 0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5, 0.5)

        # Back face
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(-0.5, 0.5, -0.5)

        # Right face
        glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(0.5, -0.5, 0.5)

        # Left face
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(-0.5, 0.5, -0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        glVertex3f(-0.5, -0.5, 0.5)

        glEnd()
        glPopMatrix()


def draw_walls():
    wall_height = 25.0  # Height of the walls
    ground_size = 7.0   # Size of the ground (matches your GROUND_SIZE)

    glColor3f(0.5, 0.5, 0.5)  # Gray color for walls
    glBegin(GL_QUADS)

    # North wall
    glVertex3f(-ground_size, 0, -ground_size)
    glVertex3f(ground_size, 0, -ground_size)
    glVertex3f(ground_size, wall_height, -ground_size)
    glVertex3f(-ground_size, wall_height, -ground_size)

    # South wall
    glVertex3f(-ground_size, 0, ground_size)
    glVertex3f(ground_size, 0, ground_size)
    glVertex3f(ground_size, wall_height, ground_size)
    glVertex3f(-ground_size, wall_height, ground_size)

    # East wall
    glVertex3f(ground_size, 0, -ground_size)
    glVertex3f(ground_size, 0, ground_size)
    glVertex3f(ground_size, wall_height, ground_size)
    glVertex3f(ground_size, wall_height, -ground_size)

    # West wall
    glVertex3f(-ground_size, 0, -ground_size)
    glVertex3f(-ground_size, 0, ground_size)
    glVertex3f(-ground_size, wall_height, ground_size)
    glVertex3f(-ground_size, wall_height, -ground_size)

    glEnd()


def init_mouse_handling():
    """Initializes mouse handling by hiding the cursor and locking it to the center of the window."""
    pygame.mouse.set_visible(False)  # Hide the mouse cursor
    pygame.mouse.set_pos(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)  # Recenter the mouse at the center of the screen


def handle_camera():
    global camera_angle_x, camera_angle_y, player_rotation

    # Get mouse movement
    mouse_rel = pygame.mouse.get_rel()

    # Apply the mouse movement to the camera angles
    camera_angle_x -= mouse_rel[0] * camera_sensitivity
    camera_angle_y -= mouse_rel[1] * camera_sensitivity

    # Limit vertical camera rotation
    camera_angle_y = max(min(camera_angle_y, math.pi / 3), -math.pi / 3)

    # Sync player rotation with camera angle
    player_rotation = camera_angle_x

    # Recenter the mouse after processing the movement to prevent it from leaving the window
    pygame.mouse.set_pos(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

    # Calculate camera position and look direction (unchanged from your original code)
    camera_distance = 5
    dir_x = math.cos(camera_angle_y) * math.sin(camera_angle_x)
    dir_y = math.sin(camera_angle_y)
    dir_z = math.cos(camera_angle_y) * math.cos(camera_angle_x)
    camera_x = player_pos[0] + camera_distance * dir_x
    camera_y = player_pos[1] + camera_distance * dir_y
    camera_z = player_pos[2] + camera_distance * dir_z

    if camera_y < 0.5:
        camera_y = 0.5

    # Camera collision detection (unchanged from your original code)
    wall_buffer = 0.5
    if camera_x > GROUND_SIZE - wall_buffer:
        camera_x = GROUND_SIZE - wall_buffer
    if camera_x < -GROUND_SIZE + wall_buffer:
        camera_x = -GROUND_SIZE + wall_buffer
    if camera_z > GROUND_SIZE - wall_buffer:
        camera_z = GROUND_SIZE - wall_buffer
    if camera_z < -GROUND_SIZE + wall_buffer:
        camera_z = -GROUND_SIZE + wall_buffer

    # Look at the cube's position
    glLoadIdentity()
    gluLookAt(
        camera_x, camera_y, camera_z,
        player_pos[0], player_pos[1], player_pos[2],
        0, 1, 0
    )


def handle_movement():
    global player_pos, player_velocity, is_jumping, is_paused, current_checkpoint, LEVEL_COMPLETED
    keys = pygame.key.get_pressed()

    if not is_paused:
        # Calculate movement direction based on cube's rotation
        forward_vec = [math.sin(player_rotation), 0, math.cos(player_rotation)]
        right_vec = [math.cos(player_rotation), 0, -math.sin(player_rotation)]

        # Movement Controls always relative to cube's facing
        if keys[K_w]:
            player_pos[0] -= forward_vec[0] * player_speed
            player_pos[2] -= forward_vec[2] * player_speed
        if keys[K_s]:
            player_pos[0] += forward_vec[0] * player_speed
            player_pos[2] += forward_vec[2] * player_speed
        if keys[K_a]:
            player_pos[0] -= right_vec[0] * player_speed
            player_pos[2] -= right_vec[2] * player_speed
        if keys[K_d]:
            player_pos[0] += right_vec[0] * player_speed
            player_pos[2] += right_vec[2] * player_speed

        # Jumping
        if not is_jumping and keys[K_SPACE]:
            player_velocity[1] = jump_power
            is_jumping = True

        # Apply gravity
        player_velocity[1] += gravity
        player_pos[1] += player_velocity[1]

        # Check for collisions with ground
        if player_pos[1] <= 0.5:
            player_pos[1] = 0.5
            is_jumping = False
            player_velocity[1] = 0

        # Check for collisions with all platforms
        collision_offset = 0.4
        current_time = time.time()

        for platform in PLATFORMS:
            platform_pos = tuple(platform['pos'])  # Convert list to tuple
            # Skip collision check if it's a triggered trap that has expired
            if platform.get('trap') and platform_pos in trap_timers:
                if current_time - trap_timers[platform_pos] > TRAP_DURATION:
                    continue

            if (
                platform['pos'][0] - platform['size'][0] / 2 - collision_offset <= player_pos[0] <= platform['pos'][0] + platform['size'][0] / 2 + collision_offset and
                platform['pos'][1] - collision_offset <= player_pos[1] <= platform['pos'][1] + platform['size'][1] + collision_offset and
                platform['pos'][2] - platform['size'][2] / 2 - collision_offset <= player_pos[2] <= platform['pos'][2] + platform['size'][2] / 2 + collision_offset
            ):
                player_pos[1] = platform['pos'][1] + platform['size'][1] + collision_offset
                is_jumping = False
                player_velocity[1] = 0

                # Handle checkpoint platforms
                if platform.get('checkpoint'):
                    current_checkpoint = platform['pos'].copy()
                    current_checkpoint[1] += platform['size'][1] + collision_offset

                # Start timer for trap platforms on first touch
                if platform.get('trap') and platform_pos not in trap_timers:
                    trap_timers[platform_pos] = current_time

                # Handle boost platforms
                if platform.get('boost') and keys[K_SPACE]:
                    player_velocity[1] = BOOST_POWER
                    is_jumping = True

                # Check if it's the finish platform
                if platform.get('finish'):
                    LEVEL_COMPLETED = True
                    is_paused = True

            wall_buffer = 0.5  # Distance from wall to stop player
            if player_pos[0] > GROUND_SIZE - wall_buffer:
                player_pos[0] = GROUND_SIZE - wall_buffer
            if player_pos[0] < -GROUND_SIZE + wall_buffer:
                player_pos[0] = -GROUND_SIZE + wall_buffer
            if player_pos[2] > GROUND_SIZE - wall_buffer:
                player_pos[2] = GROUND_SIZE - wall_buffer
            if player_pos[2] < -GROUND_SIZE + wall_buffer:
                player_pos[2] = -GROUND_SIZE + wall_buffer


def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(math.degrees(player_rotation), 0, 1, 0)
    glBegin(GL_QUADS)
    glColor3f(1, 0, 0)  # Red color

    # Front face
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(-0.5, 0.5, -0.5)

    # Back face
    glVertex3f(-0.5, -0.5, 0.5)
    glVertex3f(0.5, -0.5, 0.5)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(-0.5, 0.5, 0.5)

    # Top face
    glVertex3f(-0.5, 0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(-0.5, 0.5, 0.5)

    # Bottom face
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(0.5, -0.5, 0.5)
    glVertex3f(-0.5, -0.5, 0.5)

    # Right face
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(0.5, -0.5, 0.5)

    # Left face
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(-0.5, 0.5, -0.5)
    glVertex3f(-0.5, 0.5, 0.5)
    glVertex3f(-0.5, -0.5, 0.5)

    glEnd()
    glPopMatrix()


def reset_to_checkpoint():
    global player_pos, trap_timers, current_checkpoint, SCORE_SAVED, checkpoint_resets_remaining

    if checkpoint_resets_remaining <= 0:
        return  # Don't allow reset if no resets remaining

    # Reset player position to last checkpoint or start position
    if current_checkpoint:
        player_pos = current_checkpoint.copy()
    else:
        player_pos = PLAYER_START_POS.copy()

    # Clear all trap timers to reset traps
    trap_timers.clear()

    # Reset the score saved flag
    SCORE_SAVED = False

    # Decrease remaining resets
    checkpoint_resets_remaining -= 1


def draw_resets_remaining():
    font = pygame.font.SysFont('Arial', 24)
    resets_text = font.render(f"Resets: {checkpoint_resets_remaining}", True, (255, 255, 255))
    resets_surface = pygame.Surface((resets_text.get_width(), resets_text.get_height()), pygame.SRCALPHA)
    resets_surface.blit(resets_text, (0, 0))

    x = 10  # Position on the left side
    y = 10  # Position at the top

    draw_2d_text([resets_surface], [(x, y)], [(resets_surface.get_width(), resets_surface.get_height())])


def draw_timer():
    global elapsed_time
    if not is_paused:
        current_time = time.time()
        elapsed_time = current_time - start_time
    font = pygame.font.SysFont('Arial', 24)
    timer_text = font.render(f"Time: {int(elapsed_time)}", True, (255, 255, 255))
    timer_surface = pygame.Surface((timer_text.get_width(), timer_text.get_height()), pygame.SRCALPHA)
    timer_surface.blit(timer_text, (0, 0))

    x = WINDOW_WIDTH - timer_surface.get_width() - 10
    y = 10

    draw_2d_text([timer_surface], [(x, y)], [(timer_surface.get_width(), timer_surface.get_height())])


def pause_menu():
    font = pygame.font.SysFont('Arial', 36)
    pause_text = font.render("PAUSED", True, (0, 0, 0))
    pause_surface = pygame.Surface((pause_text.get_width(), pause_text.get_height()), pygame.SRCALPHA)
    pause_surface.blit(pause_text, (0, 0))

    x = (WINDOW_WIDTH - pause_surface.get_width()) // 2
    y = (WINDOW_HEIGHT - pause_surface.get_height()) // 2

    draw_2d_text([pause_surface], [(x, y)], [(pause_surface.get_width(), pause_surface.get_height())])


def draw_completion_screen():
    global elapsed_time, SCORE_SAVED
    if not SCORE_SAVED:
        save_score(elapsed_time)
        SCORE_SAVED = True

    # Get top scores
    top_scores = get_top_scores()

    # Create all text surfaces
    surfaces = []
    positions = []
    sizes = []

    font = pygame.font.SysFont('Arial', 48)
    scores_font = pygame.font.SysFont('Arial', 36)

    # Add completion text
    completion_surface = font.render("Level Complete!", True, (0, 0, 0))
    time_surface = font.render(f"Your Time: {int(elapsed_time)} seconds", True, (0, 0, 0))
    high_scores_surface = font.render("Top Times:", True, (0, 0, 0))

    # Calculate total height
    total_height = completion_surface.get_height() + time_surface.get_height() + high_scores_surface.get_height()
    total_height += len(top_scores) * scores_font.get_height() + (len(top_scores) + 3) * 10  # Adding spacing

    current_y = (WINDOW_HEIGHT - total_height) // 2

    # Add main surfaces
    for surface in [completion_surface, time_surface, high_scores_surface]:
        x = (WINDOW_WIDTH - surface.get_width()) // 2
        surfaces.append(surface)
        positions.append((x, current_y))
        sizes.append((surface.get_width(), surface.get_height()))
        current_y += surface.get_height() + 10

    # Add score surfaces
    for i, (name, time, date) in enumerate(top_scores, 1):
        score_surface = scores_font.render(f"{i}. {name}: {int(time)}s", True, (0, 0, 0))
        x = (WINDOW_WIDTH - score_surface.get_width()) // 2
        surfaces.append(score_surface)
        positions.append((x, current_y))
        sizes.append((score_surface.get_width(), score_surface.get_height()))
        current_y += score_surface.get_height() + 10

    draw_2d_text(surfaces, positions, sizes)


def init_database():
    """Initialize the database and create the high scores table if it doesn't exist."""
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS high_scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  player_name TEXT,
                  completion_time REAL,
                  date TEXT)''')
    conn.commit()
    conn.close()


def save_score(completion_time):
    """Save the score to the database."""
    player_name = get_username()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute("INSERT INTO high_scores (player_name, completion_time, date) VALUES (?, ?, ?)",
              (player_name, completion_time, current_date))
    conn.commit()
    conn.close()


def get_top_scores(limit=5):
    """Retrieve the top scores from the database."""
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute("SELECT player_name, completion_time, date FROM high_scores ORDER BY completion_time ASC LIMIT ?", (limit,))
    scores = c.fetchall()
    conn.close()
    return scores


def reset_database():
    """Reset the high scores database by deleting all records."""
    try:
        conn = sqlite3.connect('game_scores.db')
        c = conn.cursor()
        c.execute("DELETE FROM high_scores")  # Delete all records
        conn.commit()
        conn.close()
        print("Database reset successfully")
    except sqlite3.Error as e:
        print(f"Error resetting database: {e}")


def get_username():
    username = ""
    input_active = True
    font = pygame.font.SysFont('Arial', 32)

    while input_active:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                else:
                    if len(username) < 20:
                        username += event.unicode

        prompt_text = font.render("Enter Username:", True, (0, 0, 0))
        input_text = font.render(username + "|", True, (0, 0, 0))

        surfaces = [prompt_text, input_text]
        positions = [
            ((WINDOW_WIDTH - prompt_text.get_width()) // 2, WINDOW_HEIGHT // 2 - 25),
            ((WINDOW_WIDTH - input_text.get_width()) // 2, WINDOW_HEIGHT // 2 + 25)
        ]
        sizes = [(s.get_width(), s.get_height()) for s in surfaces]

        draw_2d_text(surfaces, positions, sizes)
        pygame.display.flip()

    return username if username else "Player"


def draw_2d_text(surfaces, positions, sizes):
    """Helper function to draw 2D text with proper matrix handling"""
    # Save the current matrices
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Disable depth testing temporarily
    glDisable(GL_DEPTH_TEST)

    # Draw all surfaces
    for surface, pos, size in zip(surfaces, positions, sizes):
        # Convert surface to texture
        text_data = pygame.image.tostring(surface, "RGBA", True)
        text_texture = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, text_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, size[0], size[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        # Draw the texture
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(pos[0], pos[1])
        glTexCoord2f(1, 1); glVertex2f(pos[0] + size[0], pos[1])
        glTexCoord2f(1, 0); glVertex2f(pos[0] + size[0], pos[1] + size[1])
        glTexCoord2f(0, 0); glVertex2f(pos[0], pos[1] + size[1])
        glEnd()

        glDeleteTextures([text_texture])

    # Restore state
    glDisable(GL_BLEND)
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)

    # Restore matrices
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def handle_events():
    global is_paused, start_time, stored_time, elapsed_time, LEVEL_COMPLETED, pause_start_time, checkpoint_resets_remaining
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        if event.type == pygame.VIDEORESIZE:
            resize_window(event.w, event.h)
        if event.type == pygame.KEYDOWN:
            if event.key == K_ESCAPE and not LEVEL_COMPLETED:
                is_paused = not is_paused
                if is_paused:
                    pause_start_time = time.time()
                    stored_time = elapsed_time
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
                else:
                    pause_duration = time.time() - pause_start_time
                    start_time = start_time + pause_duration
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)

            if event.key == K_BACKSPACE and checkpoint_resets_remaining > 0:
                reset_to_checkpoint()

            if event.key == K_q and is_paused:
                pygame.quit()
                quit()

            if event.key == K_r and event.mod & pygame.KMOD_CTRL:
                reset_database()


def cleanup():
    global ground_texture
    try:
        if ground_texture is not None and glIsTexture(ground_texture):
            glDeleteTextures([ground_texture])
    except:
        pass  # Ignore any OpenGL errors during cleanup
    finally:
        pygame.quit()


def resize_window(width, height):
    if height == 0:
        height = 1
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(width)/float(height), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)


def main():
    global ground_texture, is_paused
    ground_texture = load_texture('grass.jpg')
    clock = pygame.time.Clock()

    # Initialize the database
    init_database()

    init_mouse_handling()

    pygame.mouse.set_visible(False)  # Hide the cursor
    pygame.event.set_grab(True)      # Lock the mouse to the window

    try:
        while True:
            handle_events()

            # Clear the screen
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            if not is_paused:
                glLoadIdentity()  # Reset the modelview matrix
                glTranslatef(0.0, 0.0, -5)  # Move back into the scene
                handle_camera()
                handle_movement()
                draw_ground()
                draw_walls()
                draw_platforms()
                draw_player()
                draw_timer()
                draw_resets_remaining()
            else:
                draw_ground()
                draw_walls()
                draw_platforms()
                draw_player()
                draw_timer()
                draw_resets_remaining()
                if LEVEL_COMPLETED:
                    draw_completion_screen()
                else:
                    pause_menu()

            pygame.display.flip()
            clock.tick(60)

    except SystemExit:
        cleanup()
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        cleanup()
        return


if __name__ == '__main__':
    main()
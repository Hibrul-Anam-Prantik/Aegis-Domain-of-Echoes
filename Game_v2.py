from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys
import time
import os

# Provide safe fallbacks for GLUT bitmap fonts for static analysis/time-of-import safety
if 'GLUT_BITMAP_HELVETICA_18' not in globals():
    GLUT_BITMAP_HELVETICA_18 = 1

if 'GLUT_BITMAP_TIMES_ROMAN_24' not in globals():
    GLUT_BITMAP_TIMES_ROMAN_24 = 2

# ---------------- CAMERA ----------------
camera_angle = 0        
camera_pitch = 15       
camera_distance = 300   
camera_height = 90      
fov_y = 120

# ---------------- WORLD ----------------
GRID_LENGTH = 1000

# ---------------- PLAYER ----------------
pos_x = 0
pos_y = 0
pos_angle = 0
player_x = pos_x
player_y = pos_y
player_z = 0
person_one = False
domain_mode = False
pos_z = 0
is_jumping = False
jump_timer = 0
JUMP_FRAMES = 30
MAX_JUMP_HEIGHT = 80

building_data = []
tree_data = []
ash_particles = []

is_swinging = False
katana_swing_angle = 0
orb_active = False
orb_pos = [0, 0, 0]
orb_dir = [0, 0, 0]

keys = {b'w': False, b's': False, b'a': False, b'd': False}

# ================= ENGINEER GLOBALS =================
enemies = []
enemy_speed = 3.0
enemy_radius = 20
orb_radius = 15
cheat_mode = False

player_health = 5
max_health = 5
player_iframes = 0  
score = 0
game_over = False
loot_drops = []
last_orb_fire_time = 0.0 

# --- BOSS & DOMAIN ANIMATION GLOBALS ---
boss_active = False
boss_defeated = False
boss = {'x': 0, 'y': 0, 'z': 0, 'radius': 50} 
boss_health = 100
boss_max_health = 100 
boss_hit_this_swing = False
boss_is_rising = False 

domain_animating = False      # NEW: Tracks the cinematic spin state
domain_anim_angle = 0         # NEW: Tracks the 360 rotation progress

boss_orb_active = False
boss_orb_pos = [0, 0, 0]
boss_orb_dir = [0, 0, 0]
boss_orb_radius = 20
boss_orb_speed = 15
boss_orb_cooldown = 0 

# ================= WORLD GENERATION =================

# Boss shockwave
boss_shockwave_active = False
boss_shockwave_radius = 0.0
boss_shockwave_speed = 10.0
boss_shockwave_cooldown = 0
def generate_world_data():
    global building_data, tree_data, ash_particles
    building_data, tree_data, ash_particles = [], [], []
    limit = GRID_LENGTH - 100 
    step = 120 
    counter = 0

    for i in range(-limit, limit + 1, step):
        points = [(i, limit), (i, -limit), (limit, i), (-limit, i)]
        for x, y in points:
            if counter % 3 == 0 or counter % 3 == 1: 
                h = random.randint(5, 10) 
                building_data.append((x, y, h))
            else:
                tree_data.append((x + random.uniform(-40, 40), y + random.uniform(-40, 40)))
            tree_data.append((x + random.uniform(-100, 100), y + random.uniform(-100, 100)))
            counter += 1

    for _ in range(8000):
        ash_particles.append((random.uniform(-GRID_LENGTH, GRID_LENGTH), 
                             random.uniform(-GRID_LENGTH, GRID_LENGTH), 
                             random.uniform(0.15, 0.35)))

# ================= PHYSICS & ENTITY BEHAVIOR =================
def distance_3d(p1, p2):
    return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 + (p2[2]-p1[2])**2)

def spawn_enemy():
    global enemies
    x = random.uniform(-800, 800)
    y = random.uniform(-800, 800)
    z = 0
    enemies.append({'x': x, 'y': y, 'z': z, 'radius': enemy_radius})

def update_behavior():
    global enemies, pos_x, pos_y, score, max_health, player_health, domain_mode
    global boss_active, boss_defeated, boss, boss_orb_active, boss_orb_pos, boss_orb_dir, boss_orb_cooldown
    global boss_is_rising, domain_animating, domain_anim_angle
    global boss_shockwave_active, boss_shockwave_radius, boss_shockwave_speed, boss_shockwave_cooldown
    
    # --- BOSS SPAWN TRIGGER ---
    # NEW: Trigger the animation state instead of instant rising
    if score >= 500 and not boss_active and not boss_defeated and not domain_animating:
        enemies.clear() 
        domain_animating = True   
        domain_anim_angle = 0     

        boss_active = True
        max_health = 10
        player_health = 10 
        boss['x'] = random.uniform(-400, 400) # Spawn a bit closer so we can see him
        boss['y'] = random.uniform(-400, 400)
        boss['z'] = -400 
        boss_is_rising = False # Wait for animation to finish before rising!

    # --- REGULAR ENEMY BEHAVIOR ---
    if not boss_active:
        while len(enemies) < 5:
            spawn_enemy()
            
        for i, e in enumerate(enemies):
            dist = distance_3d((e['x'], e['y'], e['z']), (pos_x, pos_y, 0))
            if dist > 35:
                e['x'] += (pos_x - e['x']) / dist * enemy_speed
                e['y'] += (pos_y - e['y']) / dist * enemy_speed

            for j, other in enumerate(enemies):
                if i != j: 
                    dist_between = distance_3d((e['x'], e['y'], 0), (other['x'], other['y'], 0))
                    if dist_between < (enemy_radius * 2) and dist_between > 0:
                        overlap = (enemy_radius * 2) - dist_between
                        e['x'] += ((e['x'] - other['x']) / dist_between) * (overlap * 0.1)
                        e['y'] += ((e['y'] - other['y']) / dist_between) * (overlap * 0.1)

    # --- BOSS BEHAVIOR ---
    if boss_active and not domain_animating: # Don't update boss during cinematic
        if boss_is_rising:
            boss['z'] += 4.0 
            if boss['z'] >= 0:
                boss['z'] = 0
                boss_is_rising = False 
        
        else:
            dist = distance_3d((boss['x'], boss['y'], 0), (pos_x, pos_y, 0))
            if dist > 140:
                boss['x'] += (pos_x - boss['x']) / dist * 1.5 
                boss['y'] += (pos_y - boss['y']) / dist * 1.5
            
            if boss_orb_cooldown > 0:
                boss_orb_cooldown -= 1

            if not boss_orb_active and boss_orb_cooldown <= 0:
                boss_orb_active = True
                boss_orb_cooldown = 120 
                boss_orb_pos = [boss['x'], boss['y'], 80] 
                dist_p = distance_3d(boss_orb_pos, (pos_x, pos_y, 60))
                if dist_p > 0:
                    boss_orb_dir = [(pos_x - boss_orb_pos[0])/dist_p, (pos_y - boss_orb_pos[1])/dist_p, 0]
                    
            if boss_orb_active:
                boss_orb_pos[0] += boss_orb_dir[0] * boss_orb_speed
                boss_orb_pos[1] += boss_orb_dir[1] * boss_orb_speed
                if abs(boss_orb_pos[0]) > 1000 or abs(boss_orb_pos[1]) > 1000:
                    boss_orb_active = False

            # Boss Shockwave logic: cooldown, random trigger, and expansion
            
            
        if boss_shockwave_cooldown > 0:
            boss_shockwave_cooldown -= 1

        if not boss_shockwave_active and boss_shockwave_cooldown <= 0:
            # Random chance to trigger a shockwave attack
            if random.randint(1, 100) == 1:
                boss_shockwave_active = True
                boss_shockwave_radius = 0.0
                boss_shockwave_cooldown = 360  # cooldown before next possible shockwave

        if boss_shockwave_active:
            boss_shockwave_radius += boss_shockwave_speed
            # Deactivate when it grows beyond a sensible limit
            if boss_shockwave_radius > 1200:
                boss_shockwave_active = False

def check_collisions():
    global orb_active, orb_pos, orb_radius, enemies, is_swinging, pos_x, pos_y, cheat_mode
    global player_health, max_health, score, game_over, loot_drops, player_iframes
    global boss_active, boss_health, boss_defeated, boss, boss_orb_active, boss_orb_pos, boss_orb_radius, boss_hit_this_swing, boss_is_rising, domain_animating
    global boss_shockwave_active, boss_shockwave_radius
    
    if game_over or boss_defeated or domain_animating: return # Freeze collisions during animation
    
    player_pos = (pos_x, pos_y, 0)

    if player_iframes > 0:
        player_iframes -= 1
    
    if not is_swinging:
        boss_hit_this_swing = False
        
    # --- BOSS COLLISIONS ---
    if boss_active:
        if not boss_is_rising:
            if orb_active:
                dist_2d = math.hypot(orb_pos[0] - boss['x'], orb_pos[1] - boss['y'])
                if dist_2d <= (orb_radius + boss['radius']):
                    boss_health -= 10
                    orb_active = False 
                    
            if is_swinging and not boss_hit_this_swing:
                if distance_3d(player_pos, (boss['x'], boss['y'], 0)) < 160: 
                    rad_p = math.radians(pos_angle)
                    forward_x = math.sin(rad_p)
                    forward_y = -math.cos(rad_p)
                    dx = boss['x'] - pos_x
                    dy = boss['y'] - pos_y
                    dist_to_boss = math.hypot(dx, dy)
                    if dist_to_boss > 0:
                        dot_product = (forward_x * (dx/dist_to_boss)) + (forward_y * (dy/dist_to_boss))
                        if dot_product > 0.5: 
                            boss_health -= 5
                            boss_hit_this_swing = True 
        
        if boss_orb_active and not cheat_mode:
            dist_2d = math.hypot(boss_orb_pos[0] - pos_x, boss_orb_pos[1] - pos_y)
            if dist_2d <= (boss_orb_radius + 20) and player_iframes <= 0:
                player_health -= 1
                player_iframes = 60 
                boss_orb_active = False 
                if player_health <= 0:
                    player_health = 0
                    game_over = True
                    
        if boss_health <= 0:
            boss_active = False
            boss_defeated = True
            boss_orb_active = False
            score += 1000 
            for _ in range(10):
                loot_drops.append({'type': 'coin', 'x': boss['x'] + random.uniform(-50,50), 'y': boss['y'] + random.uniform(-50,50), 'z': 10})

    # --- BOSS SHOCKWAVE COLLISION (expanding ring) ---
    if boss_shockwave_active and not cheat_mode and player_iframes <= 0:
            # Distance in 2D between player and boss
            dist_2d = math.hypot(pos_x - boss['x'], pos_y - boss['y'])
            # If the player is near the ring and not too high (pos_z < 30) they take damage
            if abs(dist_2d - boss_shockwave_radius) <= 20 and pos_z < 30:
                player_health -= 2
                player_iframes = 90
                # Optionally end the shockwave on hit to avoid multiple hits
                boss_shockwave_active = False
                if player_health <= 0:
                    player_health = 0
                    game_over = True

    # --- REGULAR ENEMY COLLISIONS ---
    if not boss_active and not boss_defeated:
        alive_enemies = []
        hit_occurred = False
        
        for e in enemies:
            e_pos = (e['x'], e['y'], e['z'])
            killed = False
            damaged_player = False
            
            if distance_3d(player_pos, e_pos) < (enemy_radius + 15):
                if not cheat_mode and player_iframes <= 0: 
                    player_health -= 1
                    player_iframes = 60 
                    damaged_player = True 
                    if player_health <= 0:
                        player_health = 0
                        game_over = True
                        
            if not damaged_player and not killed and orb_active:
                dist_2d = math.hypot(orb_pos[0] - e['x'], orb_pos[1] - e['y'])
                if dist_2d <= (orb_radius + e['radius'] + 10):
                    hit_occurred = True
                    killed = True
                    score += 20
                    
            if not damaged_player and not killed and is_swinging:
                if distance_3d(player_pos, e_pos) < 120: 
                    rad_p = math.radians(pos_angle)
                    forward_x = math.sin(rad_p)
                    forward_y = -math.cos(rad_p)
                    dx = e['x'] - pos_x
                    dy = e['y'] - pos_y
                    dist_to_enemy = math.hypot(dx, dy)
                    if dist_to_enemy > 0:
                        dot_product = (forward_x * (dx/dist_to_enemy)) + (forward_y * (dy/dist_to_enemy))
                        if dot_product > 0.5:
                            killed = True
                            score += 10
                    
            if killed:
                drop_chance = random.random()
                if drop_chance < 0.2:
                    loot_drops.append({'type': 'heart', 'x': e['x'], 'y': e['y'], 'z': 10})
                elif drop_chance < 0.6:
                    loot_drops.append({'type': 'coin', 'x': e['x'], 'y': e['y'], 'z': 10})

            if not killed and not damaged_player:
                alive_enemies.append(e)
                
        enemies = alive_enemies
        if hit_occurred: orb_active = False

    # --- LOOT COLLISIONS ---
    alive_loot = []
    for item in loot_drops:
        if distance_3d(player_pos, (item['x'], item['y'], 0)) < 40:
            if item['type'] == 'heart':
                if player_health < max_health: player_health += 1 
            elif item['type'] == 'coin':
                score += 50
        else:
            alive_loot.append(item)
    loot_drops = alive_loot

def auto_guardian():
    global enemies, pos_angle, pos_x, pos_y, is_swinging, boss_active, boss, boss_is_rising, domain_animating
    
    if domain_animating: return # Do nothing during cutscene

    if boss_active:
        if boss_is_rising: return 

        dx = boss['x'] - pos_x
        dy = boss['y'] - pos_y
        dist = math.hypot(dx, dy)
        
        if dist > 0: pos_angle = math.degrees(math.atan2(dy, dx)) + 90
        
        if dist > 140: 
            speed = 15 
            pos_x += (dx / dist) * speed
            pos_y += (dy / dist) * speed
        else:
            is_swinging = True 
        return 

    if not enemies: return
    nearest = min(enemies, key=lambda e: distance_3d((pos_x, pos_y, 0), (e['x'], e['y'], e['z'])))
    dx = nearest['x'] - pos_x
    dy = nearest['y'] - pos_y
    dist = math.hypot(dx, dy)
    
    if dist > 0: pos_angle = math.degrees(math.atan2(dy, dx)) + 90
    
    if dist > 60:
        speed = 12
        pos_x += (dx / dist) * speed
        pos_y += (dy / dist) * speed
    else:
        is_swinging = True

# ================= UI & RENDER SYSTEM =================
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

def draw_rect(x, y, width, height, r, g, b, a=1.0):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(r, g, b, a)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()
    glDisable(GL_BLEND)

def draw_ui():
    global player_health, max_health, score, game_over, boss_active, boss_health, boss_max_health, boss_defeated
    global last_orb_fire_time, cheat_mode, domain_animating

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw UI overlay on top of the 3D scene. Disable depth test/lighting so it is always visible.
    glPushAttrib(GL_ENABLE_BIT)
    glDisable(GL_DEPTH_TEST)
    try:
        glDisable(GL_LIGHTING)
    except Exception:
        pass

    # Hide UI while domain is expanding for cinematic effect
    if not domain_animating:
        bar_x = 20
        bar_y = 750
        bar_width = 200
        bar_height = 20
        draw_rect(bar_x, bar_y, bar_width, bar_height, 0.2, 0.2, 0.2, 0.8) 
        health_ratio = max(0, player_health) / max_health
        draw_rect(bar_x, bar_y, bar_width * health_ratio, bar_height, 0.0, 1.0, 0.0, 0.8) 
        
        glColor3f(1.0, 1.0, 1.0)
        draw_text(bar_x, bar_y + 25, f"HEALTH: {player_health} / {max_health}", font=GLUT_BITMAP_HELVETICA_18)

        glColor3f(1.0, 1.0, 1.0) 
        draw_text(20, 710, f"SCORE: {score}")

        current_time = time.time()
        time_left = max(0.0, 3.0 - (current_time - last_orb_fire_time))
        if time_left > 0:
            glColor3f(1.0, 0.5, 0.0) 
            draw_text(20, 680, f"ORB COOLDOWN: {time_left:.1f}s")
        else:
            glColor3f(0.0, 1.0, 0.0) 
            draw_text(20, 680, "ORB READY")

        if cheat_mode:
            glColor3f(1.0, 0.0, 1.0) 
            draw_text(20, 650, "CHEAT MODE: ON")
        else:
            glColor3f(0.5, 0.5, 0.5) 
            draw_text(20, 650, "CHEAT MODE: OFF")
        
        if boss_active:
            boss_bar_width = 400
            boss_bar_x = (1000 - boss_bar_width) / 2
            boss_bar_y = 740
            draw_rect(boss_bar_x, boss_bar_y, boss_bar_width, 25, 0.2, 0.0, 0.0, 0.8) 
            boss_health_ratio = max(0, boss_health) / boss_max_health
            draw_rect(boss_bar_x, boss_bar_y, boss_bar_width * boss_health_ratio, 25, 1.0, 0.0, 0.0, 0.9) 
            
            glColor3f(1.0, 1.0, 1.0) 
            draw_text(boss_bar_x + 150, boss_bar_y + 30, f"DOMAIN BOSS", font=GLUT_BITMAP_TIMES_ROMAN_24)
    
    if game_over:
        draw_rect(0, 0, 1000, 800, 0.2, 0.0, 0.0, 0.7) 
        glColor3f(1.0, 0.0, 0.0) 
        draw_text(420, 450, "WASTED!!", font=GLUT_BITMAP_TIMES_ROMAN_24)
        glColor3f(1.0, 1.0, 1.0)
        draw_text(420, 400, f"FINAL SCORE: {score}")
        draw_text(300, 350, "PRESS 'ESC' TO EXIT OR 'R' TO RESTART")

    elif boss_defeated:
        draw_rect(0, 0, 1000, 800, 0.0, 0.2, 0.0, 0.7) 
        glColor3f(0.0, 1.0, 0.0) 
        draw_text(310, 450, "FINAL BOSS DEFEATED, GAME!!", font=GLUT_BITMAP_TIMES_ROMAN_24)
        glColor3f(1.0, 1.0, 1.0) 
        draw_text(420, 400, f"FINAL SCORE: {score}")
        draw_text(320, 350, "PRESS 'ESC' TO EXIT OR 'R' TO RESTART")
    # Restore GL state and matrices
    glPopAttrib()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

def draw_loot():
    global loot_drops
    for item in loot_drops:
        glPushMatrix()
        glTranslatef(item['x'], item['y'], item['z'])
        glRotatef(pos_angle * 3, 0, 0, 1) 
        if item['type'] == 'coin':
            glColor3f(1.0, 0.84, 0.0)
            glScalef(1.0, 1.0, 0.2)
            glutSolidSphere(12, 10, 10) 
        elif item['type'] == 'heart':
            glColor3f(1.0, 0.0, 0.0) 
            glTranslatef(-4, 0, 0)
            glutSolidSphere(6, 10, 10)
            glTranslatef(8, 0, 0)
            glutSolidSphere(6, 10, 10)
            glTranslatef(-4, 0, -5)
            glutSolidSphere(6, 10, 10)
        glPopMatrix()

def draw_skeleton(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    angle = math.degrees(math.atan2(y, x))
    glRotatef(angle - 90, 0, 0, 1) 
    
    glPushMatrix()
    glTranslatef(0, 0, 60)
    glColor3f(0.9, 0.9, 0.9) 
    gluSphere(gluNewQuadric(), 15, 10, 10)
    
    glColor3f(0.5, 1.0, 0.0)
    for dx in [-6, 6]:
        glPushMatrix()
        glTranslatef(dx, 12, 3)
        gluSphere(gluNewQuadric(), 4, 10, 10)
        glPopMatrix()
        
    glColor3f(0.1, 0.1, 0.1) 
    glPushMatrix()
    glTranslatef(0, 0, 12) 
    glRotatef(15, 1, 0, 0) 
    glPushMatrix()
    glScalef(1.5, 1.5, 0.1)
    glutSolidCube(25) 
    glPopMatrix()
    glTranslatef(0, 0, 2)
    gluCylinder(gluNewQuadric(), 12, 8, 15, 10, 10)
    glPopMatrix()
    glPopMatrix() 
    
    glPushMatrix()
    glTranslatef(0, 0, 30)
    glColor3f(0.7, 0.7, 0.7)
    glScalef(1.2, 0.5, 1.5)
    glutSolidCube(20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(15, 10, 30)
    glColor3f(0.6, 0.6, 0.6)
    glRotatef(45, 1, 0, 0) 
    gluCylinder(gluNewQuadric(), 3, 3, 30, 10, 10) 
    
    glTranslatef(0, 0, 30)
    glColor3f(0.4, 0.2, 0.0) 
    gluCylinder(gluNewQuadric(), 3, 3, 20, 10, 10)
    
    glTranslatef(0, 0, 20)
    glColor3f(1.0, 0.5, 0.0) 
    gluSphere(gluNewQuadric(), 8, 10, 10)
    glTranslatef(0, 0, 2)
    glColor3f(1.0, 1.0, 0.0) 
    gluSphere(gluNewQuadric(), 5, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

def draw_enemies():
    for e in enemies:
        draw_skeleton(e['x'], e['y'], e['z'])

def draw_boss():
    global boss
    glPushMatrix()
    glTranslatef(boss['x'], boss['y'], boss['z'])
    
    angle = math.degrees(math.atan2(pos_y - boss['y'], pos_x - boss['x']))
    glRotatef(angle - 90, 0, 0, 1) 
    glScalef(2.5, 2.5, 2.5) 
    
    glPushMatrix()
    glTranslatef(0, 0, 60)
    glColor3f(0.9, 0.9, 0.9) 
    gluSphere(gluNewQuadric(), 15, 10, 10)
    
    glColor3f(1.0, 1.0, 0.0)
    for dx in [-6, 6]:
        glPushMatrix()
        glTranslatef(dx, 12, 3)
        gluSphere(gluNewQuadric(), 4, 10, 10)
        glPopMatrix()
        
    glColor3f(1.0, 0.5, 0.0) 
    glPushMatrix()
    glTranslatef(0, 0, 12) 
    glRotatef(15, 1, 0, 0) 
    glPushMatrix()
    glScalef(1.5, 1.5, 0.1)
    glutSolidCube(25) 
    glPopMatrix()
    glTranslatef(0, 0, 2)
    gluCylinder(gluNewQuadric(), 12, 8, 15, 10, 10)
    glPopMatrix()
    glPopMatrix() 
    
    glPushMatrix()
    glTranslatef(0, 0, 30)
    glColor3f(0.7, 0.7, 0.7)
    glScalef(1.8, 1.0, 1.5) 
    glutSolidCube(20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(15, 10, 30)
    glColor3f(0.6, 0.6, 0.6)
    glRotatef(45, 1, 0, 0) 
    gluCylinder(gluNewQuadric(), 3, 3, 30, 10, 10) 
    
    glTranslatef(0, 0, 30)
    glColor3f(0.4, 0.2, 0.0) 
    gluCylinder(gluNewQuadric(), 4, 4, 25, 10, 10) 
    
    glTranslatef(0, 0, 25)
    glColor3f(1.0, 0.5, 0.0) 
    gluSphere(gluNewQuadric(), 12, 10, 10)
    glTranslatef(0, 0, 2)
    glColor3f(1.0, 1.0, 0.0) 
    gluSphere(gluNewQuadric(), 8, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

def draw_boss_orb():
    global boss_orb_pos, boss_orb_radius
    glPushMatrix()
    glTranslatef(boss_orb_pos[0], boss_orb_pos[1], boss_orb_pos[2])
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glColor4f(1.0, 0.5, 0.0, 0.9) 
    glutSolidSphere(boss_orb_radius, 20, 20)
    glDisable(GL_BLEND)
    glPopMatrix()

def draw_boss_shockwave():
    global boss, boss_shockwave_radius, boss_shockwave_active
    # NEW: Render the expanding shockwave
    if boss_shockwave_active:
        glPushMatrix()
        glTranslatef(boss['x'], boss['y'], 10)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        # Bright magenta wireframe outer ring
        glColor4f(1.0, 0.0, 1.0, 0.8)
        try:
            glutWireTorus(15, boss_shockwave_radius, 15, 40)
        except Exception:
            # Fallback: draw a wire circle using line loop
            segments = 80
            glBegin(GL_LINE_LOOP)
            for i in range(segments):
                a = (i / float(segments)) * (2.0 * math.pi)
                glVertex3f(math.cos(a) * boss_shockwave_radius, math.sin(a) * boss_shockwave_radius, 0)
            glEnd()

        # Slightly darker filled core ring for depth
        glColor4f(0.5, 0.0, 0.5, 0.4)
        try:
            glutSolidTorus(10, max(0.0, boss_shockwave_radius - 5), 15, 40)
        except Exception:
            # Fallback: draw a filled circle using triangle fan
            segments = 80
            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(0, 0, 0)
            for i in range(segments + 1):
                a = (i / float(segments)) * (2.0 * math.pi)
                glVertex3f(math.cos(a) * max(0.0, boss_shockwave_radius - 5), math.sin(a) * max(0.0, boss_shockwave_radius - 5), 0)
            glEnd()

        glDisable(GL_BLEND)
        glPopMatrix()

def draw_orb_projectile():
    global orb_pos
    glPushMatrix()
    glTranslatef(orb_pos[0], orb_pos[1], orb_pos[2])
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glColor4f(0, 1, 1, 0.8)
    glutSolidSphere(15, 20, 20)
    glDisable(GL_BLEND)
    glPopMatrix()

def draw_player():
    global pos_x, pos_y, pos_angle, domain_mode, is_swinging, katana_swing_angle, orb_active, game_over, player_iframes
    
    glPushMatrix()
    # Include vertical offset from jumping so the player visibly rises
    glTranslatef(pos_x, pos_y, 5 + pos_z)
    glRotatef(pos_angle, 0, 0, 1)

    if game_over:
        glRotatef(90, 0, 1, 0)  
        glTranslatef(-20, 0, -20) 

    is_blinking = player_iframes > 0 and (player_iframes // 5) % 2 == 0
    if is_blinking:
        base_color = (1.0, 0.0, 0.0) 
    else:
        base_color = (0.2, 0.2, 0.2)

    glColor3f(0.1, 0.1, 0.1)
    for s in [-1, 1]:
        glPushMatrix()
        glTranslatef(s * 12, 0, 15)
        glScalef(0.4, 0.4, 1.2)
        glutSolidCube(25)
        glPopMatrix()

    glPushMatrix()
    glColor3f(base_color[0], base_color[1], base_color[2]) 
    glTranslatef(0, 0, 50)
    glScalef(0.7, 0.4, 1.2)
    glutSolidCube(40)
    glPopMatrix()

    for s in [-1, 1]:
        glPushMatrix()
        if domain_mode: glColor3f(0.4, 0, 0.6)
        else: glColor3f(0.3, 0.2, 0.15)
        glTranslatef(s * 25, 0, 75)
        glRotatef(s * 20, 0, 1, 0)
        glScalef(0.8, 0.6, 0.3)
        glutSolidCube(30)
        glPopMatrix()

    glPushMatrix()
    if domain_mode: glColor3f(0.0, 1.0, 1.0)
    else: glColor3f(0.0, 0.5, 0.8)
    glTranslatef(0, -10, 60)
    glutSolidSphere(8, 16, 16)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 95)
    glColor3f(0.15, 0.15, 0.15)
    glutSolidSphere(12, 16, 16)
    if domain_mode: glColor3f(1.0, 0.0, 1.0)
    else: glColor3f(0.0, 1.0, 1.0)
    glPushMatrix()
    glTranslatef(0, -8, 2)
    glScalef(1.2, 0.2, 0.3)
    glutSolidCube(15)
    glPopMatrix()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-28, -5, 55)
    if is_swinging: glRotatef(-katana_swing_angle, 0, 1, 0)
    else: glRotatef(-45, 1, 0, 0) 
        
    if domain_mode: glColor3f(1.0, 0.0, 1.0)
    else: glColor3f(0.8, 0.8, 0.9)
    glPushMatrix()
    glTranslatef(0, 0, 50)
    glScalef(0.05, 0.01, 5.0)
    glutSolidCube(20)
    glPopMatrix()
    glColor3f(0.2, 0.1, 0.0)
    glScalef(0.2, 0.2, 1.5)
    glutSolidCube(15)
    glPopMatrix()

    if not orb_active:
        glPushMatrix()
        glTranslatef(28, -8, 60) 
        if domain_mode: glColor3f(0.0, 1.0, 1.0) 
        else: glColor3f(0.5, 0.8, 1.0) 
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        if domain_mode: glColor4f(0, 1, 1, 0.4)
        else: glColor4f(0.5, 0.8, 1, 0.3)
        glutSolidSphere(15, 20, 20) 
        if domain_mode: glColor3f(1, 1, 1) 
        else: glColor3f(0.7, 0.9, 1.0)
        glutSolidSphere(7, 16, 16) 
        glDisable(GL_BLEND)
        glPopMatrix()

    if domain_mode:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glColor4f(0.5, 0, 1.0, 0.2)
        glutSolidSphere(70, 20, 20)
        glDisable(GL_BLEND)

    glPopMatrix()

def draw_ground():
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glEnd()
    glBegin(GL_POINTS)
    for px, py, pc in ash_particles:
        glColor3f(pc, pc, pc)
        glVertex3f(px, py, 1)
    glEnd()

def draw_tree(x, y):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glColor3f(0.3, 0.15, 0.05) 
    glPushMatrix()
    glTranslatef(0, 0, 40)
    glScalef(0.4, 0.4, 2.0) 
    glutSolidCube(40) 
    glPopMatrix()
    if domain_mode: glColor3f(0.5, 0.0, 0.0) 
    else: glColor3f(0.0, 0.4, 0.0)
    glPushMatrix()
    glTranslatef(0, 0, 80)
    glutSolidSphere(35, 20, 20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 115)
    glutSolidSphere(25, 15, 15)
    glPopMatrix()
    glPopMatrix()

def draw_broken_building(x, y, height_floors):
    for i in range(height_floors):
        glPushMatrix()
        offset_x = (i * 0.8) if i % 2 == 0 else (i * -0.5)
        glTranslatef(x + offset_x, y, i * 40) 
        if domain_mode: glColor3f(1.0, 0.9, 0.8) 
        else: glColor3f(0.9, 0.9, 0.9)
        glutSolidCube(60) 
        glColor3f(0.1, 0.1, 0.1) 
        for k in range(-1, 2, 2):
            glPushMatrix()
            glTranslatef(0, k * 30.1, 15)
            glScalef(0.6, 0.1, 0.4)
            glutSolidCube(15)
            glPopMatrix()
        for l in range(-1, 2, 2):
            glPushMatrix()
            glTranslatef(l * 30.1, 0, 15)
            glScalef(0.1, 0.6, 0.4)
            glutSolidCube(15)
            glPopMatrix()
        glPopMatrix()

def draw_scenery():
    for x, y, fl in building_data:
        draw_broken_building(x, y, fl)
    for x, y in tree_data:
        draw_tree(x, y)

# ================= CAMERA =================
def camera_position():
    az = math.radians(camera_angle)
    pitch = math.radians(camera_pitch)
    horiz = camera_distance * math.cos(pitch)
    cx = player_x - math.cos(az) * horiz
    cy = player_y - math.sin(az) * horiz
    cz = player_z + camera_height + math.sin(pitch) * camera_distance
    return (cx, cy, cz)

def camera_control():
    global person_one
    if person_one:
        rad = math.radians(pos_angle + 90)
        xEye = pos_x - math.cos(rad) * 30
        yEye = pos_y - math.sin(rad) * 30
        zEye = 90
        lookx = pos_x - math.cos(rad) * 300
        looky = pos_y - math.sin(rad) * 300
        lookz = 60
        return (xEye, yEye, zEye, lookx, looky, lookz)

    cx, cy, cz = camera_position()
    lookx = player_x
    looky = player_y
    lookz = player_z + 60
    return (cx, cy, cz, lookx, looky, lookz)

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fov_y, 1.25, 0.1, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    ex, ey, ez, lx, ly, lz = camera_control()
    gluLookAt(ex, ey, ez, lx, ly, lz, 0, 0, 1)

# ================= INPUT =================
def keyboardListener(key, x, y):
    global keys, domain_mode, orb_active, orb_pos, orb_dir, pos_x, pos_y, cheat_mode
    global game_over, player_health, max_health, score, enemies, loot_drops, camera_distance
    global boss_active, boss_defeated, boss_health, boss_orb_active, last_orb_fire_time, boss_is_rising, domain_animating
    global is_jumping, jump_timer, JUMP_FRAMES, pos_z

    if key == b'\x1b': 
        os._exit(0) 

    if key == b'r' or key == b'R':
        game_over = False
        boss_defeated = False 
        boss_active = False
        boss_health = 100
        boss_orb_active = False
        boss_is_rising = False
        domain_mode = False
        domain_animating = False
            
        score = 0
        max_health = 5 
        player_health = max_health 
        pos_x = 0
        pos_y = 0
        orb_active = False 
        last_orb_fire_time = 0.0
            
        enemies.clear()
        loot_drops.clear()
        for k in keys: keys[k] = False 
        return 

    if key in keys:
        keys[key] = True

    # Jump: spacebar
    if key == b' ' and not is_jumping and not domain_animating:
        is_jumping = True
        jump_timer = JUMP_FRAMES

    if key == b'x' or key == b'X': domain_mode = not domain_mode
    if key == b'c' or key == b'C': cheat_mode = not cheat_mode
    
    if key == b'f' or key == b'F':
        if not cheat_mode and not domain_animating: # Cannot fire during cutscene
            current_time = time.time()
            if not orb_active and (current_time - last_orb_fire_time) >= 3.0:
                orb_active = True
                orb_pos = [pos_x, pos_y, 60]
                rad_p = math.radians(pos_angle)
                orb_dir = [math.sin(rad_p), -math.cos(rad_p), 0] 
                last_orb_fire_time = current_time
            
    zoom_step = 20
    if key == b'+' or key == b'=':
        camera_distance = max(30, camera_distance - zoom_step)
    elif key == b'-':
        camera_distance = camera_distance + zoom_step

def specialKeyListener(key, x, y):
    global camera_angle, camera_pitch, domain_animating
    if domain_animating: return # Freeze camera controls during animation
    
    if key == GLUT_KEY_RIGHT: camera_angle -= 3
    elif key == GLUT_KEY_LEFT: camera_angle += 3
    elif key == GLUT_KEY_UP: camera_pitch = max(-10, camera_pitch - 3)
    elif key == GLUT_KEY_DOWN: camera_pitch = min(80, camera_pitch + 3)

def keyboardUpListener(key, x, y):
    global keys
    if key in keys: keys[key] = False

def mouseListener(button, state, x, y):
    global is_swinging, person_one, game_over, boss_defeated, cheat_mode, domain_animating
    if game_over or boss_defeated or domain_animating: return 
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if not cheat_mode: 
            is_swinging = True
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        person_one = not person_one  

# ================= LOGIC =================
def update_logic():
    global pos_x, pos_y, pos_angle, is_swinging, katana_swing_angle
    global orb_active, orb_pos, orb_dir, player_x, player_y, player_z
    global camera_angle, cheat_mode, game_over, boss_defeated, boss_active
    global domain_animating, domain_anim_angle, domain_mode, boss_is_rising

    if game_over or boss_defeated: return 

    # NEW: Cinematic Animation Logic
    if domain_animating:
        camera_angle += 3.0       # Auto-spin the camera
        domain_anim_angle += 3.0  # Track exactly how far we spun
        
        # When we reach halfway (180 degrees), swap the colors to dark mode
        if domain_anim_angle >= 180 and not domain_mode:
            domain_mode = True
            
        # When we finish spinning 360 degrees
        if domain_anim_angle >= 360:
            domain_animating = False # End cutscene
            boss_is_rising = True    # Tell the boss to start climbing out of the ground
            
        return # **CRITICAL: Freeze all player input and movement below while spinning!**

    if not boss_active and random.randint(1, 60) == 1: 
        spawn_enemy()
        
    update_behavior()
    check_collisions()
    
    if cheat_mode:
        auto_guardian()
    else:
        speed = 10
        az = math.radians(camera_angle)
        forward_x = math.cos(az)
        forward_y = math.sin(az)
        right_x = -math.sin(az)
        right_y = math.cos(az)

        mvx = 0.0
        mvy = 0.0

        if keys[b'w']: mvx += forward_x; mvy += forward_y
        if keys[b's']: mvx -= forward_x; mvy -= forward_y
        if keys[b'd']: mvx -= right_x; mvy -= right_y
        if keys[b'a']: mvx += right_x; mvy += right_y

        length = math.hypot(mvx, mvy)
        if length > 0:
            mvx /= length
            mvy /= length
            pos_x += mvx * speed
            pos_y += mvy * speed
            pos_angle = math.degrees(math.atan2(mvy, mvx)) + 90

    world_limit = GRID_LENGTH - 200
    pos_x = max(-world_limit, min(world_limit, pos_x))
    pos_y = max(-world_limit, min(world_limit, pos_y))

    player_x = pos_x
    player_y = pos_y
    player_z = 0

    if is_swinging:
        katana_swing_angle += 15
        if katana_swing_angle > 180:
            katana_swing_angle = 0
            is_swinging = False

    if orb_active:
        orb_pos[0] += orb_dir[0] * 25 
        orb_pos[1] += orb_dir[1] * 25
        orb_pos[2] += orb_dir[2] * 25
        if abs(orb_pos[0]) > GRID_LENGTH or abs(orb_pos[1]) > GRID_LENGTH or abs(orb_pos[2]) > GRID_LENGTH:
            orb_active = False

    # Jump math
    global pos_z, is_jumping, jump_timer, JUMP_FRAMES, MAX_JUMP_HEIGHT
    if is_jumping:
        if jump_timer > 0:
            jump_timer -= 1
            t = (JUMP_FRAMES - jump_timer) / float(JUMP_FRAMES)
            pos_z = math.sin(t * math.pi) * MAX_JUMP_HEIGHT
        else:
            is_jumping = False
            pos_z = 0
    player_z = pos_z

# ================= RENDER =================
def showScreen():
    update_logic()

    if domain_mode: glClearColor(0.08, 0.0, 0.0, 1.0)
    else: glClearColor(0.4, 0.3, 0.2, 1.0)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setupCamera()

    draw_ground()
    draw_scenery()
    
    # NEW: The Expanding Domain Sphere Visual
    if domain_animating:
        glPushMatrix()
        glTranslatef(pos_x, pos_y, 0) # Center the sphere on the player
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Calculate size based on spin progress (grows massively over the 360 frames)
        expansion_radius = domain_anim_angle * 15 
        
        # Draw a glowing, expanding dark purple dome
        glColor4f(0.2, 0.0, 0.4, 0.6)
        glutSolidSphere(expansion_radius, 40, 40)
        
        glDisable(GL_BLEND)
        glPopMatrix()

    if not boss_active: draw_enemies()
    if boss_active: draw_boss()
    # Draw the boss shockwave ring (if active)
    draw_boss_shockwave()
    if boss_orb_active: draw_boss_orb()
        
    draw_loot() 
    draw_player()

    if orb_active: draw_orb_projectile()
        
    draw_ui() 
    glutSwapBuffers()

# ================= MAIN =================
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutCreateWindow(b"Gate Base System")

    glEnable(GL_DEPTH_TEST) 
    generate_world_data()
    
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(showScreen)
    glutKeyboardUpFunc(keyboardUpListener)

    glutMainLoop() 

if __name__ == "__main__":
    main()
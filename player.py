from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random 
import enemy
import physics
import boss

# ---------------- CAMERA ----------------
# New camera variables (azimuth, pitch, distance, vertical offset)
camera_angle = 0        # horizontal angle around player (degrees)
camera_pitch = 15       # tilt angle (degrees). Positive looks down onto the player
camera_distance = 300   # distance from player
camera_height = 90      # vertical offset added to player z for camera base height

fov_y = 120

# ---------------- WORLD ----------------
GRID_LENGTH = 1000

# ---------------- PLAYER ----------------
# Core player position/rotation used by the rest of the code (keep these names)
pos_x = 0
pos_y = 0
pos_angle = 0

# New explicit player coordinates required by the task (kept in sync with pos_*)
player_x = pos_x
player_y = pos_y
player_z = 0

# Player HP and damage cooldown (frames)
player_hp = 100
dmg_cooldown = 0
DMG_COOLDOWN_FRAMES = 30

person_one = False

# kill counter and domain expansion flag
kill_count = 0
domain_expansion_triggered = False

# ---------------- DOMAIN MODE ----------------

domain_mode = False


building_data = []
tree_data = []
ash_particles = []


is_swinging = False
katana_swing_angle = 0
katana_swing_timer = 0
orb_active = False
orb_pos = [0, 0, 0]
orb_dir = [0, 0]
is_jumping = False
jump_timer = 0
JUMP_FRAMES = 30


keys = {b'w': False, b's': False, b'a': False, b'd': False}

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


# ================= CAMERA =================

def camera_position():
    """Return camera world position computed from spherical offsets around the player.

    Uses camera_angle (azimuth), camera_pitch (elevation tilt) and camera_distance.
    """
    # convert to radians
    az = math.radians(camera_angle)
    pitch = math.radians(camera_pitch)

    # horizontal projection of the distance
    horiz = camera_distance * math.cos(pitch)

    cx = player_x - math.cos(az) * horiz
    cy = player_y - math.sin(az) * horiz
    cz = player_z + camera_height + math.sin(pitch) * camera_distance

    return (cx, cy, cz)


def camera_control():
    """Return eye (camera) and look-at coordinates for gluLookAt.

    If person_one (first-person toggle) is active keep the existing tiny first-person view.
    Otherwise compute a third-person chase camera that orbits the player.
    """
    global person_one

    if person_one:
        # keep the existing (small) first-person style camera behavior
        rad = math.radians(pos_angle + 90)
        xEye = pos_x - math.cos(rad) * 30
        yEye = pos_y - math.sin(rad) * 30
        zEye = 90
        lookx = pos_x - math.cos(rad) * 300
        looky = pos_y - math.sin(rad) * 300
        lookz = 60
        return (xEye, yEye, zEye, lookx, looky, lookz)

    # third-person chase camera
    cx, cy, cz = camera_position()
    # always look at the player's eye level (slightly above ground)
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
    # use a simple up-vector (Z-up world)
    gluLookAt(ex, ey, ez, lx, ly, lz, 0, 0, 1)
    # Note: drawing should not be performed from setupCamera() to avoid
    # unintended re-entry or state changes. Enemy drawing is done in the
    # main render function so it executes after the scene/camera is set.


# ================= WORLD =================

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

# ================= PLAYER =================

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
    global pos_x, pos_y, pos_angle, domain_mode, player_z

    glPushMatrix()
    # apply vertical offset so jump is visible
    glTranslatef(pos_x, pos_y, player_z + 5)
    glRotatef(pos_angle, 0, 0, 1)

    glColor3f(0.1, 0.1, 0.1)
    for s in [-1, 1]:
        glPushMatrix()
        glTranslatef(s * 12, 0, 15)
        glScalef(0.4, 0.4, 1.2)
        glutSolidCube(25)
        glPopMatrix()

    
    glPushMatrix()
    glColor3f(0.2, 0.2, 0.2)
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
    
    if is_swinging:
        glRotatef(-katana_swing_angle, 0, 1, 0)
    else:
        glRotatef(-45, 1, 0, 0) 
        
    if domain_mode: glColor3f(1.0, 0.0, 1.0)
    else: glColor3f(0.8, 0.8, 0.9)
    glPushMatrix()
    glTranslatef(0, 0, 50)
    glScalef(0.05, 0.01, 5.0)
    glutSolidCube(20)
    glPopMatrix()

    # draw an extended katana blade in front of the player while swinging
    if is_swinging:
        glPushMatrix()
        # blade appears in front of the player along local Y after the player rotation
        glTranslatef(0, 55, 60)
        # make a long, thin rectangular prism to represent the katana
        if domain_expansion_triggered:
            # buffed blade: triple size and bright glowing blue/white
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            glColor4f(0.9, 0.95, 1.0, 0.95)
            glPushMatrix()
            glScalef(0.08 * 3.0, 1.8 * 3.0, 0.06 * 3.0)
            glutSolidCube(30)
            glPopMatrix()
            glDisable(GL_BLEND)
        else:
            glColor3f(0.85, 0.85, 0.9)
            glPushMatrix()
            glScalef(0.08, 1.8, 0.06)
            glutSolidCube(30)
            glPopMatrix()
        glPopMatrix()
    glColor3f(0.2, 0.1, 0.0)
    glScalef(0.2, 0.2, 1.5)
    glutSolidCube(15)
    glPopMatrix()

    if not orb_active:
        glPushMatrix()
        glTranslatef(28, -8, 60) 
        
        if domain_mode:
            glColor3f(0.0, 1.0, 1.0) 
        else:
            glColor3f(0.5, 0.8, 1.0) 
        
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


def draw_tree(x, y):
    glPushMatrix()
    glTranslatef(x, y, 0)

    glColor3f(0.3, 0.15, 0.05) 
    glPushMatrix()
    glTranslatef(0, 0, 40)
    glScalef(0.4, 0.4, 2.0) 
    glutSolidCube(40) 
    glPopMatrix()
    
    if domain_mode:
        glColor3f(0.5, 0.0, 0.0) 
    else:
        glColor3f(0.0, 0.4, 0.0)
    
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
    # When domain expansion is active render buildings in a neon wireframe style
    if domain_expansion_triggered:
        # neon color (cyan-magenta mix) and additive blending for glow
        neon_r, neon_g, neon_b = (0.8, 0.2, 1.0)
        glPushAttrib(GL_POLYGON_BIT | GL_COLOR_BUFFER_BIT)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glLineWidth(1.6)

        for i in range(height_floors):
            glPushMatrix()
            offset_x = (i * 0.8) if i % 2 == 0 else (i * -0.5)
            glTranslatef(x + offset_x, y, i * 40)
            glColor3f(neon_r, neon_g, neon_b)
            glutSolidCube(60)

            # decorative trims as wireframe
            for k in range(-1, 2, 2):
                glPushMatrix()
                glTranslatef(0, k * 30.1, 15)
                glScalef(0.6, 0.1, 0.4)
                glColor3f(neon_r, neon_g, neon_b)
                glutSolidCube(15)
                glPopMatrix()
            for l in range(-1, 2, 2):
                glPushMatrix()
                glTranslatef(l * 30.1, 0, 15)
                glScalef(0.1, 0.6, 0.4)
                glColor3f(neon_r, neon_g, neon_b)
                glutSolidCube(15)
                glPopMatrix()
            glPopMatrix()

        # restore state
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDisable(GL_BLEND)
        glPopAttrib()
        return

    # default rendering (non-domain)
    for i in range(height_floors):
        glPushMatrix()
        
        offset_x = (i * 0.8) if i % 2 == 0 else (i * -0.5)
        glTranslatef(x + offset_x, y, i * 40) 
        
        if domain_mode:
            glColor3f(1.0, 0.9, 0.8) 
        else:
            glColor3f(0.9, 0.9, 0.9)
            
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
    # If domain expansion has triggered, render scenery in wireframe neon
    if domain_expansion_triggered:
        glPushAttrib(GL_POLYGON_BIT | GL_COLOR_BUFFER_BIT)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glLineWidth(1.4)
        # draw all world geometry in neon wireframe
        for x, y, fl in building_data:
            draw_broken_building(x, y, fl)
        for x, y in tree_data:
            # draw trees as wireframe spheres/cubes via existing draw_tree
            draw_tree(x, y)
        # restore
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDisable(GL_BLEND)
        glPopAttrib()
        return

    for x, y, fl in building_data:
        draw_broken_building(x, y, fl)

    for x, y in tree_data:
        draw_tree(x, y)



# ================= INPUT =================
def keyboardListener(key, x, y):
    global keys, domain_mode, orb_active, orb_pos, orb_dir, pos_x, pos_y

    # movement key state
    if key in keys:
        keys[key] = True

    if key == b'x' or key == b'X': domain_mode = not domain_mode
    
    if key == b'f' or key == b'F':
        if not orb_active:
            orb_active = True
            orb_pos = [pos_x, pos_y, 60]
            # compute forward vector from player's facing (pos_angle)
            # The project uses pos_angle such that forward = (sin(pos_angle), -cos(pos_angle))
            rad_p = math.radians(pos_angle)
            orb_dir = [math.sin(rad_p), -math.cos(rad_p)]
        # start katana swing for 15 frames
        global is_swinging, katana_swing_timer, katana_swing_angle
        is_swinging = True
        katana_swing_timer = 15
        katana_swing_angle = 0

    if key == b' ':
        # space triggers a jump to dodge shockwaves
        global is_jumping, jump_timer
        if not is_jumping:
            is_jumping = True
            jump_timer = JUMP_FRAMES

    # Zoom controls: + to zoom in, - to zoom out
    global camera_distance
    zoom_step = 20
    if key == b'+' or key == b'=':
        camera_distance = max(30, camera_distance - zoom_step)
    elif key == b'-':
        camera_distance = camera_distance + zoom_step


def specialKeyListener(key, x, y):
    global camera_angle, camera_pitch

    # Arrow keys rotate the camera around the player or tilt it up/down.
    if key == GLUT_KEY_RIGHT:
        camera_angle -= 3
    elif key == GLUT_KEY_LEFT:
        camera_angle += 3
    elif key == GLUT_KEY_UP:
        # tilt camera upward (decrease pitch)
        camera_pitch = max(-10, camera_pitch - 3)
    elif key == GLUT_KEY_DOWN:
        # tilt camera downward (increase pitch)
        camera_pitch = min(80, camera_pitch + 3)

def keyboardUpListener(key, x, y):
    global keys
    if key in keys: keys[key] = False

def mouseListener(button, state, x, y):
    global is_swinging, person_one

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # left click also triggers a katana swing for 15 frames
        is_swinging = True
        global katana_swing_timer, katana_swing_angle
        katana_swing_timer = 15
        katana_swing_angle = 0

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        person_one = not person_one  


def update_logic():
    global pos_x, pos_y, pos_angle, is_swinging, katana_swing_angle, katana_swing_timer, orb_active, orb_pos
    global player_x, player_y, player_z, camera_angle, player_hp, dmg_cooldown, kill_count, domain_expansion_triggered
    # jump state needs to be global because we both read and assign it here
    global is_jumping, jump_timer

    base_speed = 10
    # apply domain expansion buff: double movement speed
    if domain_expansion_triggered:
        speed = base_speed * 2
    else:
        speed = base_speed

    # spawn a few enemies once (lazy init)
    if len(enemy.enemies) == 0:
        # spawn a modest number based on GRID_LENGTH
        enemy.spawn_random_enemies(12, GRID_LENGTH, margin=200)
    # update enemies
    try:
        enemy.update_enemies()
    except Exception:
        pass

    # Movement relative to camera orientation
    az = math.radians(camera_angle)
    forward_x = math.cos(az)
    forward_y = math.sin(az)

    right_x = -math.sin(az)
    right_y = math.cos(az)

    mvx = 0.0
    mvy = 0.0

    if keys[b'w']:
        mvx += forward_x
        mvy += forward_y
    if keys[b's']:
        mvx -= forward_x
        mvy -= forward_y
    if keys[b'd']:
        mvx -= right_x
        mvy -= right_y
    if keys[b'a']:
        mvx += right_x
        mvy += right_y

    # normalize to avoid faster diagonal movement
    length = math.hypot(mvx, mvy)
    if length > 0:
        mvx /= length
        mvy /= length
        pos_x += mvx * speed
        pos_y += mvy * speed
        # player should face movement direction automatically
        # update facing only when there is movement — keeps last facing after key release
        pos_angle = math.degrees(math.atan2(mvy, mvx)) + 90

    world_limit = GRID_LENGTH - 200
    pos_x = max(-world_limit, min(world_limit, pos_x))
    pos_y = max(-world_limit, min(world_limit, pos_y))

    # keep explicit player coordinates in sync
    player_x = pos_x
    player_y = pos_y
    # If the player is jumping, compute a simple parabolic vertical offset
    # based on the remaining jump_timer. We use a normalized parameter u in [0,1]
    # and the parabola h(u) = 4 * H * u * (1-u) which peaks at u=0.5 with height H.
    if is_jumping:
        elapsed = float(JUMP_FRAMES - jump_timer)
        # normalized progress 0..1
        u = 0.0
        if JUMP_FRAMES > 0:
            u = max(0.0, min(1.0, elapsed / float(JUMP_FRAMES)))
        # peak jump height (adjustable)
        peak_height = 120.0
        player_z = 4.0 * peak_height * u * (1.0 - u)
    else:
        player_z = 0.0

    # damage cooldown tick
    if dmg_cooldown > 0:
        dmg_cooldown -= 1

    # Check proximity to enemies for damage and apply knockback
    try:
        for e in enemy.enemies:
            if not e.get('alive', True):
                continue
            dx = pos_x - e.get('x', 0.0)
            dy = pos_y - e.get('y', 0.0)
            dist = math.hypot(dx, dy)
            if dist < 1.0 and dmg_cooldown == 0:
                # take damage
                player_hp = max(0, player_hp - 1)
                dmg_cooldown = DMG_COOLDOWN_FRAMES
                # small knockback away from the enemy
                if dist > 0.0001:
                    nx = dx / dist
                    ny = dy / dist
                else:
                    ang = random.uniform(0, math.pi * 2)
                    nx = math.cos(ang)
                    ny = math.sin(ang)
                knockback = 20.0
                pos_x += nx * knockback
                pos_y += ny * knockback
                # only apply one hit per cooldown window
                break
    except Exception:
        pass

    # re-clamp after knockback
    world_limit = GRID_LENGTH - 200
    pos_x = max(-world_limit, min(world_limit, pos_x))
    pos_y = max(-world_limit, min(world_limit, pos_y))

    # keep explicit player coordinates in sync after knockback
    player_x = pos_x
    player_y = pos_y

    # Boss shockwave updates: check for damage to player
    try:
        if boss.boss_instance is not None and boss.boss_instance.alive:
            dmg_from_shock = boss.boss_instance.update_and_check_shock(player_x, player_y)
            # if player is jumping they dodge shockwaves
            if not is_jumping and dmg_from_shock > 0 and dmg_cooldown == 0:
                # apply damage and knockback away from boss center
                player_hp = max(0, player_hp - dmg_from_shock)
                dmg_cooldown = DMG_COOLDOWN_FRAMES
                dx = player_x - boss.boss_instance.x
                dy = player_y - boss.boss_instance.y
                dist = math.hypot(dx, dy)
                if dist > 0.0001:
                    nx = dx / dist
                    ny = dy / dist
                else:
                    ang = random.uniform(0, math.pi * 2)
                    nx = math.cos(ang)
                    ny = math.sin(ang)
                kb = 40.0
                pos_x += nx * kb
                pos_y += ny * kb
                print(f"Player hit by shockwave for {dmg_from_shock}. HP={player_hp}")
    except Exception:
        pass

    # handle jump timer: count down and snap to ground on landing
    if is_jumping:
        jump_timer -= 1
        if jump_timer <= 0:
            is_jumping = False
            # ensure vertical coordinate resets exactly to ground level when landing
            player_z = 0.0

    # check player death
    if player_hp <= 0:
        print("Player HP reached 0. Game over.")
        try:
            glutLeaveMainLoop()
        except Exception:
            import os
            os._exit(0)

    # handle katana swing timer (15 frames total)
    if katana_swing_timer > 0:
        katana_swing_timer -= 1
        is_swinging = True
        # compute a sweep angle between 0..180 over the duration
        frames_total = 15
        progress = (frames_total - katana_swing_timer) / float(frames_total)
        katana_swing_angle = progress * 180.0
        # apply hit detection once at the mid-point of the swing
        # (single application to avoid repeated removals across frames)
        if katana_swing_timer == 7:
            try:
                # adjust hitbox when domain expansion buff is active (triple size)
                reach = 120.0 * (3.0 if domain_expansion_triggered else 1.0)
                width = 60.0 * (3.0 if domain_expansion_triggered else 1.0)
                removed = physics.remove_enemies_in_swing(enemy.enemies, player_x, player_y, pos_angle, reach=reach, width=width)
                if removed > 0:
                    kill_count += removed
                    print(f"Kill count: {kill_count}")
                # also damage boss if within swing area (use hit_by_swing)
                try:
                    if boss.boss_instance is not None and boss.boss_instance.alive:
                        if boss.boss_instance.hit_by_swing(player_x, player_y, pos_angle, reach=reach, width=width):
                            dmg = 10 * (3 if domain_expansion_triggered else 1)
                            boss.boss_instance.take_damage(dmg)
                            print(f"Boss HP: {boss.boss_instance.hp}")
                            if not boss.boss_instance.alive:
                                print("Boss defeated!")
                except Exception:
                    pass
            except Exception:
                pass
            # trigger domain expansion and clear remaining enemies when threshold met
            if kill_count >= 10 and not domain_expansion_triggered:
                domain_expansion_triggered = True
                try:
                    enemy.clear_enemies()
                except Exception:
                    pass
                try:
                    boss.spawn_boss(0.0, 0.0, 0.0, hp=500, size=500.0)
                except Exception:
                    pass
        if katana_swing_timer == 0:
            is_swinging = False
            katana_swing_angle = 0

    if orb_active:
        orb_pos[0] += orb_dir[0] * 25 
        orb_pos[1] += orb_dir[1] * 25

        # orb collision with enemies
        try:
            ox, oy = orb_pos[0], orb_pos[1]
            removed_total = 0
            # iterate backwards so we can remove safely
            for i in range(len(enemy.enemies)-1, -1, -1):
                e = enemy.enemies[i]
                if not e.get('alive', True):
                    continue
                ex = e.get('x', 0.0)
                ey = e.get('y', 0.0)
                dist = math.hypot(ox - ex, oy - ey)
                # collision threshold: orb radius (~15) + small margin
                threshold = 15.0 + e.get('size', 20.0) * 0.3
                if dist <= threshold:
                    try:
                        enemy.enemies.pop(i)
                        removed_total += 1
                    except Exception:
                        if 'alive' in e:
                            e['alive'] = False
                            removed_total += 1
            if removed_total > 0:
                kill_count += removed_total
                print(f"Kill count: {kill_count}")
                # orb disappears on hit
                orb_active = False
                # if orb hit, also damage boss if near (use hit_by_swing with direction from orb)
                try:
                    if boss.boss_instance is not None and boss.boss_instance.alive:
                        # approximate an angle from orb direction
                        ang = math.degrees(math.atan2(orb_dir[1], orb_dir[0]))
                        if boss.boss_instance.hit_by_swing(ox, oy, ang, reach=30.0, width=30.0):
                            boss.boss_instance.take_damage(15)
                            print(f"Boss HP: {boss.boss_instance.hp}")
                            if not boss.boss_instance.alive:
                                print("Boss defeated!")
                except Exception:
                    pass
                if kill_count >= 10 and not domain_expansion_triggered:
                    domain_expansion_triggered = True
                    try:
                        enemy.clear_enemies()
                    except Exception:
                        pass
                    try:
                        boss.spawn_boss(0.0, 0.0, 0.0, hp=500, size=500.0)
                    except Exception:
                        pass
        except Exception:
            pass

        if abs(orb_pos[0]) > GRID_LENGTH or abs(orb_pos[1]) > GRID_LENGTH:
            orb_active = False

# ================= RENDER =================
def showScreen():

    update_logic()

    # dramatic visual shift when domain expansion is triggered
    if domain_expansion_triggered:
        # very dark red / near-black background
        glClearColor(0.06, 0.01, 0.02, 1.0)
    elif domain_mode:
        glClearColor(0.08, 0.0, 0.0, 1.0)
    else:
        glClearColor(0.4, 0.3, 0.2, 1.0)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    setupCamera()

    draw_ground()
    draw_scenery()
    # draw enemies in the main render loop (after scenery so they appear in world)
    try:
        enemy.draw_enemies()
    except Exception:
        pass
    # draw boss if present
    try:
        boss.draw_boss()
    except Exception:
        pass
    # draw boss healthbar UI if boss alive
    try:
        boss.draw_boss_healthbar()
    except Exception:
        pass
    draw_player()

    if orb_active:
        draw_orb_projectile()
    glutSwapBuffers()


# ================= MAIN =================
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutCreateWindow(b"Gate Base System")

    glEnable(GL_DEPTH_TEST)
    generate_world_data()
    glClearColor(0.5, 0.8, 0.9, 1)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(showScreen)

    glutKeyboardUpFunc(keyboardUpListener)

    glutMainLoop() 


if __name__ == "__main__":
    main()
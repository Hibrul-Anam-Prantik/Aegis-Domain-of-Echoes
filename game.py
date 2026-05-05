from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time
import sys

# ---------------- PHYSICS ----------------

def remove_enemies_in_swing(enemies, px, py, angle_deg, reach=120.0, width=60.0):
    """
    Remove enemies inside a rectangular swing hitbox in front of the player.

    - enemies: list of enemy dicts with 'x' and 'y' keys (mutated in-place)
    - px,py: player position
    - angle_deg: player facing in degrees (same convention as pos_angle)
    - reach: forward distance of the hitbox
    - width: total lateral width of the hitbox

    Returns the number of enemies removed.
    """
    if not enemies:
        return 0

    rad = math.radians(angle_deg)
    # forward vector used by project: forward = (sin(angle), -cos(angle))
    fx = math.sin(rad)
    fy = -math.cos(rad)
    # right vector perpendicular to forward
    rx = fy
    ry = -fx

    half_w = width * 0.5

    removed = 0
    # iterate backwards so we can remove from list safely
    for i in range(len(enemies)-1, -1, -1):
        e = enemies[i]
        ex = e.get('x', 0.0)
        ey = e.get('y', 0.0)
        dx = ex - px
        dy = ey - py
        forward_dist = dx * fx + dy * fy
        lateral = dx * rx + dy * ry
        # optionally take enemy size into account
        size = e.get('size', 20.0)
        # enlarge hit area slightly by enemy size
        if 0 <= forward_dist <= (reach + size*0.5) and abs(lateral) <= (half_w + size*0.5):
            try:
                enemies.pop(i)
                removed += 1
            except Exception:
                # if removal fails, mark as dead if supported
                if 'alive' in e:
                    e['alive'] = False
                    removed += 1
    return removed


# ---------------- ENEMIES ----------------

# public enemy list
enemies = []

# tuning params (adjustable)
enemy_speed = 3.0
enemy_radius = 20.0
separation_distance = 40.0
separation_strength = 0.12


def spawn_enemy(x=None, y=None):
    """Spawn a single enemy at (x,y) or random position if None."""
    if x is None:
        x = random.uniform(-800, 800)
    if y is None:
        y = random.uniform(-800, 800)
    enemies.append({'x': x, 'y': y, 'z': 0.0, 'size': enemy_radius, 'alive': True})


def clear_enemies():
    """Remove all enemies from the world."""
    global enemies
    enemies[:] = []


def spawn_random_enemies(n, arena_limit, margin=200):
    """Spawn n enemies within arena_limit minus margin."""
    for _ in range(n):
        x = random.uniform(-arena_limit + margin, arena_limit - margin)
        y = random.uniform(-arena_limit + margin, arena_limit - margin)
        spawn_enemy(x, y)


def update_enemies(player_x, player_y):
    """Move enemies toward the player and apply simple separation."""
    global enemies, enemy_speed, separation_distance, separation_strength
    if not enemies:
        return

    # Move toward player
    for i, e in enumerate(enemies):
        if not e.get('alive', True):
            continue

        dx = player_x - e['x']
        dy = player_y - e['y']
        dist = math.hypot(dx, dy)

        if dist > 0.0001:
            if dist > 10.0:
                nx = dx / dist
                ny = dy / dist
                e['x'] += nx * enemy_speed
                e['y'] += ny * enemy_speed

    # Simple separation to reduce overlap
    for i, e in enumerate(enemies):
        if not e.get('alive', True):
            continue
        for j, other in enumerate(enemies):
            if i == j or not other.get('alive', True):
                continue
            dx = e['x'] - other['x']
            dy = e['y'] - other['y']
            d = math.hypot(dx, dy)
            if d > 0 and d < separation_distance:
                push = (separation_distance - d) / separation_distance * separation_strength * enemy_speed
                e['x'] += (dx / d) * push
                e['y'] += (dy / d) * push

    # clamp to world bounds if GRID_LENGTH is available
    try:
        limit = GRID_LENGTH - 200
        for e in enemies:
            e['x'] = max(-limit, min(limit, e['x']))
            e['y'] = max(-limit, min(limit, e['y']))
    except Exception:
        pass


def draw_enemy(e):
    x, y = e['x'], e['y']
    z = e.get('z', 0.0)
    s = e.get('size', enemy_radius)

    glPushMatrix()
    glTranslatef(x, y, z)

    glColor3f(0.0, 0.0, 0.0)
    for sgn in [-1, 1]:
        glPushMatrix()
        glTranslatef(sgn * 12, 0, 15)
        glScalef(0.4, 0.4, 1.2)
        glutSolidCube(25)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 50)
    glScalef(0.7, 0.4, 1.2)
    glutSolidCube(40)
    glPopMatrix()

    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side * 25, -10, 60)
        glRotatef(-20, 1, 0, 0)
        glScalef(0.6, 0.15, 0.3)
        glutSolidCube(30)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 95)
    glutSolidSphere(12, 16, 16)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(x, y, z + 50)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.05, 0.05, 0.05, 0.12)
    glutSolidSphere(s * 0.9, 12, 12)
    glDisable(GL_BLEND)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(x, y, max(1.0, z))
    glColor3f(0.01, 0.01, 0.01)
    glPushMatrix()
    glScalef(0.06, 0.06, 0.001)
    glutSolidCube(18)
    glPopMatrix()
    glPopMatrix()
    # pop the outermost matrix pushed at the start of draw_enemy
    glPopMatrix()


def draw_enemies():
    for e in enemies:
        if not e.get('alive', True):
            continue
        draw_enemy(e)


def enemy_near(x, y, radius):
    r2 = radius * radius
    for e in enemies:
        if not e.get('alive', True):
            continue
        dx = e['x'] - x
        dy = e['y'] - y
        if dx * dx + dy * dy <= r2:
            return True
    return False


# ---------------- BOSS ----------------

class Boss:
    def __init__(self, x=0.0, y=0.0, z=0.0, hp=500, size=400.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.hp = int(hp)
        self.hp_max = int(hp)
        self.size = float(size)
        self.alive = True
        self.last_shock_time = time.time()
        self.shock_interval = 4.0
        self.rings = []

    def draw(self):
        if not self.alive:
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z + self.size * 0.1)

        glPushMatrix()
        glColor3f(0.12, 0.05, 0.15)
        glTranslatef(0, 0, self.size * 0.3)
        glScalef(self.size * 0.3, self.size * 0.3, self.size * 0.6)
        glutSolidSphere(1.0 * 20, 24, 24)
        glPopMatrix()

        glPushMatrix()
        glColor3f(0.9, 0.78, 0.72)
        glTranslatef(0, 0, self.size * 0.75)
        glutSolidSphere(self.size * 0.08, 20, 20)
        glPopMatrix()

        glPushMatrix()
        glColor3f(0.22, 0.06, 0.3)
        glTranslatef(0, 0, self.size * 0.05)
        glScalef(1.0, 1.0, 0.6)
        glutSolidSphere(self.size * 0.4, 28, 16)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, 2)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glColor4f(0.8, 0.2, 0.9, 0.15)
        glutSolidSphere(self.size * 0.35, 24, 12)
        glDisable(GL_BLEND)
        glPopMatrix()

        glPopMatrix()

    def update(self):
        pass

    def spawn_shockwave(self):
        ring = {
            'radius': 0.0,
            'speed': max(150.0, self.size * 0.6),
            'thickness': max(8.0, self.size * 0.03),
            'max_radius': self.size * 3.0,
            'hit_player': False,
            'created': time.time(),
        }
        self.rings.append(ring)

    def update_and_check_shock(self, px=None, py=None):
        now = time.time()
        total_damage = 0
        if now - self.last_shock_time >= self.shock_interval:
            self.last_shock_time = now
            self.spawn_shockwave()

        new_rings = []
        for r in self.rings:
            dt = now - r.get('created', now)
            r['radius'] += r['speed'] * 0.016
            if px is not None and py is not None and not r.get('hit_player', False):
                dx = px - self.x
                dy = py - self.y
                dist = math.hypot(dx, dy)
                if abs(dist - r['radius']) <= (r['thickness'] * 0.5):
                    r['hit_player'] = True
                    total_damage += 8
            if r['radius'] <= r['max_radius']:
                new_rings.append(r)
        self.rings = new_rings
        return total_damage

    def take_damage(self, amount):
        self.hp -= int(amount)
        if self.hp <= 0:
            self.alive = False

    def hit_by_swing(self, px, py, angle_deg, reach=120.0, width=60.0):
        rad = math.radians(angle_deg)
        fx = math.sin(rad)
        fy = -math.cos(rad)
        rx = fy
        ry = -fx

        dx = self.x - px
        dy = self.y - py
        forward_dist = dx * fx + dy * fy
        lateral = dx * rx + dy * ry

        half_w = width * 0.5
        size_half = self.size * 0.5

        if 0 <= forward_dist <= (reach + size_half) and abs(lateral) <= (half_w + size_half):
            return True
        return False

    def aabb_hit(self, px, py, reach=120.0, width=60.0):
        half = self.size * 0.6
        if px < (self.x - half) or px > (self.x + half):
            return False
        if py < (self.y - half) or py > (self.y + half):
            return False
        return True

    def take_damage_area(self, amount):
        self.take_damage(amount)


boss_instance = None


def spawn_boss(x=0.0, y=0.0, z=0.0, hp=500, size=400.0):
    global boss_instance
    if boss_instance is None or not getattr(boss_instance, 'alive', False):
        boss_instance = Boss(x, y, z, hp=hp, size=size)
    return boss_instance


def clear_boss():
    global boss_instance
    boss_instance = None


def draw_boss():
    global boss_instance
    if boss_instance is None:
        return
    boss_instance.draw()
    if getattr(boss_instance, 'rings', None):
        for r in boss_instance.rings:
            glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_LINE_BIT)
            try:
                glPushMatrix()
                glTranslatef(boss_instance.x, boss_instance.y, 1.0)
                glColor4f(0.6, 0.2, 0.9, 0.6)
                glDisable(GL_LIGHTING)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE)
                sides = 64
                radius = r['radius']
                glLineWidth(2.0)
                glBegin(GL_LINE_LOOP)
                for i in range(sides):
                    theta = 2.0 * math.pi * float(i) / float(sides)
                    glVertex3f(math.cos(theta) * radius, math.sin(theta) * radius, 0.5)
                glEnd()
                glPopMatrix()
            finally:
                glPopAttrib()
        glColor3f(1.0, 1.0, 1.0)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)


def draw_boss_healthbar():
    global boss_instance
    if boss_instance is None or not getattr(boss_instance, 'alive', False):
        return

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT)
    bar_w = 800
    bar_h = 28
    x0 = 100
    y0 = 760
    try:
        warning = globals().get('shock_warning', False)
    except Exception:
        warning = False
    if warning:
        glColor3f(0.12, 0.02, 0.18)
    else:
        glColor3f(0.05, 0.05, 0.05)
    glBegin(GL_QUADS)
    glVertex2f(x0, y0)
    glVertex2f(x0 + bar_w, y0)
    glVertex2f(x0 + bar_w, y0 + bar_h)
    glVertex2f(x0, y0 + bar_h)
    glEnd()

    hp_frac = max(0.0, min(1.0, float(boss_instance.hp) / float(boss_instance.hp_max)))
    glColor3f(0.8 * (1.0 - hp_frac) + 0.1, 0.2 * hp_frac + 0.1, 0.9 * hp_frac + 0.1)
    glBegin(GL_QUADS)
    glVertex2f(x0 + 4, y0 + 4)
    glVertex2f(x0 + 4 + (bar_w - 8) * hp_frac, y0 + 4)
    glVertex2f(x0 + 4 + (bar_w - 8) * hp_frac, y0 + 4 + (bar_h - 8))
    glVertex2f(x0 + 4, y0 + 4 + (bar_h - 8))
    glEnd()

    if warning:
        glColor3f(0.9, 0.5, 1.0)
    else:
        glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x0, y0)
    glVertex2f(x0 + bar_w, y0)
    glVertex2f(x0 + bar_w, y0 + bar_h)
    glVertex2f(x0, y0 + bar_h)
    glEnd()

    glPopAttrib()
    glEnable(GL_DEPTH_TEST)

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def update_boss():
    global boss_instance
    if boss_instance is None:
        return
    boss_instance.update()
# ---------------- PLAYER / GAME ----------------

# Camera / world / player variables
camera_angle = 0
camera_pitch = 15
camera_distance = 300
camera_height = 90
fov_y = 120
GRID_LENGTH = 1000
pos_x = 0
pos_y = 0
pos_angle = 0
player_x = pos_x
player_y = pos_y
player_z = 0
player_hp = 100
dmg_cooldown = 0
DMG_COOLDOWN_FRAMES = 30
person_one = False
kill_count = 0
domain_expansion_triggered = False
# shock warning flag
shock_warning = False

building_data = []
tree_data = []
ash_particles = []

is_swinging = False
katana_swing_angle = 0
katana_swing_timer = 0
orb_active = False
orb_pos = [0,0,0]
orb_dir = [0,0]
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
                tree_data.append((x + random.uniform(-40,40), y + random.uniform(-40,40)))
            tree_data.append((x + random.uniform(-100, 100), y + random.uniform(-100,100)))
            counter += 1
    for _ in range(8000):
        ash_particles.append((random.uniform(-GRID_LENGTH, GRID_LENGTH), random.uniform(-GRID_LENGTH, GRID_LENGTH), random.uniform(0.15, 0.35)))

# Camera helpers
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
    global pos_x, pos_y, pos_angle, domain_expansion_triggered, player_z, domain_mode, shock_warning
    glPushMatrix()
    # isolate GL state for player so domain/shock-mode lighting changes don't leak
    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT)
    try:
        if domain_expansion_triggered or shock_warning:
            glDisable(GL_LIGHTING)
        glTranslatef(pos_x, pos_y, player_z + 5)
        glRotatef(pos_angle, 0, 0, 1)

        if domain_expansion_triggered or shock_warning:
            glColor3f(0.22, 0.04, 0.6)
        else:
            glColor3f(0.1, 0.1, 0.1)
        for s in [-1, 1]:
            glPushMatrix()
            glTranslatef(s * 12, 0, 15)
            glScalef(0.4, 0.4, 1.2)
            glutSolidCube(25)
            glPopMatrix()

        glPushMatrix()
        if domain_expansion_triggered or shock_warning:
            glColor3f(0.36, 0.18, 0.9)
        else:
            glColor3f(0.2, 0.2, 0.2)
        glTranslatef(0, 0, 50)
        glScalef(0.7, 0.4, 1.2)
        glutSolidCube(40)
        glPopMatrix()

        for s in [-1, 1]:
            glPushMatrix()
            if domain_expansion_triggered or shock_warning: glColor3f(0.4, 0, 0.6)
            else: glColor3f(0.3, 0.2, 0.15)
            glTranslatef(s * 25, 0, 75)
            glRotatef(s * 20, 0, 1, 0)
            glScalef(0.8, 0.6, 0.3)
            glutSolidCube(30)
            glPopMatrix()

        glPushMatrix()
        if domain_expansion_triggered or shock_warning: glColor3f(0.0, 1.0, 1.0)
        else: glColor3f(0.0, 0.5, 0.8)
        glTranslatef(0, -10, 60)
        glutSolidSphere(8, 16, 16)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, 95)
        if domain_expansion_triggered or shock_warning:
            glColor3f(0.18, 0.12, 0.65)
        else:
            glColor3f(0.15, 0.15, 0.15)
        glutSolidSphere(12, 16, 16)
        if domain_expansion_triggered:
            glColor3f(1.0, 0.0, 1.0)
        else:
            glColor3f(0.0, 1.0, 1.0)
        glPushMatrix()
        glTranslatef(0, -8, 2)
        glScalef(1.2, 0.2, 0.3)
        glutSolidCube(15)
        glPopMatrix()
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, 115)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glColor4f(1.0, 0.9, 0.2, 0.9)
        glutSolidSphere(5, 12, 12)
        glDisable(GL_BLEND)
        glPopMatrix()

    finally:
        glPopAttrib()

    glPushMatrix()
    glTranslatef(-28, -5, 55)
    global is_swinging, katana_swing_angle
    if is_swinging:
        glRotatef(-katana_swing_angle, 0, 1, 0)
    else:
        glRotatef(-45, 1, 0, 0)
    if domain_expansion_triggered: glColor3f(1.0, 0.0, 1.0)
    else: glColor3f(0.8, 0.8, 0.9)
    glPushMatrix()
    glTranslatef(0, 0, 50)
    glScalef(0.05, 0.01, 5.0)
    glutSolidCube(20)
    glPopMatrix()

    if is_swinging:
        glPushMatrix()
        glTranslatef(0, 55, 60)
        if domain_expansion_triggered:
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
        if domain_expansion_triggered:
            glColor3f(0.0, 1.0, 1.0)
        else:
            glColor3f(0.5, 0.8, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        if domain_expansion_triggered: glColor4f(0, 1, 1, 0.4)
        else: glColor4f(0.5, 0.8, 1, 0.3)
        glutSolidSphere(15, 20, 20)
        if domain_expansion_triggered: glColor3f(1, 1, 1)
        else: glColor3f(0.7, 0.9, 1.0)
        glutSolidSphere(7, 16, 16)
        glDisable(GL_BLEND)
        glPopMatrix()

    if domain_expansion_triggered:
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
    if domain_expansion_triggered:
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
    if domain_expansion_triggered:
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
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDisable(GL_BLEND)
        glPopAttrib()
        return
    for i in range(height_floors):
        glPushMatrix()
        offset_x = (i * 0.8) if i % 2 == 0 else (i * -0.5)
        glTranslatef(x + offset_x, y, i * 40)
        if domain_expansion_triggered:
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
    if domain_expansion_triggered:
        glPushAttrib(GL_POLYGON_BIT | GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT)
        glDisable(GL_LIGHTING)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glLineWidth(1.4)
        for x, y, fl in building_data:
            draw_broken_building(x, y, fl)
        for x, y in tree_data:
            draw_tree(x, y)
        glPopAttrib()
        return
    glPushAttrib(GL_POLYGON_BIT | GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT)
    try:
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glColor3f(0.9, 0.9, 0.9)
        for x, y, fl in building_data:
            draw_broken_building(x, y, fl)
        for x, y in tree_data:
            draw_tree(x, y)
    finally:
        glPopAttrib()


def keyboardListener(key, x, y):
    global keys, domain_expansion_triggered, orb_active, orb_pos, orb_dir, pos_x, pos_y, pos_angle
    global is_swinging, katana_swing_timer, katana_swing_angle, camera_distance
    if key in keys:
        keys[key] = True
    if key == b'x' or key == b'X':
        # domain mode toggles a non-gameplay visual mode
        pass
    if key == b'f' or key == b'F':
        if not orb_active:
            orb_active = True
            orb_pos[:] = [pos_x, pos_y, 60]
            rad_p = math.radians(pos_angle)
            orb_dir[0] = math.sin(rad_p)
            orb_dir[1] = -math.cos(rad_p)
        is_swinging = True
        katana_swing_timer = 15
        katana_swing_angle = 0
    if key == b' ':
        global is_jumping, jump_timer
        if not is_jumping:
            is_jumping = True
            jump_timer = JUMP_FRAMES
    zoom_step = 20
    if key == b'+' or key == b'=':
        camera_distance = max(30, camera_distance - zoom_step)
    elif key == b'-':
        camera_distance = camera_distance + zoom_step


def specialKeyListener(key, x, y):
    global camera_angle, camera_pitch
    if key == GLUT_KEY_RIGHT:
        camera_angle -= 3
    elif key == GLUT_KEY_LEFT:
        camera_angle += 3
    elif key == GLUT_KEY_UP:
        camera_pitch = max(-10, camera_pitch - 3)
    elif key == GLUT_KEY_DOWN:
        camera_pitch = min(80, camera_pitch + 3)


def keyboardUpListener(key, x, y):
    global keys
    if key in keys:
        keys[key] = False


def mouseListener(button, state, x, y):
    global is_swinging, person_one, katana_swing_timer, katana_swing_angle
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        is_swinging = True
        katana_swing_timer = 15
        katana_swing_angle = 0
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        person_one = not person_one


def update_logic():
    global pos_x, pos_y, pos_angle, is_swinging, katana_swing_angle, katana_swing_timer, orb_active, orb_pos
    global player_x, player_y, player_z, camera_angle, player_hp, dmg_cooldown, kill_count, domain_expansion_triggered
    global is_jumping, jump_timer

    base_speed = 10
    if domain_expansion_triggered:
        speed = base_speed * 2
    else:
        speed = base_speed

    if len(enemies) == 0:
        spawn_random_enemies(12, GRID_LENGTH, margin=200)
    try:
        update_enemies(player_x, player_y)
    except Exception:
        pass

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

    if is_jumping:
        elapsed = float(JUMP_FRAMES - jump_timer)
        u = 0.0
        if JUMP_FRAMES > 0:
            u = max(0.0, min(1.0, elapsed / float(JUMP_FRAMES)))
        peak_height = 120.0
        player_z = 4.0 * peak_height * u * (1.0 - u)
    else:
        player_z = 0.0

    if dmg_cooldown > 0:
        dmg_cooldown -= 1

    try:
        for e in list(enemies):
            if not e.get('alive', True):
                continue
            dx = pos_x - e.get('x', 0.0)
            dy = pos_y - e.get('y', 0.0)
            dist = math.hypot(dx, dy)
            if dist < 1.0 and dmg_cooldown == 0:
                player_hp = max(0, player_hp - 1)
                dmg_cooldown = DMG_COOLDOWN_FRAMES
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
                break
    except Exception:
        pass

    world_limit = GRID_LENGTH - 200
    pos_x = max(-world_limit, min(world_limit, pos_x))
    pos_y = max(-world_limit, min(world_limit, pos_y))
    player_x = pos_x
    player_y = pos_y

    try:
        if boss_instance is not None and boss_instance.alive:
            dmg_from_shock = boss_instance.update_and_check_shock(player_x, player_y)
            if not is_jumping and dmg_from_shock > 0 and dmg_cooldown == 0:
                player_hp = max(0, player_hp - dmg_from_shock)
                dmg_cooldown = DMG_COOLDOWN_FRAMES
                dx = player_x - boss_instance.x
                dy = player_y - boss_instance.y
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

    if is_jumping:
        jump_timer -= 1
        if jump_timer <= 0:
            is_jumping = False
            player_z = 0.0

    if player_hp <= 0:
        print("Player HP reached 0. Game over.")
        try:
            glutLeaveMainLoop()
        except Exception:
            import os
            os._exit(0)

    if katana_swing_timer > 0:
        katana_swing_timer -= 1
        is_swinging = True
        frames_total = 15
        progress = (frames_total - katana_swing_timer) / float(frames_total)
        katana_swing_angle = progress * 180.0
        if katana_swing_timer == 7:
            try:
                reach = 120.0 * (3.0 if domain_expansion_triggered else 1.0)
                width = 60.0 * (3.0 if domain_expansion_triggered else 1.0)
                removed = remove_enemies_in_swing(enemies, player_x, player_y, pos_angle, reach=reach, width=width)
                if removed > 0:
                    kill_count += removed
                    print(f"Kill count: {kill_count}")
                try:
                    if boss_instance is not None and boss_instance.alive:
                        if boss_instance.hit_by_swing(player_x, player_y, pos_angle, reach=reach, width=width):
                            dmg = 10 * (3 if domain_expansion_triggered else 1)
                            boss_instance.take_damage(dmg)
                            print(f"Boss HP: {boss_instance.hp}")
                            if not boss_instance.alive:
                                print("Boss defeated!")
                except Exception:
                    pass
            except Exception:
                pass
            if kill_count >= 10 and not domain_expansion_triggered:
                domain_expansion_triggered = True
                try:
                    clear_enemies()
                except Exception:
                    pass
                try:
                    spawn_boss(0.0, 0.0, 0.0, hp=500, size=500.0)
                except Exception:
                    pass
        if katana_swing_timer == 0:
            is_swinging = False
            katana_swing_angle = 0

    if orb_active:
        orb_pos[0] += orb_dir[0] * 25
        orb_pos[1] += orb_dir[1] * 25
        try:
            ox, oy = orb_pos[0], orb_pos[1]
            removed_total = 0
            for i in range(len(enemies)-1, -1, -1):
                e = enemies[i]
                if not e.get('alive', True):
                    continue
                ex = e.get('x', 0.0)
                ey = e.get('y', 0.0)
                dist = math.hypot(ox - ex, oy - ey)
                threshold = 15.0 + e.get('size', 20.0) * 0.3
                if dist <= threshold:
                    try:
                        enemies.pop(i)
                        removed_total += 1
                    except Exception:
                        if 'alive' in e:
                            e['alive'] = False
                            removed_total += 1
            if removed_total > 0:
                kill_count += removed_total
                print(f"Kill count: {kill_count}")
                orb_active = False
                try:
                    if boss_instance is not None and boss_instance.alive:
                        ang = math.degrees(math.atan2(orb_dir[1], orb_dir[0]))
                        if boss_instance.hit_by_swing(ox, oy, ang, reach=30.0, width=30.0):
                            boss_instance.take_damage(15)
                            print(f"Boss HP: {boss_instance.hp}")
                            if not boss_instance.alive:
                                print("Boss defeated!")
                except Exception:
                    pass
                if kill_count >= 10 and not domain_expansion_triggered:
                    domain_expansion_triggered = True
                    try:
                        clear_enemies()
                    except Exception:
                        pass
                    try:
                        spawn_boss(0.0, 0.0, 0.0, hp=500, size=500.0)
                    except Exception:
                        pass
        except Exception:
            pass
        if abs(orb_pos[0]) > GRID_LENGTH or abs(orb_pos[1]) > GRID_LENGTH:
            orb_active = False


def showScreen():
    update_logic()
    global shock_warning
    shock_warning = False
    try:
        if boss_instance is not None and boss_instance.alive:
            t_until = (boss_instance.last_shock_time + boss_instance.shock_interval) - time.time()
            if 0.0 <= t_until <= 1.0:
                shock_warning = True
    except Exception:
        shock_warning = False
    if domain_expansion_triggered:
        glClearColor(0.06, 0.01, 0.02, 1.0)
    else:
        glClearColor(0.4, 0.3, 0.2, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setupCamera()
    draw_ground()
    if domain_expansion_triggered:
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT)
        try:
            glColor3f(0.7, 0.1, 0.9)
            draw_scenery()
        finally:
            glPopAttrib()
    else:
        draw_scenery()
    try:
        draw_enemies()
    except Exception:
        pass
    try:
        draw_boss()
    except Exception:
        pass
    try:
        draw_boss_healthbar()
    except Exception:
        pass
    draw_player()
    if orb_active:
        draw_orb_projectile()
    glutSwapBuffers()


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

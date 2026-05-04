from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

"""Simple shadow-enemy module.

API:
- enemies: list of enemy dicts
- spawn_enemy(x, y, size=20)
- spawn_random_enemies(count, grid_length, margin=0)
- clear_enemies()
- update_enemies()
- draw_enemies()
- enemy_near(x, y, radius) -> True/False

Integration notes:
- Call spawn_random_enemies(...) once (for example in generate_world_data()).
- In your main update loop call update_enemies().
- In your render loop call draw_enemies() after drawing the world.

Enemies are drawn as dark spheres with a faint ash-colored aura and will
wander slowly. This file only uses the allowed OpenGL calls.
"""

# public enemy list
enemies = []

# parameters
WANDER_STRENGTH = 0.6  # how much enemies wander each update
MAX_SPEED = 1.8


def spawn_enemy(x, y, size=20):
    """Spawn a single shadow enemy at (x,y).

    Returns the created enemy dict.
    """
    e = {
        'x': float(x),
        'y': float(y),
        'z': 0.0,
        'size': float(size),
        'hp': 100,
        'alive': True,
        'vx': 0.0,
        'vy': 0.0,
    }
    enemies.append(e)
    return e


def spawn_random_enemies(count, grid_length, margin=0, size_range=(12, 32)):
    """Spawn `count` enemies randomly within [-grid_length+margin, grid_length-margin]."""
    limit = max(0, grid_length - margin)
    for _ in range(count):
        x = random.uniform(-limit, limit)
        y = random.uniform(-limit, limit)
        size = random.uniform(size_range[0], size_range[1])
        spawn_enemy(x, y, size)


def clear_enemies():
    enemies.clear()


def update_enemies():
    """Simple per-frame update for enemies: random wandering and clamped speed."""
    for e in enemies:
        if not e['alive']:
            continue
        # random wander
        ang = random.uniform(0, math.pi * 2)
        e['vx'] += math.cos(ang) * (WANDER_STRENGTH * 0.1)
        e['vy'] += math.sin(ang) * (WANDER_STRENGTH * 0.1)

        # clamp speed
        speed = math.hypot(e['vx'], e['vy'])
        if speed > MAX_SPEED:
            e['vx'] = (e['vx'] / speed) * MAX_SPEED
            e['vy'] = (e['vy'] / speed) * MAX_SPEED

        # apply velocity
        e['x'] += e['vx']
        e['y'] += e['vy']

        # slow down a bit (friction)
        e['vx'] *= 0.96
        e['vy'] *= 0.96


def draw_enemy(e):
    """Draw a single shadow enemy using simple OpenGL primitives."""
    x, y, z = e['x'], e['y'], e['z']
    s = e['size']

    # draw dark body
    glPushMatrix()
    glTranslatef(x, y, z + s * 0.6)
    glColor3f(0.03, 0.03, 0.03)  # nearly black
    glutSolidSphere(s * 0.6, 18, 18)
    glPopMatrix()

    # draw ash aura (semi-transparent)
    glPushMatrix()
    glTranslatef(x, y, z + s * 0.6)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.25, 0.25, 0.25, 0.28)  # ash gray with alpha
    glutSolidSphere(s * 1.1, 12, 12)
    glDisable(GL_BLEND)
    glPopMatrix()

    # small shadow on ground (flat)
    glPushMatrix()
    glTranslatef(x, y, 1.0)
    glColor3f(0.02, 0.02, 0.02)
    # scale a flattened cube as simple ground shadow
    glPushMatrix()
    glScalef(s * 0.05, s * 0.03, 0.001)
    glutSolidCube(20)
    glPopMatrix()
    glPopMatrix()


def draw_enemies():
    for e in enemies:
        if not e.get('alive', True):
            continue
        draw_enemy(e)


def enemy_near(x, y, radius):
    """Return True if any alive enemy is within radius of (x,y)."""
    r2 = radius * radius
    for e in enemies:
        if not e.get('alive', True):
            continue
        dx = e['x'] - x
        dy = e['y'] - y
        if dx * dx + dy * dy <= r2:
            return True
    return False


# optional small self-test when run directly
if __name__ == '__main__':
    # spawn a few enemies for quick visual test when importing into a running app
    spawn_random_enemies(10, 400, margin=50)
    print('spawned', len(enemies))

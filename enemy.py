from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

"""Shadow enemy module that draws enemies matching the player's blocky model
but colored black and with arms extended forward (zombie pose).

API:
- enemies: list
- spawn_enemy(x, y, size=20)
- spawn_random_enemies(count, grid_length, margin=0)
- update_enemies()
- draw_enemies()
- clear_enemies()
"""

# public list
enemies = []

# simple movement parameters
WANDER_STRENGTH = 0.6
MAX_SPEED = 1.8


def spawn_enemy(x, y, size=20):
    e = {
        'x': float(x),
        'y': float(y),
        'z': 0.0,
        'size': float(size),
        'alive': True,
        'vx': 0.0,
        'vy': 0.0,
    }
    enemies.append(e)
    return e


def spawn_random_enemies(count, grid_length, margin=0, size_range=(20, 28)):
    limit = max(0, grid_length - margin)
    for _ in range(count):
        x = random.uniform(-limit, limit)
        y = random.uniform(-limit, limit)
        size = random.uniform(size_range[0], size_range[1])
        spawn_enemy(x, y, size)


def clear_enemies():
    enemies.clear()


def update_enemies():
    for e in enemies:
        if not e.get('alive', True):
            continue
        ang = random.uniform(0, math.pi * 2)
        e['vx'] += math.cos(ang) * (WANDER_STRENGTH * 0.05)
        e['vy'] += math.sin(ang) * (WANDER_STRENGTH * 0.05)

        speed = math.hypot(e['vx'], e['vy'])
        if speed > MAX_SPEED:
            e['vx'] = (e['vx'] / speed) * MAX_SPEED
            e['vy'] = (e['vy'] / speed) * MAX_SPEED

        e['x'] += e['vx']
        e['y'] += e['vy']

        e['vx'] *= 0.95
        e['vy'] *= 0.95


def draw_enemy(e):
    x, y, z = e['x'], e['y'], e['z']
    s = e['size']

    # Draw the blocky player-like model but in black color
    glPushMatrix()
    glTranslatef(x, y, 0)

    # torso side blocks
    glColor3f(0.0, 0.0, 0.0)
    for sgn in [-1, 1]:
        glPushMatrix()
        glTranslatef(sgn * 12, 0, 15)
        glScalef(0.4, 0.4, 1.2)
        glutSolidCube(25)
        glPopMatrix()

    # torso center
    glPushMatrix()
    glTranslatef(0, 0, 50)
    glScalef(0.7, 0.4, 1.2)
    glutSolidCube(40)
    glPopMatrix()

    # arms forward (zombie pose) - scaled rectangles in front
    for side in [-1, 1]:
        glPushMatrix()
        # position in front of torso
        glTranslatef(side * 25, -10, 60)
        # rotate so arms point forward a bit
        glRotatef(-20, 1, 0, 0)
        glScalef(0.6, 0.15, 0.3)
        glutSolidCube(30)
        glPopMatrix()

    # head
    glPushMatrix()
    glTranslatef(0, 0, 95)
    glutSolidSphere(12, 16, 16)
    glPopMatrix()

    # optional faint aura (very subtle)
    glPushMatrix()
    glTranslatef(x, y, 50)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.05, 0.05, 0.05, 0.12)
    glutSolidSphere(s * 0.9, 12, 12)
    glDisable(GL_BLEND)
    glPopMatrix()

    # ground shadow
    glPushMatrix()
    glTranslatef(x, y, 1.0)
    glColor3f(0.01, 0.01, 0.01)
    glPushMatrix()
    glScalef(0.06, 0.06, 0.001)
    glutSolidCube(18)
    glPopMatrix()
    glPopMatrix()
    # pop the matrix pushed for the whole enemy model
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


if __name__ == '__main__':
    spawn_random_enemies(6, 300, margin=50)
    print('spawned', len(enemies))

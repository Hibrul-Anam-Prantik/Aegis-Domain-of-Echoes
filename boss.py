from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time


class Boss:
    """A simple boss entity rendered as a towering obelisk.

    Attributes:
        x,y,z: position
        hp: health points
        size: base size for rendering (height scale)
        alive: bool
    """
    def __init__(self, x=0.0, y=0.0, z=0.0, hp=500, size=400.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.hp = int(hp)
        self.hp_max = int(hp)
        self.size = float(size)
        self.alive = True
        # shockwave state
        self.last_shock_time = time.time()
        self.shock_interval = 4.0
        self.rings = []

    def draw(self):
        if not self.alive:
            return
        glPushMatrix()
        # position the figure
        glTranslatef(self.x, self.y, self.z + self.size * 0.1)
        # torso
        glPushMatrix()
        glColor3f(0.12, 0.05, 0.15)
        glTranslatef(0, 0, self.size * 0.3)
        glScalef(self.size * 0.3, self.size * 0.3, self.size * 0.6)
        glutSolidSphere(1.0 * 20, 24, 24)
        glPopMatrix()

        # head
        glPushMatrix()
        glColor3f(0.9, 0.78, 0.72)
        glTranslatef(0, 0, self.size * 0.75)
        glutSolidSphere(self.size * 0.08, 20, 20)
        glPopMatrix()

        # skirt / lower body (large sphere)
        glPushMatrix()
        glColor3f(0.22, 0.06, 0.3)
        glTranslatef(0, 0, self.size * 0.05)
        glScalef(1.0, 1.0, 0.6)
        glutSolidSphere(self.size * 0.4, 28, 16)
        glPopMatrix()

        # subtle glowing ring around base
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
        # legacy placeholder retained for compatibility
        pass

    def spawn_shockwave(self):
        # create a ring with initial radius zero
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
        """Update rings; if any ring intersects player position return damage amount (sum).

        Returns total_damage (int).
        """
        now = time.time()
        total_damage = 0
        # spawn new shockwave if interval passed
        if now - self.last_shock_time >= self.shock_interval:
            self.last_shock_time = now
            self.spawn_shockwave()

        # update rings
        new_rings = []
        for r in self.rings:
            dt = now - r.get('created', now)
            # grow using speed * elapsed_from_creation
            # but we'll advance by a small step to avoid huge jumps
            r['radius'] += r['speed'] * 0.016  # assume ~60fps step
            # check collision with player if provided and not yet hit
            if px is not None and py is not None and not r.get('hit_player', False):
                dx = px - self.x
                dy = py - self.y
                dist = math.hypot(dx, dy)
                # ring intersects if distance near radius within thickness
                if abs(dist - r['radius']) <= (r['thickness'] * 0.5):
                    r['hit_player'] = True
                    # damage scales with ring age/size; use fixed damage
                    total_damage += 8
            # keep ring if not past max_radius
            if r['radius'] <= r['max_radius']:
                new_rings.append(r)
        self.rings = new_rings
        return total_damage

    def take_damage(self, amount):
        self.hp -= int(amount)
        if self.hp <= 0:
            self.alive = False

    def hit_by_swing(self, px, py, angle_deg, reach=120.0, width=60.0):
        """Test whether a rectangular swing originating at (px,py) with orientation
        angle_deg hits the boss. Returns True if hit.
        Uses same forward/right projection convention as physics.remove_enemies_in_swing.
        """
        # forward vector used by project: forward = (sin(angle), -cos(angle))
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
        """Simple AABB-like test against a rectangular frontal area.

        For the boss, we'll treat its footprint as a large square centered at (x,y)
        with half-size proportional to self.size.
        """
        half = self.size * 0.6
        if px < (self.x - half) or px > (self.x + half):
            return False
        if py < (self.y - half) or py > (self.y + half):
            return False
        return True

    def take_damage_area(self, amount):
        self.take_damage(amount)


# module-level boss instance (None if not present)
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
    # draw shockwave rings on floor
    if getattr(boss_instance, 'rings', None):
        for r in boss_instance.rings:
            glPushMatrix()
            glTranslatef(boss_instance.x, boss_instance.y, 1.0)
            # neon ring color
            glColor4f(0.6, 0.2, 0.9, 0.6)
            glDisable(GL_LIGHTING)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            # draw circle as line loop
            sides = 64
            radius = r['radius']
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            for i in range(sides):
                theta = 2.0 * math.pi * float(i) / float(sides)
                glVertex3f(math.cos(theta) * radius, math.sin(theta) * radius, 0.5)
            glEnd()
            glDisable(GL_BLEND)
            glEnable(GL_LIGHTING)
            glPopMatrix()


def draw_boss_healthbar():
    """Draw a large boss health bar at the top of the screen using 2D orthographic projection.

    This function assumes a fixed window aspect roughly matching the main window.
    """
    global boss_instance
    if boss_instance is None or not getattr(boss_instance, 'alive', False):
        return

    # Save matrices and attributes
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    # Use screen coords: 0..1000 x 0..800 (matches window size used in main())
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # draw background bar
    glDisable(GL_DEPTH_TEST)
    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT)
    bar_w = 800
    bar_h = 28
    x0 = 100
    y0 = 760
    # background
    glColor3f(0.05, 0.05, 0.05)
    glBegin(GL_QUADS)
    glVertex2f(x0, y0)
    glVertex2f(x0 + bar_w, y0)
    glVertex2f(x0 + bar_w, y0 + bar_h)
    glVertex2f(x0, y0 + bar_h)
    glEnd()

    # health fill
    hp_frac = max(0.0, min(1.0, float(boss_instance.hp) / float(boss_instance.hp_max)))
    glColor3f(0.8 * (1.0 - hp_frac) + 0.1, 0.2 * hp_frac + 0.1, 0.9 * hp_frac + 0.1)
    glBegin(GL_QUADS)
    glVertex2f(x0 + 4, y0 + 4)
    glVertex2f(x0 + 4 + (bar_w - 8) * hp_frac, y0 + 4)
    glVertex2f(x0 + 4 + (bar_w - 8) * hp_frac, y0 + 4 + (bar_h - 8))
    glVertex2f(x0 + 4, y0 + 4 + (bar_h - 8))
    glEnd()

    # Draw border
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

    # restore matrices
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

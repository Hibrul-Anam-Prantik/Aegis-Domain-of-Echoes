from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random 

# ---------------- CAMERA ----------------
cam_angle = 0
cam_height = 270
cam_radius = 300

fov_y = 120

# ---------------- WORLD ----------------
GRID_LENGTH = 1000

# ---------------- PLAYER ----------------
pos_x = 0
pos_y = 0
pos_angle = 0

person_one = False

# ---------------- DOMAIN MODE ----------------

domain_mode = False


building_data = []
tree_data = []
ash_particles = []


is_swinging = False
katana_swing_angle = 0
orb_active = False
orb_pos = [0, 0, 0]
orb_dir = [0, 0]


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
    rad = math.radians(cam_angle)
    x = cam_radius * math.cos(rad)
    y = cam_radius * math.sin(rad)
    z = cam_height
    return (x, y, z)


def camera_control():
    global person_one, pos_x, pos_y, pos_angle

    if person_one:
        rad = math.radians(pos_angle + 90)

        xEye = pos_x - math.cos(rad) * 30
        yEye = pos_y - math.sin(rad) * 30
        zEye = 90

        lookx = pos_x - math.cos(rad) * 300
        looky = pos_y - math.sin(rad) * 300
        lookz = 60

        return (xEye, yEye, zEye, lookx, looky, lookz)
    else:
        x, y, z = camera_position()
        return (x, y, z, 0, 0, 0)


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fov_y, 1.25, 0.1, 5000)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    ex, ey, ez, lx, ly, lz = camera_control()

    gluLookAt(ex, ey, ez, lx, ly, lz, 0, 0, 1)


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
    global pos_x, pos_y, pos_angle, domain_mode
    
    glPushMatrix()
    glTranslatef(pos_x, pos_y, 5)
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

def setup_fog():

    glEnable(GL_FOG)
    
    fog_color = [0.4, 0.3, 0.2, 1.0] 
    
    glFogfv(GL_FOG_COLOR, fog_color) 
    glFogi(GL_FOG_MODE, GL_EXP2)      
    glFogf(GL_FOG_DENSITY, 0.0007)
    glHint(GL_FOG_HINT, GL_NICEST)

def draw_scenery():

    for x, y, fl in building_data:
        draw_broken_building(x, y, fl)
        
    for x, y in tree_data:
        draw_tree(x, y)



# ================= INPUT =================
def keyboardListener(key, x, y):
    global keys, domain_mode, orb_active, orb_pos, orb_dir, pos_x, pos_y

    if key in keys: keys[key] = True 

    if key == b'g' or key == b'G': domain_mode = not domain_mode
    
    if key == b'f' or key == b'F':
        if not orb_active:
            orb_active = True
            rad = math.radians(pos_angle + 90)
            orb_pos = [pos_x, pos_y, 60]
            orb_dir = [-math.cos(rad), -math.sin(rad)]


def specialKeyListener(key, x, y):
    global cam_angle, cam_height

    if key == GLUT_KEY_UP:
        cam_height += 15
    elif key == GLUT_KEY_DOWN:
        cam_height -= 15
    elif key == GLUT_KEY_LEFT:
        cam_angle -= 2
    elif key == GLUT_KEY_RIGHT:
        cam_angle += 2

def keyboardUpListener(key, x, y):
    global keys
    if key in keys: keys[key] = False

def mouseListener(button, state, x, y):
    global is_swinging, person_one

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        is_swinging = True

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        person_one = not person_one  


def update_logic():
    global pos_x, pos_y, pos_angle, is_swinging, katana_swing_angle, orb_active, orb_pos
    
    speed = 10
    rad = math.radians(pos_angle + 90)
    
    if keys[b'w']:
        pos_x -= speed * math.cos(rad)
        pos_y -= speed * math.sin(rad)

    if keys[b's']:
        pos_x += speed * math.cos(rad)
        pos_y += speed * math.sin(rad)

    if keys[b'a']: pos_angle += 4
    if keys[b'd']: pos_angle -= 4

    world_limit = GRID_LENGTH - 200
    
    pos_x = max(-world_limit, min(world_limit, pos_x))
    pos_y = max(-world_limit, min(world_limit, pos_y))

    if is_swinging:
        katana_swing_angle += 15 
        if katana_swing_angle > 180:
            katana_swing_angle = 0
            is_swinging = False

    if orb_active:
        orb_pos[0] += orb_dir[0] * 25 
        orb_pos[1] += orb_dir[1] * 25

        if abs(orb_pos[0]) > GRID_LENGTH or abs(orb_pos[1]) > GRID_LENGTH:
            orb_active = False

# ================= RENDER =================
def showScreen():

    update_logic()

    if domain_mode:
        glClearColor(0.08, 0.0, 0.0, 1.0)

    else:
        glClearColor(0.4, 0.3, 0.2, 1.0)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    setup_fog()
    setupCamera()

    draw_ground()
    draw_scenery()
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
    setup_fog()
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
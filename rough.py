from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random 

# ---------------- CAMERA ----------------
cam_angle = 0
cam_height = 400
cam_radius = 700

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

# কোডের শুরুতে এই লিস্টগুলো ডিক্লেয়ার করুন
building_data = []
tree_data = []
ash_particles = []

# --- এগুলি গ্লোবাল সেকশনে অ্যাড করুন ---
is_swinging = False
katana_swing_angle = 0
orb_active = False
orb_pos = [0, 0, 0]
orb_dir = [0, 0]
# ৮-ওয়ে মুভমেন্টের জন্য কি-স্টেট ট্র্যাকিং
keys = {b'w': False, b's': False, b'a': False, b'd': False}

def generate_world_data():
    global building_data, tree_data, ash_particles
    building_data, tree_data, ash_particles = [], [], []
    
    limit = GRID_LENGTH - 100 
    step = 120 

    # লজিক: প্রতি ৩টি অবজেক্টের মধ্যে ২টা বিল্ডিং এবং ১টা গাছ থাকবে (Fixed Pattern)
    # এতে করে চারপাশেই বিল্ডিংয়ের সংখ্যা সমান থাকবে।
    counter = 0

    for i in range(-limit, limit + 1, step):
        # চারপাশের বাউন্ডারি পয়েন্টগুলো: সামনে, পিছনে, ডানে, বামে
        points = [(i, limit), (i, -limit), (limit, i), (-limit, i)]
        
        for x, y in points:
            # প্যাটার্ন অনুযায়ী বিল্ডিং এবং গাছ ভাগ করা
            if counter % 3 == 0 or counter % 3 == 1: 
                # বিল্ডিং জেনারেট (৫৫-৬০% এর সমতুল্য)
                h = random.randint(5, 10) 
                building_data.append((x, y, h))
            else:
                # গাছ জেনারেট
                tree_data.append((x + random.uniform(-40, 40), y + random.uniform(-40, 40)))
            
            # অরণ্য ঘন রাখার জন্য সবসময় ব্যাকগ্রাউন্ডে একটি অতিরিক্ত গাছ
            tree_data.append((x + random.uniform(-100, 100), y + random.uniform(-100, 100)))
            
            counter += 1

    # গ্রাউন্ডের ছাই কণা
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
    # মেইন ফ্লোর (Solid Base)
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glEnd()

    # ছাইয়ের কণাগুলো ড্র করা (পয়েন্ট হিসেবে)
    glBegin(GL_POINTS)
    for px, py, pc in ash_particles:
        glColor3f(pc, pc, pc)
        glVertex3f(px, py, 1) # মাটির সামান্য উপরে
    glEnd()



# ================= PLAYER =================

def draw_orb_projectile():
    global orb_pos
    glPushMatrix()
    glTranslatef(orb_pos[0], orb_pos[1], orb_pos[2])
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glColor4f(0, 1, 1, 0.8) # উজ্জ্বল সায়ান কালার
    glutSolidSphere(15, 20, 20)
    glDisable(GL_BLEND)
    glPopMatrix()

def draw_player():
    global pos_x, pos_y, pos_angle, domain_mode
    
    glPushMatrix()
    glTranslatef(pos_x, pos_y, 5)
    glRotatef(pos_angle, 0, 0, 1)

    # ১. লোয়ার বডি ও পা
    glColor3f(0.1, 0.1, 0.1)
    for s in [-1, 1]:
        glPushMatrix()
        glTranslatef(s * 12, 0, 15)
        glScalef(0.4, 0.4, 1.2)
        glutSolidCube(25)
        glPopMatrix()

    # ২. আপার বডি
    glPushMatrix()
    glColor3f(0.2, 0.2, 0.2)
    glTranslatef(0, 0, 50)
    glScalef(0.7, 0.4, 1.2)
    glutSolidCube(40)
    glPopMatrix()

    # ৩. শোল্ডার গার্ড
    for s in [-1, 1]:
        glPushMatrix()
        if domain_mode: glColor3f(0.4, 0, 0.6)
        else: glColor3f(0.3, 0.2, 0.15)
        glTranslatef(s * 25, 0, 75)
        glRotatef(s * 20, 0, 1, 0)
        glScalef(0.8, 0.6, 0.3)
        glutSolidCube(30)
        glPopMatrix()

    # ৪. গেট কোর
    glPushMatrix()
    if domain_mode: glColor3f(0.0, 1.0, 1.0)
    else: glColor3f(0.0, 0.5, 0.8)
    glTranslatef(0, -10, 60)
    glutSolidSphere(8, 16, 16)
    glPopMatrix()

    # ৫. মাথা ও সাইবার ভাইজর
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

# ৬. ক্যাটানা (ডান হাতে) - একদম আপনার অরিজিনাল কোড
    glPushMatrix()
    glTranslatef(-28, -5, 55)
    
    # শুধু এই নিচের ৩টি লাইন সুইং লজিকের জন্য যোগ করা হয়েছে, বাকি সব সেম
    if is_swinging:
        glRotatef(-katana_swing_angle, 0, 1, 0) # সুইং স্পিড ও আর্ক কন্ট্রোল
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

    # ৭. কাইনেটিক অরব (বাম হাতে) - শুধু ১টি if কন্ডিশন যোগ করা হয়েছে
    if not orb_active: # অরব ফায়ার করলে হাত খালি দেখাবে, এছাড়া আপনার কোডই থাকবে
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

    # ৮. ক্যারেক্টার অরা (Domain Mode Only)
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
    # গুড়ি
    glColor3f(0.3, 0.15, 0.05) 
    glPushMatrix()
    glTranslatef(0, 0, 40)
    glScalef(0.4, 0.4, 2.0) 
    glutSolidCube(40) 
    glPopMatrix()
    
    # ৩. গাঢ় সবুজ পাতা (Deep Green)
    if domain_mode:
        glColor3f(0.5, 0.0, 0.0) 
    else:
        glColor3f(0.0, 0.4, 0.0) # Deep Green
    
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
    # বিল্ডিং এর উচ্চতা এবং শেপ আপডেট
    for i in range(height_floors):
        glPushMatrix()
        
        # মোটা বিল্ডিং করার জন্য অফসেট সামান্য অ্যাডজাস্ট করা
        offset_x = (i * 0.8) if i % 2 == 0 else (i * -0.5)
        glTranslatef(x + offset_x, y, i * 40) 
        
        # ১. সাদাটে হালকা রঙ
        if domain_mode:
            glColor3f(1.0, 0.9, 0.8) 
        else:
            glColor3f(0.9, 0.9, 0.9) # Light White/Grey
            
        # ২. মোটা বিল্ডিং (৬০ সাইজ)
        glutSolidCube(60) 

        # জানালার রঙ (অন্ধকার জানালা)
        glColor3f(0.1, 0.1, 0.1) 
        for k in range(-1, 2, 2):
            glPushMatrix()
            glTranslatef(0, k * 30.1, 15) # ৬০ সাইজের জন্য অফসেট বাড়ানো হয়েছে
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
    glEnable(GL_FOG) # কুয়াশা সক্রিয় করা
    
    # বিকেলের আকাশের রঙ (Dusty Orange/Grey)
    # এই রঙটি কুয়াশার জন্য ব্যবহার করলে বিকেলের আমেজ আসবে
    fog_color = [0.4, 0.3, 0.2, 1.0] 
    
    glFogfv(GL_FOG_COLOR, fog_color)      # কুয়াশার রঙ সেট করা
    glFogi(GL_FOG_MODE, GL_EXP2)          # কুয়াশার ধরন (Exponential 2)
    glFogf(GL_FOG_DENSITY, 0.0007)        # আপনার রিকোয়েস্ট অনুযায়ী ঘনত্ব ০.০০০৭
    glHint(GL_FOG_HINT, GL_NICEST)        # রেন্ডারিং কোয়ালিটি স্মুথ করা

def draw_scenery():
    # ১. বিল্ডিং ড্র করা
    for x, y, fl in building_data:
        draw_broken_building(x, y, fl)
        
    # ২. গাছ ড্র করা
    for x, y in tree_data:
        draw_tree(x, y)



# ================= INPUT =================
def keyboardListener(key, x, y):
    global keys, domain_mode, orb_active, orb_pos, orb_dir, pos_x, pos_y
    if key in keys: keys[key] = True # কি চেপে ধরলে True হবে
    if key == b'g' or key == b'G': domain_mode = not domain_mode
    
    # 'f' চাপলে অরব ফায়ার হবে
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
        is_swinging = True # মাউস ক্লিকে ক্যাটানা সুইং শুরু
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        person_one = not person_one  


def update_logic():
    global pos_x, pos_y, pos_angle, is_swinging, katana_swing_angle, orb_active, orb_pos
    
    speed = 10
    rad = math.radians(pos_angle + 90)
    
    # ৮-ওয়ে মুভমেন্ট প্রসেসিং
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

    # ক্যাটানা সুইং (১৮০ ডিগ্রি ঘুরে আসবে)
    if is_swinging:
        katana_swing_angle += 15 # সুইং স্পিড
        if katana_swing_angle > 180:
            katana_swing_angle = 0
            is_swinging = False

    # অরব মুভমেন্ট
    if orb_active:
        orb_pos[0] += orb_dir[0] * 25 # ফায়ার স্পিড
        orb_pos[1] += orb_dir[1] * 25
        # বাউন্ডারি পার হলে অরব শেষ
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
# ⛩️ REVERSE ISEKAI: GATE OF THE SHATTERED REALMS

**"Reverse Isekai"** is a high-octane 3D Arena-Defense game built with Python and PyOpenGL. Players take on the role of the **Gatekeeper**, the last line of defense at the universal origin $(0, 0, 0)$, tasked with protecting the portal from multidimensional threats.

---

## 🌀 Project Concept: The Dimensional Breach

The core innovation of this project is the **Dimensional Shift** mechanic. Instead of static levels, the game utilizes real-time matrix transformations to physically collapse the current reality and rebuild a new one around the player.

### ✨ Key Features

- **Dual-Realm Transitions:** Seamlessly swap between a **Traditional Zen Dojo** and a **Neon Cyber-Void** using global `glScalef` and `glRotatef` animations.
- **Omnidirectional 3D Combat:** Defend against enemies swarming from all $(x, y, z)$ coordinates.
- **Hierarchical Action:** A fully modeled 3D Ronin with a Katana system controlled via complex Matrix Stacks.
- **Dynamic Cinematic Camera:** A `gluLookAt` system that responds to player movement and dimensional shifts.

---

## 🛠️ Technical Implementation

### 1. Hierarchical 3D Modeling

We utilize `glPushMatrix()` and `glPopMatrix()` to create a parent-child relationship for the character model.

- **Torso (Parent):** Controls the main translation.
- **Katana (Child):** Inherits the character's position but performs independent `glRotatef` arcs for slashing.

### 2. The Dimensional Shift (Matrix Manipulation)

When a dimension breach occurs, the entire world’s ModelView Matrix is manipulated via a `transitionFactor`:

- **Step 1:** `glScalef` shrinks the world to a singular point.
- **Step 2:** Geometry and color states are swapped.
- **Step 3:** `glRotatef` and `glScalef` expand the new world with a "Black Hole" effect.

### 3. 3D Collision Physics

Combat is calculated using 3D Distance-Based Collision Detection:
$$Distance = \sqrt{(x_2-x_1)^2 + (y_2-y_1)^2 + (z_2-z_1)^2}$$
If the distance between an Energy Orb and an Enemy is $\le$ the sum of their radii, a hit is registered.

---

## 👥 Team & Responsibilities

### **Member 1: The Architect (Environment & Camera)**

- **Feature:** Multi-Realm Construction (Dojo & Glitch Void).
- **Feature:** Perspective Control (`gluPerspective`) and Dynamic Camera (`gluLookAt`).
- **Feature:** 3D HUD & World-Space Text UI.

### **Member 2: The Animator (Hierarchical Modeling & FX)**

- **Feature:** 3D Hierarchical Gatekeeper Character Model.
- **Feature:** Independent Katana Slash System (Matrix Nesting).
- **Feature:** Global Transformation FX for Dimension Shifting.

### **Member 3: The Engineer (Physics & AI)**

- **Feature:** 3D Vector AI (Enemies spawning at random coords and tracking to $(0,0,0)$).
- **Feature:** Projectile Trajectory Logic for 3D Energy Orbs.
- **Feature:** Distance-based 3D Collision Engine.

---

## 🕹️ Controls

- **Arrows:** Rotate Character / Adjust Camera.
- **Space:** Melee Katana Slash.
- **F:** Fire Ranged Energy Orb.
- **C:** Toggle Cheat Mode (Auto-Guardian).
- **T:** Trigger Dimensional Breach (Teleport).

---

## 🚀 Installation & Running

1. Install dependencies:

   ```bash
   pip install PyOpenGL PyOpenGL_accelerate
   ```

2. Run the game::

   ```bash
   python ReverseIsekai.py
   ```

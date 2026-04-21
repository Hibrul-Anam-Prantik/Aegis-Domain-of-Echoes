# ⛩️ Project Title: "REVERSE ISEKAI: GATE OF THE SHATTERED REALMS"

## The Vision:

Imagine a 3D Arena-Defense game where the environment isn't just a stage—it’s an active participant in the combat. You are the Gatekeeper, the last line of defense at the center of the universe (0,0,0).

The core "Hook" is the Dimensional Breach (Domain Expansion). Unlike standard games where you just move to "Level 2," our game uses real-time matrix transformations to physically collapse the current reality and rebuild a new one around the player.

## ⚔️ Core Gameplay: The Guardian's Arsenal

- **360° Omnidirectional Combat:** Enemies don't just come from the left or right; they swarm from the 3D void. The player must rotate their character in a full sphere to track targets.

- **Hierarchical Melee (The Katana):** Using Matrix Stacks, we’ll build a weapon that is physically parented to the player's hand. When the player swings, we use nested glRotatef calls to create a fluid, anime-style "Slash" arc.

- **Ranged Kinetic Orbs:** Launch high-velocity 3D spheres (gluSphere) that use vector math to travel from the center toward the enemy's 3D coordinates.

## 🌀 The Signature Feature: "The Dimensional Shift"

This is our "Domain Expansion." When a specific score is reached, the player triggers the Shatter Sequence:

- **The Animation:** We manipulate the ModelView Matrix globally. The current world (e.g., an Ancient Samurai Dojo) begins to spin (glRotatef) and shrink (glScalef) into a singular point.

- **The Swap:** In an instant, the geometry is replaced. The textures, colors, and primitive models swap from Organic/Ancient (Cylinders as bamboo, Cubes as stone) to Digital/Cyberpunk (Spheres as drones, Quads as neon grids).

- **The Gameplay Change:** Gravity or enemy speed can shift, forcing the player to adapt to the new "physics" of that dimension.

## 🛠️ Technical "Flex" (Why it's a Grade-A Project)

We are taking the foundations of Assignment 3 and pushing them to their limit:

- **Hierarchical 3D Modeling:** Building a character where the head, torso, and sword are independent objects that move in perfect sync using glPushMatrix and glPopMatrix.

- **Complex 3D Collision:** Implementing 3D distance-based hit detection between projectiles and enemy bounding boxes.

- **Cinematic Camera:** Using gluLookAt to create a "Dynamic Follow-Cam" that shakes when a dimension shifts or zooms in during a melee strike.

- **Procedural Primitives:** Every asset—from the Katana to the final Boss—is mathematically constructed using gluCylinder, gluSphere, and glutSolidCube.

## 📢 Summary

"It’s a 3D tower defense game where the player is the tower. We are utilizing the OpenGL State Machine to handle complex 3D transformations, turning simple lab primitives into a high-octane, multi-dimensional action experience. The novelty lies in the seamless transition between world geometries, proving our mastery over the 3D pipeline."

## Contributors

- [Fuad](https://github.com/mfd-7)
- [Roja](https://github.com/lamia-tarek)
- [Prantik](https://github.com/hibrul-anam-prantik)

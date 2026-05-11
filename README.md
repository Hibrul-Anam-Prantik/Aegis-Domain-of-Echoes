# ⛩️ Aegis: Domain of Echoes

### _Mainkar Chipay_ — মাইনকার চিপায়

> A 3D arena-defense game built entirely with Python and PyOpenGL. No game engine. No shortcuts. Just the OpenGL state machine, a lot of math, and pure stubbornness.

## ⬇️ Download & Play

| Platform   | Download                                                                                                                               | Status       |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| 🍎 macOS   | [MainkarChipay_mac.zip](https://github.com/Hibrul-Anam-Prantik/Computer-Graphics-Project/releases/download/v2.0/MainkarChipay_mac.zip) | ✅ Available |
| 🪟 Windows | Coming soon                                                                                                                            | 🔜           |
| 🐧 Linux   | Coming soon                                                                                                                            | 🔜           |

> **macOS users:** After unzipping, right-click the app → **Open** → click **Open** on the warning.
> If it still doesn't open, go to **System Settings → Privacy & Security** → scroll down and click **"Open Anyway"** → then try opening the app again.

---

## 🎮 What Is This Game?

You are the **Gatekeeper** — the last line of defense standing at the origin of the universe `(0, 0, 0)`. Skeleton warriors swarm you from every direction. Kill enough of them, and something far worse wakes up.

This is a **third-person 3D arena-defense** game where the player is the tower. Every asset — from the katana blade to the final boss — is mathematically constructed using OpenGL primitives (`gluSphere`, `gluCylinder`, `glutSolidCube`). There are no textures, no imported models. Everything you see is geometry.

---

## 🌀 The Signature Idea: Domain Expansion

The core innovation of this project isn't just the combat — it's the **Dimensional Shift**.

When you reach a score of **500**, you trigger the _Domain Expansion_:

- The camera performs a full **360° cinematic barrel roll**, locking out player input.
- The world visually shifts — tree foliage turns blood-red, buildings glow amber, the player's katana turns magenta.
- The **Final Boss rises from underground**, emerging from `z = -400` to the surface in a slow, dramatic ascent.
- The boss's health pool is `100`, and it attacks with two distinct mechanics: a **seeking orb** and an **expanding shockwave ring**.

This wasn't just an aesthetic choice — it required manipulating the ModelView Matrix globally during a live frame loop, freezing all game logic mid-animation and resuming it cleanly after. That's not trivial in immediate-mode OpenGL.

---

## ⚔️ Gameplay Systems We Built

### Regular Combat Phase

Skeleton enemies (up to 5 at a time) spawn randomly across the arena and pursue you using a vector-based AI. They have **separation behavior** — they push each other apart so they don't stack on top of you all at once. Kill them with your katana (melee) or fire an energy orb (ranged). They drop **hearts** (health pickups) and **coins** (score).

### The Final Boss

Once the Domain Expansion cinematic plays out, the boss enters the arena. It:

- Slowly **walks toward you** when you're far away
- Fires a **seeking orb** that tracks your position with a cooldown
- Periodically launches an **expanding shockwave ring** that spreads outward — you have to jump over it or get out of its path

The boss is invulnerable while rising. Once it's on the ground, everything is fair game. Beating it gives **+1000 score** and a shower of coin drops.

### Loot System

Enemies drop loot on death (random chance):

- 🪙 **Coin** — picked up automatically for +50 score
- ❤️ **Heart** — restores 1 HP if you're not at max health

The boss drops 10 coins on defeat.

---

## 🛠️ Technical Highlights (The OpenGL Stuff)

We built this from scratch using the fixed-function pipeline. Here's what we actually implemented:

**Hierarchical 3D Modeling** — The player character is assembled from individual `glutSolidCube`, `gluSphere`, and `gluCylinder` calls, nested inside `glPushMatrix` / `glPopMatrix` stacks. The katana is a _child_ of the arm — it inherits the player's rotation and independently animates the swing arc via `glRotatef`.

**3D Vector Math for AI** — Enemy movement uses normalized direction vectors toward the player. The dot product between the player's forward vector and the direction to a target is what determines whether a swing actually _hits_ — if the dot product is `> 0.5`, the target is "in front" of you.

**Distance-Based Collision** — All hit detection uses the 3D Euclidean distance formula. Projectile-vs-enemy, projectile-vs-boss, shockwave-ring-vs-player (using ring delta tolerance `|dist - radius| ≤ 20`).

**Dynamic Follow Camera** — `gluLookAt` is set up each frame to follow the player smoothly. During the Domain Expansion cinematic, the camera angle auto-increments to perform the barrel roll. There's also a first-person mode toggle.

**Invincibility Frames** — On taking damage, the player enters an iframe window (`player_iframes = 60` frames ≈ 1 second). During this time, the player model blinks red. All damage sources are blocked until iframes expire.

**Procedural World Generation** — `generate_world_data()` populates the arena with randomly placed broken buildings and trees using a grid step pattern. 8,000 ash/dust particles are scattered across the ground plane as ambient atmosphere.

**Jump Physics** — The jump arc is computed using a sine easing: `pos_z = sin(t * π) * MAX_JUMP_HEIGHT`, where `t` is the normalized frame progress. The camera look-target includes `player_z` so you can visually see the jump.

---

## 📁 Project Files

| File                      | Description                                                                        |
| ------------------------- | ---------------------------------------------------------------------------------- |
| `Aegis_DoE_v2.0.py`       | **Current build** — fully featured with blending, boss shockwave, domain cinematic |
| `Aegis_DomainOfEchoes.py` | Version 1 — same logic, template-only rendering (no blending/transparency)         |
| `test2.py`                | Scratch/test file used during development                                          |
| `README.md`               | This file                                                                          |
| `features.md`             | Technical feature breakdown                                                        |
| `instructions.md`         | Controls and setup guide                                                           |

---

## 👥 Team

| Member                                            | Role                                                                                                                                                                                                  |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Fuad](https://github.com/mfd-7)                  | World Builder — base arena skeleton, procedural buildings, trees, and domain environment                                                                                                              |
| [Roja](https://github.com/lamia-tarek)            | Game Feel — health system, coin pickups, loot drops, enemy models                                                                                                                                     |
| [Prantik](https://github.com/hibrul-anam-prantik) | Game Designer & Lead Developer — original concept & idea, enemy AI, boss lifecycle, collision engine, shockwave, Domain Expansion cinematic, full codebase debugging & integration, v1 → v2.0 upgrade |

### A note on contributions

The game concept — the arena-defense structure, the Domain Expansion mechanic, the boss design, and the overall vision of _Aegis: Domain of Echoes_ — was **Prantik's original idea**. He also led the technical side: building the enemy AI, boss mechanics, collision engine, shockwave attack, and Domain Expansion cinematic, while debugging and integrating everyone's work into the final v2.0 build. Fuad built the world — the arena layout, broken buildings, trees, and domain environment. Roja implemented the game-feel layer — health, coin pickups, loot drops, and enemy visuals. It was a collaborative effort, with Prantik driving both the creative and technical direction throughout.

---

## 📜 License

MIT License — see `LICENSE` for details.

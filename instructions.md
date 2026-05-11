# 📖 Instructions — Aegis: Domain of Echoes

> How to install, run, and play the game.

---

## ⚙️ Requirements

- **Python 3.8+**
- **PyOpenGL** and **PyOpenGL_accelerate**
- A system with OpenGL support (any modern GPU works — integrated graphics is fine)
- Works on **Windows**, **Linux**, and **macOS**

---

## 🚀 Installation & Running

**Step 1 — Install dependencies:**

```bash
pip install PyOpenGL PyOpenGL_accelerate
```

> On some Linux systems you may also need:
>
> ```bash
> sudo apt-get install freeglut3-dev
> ```

**Step 2 — Clone the repository:**

```bash
git clone https://github.com/Hibrul-Anam-Prantik/Computer-Graphics-Project.git
cd Computer-Graphics-Project
```

**Step 3 — Run the game:**

```bash
python Aegis_DoE_v2.0.py
```

> Use `Aegis_DomainOfEchoes.py` if you want the v1 build (no transparency effects, otherwise identical gameplay).

---

## 🎮 Controls

### Movement

| Key | Action                |
| --- | --------------------- |
| `W` | Move forward          |
| `S` | Move backward         |
| `A` | Strafe / rotate left  |
| `D` | Strafe / rotate right |

Movement is relative to the camera direction.

---

### Combat

| Key                 | Action                                              |
| ------------------- | --------------------------------------------------- |
| `Left Mouse Button` | Swing katana (melee attack)                         |
| `F`                 | Fire energy orb (ranged attack) — 3 second cooldown |

**Melee range:** ~120 units in front of the player. The hit detection uses a forward cone — you must be roughly facing the enemy.

**Orb:** Travels in your facing direction. One orb at a time. The HUD shows "ORB READY" (green) or "ORB COOLDOWN: Xs" (orange).

---

### Camera

| Key                  | Action                                    |
| -------------------- | ----------------------------------------- |
| `Arrow Up / Down`    | Adjust camera pitch (tilt up/down)        |
| `Arrow Left / Right` | Orbit camera around the player            |
| `+`                  | Zoom camera in                            |
| `-`                  | Zoom camera out                           |
| `Right Mouse Button` | Toggle first-person / third-person camera |

Default is third-person follow cam. First-person mode locks the view behind the player's head.

---

### Misc

| Key     | Action                                                    |
| ------- | --------------------------------------------------------- |
| `Space` | Jump                                                      |
| `X`     | Toggle Domain Mode visuals (color palette shift — debug)  |
| `C`     | Toggle Cheat Mode (AI takes over + invincible)            |
| `R`     | Restart the game (works at any time, including game over) |
| `ESC`   | Quit the game                                             |

---

## 🧠 How to Play

### Phase 1 — Regular Enemies

Skeleton warriors spawn around the arena (up to 5 at a time). They move toward you and deal contact damage.

- Use your **katana** for fast close-range kills (+10 score each)
- Use your **orb** for safer ranged kills (+20 score each)
- Pick up **coins** (🪙) dropped by dead enemies for +50 score
- Pick up **hearts** (❤️) to restore 1 HP

Your goal: reach **500 score** to trigger the Domain Expansion.

---

### Phase 2 — Domain Expansion

When you hit 500 score, the screen goes cinematic:

- All enemies are cleared
- The camera performs a 360° barrel roll — **don't panic, you can't do anything here**
- The world's color palette shifts (domain mode activates)
- Your health is refilled to **10/10**

Wait for the cinematic to end. The boss will start rising from the ground.

---

### Phase 3 — The Final Boss

The boss is a 2.5× scaled skeleton with glowing eyes and a more powerful orb launcher. It has **100 HP**.

**Boss attacks:**

- **Seeking Orb** — Fires a glowing orange ball toward your position. Dodge by sidestepping. Deals **1 damage**.
- **Shockwave Ring** — A magenta ring expands outward from the boss. **Jump over it** to avoid 2 damage. You can see it coming — the ring is large and slow enough to react to.

**How to damage the boss:**

- **Katana swing** hits for **5 damage** per swing (you must be close and facing it)
- **Your orb** hits for **10 damage** — most efficient if you can land it reliably

**Defeating the boss** rewards +1000 score and drops 10 coins. You win.

---

## 💀 Game Over

If your health reaches 0, the screen turns red and shows "WASTED!!" with your final score.

Press `R` to restart from the beginning, or `ESC` to quit.

---

## 💡 Tips

- **Invincibility frames exist** — after taking a hit, you blink red and are briefly invincible. Use this window to reposition.
- **Jump to dodge the shockwave** — the shockwave ring only damages you if `pos_z < 30`, so even a small hop is enough.
- **Face your target before swinging** — the katana uses a forward cone check, not just proximity. Side-swinging does nothing.
- **The orb is on a real-time 3s cooldown** — don't spam the key; the HUD tells you exactly when it's ready.
- **Cheat mode (`C`) is there if you just want to watch** — the AI will fight for you and you'll be invincible.

---

## 🐛 Known Issues / Notes

- GLUT bitmap fonts (`GLUT_BITMAP_HELVETICA_18`) may render slightly differently depending on your system's GLUT version. The game adds safe fallbacks at import time.
- On some setups, `glutWireTorus` may not be available — the shockwave will fall back to a manual line-loop circle.
- Frame-based timers (enemy AI, iframes) are tied to render speed. On very fast machines, enemy and boss movement may be faster than intended. The orb cooldown uses real `time.time()` and is not affected.
- The window aspect ratio is fixed at `1000 × 800`. Do not resize the window during gameplay.

# 🛠️ Features — Aegis: Domain of Echoes

> A detailed breakdown of every implemented feature in the game, mapped to the actual code that makes it work.

---

## Core Architecture

The game runs on a single-file global-state loop. `showScreen()` calls `update_logic()` each frame, which handles input, movement, jump math, and the cinematic sequence. Then it calls `update_behavior()` for AI/boss updates, `check_collisions()` for all damage and pickup logic, and finally renders everything.

No game engine. No ECS. Just globals, frame counters, and the OpenGL state machine.

---

## 1. 🌀 Domain Expansion (Cinematic)

**What it does:** When the player hits 500 score, all enemies are cleared and the world transforms. The camera performs a full 360° barrel roll, player input is locked, and domain visuals kick in — the color palette of the world shifts, a purple aura surrounds the player, and the boss begin rising.

**How it works:**

- `domain_animating = True` freezes all collision and AI logic
- `domain_anim_angle` increments each frame; when it reaches 360°, the cinematic ends and `boss_is_rising = True` begins
- The camera's azimuth is overridden to follow `domain_anim_angle` during this window
- `domain_mode` flag changes tree, building, katana, and player aura colors globally

**Key code:** `update_behavior()`, `update_logic()`, `showScreen()`, `draw_ui()`

---

## 2. 👹 Boss Rise Cinematic

**What it does:** After the domain cinematic ends, the Final Boss spawns underground at `z = -400` and slowly rises to the surface. It is invulnerable and non-interactive while rising.

**How it works:**

- `boss['z'] += 4.0` each frame until `boss['z'] >= 0`
- All collision checks skip the boss while `boss_is_rising = True`
- `draw_boss()` translates to `boss['z']` so it visually rises from the ground

**Key code:** `update_behavior()`, `draw_boss()`, `check_collisions()`

---

## 3. 🔮 Boss Orb Projectile (Seeking)

**What it does:** The boss periodically fires a glowing orb that travels toward the player's position at the time of firing. It deals 1 damage on contact and has a frame-based cooldown of 120 frames between shots.

**How it works:**

- Direction vector computed at fire time: `boss_orb_dir = normalize(player_pos - boss_orb_pos)`
- Each frame: `boss_orb_pos += boss_orb_dir * boss_orb_speed`
- Collision with player uses 2D `math.hypot` distance check
- `player_iframes = 60` applied on hit to prevent stacking damage

**Key code:** `update_behavior()`, `draw_boss_orb()`, `check_collisions()`

---

## 4. 💥 Boss Shockwave (Expanding Ring)

**What it does:** The boss randomly triggers a shockwave — a magenta ring that expands outward from the boss's position. If the player is near the ring's leading edge AND close to the ground (i.e., hasn't jumped), they take 2 damage.

**How it works:**

- `boss_shockwave_radius += boss_shockwave_speed` each frame
- Collision: `abs(dist_to_boss - boss_shockwave_radius) <= 20 and pos_z < 30`
- Jumping over the shockwave is a valid dodge mechanic
- Ring deactivates after reaching radius `> 1200` or on player hit
- Cooldown: 360 frames before the next possible shockwave

**Rendering (v2.0):** `glutWireTorus` with a `glutSolidTorus` inner fill, blended with additive alpha
**Rendering (v1):** Quad-based ring using `GL_QUADS` with manual angle segments

**Key code:** `update_behavior()`, `draw_boss_shockwave()`, `check_collisions()`

---

## 5. 🦘 Player Jump & Camera Follow

**What it does:** The player can jump with a sine-eased arc. The camera follow target includes the player's vertical position so the jump is visible in frame.

**How it works:**

- `t = jump_timer / JUMP_FRAMES` (normalized 0→1 over the jump duration)
- `pos_z = sin(t * π) * MAX_JUMP_HEIGHT`
- `camera_control()` uses `player_z + 60` as the look-at target
- Jumping over shockwaves is the core defensive mechanic tied to this

**Tuning knobs:** `JUMP_FRAMES = 30`, `MAX_JUMP_HEIGHT = 80`

**Key code:** `update_logic()`, `draw_player()`, `camera_control()`

---

## 6. ⚔️ Katana Melee & Hit Detection

**What it does:** The player swings a katana with a visible animation arc. Enemies and the boss within melee range and in the player's forward cone take damage.

**How it works:**

- `is_swinging = True` triggers `katana_swing_angle` animation over multiple frames
- Hit detection uses a **dot product test**: forward vector of player dotted against the direction to the target
- If `dot_product > 0.5`, the target is within the ~60° forward cone
- Range check: `distance_3d(player, enemy) < 120`
- Boss can only be hit once per swing (`boss_hit_this_swing` flag)

**Hierarchical rendering:** The katana is translated and rotated as a child of the player's arm position via nested `glPushMatrix` / `glPopMatrix`

**Key code:** `draw_player()`, `check_collisions()`

---

## 7. 🌊 Player Orb Ability (Projectile)

**What it does:** The player fires a cyan energy sphere forward with a 3-second real-time cooldown. It travels in the player's facing direction and destroys the first thing it hits.

**How it works:**

- `orb_dir` is computed from `pos_angle` at fire time using trigonometry
- Cooldown enforced via `time.time() - last_orb_fire_time >= 3.0`
- Collision with enemies uses `math.hypot` in 2D; collision with boss uses the same check with the boss radius
- Orb deactivates when it exits the arena bounds or on hit

**Visual:** Rendered as a blended cyan sphere (`GL_BLEND`, additive in v2.0; solid in v1)

**Key code:** `keyboardListener()`, `update_logic()`, `draw_orb_projectile()`, `check_collisions()`

---

## 8. 💀 Enemy AI & Spawning

**What it does:** Up to 5 skeleton enemies are always active during the pre-boss phase. They pursue the player using vector movement and avoid clumping with a separation force.

**How it works:**

- `spawn_enemy()` places enemies at random `(x, y)` within ±800 units
- Each frame: `enemy.pos += normalize(player_pos - enemy_pos) * enemy_speed`
- Separation: if two enemies are closer than `2 * enemy_radius`, a small push force separates them
- A **stopping distance of 35 units** prevents enemies from walking into each other on top of the player

**Loot drops on kill:**

- 20% chance: ❤️ heart
- 40% chance: 🪙 coin
- 40% chance: nothing

**Key code:** `spawn_enemy()`, `update_behavior()`, `check_collisions()`

---

## 9. 🛡️ Collision, Damage & Invincibility Frames

**What it does:** All damage sources are centralized in `check_collisions()`. On taking a hit, the player enters an invincibility window during which no further damage can be applied. The player model blinks red as visual feedback.

**How it works:**

- `player_iframes` is set on hit (60 frames for orb/melee hits, 90 frames for shockwave)
- `player_iframes` decrements by 1 each frame in `check_collisions()`
- Blink logic in `draw_player()`: `is_blinking = player_iframes > 0 and (player_iframes // 5) % 2 == 0`
- All damage sources check `player_iframes <= 0` before applying damage

**Key code:** `check_collisions()`, `draw_player()`

---

## 10. 🖥️ HUD, Boss Bar & Overlays

**What it does:** A persistent heads-up display shows health, score, orb cooldown status, cheat mode indicator, and the boss HP bar. Game Over and Victory screens are rendered as full-screen overlays.

**How it works:**

- `draw_ui()` switches to orthographic 2D projection (`gluOrtho2D`) and disables depth test so UI always renders on top
- Health bar: a gray background rect + a green fill rect scaled by `player_health / max_health`
- Boss bar: centered red bar, only visible during boss phase
- Orb cooldown: green "ORB READY" text or orange countdown timer using `time.time()`
- Overlays are conditionally rendered based on `game_over` and `boss_defeated` flags
- UI is hidden entirely during `domain_animating` for a clean cinematic window

**Key code:** `draw_ui()`, `draw_rect()`, `draw_text()`

---

## 11. ✨ Procedural World & Atmosphere

**What it does:** The arena is populated with broken buildings and trees generated procedurally at startup. 8,000 ash/dust particles cover the ground for atmosphere.

**How it works:**

- `generate_world_data()` iterates a grid at 120-unit steps along the arena border
- Every 3rd group of positions spawns trees (with random jitter offsets); others become buildings
- Buildings are rendered as staggered stacks of `glutSolidCube` with offset per floor for a "broken" look
- Trees use a `gluCylinder` trunk + two `glutSolidSphere` foliage layers
- In `domain_mode`, tree foliage turns blood-red (`0.5, 0.0, 0.0`) and buildings glow amber

**Ash particles:** `GL_POINTS` drawn across the ground plane, each with a random grayscale brightness `[0.15, 0.35]`

**Key code:** `generate_world_data()`, `draw_scenery()`, `draw_broken_building()`, `draw_tree()`, `draw_ground()`

---

## 12. 🤖 Auto-Guardian (Cheat Mode)

**What it does:** Toggling cheat mode hands control of the player to an AI that automatically targets and kills enemies and the boss. Also disables all incoming damage.

**How it works:**

- `auto_guardian()` called each frame when `cheat_mode = True`
- Finds the nearest enemy using `min(enemies, key=distance)` and steers toward it
- If within melee range, sets `is_swinging = True`
- Boss targeting: moves to within 140 units, then swings continuously
- `cheat_mode` flag also skips all damage application in `check_collisions()`

**Key code:** `auto_guardian()`, `check_collisions()`, `keyboardListener()`

---

## What Changed from v1 → v2.0 (Prantik)

| Feature                 | v1 (`Aegis_DomainOfEchoes.py`)               | v2.0 (`Aegis_DoE_v2.0.py`)                                                |
| ----------------------- | -------------------------------------------- | ------------------------------------------------------------------------- |
| Transparency / Blending | No — solid colors only (template constraint) | Yes — `GL_BLEND` with additive blending on orbs, domain sphere, shockwave |
| Shockwave rendering     | Quad ring using `GL_QUADS`                   | `glutWireTorus` + `glutSolidTorus` with fallback                          |
| `draw_rect` alpha       | Ignored (solid fill)                         | Used properly with `GL_BLEND`                                             |
| Player orb visual       | Solid sphere                                 | Two-layer blended sphere (outer glow + inner core)                        |
| Boss orb visual         | Solid orange sphere                          | Blended with additive `GL_SRC_ALPHA, GL_ONE`                              |
| `glPushAttrib`          | Removed (template restriction)               | Restored for correct GL state management                                  |

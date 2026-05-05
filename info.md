# ⛩️ Aegis: Domain of Echoes

Tagline: A neon-soaked chase against a rising domain boss—dodge the shockwaves, master the roll, and survive the final clash.

---

## High-level game idea

Aegis: Domain of Echoes is a third-person, stylized arena action game built with PyOpenGL. The player explores a modular arena, fights roaming skeletons and a unique Domain Boss. When the score threshold is reached the boss triggers a cinematic "Domain Expansion" (camera barrel roll and darkening ground). The boss slowly rises from below and uses two main attacks: a seeking orb projectile and an expanding shockwave ring. The player can jump, swing a katana, and fire a timed orb ability to damage the boss and enemies. The game uses immediate-mode OpenGL and frame-based animations.

Design goals:

- Fast, predictable physics and simple, tunable frame-based animations.
- Clear telegraphs for boss attacks (visual rings, glow) so skilled players can dodge.
- Cinematic domain expansion and boss-rise sequence that disable normal player input.
- Lightweight codebase with global-state driven game loop for easy modification.

---

## Core game logic / systems

- Main loop: `showScreen()` calls `update_logic()` then renders the scene.
- World generation: `generate_world_data()` populates building and tree data and ash particles.
- Player state: `pos_x`, `pos_y`, `pos_angle`, `pos_z` (jump height), `player_iframes` (invulnerability/blink timer), health and score.
- Enemies: `enemies[]` are spawned and moved toward the player. Collision and damage handled in `check_collisions()`.
- Boss lifecycle:
  - Spawn: triggered by score threshold (example: 500).
  - Cinematic: `domain_animating`, `domain_anim_angle` drive the camera barrel-roll and domain visuals.
  - Rise: `boss_is_rising` drives boss z position from underground to surface.
  - Active: boss moves and attacks (orb + shockwave). State variables: `boss_active`, `boss_health`.
  - Defeat: `boss_defeated` flag and UI overlay; recommended to add `boss_defeat_anim` if a defeat animation is desired instead of instant overlay.
- Boss attacks:
  - Orb: `boss_orb_active`, `boss_orb_pos`, `boss_orb_dir`, `boss_orb_speed`, `boss_orb_cooldown` — a seeking projectile.
  - Shockwave: `boss_shockwave_active`, `boss_shockwave_radius`, `boss_shockwave_speed`, `boss_shockwave_cooldown` — expanding ring. Collision detected by checking `abs(dist_to_boss - boss_shockwave_radius) <= tolerance` and `pos_z` threshold.
- UI: `draw_ui()` renders health, score, boss health bar and overlays. UI rendering disables depth so it appears on top.

---

## Controls

- Movement: W/A/S/D (relative to camera) — move and turn.
- Jump: Spacebar — fixed-frame sine-eased jump (height tuned by `MAX_JUMP_HEIGHT` and duration by `JUMP_FRAMES`).
- Swing katana: Left mouse (sets `is_swinging`) — close-range melee.
- Fire orb (ranged): F — spawns an orb projectile from the player with a 3s cooldown (`last_orb_fire_time`).
- Toggle domain mode (visual debug): X
- Toggle cheat mode (invulnerable / auto-attack): C
- Restart when dead/defeated: R
- Quit: ESC

Notes:

- Orb cooldown is enforced with real time (seconds). Other timers use frame counts for consistency.
- `player_iframes` is set on hit (e.g., 60 frames ≈ 1s at 60 FPS).

---

## Where to look in code (quick map)

- `Game_v2.py` — main playable build (current active file): contains the overall game loop, world gen, input, rendering and game logic.
  - `generate_world_data()` — world
  - `update_behavior()` — enemy + boss AI and attacks
  - `update_logic()` — input handling, player movement, jump math, cutscenes
  - `check_collisions()` — collision detection, damage, boss death
  - `draw_boss_shockwave()` — shockwave visual
  - `draw_player()` — draw and blink logic
  - `draw_ui()` — HUD and overlays

- `test.py`, `test2.py`, `demo.py` — variants / earlier iterations with similar code. Useful for reference.

---

## Team feature breakdown — implementation features (12)

Below are 12 concrete, code-level features (each maps to specific functions/files). These are implementation tasks — not abstract product-level items — so each can be assigned and implemented independently.

1. Domain Expansion (Cinematic) — feature
   - Purpose: trigger and animate the domain expansion cutscene (camera barrel-roll, darkening ground, domain visuals).
   - Key code: `domain_animating`, `domain_anim_angle`, `update_logic()`, `showScreen()`.
   - Files: `Game_v2.py` (`update_logic()`, `showScreen()`, `draw_ui()`).
   - Acceptance: when score threshold reached the camera auto-spins, domain visuals (expanding sphere/dome) render and player input is disabled for the duration; domain ends at 360° and boss rise begins.

2. Boss Rise Cinematic — feature
   - Purpose: boss spawns underground and rises slowly after the cinematic, invulnerable until fully risen.
   - Key code: `boss['z']`, `boss_is_rising`, `update_behavior()`, `draw_boss()`.
   - Files: `Game_v2.py` (`update_behavior()`, `draw_boss()`).
   - Acceptance: boss.z moves from negative to 0 over multiple frames; collisions/attacks ignored while `boss_is_rising` is True.

3. Boss Orb Projectile (seeking) — feature
   - Purpose: boss fires a seeking orb toward the player with cooldown and visual feedback.
   - Key code: `boss_orb_active`, `boss_orb_pos`, `boss_orb_dir`, `boss_orb_speed`, `boss_orb_cooldown`, `draw_boss_orb()`.
   - Files: `Game_v2.py` (`update_behavior()`, `draw_boss_orb()`, `check_collisions()`).
   - Acceptance: orb telegraphs when spawned, seeks player position, damages player on hit, respects cooldown.

4. Boss Shockwave Launch (expanding ring) — feature
   - Purpose: expand ring from boss position, damage player when ring hits and player is near ground.
   - Key code: `boss_shockwave_active`, `boss_shockwave_radius`, `boss_shockwave_speed`, `boss_shockwave_cooldown`, `draw_boss_shockwave()`, collision in `check_collisions()`.
   - Files: `Game_v2.py` (`update_behavior()`, `draw_boss_shockwave()`, `check_collisions()`).
   - Acceptance: shockwave triggers per cooldown/chance, radius increases each frame, collision uses ring delta tolerance and vertical threshold, and visual is readable but not scene-occluding.

5. Player Jumping & Camera Follow — feature
   - Purpose: player jump arc (sine easing) and camera adjusting to `player_z` so jump is visible.
   - Key code: `is_jumping`, `jump_timer`, `JUMP_FRAMES`, `MAX_JUMP_HEIGHT`, `pos_z`, `camera_control()`.
   - Files: `Game_v2.py` (`update_logic()`, `draw_player()`, `camera_control()`).
   - Acceptance: spacebar initiates jump, `pos_z` follows sine curve, camera look target includes `player_z` so player is centered during jump.

6. Melee Swing & Hit Detection — feature
   - Purpose: katana swing animation and cone-based hit detection that damages boss/enemies.
   - Key code: `is_swinging`, `katana_swing_angle`, swing cone dot-product checks in `check_collisions()`.
   - Files: `Game_v2.py` (`draw_player()`, `check_collisions()`).
   - Acceptance: swing toggles animation, enemies/boss in front and within range take damage only once per swing.

7. Player Orb Ability (projectile) — feature
   - Purpose: player fires an orb that travels forward, collides with enemies/boss, has cooldown.
   - Key code: `orb_active`, `orb_pos`, `orb_dir`, `last_orb_fire_time`, `draw_orb_projectile()`, `check_collisions()`.
   - Files: `Game_v2.py` (`keyboardListener()`, `update_logic()`, `draw_orb_projectile()`, `check_collisions()`).
   - Acceptance: F fires orb if cooldown elapsed; orb moves and deals damage on collision.

8. Enemy AI & Spawning System — feature
   - Purpose: spawn enemies, simple pursuit, separation, and loot drops on death.
   - Key code: `spawn_enemy()`, `enemies[]`, `update_behavior()`, `check_collisions()`.
   - Files: `Game_v2.py` (`spawn_enemy()`, `update_behavior()`, `check_collisions()`).
   - Acceptance: enemies spawn to a target population, move toward player, avoid overlap, and drop loot when killed.

9. Collision, Damage & I-frames System — feature
   - Purpose: centralized collision checks for all damage sources and frame-locked invulnerability (blinking).
   - Key code: `check_collisions()`, `player_iframes`, damage assignments, blink logic in `draw_player()`.
   - Files: `Game_v2.py` (`check_collisions()`, `draw_player()`).
   - Acceptance: hits set `player_iframes` appropriately, decrement each frame, and blinking visual corresponds to iframe state.

10. HUD, Boss Bar & Overlays — feature

- Purpose: draw health, score, boss health bar, orb cooldown, and Game Over / Victory overlays above the 3D scene.
- Key code: `draw_ui()`, depth/lighting state changes for UI.
- Files: `Game_v2.py` (`draw_ui()`).
- Acceptance: UI renders above the scene, shows correct values, and Game Over/Victory appear only when their flags are set.

11. Particles & Visual Effects System — feature

- Purpose: ash particles, orb trails, shockwave particle bursts, and boss defeat particles; GL state-safe rendering.
- Key code: `ash_particles`, `generate_world_data()`, `draw_boss_shockwave()`, and new particle helper functions.
- Files: `Game_v2.py` (plus optional new `particles.py`).
- Acceptance: particle effects are visible, performant, and do not break UI or scene layering.

12. Options & Config Persistence — feature

- Purpose: basic options (key remap, color palettes, UI scale) stored in JSON; simple in-game menu or file-based toggles.
- Key code: new `options.py` helper or code in `Game_v2.py`, read/write JSON, and patch code to respect color schemes and keymap.
- Files: `Game_v2.py`, optional `options.py`, `config.json`.
- Acceptance: changing options affects visuals/controls and persists between runs via a config file.

---

## Implementation notes, edge-cases & tuning knobs

- Timers are frame-based (e.g., `player_iframes = 60`), so measure playtime on target machine. If your framerate varies widely, consider converting key timers to time-based (seconds using `time.time()`).
- Shockwave collision uses ring-distance math which is sensitive to `boss_shockwave_speed` and player speed: tune `boss_shockwave_speed`, `tolerance` (currently ±20), and `boss_shockwave_cooldown` for fair telegraphing.
- Jump uses sine easing: `pos_z = sin(t * pi) * MAX_JUMP_HEIGHT`. `t` is fraction of jump frames. Tune `JUMP_FRAMES` and `MAX_JUMP_HEIGHT` for feel.
- Beware OpenGL state: always restore depth mask / blend / lighting to avoid UI or scene occlusion bugs.

---

## Minimal testing checklist

- [ ] Player can move and jump; camera follows player_z.
- [ ] Player blinks for configured iframes on hit and is invulnerable while frames > 0.
- [ ] Boss cinematic (domain expansion) disables player input and performs barrel roll.
- [ ] Boss rises after cinematic and begins attacks.
- [ ] Boss orb tracks and damages player; orb cooldown enforced.
- [ ] Shockwave expands and damages player only when near ground and within ring tolerance.
- [ ] Loot spawns on enemy/boss defeat (coins/hearts).
- [ ] UI overlays are visible above 3D scene and are toggled correctly.

---

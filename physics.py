import math

def remove_enemies_in_swing(enemies, px, py, angle_deg, reach=120.0, width=60.0):
    """
    Remove enemies inside a rectangular swing hitbox in front of the player.

    - enemies: list of enemy dicts with 'x' and 'y' keys (mutated in-place)
    - px,py: player position
    - angle_deg: player facing in degrees (same convention as pos_angle)
    - reach: forward distance of the hitbox
    - width: total lateral width of the hitbox

    Returns the number of enemies removed.
    """
    if not enemies:
        return 0

    rad = math.radians(angle_deg)
    # forward vector used by project: forward = (sin(angle), -cos(angle))
    fx = math.sin(rad)
    fy = -math.cos(rad)
    # right vector perpendicular to forward
    rx = fy
    ry = -fx

    half_w = width * 0.5

    removed = 0
    # iterate backwards so we can remove from list safely
    for i in range(len(enemies)-1, -1, -1):
        e = enemies[i]
        ex = e.get('x', 0.0)
        ey = e.get('y', 0.0)
        dx = ex - px
        dy = ey - py
        forward_dist = dx * fx + dy * fy
        lateral = dx * rx + dy * ry
        # optionally take enemy size into account
        size = e.get('size', 20.0)
        # enlarge hit area slightly by enemy size
        if 0 <= forward_dist <= (reach + size*0.5) and abs(lateral) <= (half_w + size*0.5):
            try:
                enemies.pop(i)
                removed += 1
            except Exception:
                # if removal fails, mark as dead if supported
                if 'alive' in e:
                    e['alive'] = False
                    removed += 1
    return removed

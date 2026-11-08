#!/usr/bin/env python3
"""
Symulacja Kamery Cofania w Samochodzie - Parking
Backup Camera Simulation - Parking Lot

Controls / Sterowanie:
  W / ↑     - do przodu (forward)
  S / ↓     - cofanie   (reverse)
  A / ←     - skręt lewo (steer left)
  D / →     - skręt prawo (steer right)
  R         - reset pozycji (reset position)
  ESC       - wyjście (quit)
"""

import pygame
import math
import sys
import random

# ═══════════════════════════════════════════════════════════════════════════════
#  INIT
# ═══════════════════════════════════════════════════════════════════════════════
pygame.init()

CAM_W, CAM_H = 900, 750     # left panel: backup camera feed
MAP_W, MAP_H = 500, 750     # right panel: top-down map
SW  = CAM_W + MAP_W          # total width  = 1400
SH  = max(CAM_H, MAP_H)     # total height = 750

screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Symulacja Kamery Cofania | Backup Camera Simulation")
clock  = pygame.time.Clock()
FPS    = 60

font_sm = pygame.font.SysFont("segoeui", 15)
font_md = pygame.font.SysFont("segoeui", 20, bold=True)
font_lg = pygame.font.SysFont("segoeui", 30, bold=True)
font_xl = pygame.font.SysFont("segoeui", 44, bold=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  COLORS
# ═══════════════════════════════════════════════════════════════════════════════
ASPHALT   = (38,  40,  52)
ASPHALT2  = (50,  52,  65)
LINE_W    = (200, 202, 215)
LINE_Y    = (255, 215,   0)
WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
RED       = (220,  55,  55)
RED_HI    = (255, 110, 110)
GREEN     = ( 55, 210,  85)
YELLOW    = (255, 220,   0)
ORANGE    = (255, 155,  30)
GRAY      = (100, 102, 115)
DGRAY     = ( 40,  42,  55)
LGRAY     = (160, 162, 175)
SKY1      = ( 12,  15,  28)
SKY2      = ( 28,  32,  50)
GND1      = ( 42,  44,  58)
GND2      = ( 60,  63,  78)
CAR_C     = (200,  60,  60)
CAR_D     = (140,  30,  30)
CAR_WIN   = (140, 190, 240)
FOV_C     = ( 20, 160, 255)

PED_COLS = [
    (100, 165, 255), (255, 180, 60),  (100, 225, 135),
    (255, 110, 185), (200, 145, 255), (255, 225, 90),
    ( 70, 205, 220), (255, 150, 100), (140, 230, 200),
    (230, 200, 100), (180, 255, 160), (255, 160, 220),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  WORLD / PARKING LOT
# ═══════════════════════════════════════════════════════════════════════════════
WORLD_W  = 1600
WORLD_H  = 1000
METER    = 30.0      # world units per 1 real meter

SPOT_W   = 60
SPOT_H   = 100
N_SPOTS  = 20
ROW1_Y   = 80                         # top parking row start
ROW2_Y   = WORLD_H - 80 - SPOT_H      # bottom row start  (= 820)
START_X  = 100
LANE_Y   = WORLD_H // 2               # main driving lane y-centre (= 500)

top_spots = [pygame.Rect(START_X + i*SPOT_W, ROW1_Y, SPOT_W, SPOT_H) for i in range(N_SPOTS)]
bot_spots = [pygame.Rect(START_X + i*SPOT_W, ROW2_Y, SPOT_W, SPOT_H) for i in range(N_SPOTS)]

random.seed(42)
occ_top = set(random.sample(range(N_SPOTS), 13))
occ_bot = set(random.sample(range(N_SPOTS), 12))

# parked car colours (random, seeded)
_car_colors = [
    (90, 100, 160), (160, 80, 60), (60, 130, 100),
    (140, 110, 50), (80, 90, 120), (160, 60, 120),
    (100, 160, 80), (50, 110, 160),
]
rng = random.Random(99)
top_colors = [rng.choice(_car_colors) for _ in range(N_SPOTS)]
bot_colors = [rng.choice(_car_colors) for _ in range(N_SPOTS)]

# ═══════════════════════════════════════════════════════════════════════════════
#  CAMERA PROJECTION CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
CAM_FOV   = 160        # horizontal field of view in degrees
FOCAL     = 420        # focal length in pixels
HORIZON_Y = int(CAM_H * 0.40)   # = 300
GROUND_K  = FOCAL * 22           # ground-plane perspective constant  ≈ 9240

# Pre-render sky gradient (static)
_sky_surf = pygame.Surface((CAM_W, HORIZON_Y))
for _y in range(HORIZON_Y):
    _t = _y / max(1, HORIZON_Y - 1)
    pygame.draw.line(_sky_surf, (
        int(SKY1[0] + (SKY2[0] - SKY1[0]) * _t),
        int(SKY1[1] + (SKY2[1] - SKY1[1]) * _t),
        int(SKY1[2] + (SKY2[2] - SKY1[2]) * _t),
    ), (0, _y), (CAM_W, _y))

# Pre-render ground gradient (static)
_gnd_h    = CAM_H - HORIZON_Y
_gnd_surf = pygame.Surface((CAM_W, _gnd_h))
for _y in range(_gnd_h):
    _t = _y / max(1, _gnd_h - 1)
    pygame.draw.line(_gnd_surf, (
        int(GND1[0] + (GND2[0] - GND1[0]) * _t),
        int(GND1[1] + (GND2[1] - GND1[1]) * _t),
        int(GND1[2] + (GND2[2] - GND1[2]) * _t),
    ), (0, _y), (CAM_W, _y))


# ═══════════════════════════════════════════════════════════════════════════════
#  CAR
# ═══════════════════════════════════════════════════════════════════════════════
class Car:
    W = 38   # width  (world units)
    L = 76   # length (world units)

    def __init__(self):
        self.reset()

    def reset(self):
        self.x     = WORLD_W * 0.45
        self.y     = float(LANE_Y)
        self.angle = 0.0      # degrees; 0 = right (+x), 90 = down (+y)
        self.speed = 0.0
        self.collision = False
        self.col_timer  = 0
        self.odometer   = 0.0

    # ── computed properties ──────────────────────────────────────
    @property
    def fwd(self):
        a = math.radians(self.angle)
        return math.cos(a), math.sin(a)

    @property
    def rgt(self):
        fx, fy = self.fwd
        return -fy, fx

    @property
    def rear(self):
        fx, fy = self.fwd
        return self.x - fx * self.L / 2, self.y - fy * self.L / 2

    def corners(self):
        fx, fy = self.fwd
        rx, ry = self.rgt
        hw, hl = self.W / 2, self.L / 2
        return [
            (self.x + fx*hl + rx*hw, self.y + fy*hl + ry*hw),   # front-right
            (self.x + fx*hl - rx*hw, self.y + fy*hl - ry*hw),   # front-left
            (self.x - fx*hl - rx*hw, self.y - fy*hl - ry*hw),   # rear-left
            (self.x - fx*hl + rx*hw, self.y - fy*hl + ry*hw),   # rear-right
        ]

    # ── update ───────────────────────────────────────────────────
    def update(self, keys):
        MAX_FWD, MAX_REV = 5.0, 3.2
        ACC  = 0.14
        FRIC = 0.90
        STEER = 2.6

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.speed = min(self.speed + ACC, MAX_FWD)
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.speed = max(self.speed - ACC, -MAX_REV)
        else:
            self.speed *= FRIC
            if abs(self.speed) < 0.03:
                self.speed = 0.0

        if abs(self.speed) > 0.08:
            sgn = 1 if self.speed > 0 else -1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.angle -= STEER * sgn
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.angle += STEER * sgn

        fx, fy = self.fwd
        self.x = max(self.L, min(WORLD_W - self.L, self.x + fx * self.speed))
        self.y = max(self.L, min(WORLD_H - self.L, self.y + fy * self.speed))
        self.odometer += abs(self.speed)

        if self.col_timer > 0:
            self.col_timer -= 1
            if self.col_timer == 0:
                self.collision = False


# ═══════════════════════════════════════════════════════════════════════════════
#  PEDESTRIAN
# ═══════════════════════════════════════════════════════════════════════════════
class Pedestrian:
    R = 12   # collision radius

    def __init__(self):
        self.x     = random.uniform(START_X + 20, START_X + N_SPOTS*SPOT_W - 20)
        self.y     = random.uniform(ROW1_Y + SPOT_H + 10, ROW2_Y - 10)
        self.color = random.choice(PED_COLS)
        self.dir   = random.uniform(0, 360)
        self.spd   = random.uniform(0.3, 0.9)
        self.timer = random.randint(60, 240)
        self.hit   = False
        self.hit_timer = 0

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.dir   = random.uniform(0, 360)
            self.spd   = random.uniform(0.3, 0.9)
            self.timer = random.randint(60, 240)

        rad = math.radians(self.dir)
        nx  = self.x + math.cos(rad) * self.spd
        ny  = self.y + math.sin(rad) * self.spd

        bx_min = START_X + 10
        bx_max = START_X + N_SPOTS * SPOT_W - 10
        by_min = ROW1_Y + SPOT_H + 5
        by_max = ROW2_Y - 5

        if nx < bx_min or nx > bx_max:
            self.dir = 180 - self.dir
            nx = self.x
        if ny < by_min or ny > by_max:
            self.dir = -self.dir
            ny = self.y

        self.x, self.y = nx, ny

        if self.hit_timer > 0:
            self.hit_timer -= 1
            if self.hit_timer == 0:
                self.hit = False


# ═══════════════════════════════════════════════════════════════════════════════
#  PROJECTION UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def world_to_cam(wx, wy, car):
    """
    Project world point (wx, wy) into backup-camera screen space.

    Camera sits at the car's rear centre, facing backward.
    Camera basis:
      forward = -car.fwd          (camera looks opposite to car heading)
      right   = (sin a, -cos a)   (derived to form right-handed basis)

    Returns (screen_x, screen_y, depth) or None if behind/out of FOV.
    """
    rx, ry = car.rear
    dx, dy = wx - rx, wy - ry

    a = math.radians(car.angle)
    cfx, cfy =  -math.cos(a), -math.sin(a)   # camera forward
    crx, cry =   math.sin(a), -math.cos(a)   # camera right

    depth   = dx * cfx + dy * cfy
    lateral = dx * crx + dy * cry

    if depth < 1.0:
        return None

    hfov = math.radians(CAM_FOV / 2)
    if abs(math.atan2(abs(lateral), depth)) > hfov:
        return None

    sx = CAM_W // 2 + int(lateral * FOCAL / depth)
    sy = HORIZON_Y  + int(GROUND_K / depth)
    return sx, sy, depth


def cam_ground(wx, wy, car):
    """Return (sx, sy_ground) for a world ground-plane point, or None."""
    r = world_to_cam(wx, wy, car)
    if r is None:
        return None
    sx, _, depth = r
    sy = HORIZON_Y + int(GROUND_K / depth)
    return sx, sy


# ═══════════════════════════════════════════════════════════════════════════════
#  CAMERA VIEW  (left panel)
# ═══════════════════════════════════════════════════════════════════════════════
def draw_camera_view(surf, car, peds):
    # Sky + ground gradients
    surf.blit(_sky_surf, (0, 0))
    surf.blit(_gnd_surf, (0, HORIZON_Y))

    # Parking lot lines
    _cam_parking_lines(surf, car)

    # Parked cars
    _cam_parked_cars(surf, car)

    # Pedestrians — painter's algorithm: far → near
    visible = []
    for ped in peds:
        r = world_to_cam(ped.x, ped.y, car)
        if r:
            visible.append((r[2], ped, r[0]))    # (depth, ped, screen_x)
    visible.sort(reverse=True)
    for depth, ped, sx in visible:
        _cam_pedestrian(surf, sx, depth, ped)

    # Distance guide arcs + side guide lines
    _cam_guidelines(surf, car)

    # HUD overlay
    _cam_hud(surf, car)


# ── camera helpers ─────────────────────────────────────────────────────────────
def _cam_parking_lines(surf, car):
    dim   = (88, 91, 106)
    dim_y = (100, 90, 25)

    # Vertical dividers + horizontal edges per row
    for row_y, row_h in [(ROW1_Y, SPOT_H), (ROW2_Y, SPOT_H)]:
        # Horizontal top/bottom edges
        for edge_y in (row_y, row_y + row_h):
            pts = []
            for i in range(N_SPOTS + 1):
                p = cam_ground(START_X + i * SPOT_W, edge_y, car)
                if p:
                    pts.append(p)
            if len(pts) >= 2:
                pygame.draw.lines(surf, dim, False, pts, 1)

        # Vertical spot dividers
        for i in range(N_SPOTS + 1):
            wx = START_X + i * SPOT_W
            p1 = cam_ground(wx, row_y,          car)
            p2 = cam_ground(wx, row_y + row_h,  car)
            if p1 and p2:
                pygame.draw.line(surf, dim, p1, p2, 1)

    # Dashed centre-lane line
    for xi in range(START_X, START_X + N_SPOTS * SPOT_W - 1, 50):
        p1 = cam_ground(xi,       LANE_Y, car)
        p2 = cam_ground(xi + 25,  LANE_Y, car)
        if p1 and p2:
            pygame.draw.line(surf, dim_y, p1, p2, 2)


def _cam_parked_cars(surf, car):
    for i in occ_top:
        if i >= N_SPOTS:
            continue
        cx = START_X + i * SPOT_W + SPOT_W // 2
        cy = ROW1_Y + SPOT_H // 2
        _cam_box(surf, car, cx, cy, SPOT_W - 10, SPOT_H - 14, 90, top_colors[i])

    for i in occ_bot:
        if i >= N_SPOTS:
            continue
        cx = START_X + i * SPOT_W + SPOT_W // 2
        cy = ROW2_Y + SPOT_H // 2
        _cam_box(surf, car, cx, cy, SPOT_W - 10, SPOT_H - 14, 270, bot_colors[i])


def _cam_box(surf, car, wx, wy, ww, wh, hdg_deg, body_col):
    """Project and draw a rectangular box (parked car) in camera view."""
    a      = math.radians(hdg_deg)
    fx, fy = math.cos(a), math.sin(a)
    rx, ry = -fy, fx
    hw, hl = ww / 2, wh / 2

    base_world = [
        (wx + fx*hl + rx*hw, wy + fy*hl + ry*hw),
        (wx + fx*hl - rx*hw, wy + fy*hl - ry*hw),
        (wx - fx*hl - rx*hw, wy - fy*hl - ry*hw),
        (wx - fx*hl + rx*hw, wy - fy*hl + ry*hw),
    ]

    pts_bot, pts_top, depths = [], [], []
    for bx, by in base_world:
        r = world_to_cam(bx, by, car)
        if r:
            sx_b, _, dep = r
            sy_b   = HORIZON_Y + int(GROUND_K / dep)
            px_h   = max(5, int(FOCAL * 1.5 * METER / dep))   # ~1.5 m car height
            pts_bot.append((sx_b, sy_b))
            pts_top.append((sx_b, sy_b - px_h))
            depths.append(dep)

    n = min(len(pts_bot), len(pts_top))
    if n >= 3:
        try:
            roof = tuple(min(c + 25, 255) for c in body_col)
            shade = tuple(max(c - 40, 0) for c in body_col)
            # Side faces
            sides = pts_bot[:n] + list(reversed(pts_top[:n]))
            pygame.draw.polygon(surf, shade, sides)
            # Roof
            pygame.draw.polygon(surf, roof,  pts_top[:n])
            # Outline
            pygame.draw.polygon(surf, (20, 22, 32), sides,       1)
            pygame.draw.polygon(surf, (20, 22, 32), pts_top[:n], 1)
        except Exception:
            pass


def _cam_pedestrian(surf, sx, depth, ped):
    """Draw a perspective-scaled stick figure pedestrian."""
    sy_gnd = HORIZON_Y + int(GROUND_K / depth)
    scale  = max(0.2, min(3.5, 22.0 / depth))

    bh  = int(55 * scale)    # total body height (ground to top of head)
    bw  = int(14 * scale)    # torso width
    hr  = max(3, int(10 * scale))  # head radius

    head_y = sy_gnd - bh
    if head_y > CAM_H or sy_gnd < HORIZON_Y - 20 or sx < -60 or sx > CAM_W + 60:
        return

    c  = ped.color if not ped.hit else RED_HI
    cd = (max(0, c[0] - 65), max(0, c[1] - 65), max(0, c[2] - 65))

    # Shadow
    sw = max(5, int(16 * scale))
    pygame.draw.ellipse(surf, (22, 24, 36),
                        (sx - sw, sy_gnd - 4, sw * 2, 7))

    # Legs
    pygame.draw.rect(surf, cd,
                     (sx - bw // 2, sy_gnd - bh // 2, bw, bh // 2))
    # Torso
    pygame.draw.rect(surf, c,
                     (sx - bw // 2, head_y + hr, bw, bh // 2))
    # Head
    pygame.draw.circle(surf, c, (sx, head_y), hr)
    pygame.draw.circle(surf, (20, 22, 32), (sx, head_y), hr, 1)


def _cam_guidelines(surf, car):
    """
    Draw:
      - Colour-coded distance arcs: green=4m, orange=2m, red=1m
      - Yellow side guide lines extending from rear corners
    """
    rx, ry = car.rear
    a      = math.radians(car.angle)

    for dist_m, col, lw in [
        (4 * METER, GREEN,  2),
        (2 * METER, ORANGE, 2),
        (1 * METER, RED,    3),
    ]:
        pts = []
        for deg in range(-76, 77, 3):
            ang = a + math.pi + math.radians(deg)
            p   = cam_ground(rx + math.cos(ang) * dist_m,
                             ry + math.sin(ang) * dist_m, car)
            if p:
                pts.append(p)
        if len(pts) >= 2:
            pygame.draw.lines(surf, col, False, pts, lw)

    # Side guide lines from rear corners going backward
    crx, cry = car.rgt
    fx, fy   = car.fwd
    hw       = car.W / 2

    for side in (-1, 1):
        # Start slightly behind the car's rear corner
        near_x = rx + crx * hw * side - fx * 4
        near_y = ry + cry * hw * side - fy * 4
        far_x  = rx + crx * hw * side - fx * 4 * METER
        far_y  = ry + cry * hw * side - fy * 4 * METER

        p1 = cam_ground(near_x, near_y, car)
        p2 = cam_ground(far_x,  far_y,  car)
        if p1 and p2:
            pygame.draw.line(surf, YELLOW, p1, p2, 2)


def _cam_hud(surf, car):
    """Overlay HUD elements on camera view."""
    # Border — red flash on collision
    border_col = RED if car.collision else DGRAY
    pygame.draw.rect(surf, border_col, (0, 0, CAM_W, CAM_H), 5 if car.collision else 2)

    # Top bar
    pygame.draw.rect(surf, (5, 6, 16), (0, 0, CAM_W, 50))
    surf.blit(font_lg.render("KAMERA COFANIA", True, WHITE), (18, 11))
    surf.blit(font_sm.render("● REC", True, RED_HI), (CAM_W - 65, 18))

    # Distance legend (bottom-right)
    for label, col, dy in [("4m", GREEN, 110), ("2m", ORANGE, 90), ("1m", RED, 70)]:
        pygame.draw.rect(surf, col,   (CAM_W - 68, CAM_H - dy,     22, 8))
        surf.blit(font_sm.render(label, True, LGRAY),
                  (CAM_W - 42, CAM_H - dy - 2))

    # Speed
    kmh = int(abs(car.speed) * 15)
    surf.blit(font_md.render(f"{kmh} km/h", True, WHITE), (18, CAM_H - 36))

    # Gear indicator (D / R / P)
    if   car.speed < -0.08: gear, gc = "R", RED_HI
    elif car.speed >  0.08: gear, gc = "D", GREEN
    else:                   gear, gc = "P", YELLOW
    surf.blit(font_xl.render(gear, True, gc), (CAM_W - 65, CAM_H - 65))

    # Collision warning (flashing)
    if car.collision and (pygame.time.get_ticks() // 280) % 2 == 0:
        warn = font_xl.render("⚠  UWAGA!  KOLIZJA!", True, RED_HI)
        wx   = CAM_W // 2 - warn.get_width() // 2
        pygame.draw.rect(surf, (50, 0, 0),
                         (wx - 14, CAM_H // 2 - 32, warn.get_width() + 28, 62))
        surf.blit(warn, (wx, CAM_H // 2 - 26))

    # Light scan-line vignette around camera edges (cosmetic)
    _draw_vignette(surf)


def _draw_vignette(surf):
    """Draw subtle dark gradient around camera edges."""
    v = pygame.Surface((CAM_W, CAM_H), pygame.SRCALPHA)
    # Simple corner fade via semi-transparent rects (cheap approx)
    for i in range(12):
        alpha = 10 + i * 4
        pygame.draw.rect(v, (0, 0, 0, alpha),
                         (i, i, CAM_W - i*2, CAM_H - i*2), 1)
    surf.blit(v, (0, 0))


# ═══════════════════════════════════════════════════════════════════════════════
#  TOP-DOWN MAP  (right panel)
# ═══════════════════════════════════════════════════════════════════════════════
MAP_SCL = 0.40      # world units → screen pixels
MAP_X0  = CAM_W    # screen x-offset for map panel

def draw_topdown(surf, car, peds):
    """Draw the bird's-eye-view panel (car-centered / follows the player)."""
    cam_wx, cam_wy = car.x, car.y

    def w2s(wx, wy):
        """World → map-panel screen coords."""
        sx = MAP_X0 + MAP_W // 2 + int((wx - cam_wx) * MAP_SCL)
        sy =          MAP_H // 2 + int((wy - cam_wy) * MAP_SCL)
        return sx, sy

    # Background
    pygame.draw.rect(surf, ASPHALT, (MAP_X0, 0, MAP_W, MAP_H))

    # Parking row fills
    for row_y, row_h in [(ROW1_Y, SPOT_H), (ROW2_Y, SPOT_H)]:
        x1, y1 = w2s(START_X,                   row_y)
        x2, y2 = w2s(START_X + N_SPOTS * SPOT_W, row_y + row_h)
        if x2 > x1 and y2 > y1:
            pygame.draw.rect(surf, ASPHALT2, (x1, y1, x2 - x1, y2 - y1))

    # Parking lines
    for i in range(N_SPOTS + 1):
        wx = START_X + i * SPOT_W
        for row_y, row_h in [(ROW1_Y, SPOT_H), (ROW2_Y, SPOT_H)]:
            pygame.draw.line(surf, LINE_W,
                             w2s(wx, row_y), w2s(wx, row_y + row_h), 1)

    # Lane dashes
    for xi in range(START_X, START_X + N_SPOTS * SPOT_W - 1, 50):
        pygame.draw.line(surf, LINE_Y,
                         w2s(xi, LANE_Y), w2s(xi + 25, LANE_Y), 1)

    # World border
    _td_border(surf, w2s)

    # Parked cars (top row)
    for i in occ_top:
        if i < N_SPOTS:
            cx = START_X + i * SPOT_W + SPOT_W // 2
            _td_car(surf, w2s, cx, ROW1_Y + SPOT_H // 2,
                    SPOT_W - 10, SPOT_H - 14, 90, top_colors[i])

    # Parked cars (bottom row)
    for i in occ_bot:
        if i < N_SPOTS:
            cx = START_X + i * SPOT_W + SPOT_W // 2
            _td_car(surf, w2s, cx, ROW2_Y + SPOT_H // 2,
                    SPOT_W - 10, SPOT_H - 14, 270, bot_colors[i])

    # Camera FOV cone
    _td_fov_cone(surf, car, w2s)

    # Pedestrians
    for ped in peds:
        px, py = w2s(ped.x, ped.y)
        r  = max(3, int(ped.R * MAP_SCL))
        fc = RED_HI if ped.hit else ped.color
        pygame.draw.circle(surf, fc,    (px, py), r)
        pygame.draw.circle(surf, WHITE, (px, py), r, 1)

    # Player car
    cpts = [w2s(cx, cy) for cx, cy in car.corners()]
    pygame.draw.polygon(surf, RED_HI if car.collision else CAR_C, cpts)
    pygame.draw.polygon(surf, CAR_D, cpts, 2)

    # Direction arrow on car icon
    fx, fy = car.fwd
    cx0, cy0 = w2s(car.x, car.y)
    pygame.draw.line(surf, WHITE, (cx0, cy0),
                     (cx0 + int(fx * 18), cy0 + int(fy * 18)), 2)

    # Panel border + title bar
    pygame.draw.rect(surf, DGRAY, (MAP_X0, 0, MAP_W, MAP_H), 2)
    pygame.draw.rect(surf, BLACK, (MAP_X0, 0, MAP_W, 42))
    surf.blit(font_md.render("WIDOK Z GÓRY | Top View", True, WHITE),
              (MAP_X0 + 10, 11))

    # Controls legend at the bottom of the map panel
    _td_controls(surf)

    # Speed / distance info strip
    _td_info(surf, car)


def _td_border(surf, w2s):
    corners = [w2s(0, 0), w2s(WORLD_W, 0),
               w2s(WORLD_W, WORLD_H), w2s(0, WORLD_H)]
    pygame.draw.lines(surf, LGRAY, True, corners, 2)


def _td_car(surf, w2s, cx, cy, ww, wh, hdg_deg, col):
    a      = math.radians(hdg_deg)
    fx, fy = math.cos(a), math.sin(a)
    rx, ry = -fy, fx
    hw, hl = ww / 2, wh / 2
    pts = [
        w2s(cx + fx*hl + rx*hw, cy + fy*hl + ry*hw),
        w2s(cx + fx*hl - rx*hw, cy + fy*hl - ry*hw),
        w2s(cx - fx*hl - rx*hw, cy - fy*hl - ry*hw),
        w2s(cx - fx*hl + rx*hw, cy - fy*hl + ry*hw),
    ]
    pygame.draw.polygon(surf, col,   pts)
    pygame.draw.polygon(surf, DGRAY, pts, 1)


def _td_fov_cone(surf, car, w2s):
    """Draw the backup-camera FOV cone on the top-down map."""
    rx, ry = car.rear
    a      = math.radians(car.angle)
    dist   = 5 * METER    # cone reach (~5 m)

    world_pts = [(rx, ry)]
    for deg in range(-CAM_FOV // 2, CAM_FOV // 2 + 1, 5):
        ang = a + math.pi + math.radians(deg)
        world_pts.append((rx + math.cos(ang) * dist,
                          ry + math.sin(ang) * dist))
    world_pts.append((rx, ry))

    screen_pts = [w2s(wx, wy) for wx, wy in world_pts]

    alpha = pygame.Surface((MAP_W, MAP_H), pygame.SRCALPHA)
    local = [(sx - MAP_X0, sy) for sx, sy in screen_pts]
    if len(local) >= 3:
        pygame.draw.polygon(alpha, (*FOV_C, 32), local)
        pygame.draw.lines(alpha,  (*FOV_C, 90), False, local[1:-1], 1)
    surf.blit(alpha, (MAP_X0, 0))


def _td_controls(surf):
    y0 = MAP_H - 100
    pygame.draw.rect(surf, (10, 12, 22), (MAP_X0, y0, MAP_W, 100))
    for i, ln in enumerate([
        "STEROWANIE:",
        "W/↑ - do przodu    S/↓ - cofanie",
        "A/← - skręt lewo   D/→ - skręt prawo",
        "R - reset          ESC - wyjście",
    ]):
        col = WHITE if i == 0 else LGRAY
        surf.blit(font_sm.render(ln, True, col),
                  (MAP_X0 + 12, y0 + 8 + i * 21))


def _td_info(surf, car):
    """Small info strip at top-right of map panel."""
    info_y = 50
    kmh    = int(abs(car.speed) * 15)
    dist_m = car.odometer * (1.0 / METER)
    for i, ln in enumerate([
        f"Prędkość: {kmh} km/h",
        f"Dystans:  {dist_m:.0f} m",
    ]):
        surf.blit(font_sm.render(ln, True, LGRAY),
                  (MAP_X0 + 12, info_y + i * 20))


# ═══════════════════════════════════════════════════════════════════════════════
#  COLLISION DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
def check_collisions(car, peds):
    """OBB vs circle per-pedestrian collision."""
    fx, fy = car.fwd
    rx, ry = car.rgt

    for ped in peds:
        dx  = ped.x - car.x
        dy  = ped.y - car.y
        lon = dx * fx + dy * fy
        lat = dx * rx + dy * ry

        if (abs(lon) < car.L / 2 + ped.R and
                abs(lat) < car.W / 2 + ped.R):

            if not car.collision:
                car.speed *= -0.5     # bounce back
            car.collision = True
            car.col_timer  = 90      # ~1.5 s flash

            ped.hit       = True
            ped.hit_timer = 60

            # Push pedestrian out of the car
            d   = math.hypot(dx, dy) or 1
            ovr = (car.L / 2 + ped.R + 4) / d
            ped.x += dx * (ovr - 1) * 0.7
            ped.y += dy * (ovr - 1) * 0.7
            # Clamp pedestrian to valid area
            ped.x = max(START_X + 15, min(START_X + N_SPOTS*SPOT_W - 15, ped.x))
            ped.y = max(ROW1_Y + SPOT_H + 5, min(ROW2_Y - 5, ped.y))


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    car  = Car()

    # Spawn pedestrians, ensuring none start on top of the player car
    peds = []
    random.seed(123)
    for _ in range(14):
        for _attempt in range(60):
            p = Pedestrian()
            if math.hypot(p.x - car.x, p.y - car.y) > 180:
                peds.append(p)
                break

    cam_surf = pygame.Surface((CAM_W, CAM_H))

    running = True
    while running:
        clock.tick(FPS)

        # ── events ──────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    car.reset()

        # ── update ──────────────────────────────────────────────
        keys = pygame.key.get_pressed()
        car.update(keys)
        for p in peds:
            p.update()
        check_collisions(car, peds)

        # ── render ──────────────────────────────────────────────
        draw_camera_view(cam_surf, car, peds)
        screen.blit(cam_surf, (0, 0))

        draw_topdown(screen, car, peds)

        # Divider between panels
        pygame.draw.line(screen, LGRAY, (CAM_W, 0), (CAM_W, SH), 2)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

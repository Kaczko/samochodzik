#!/usr/bin/env python3
"""
Symulacja Kamery Cofania w Samochodzie - Parking  v2
Backup Camera Simulation - Parking Lot  (improved graphics)

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

CAM_W, CAM_H = 900, 750
MAP_W, MAP_H = 500, 750
SW = CAM_W + MAP_W
SH = max(CAM_H, MAP_H)

screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Symulacja Kamery Cofania | Backup Camera Simulation")
clock = pygame.time.Clock()
FPS   = 60

font_sm = pygame.font.SysFont("segoeui", 15)
font_md = pygame.font.SysFont("segoeui", 20, bold=True)
font_lg = pygame.font.SysFont("segoeui", 30, bold=True)
font_xl = pygame.font.SysFont("segoeui", 44, bold=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  COLOR PALETTE  (vibrant, daytime)
# ═══════════════════════════════════════════════════════════════════════════════
# Sky – rich blue gradient
SKY_TOP   = ( 25,  80, 185)
SKY_MID   = ( 65, 145, 230)
SKY_BOT   = (145, 205, 255)

# Ground / asphalt
GND_FAR   = ( 55,  58,  74)
GND_NEAR  = ( 78,  82, 100)
ASPHALT   = ( 44,  46,  60)
ASPHALT2  = ( 56,  59,  75)
ASPHALT3  = ( 68,  72,  90)   # lane area (slightly lighter)

# Parking lines
LINE_WHITE  = (225, 228, 245)
LINE_YELLOW = (255, 215,  20)
LINE_BLUE   = ( 55, 130, 240)   # handicapped

# General
WHITE  = (255, 255, 255)
BLACK  = (  0,   0,   0)
RED    = (220,  55,  55)
RED_HI = (255, 110, 110)
GREEN  = ( 55, 210,  85)
YELLOW = (255, 220,   0)
ORANGE = (255, 155,  30)
GRAY   = (105, 108, 125)
DGRAY  = ( 38,  40,  54)
LGRAY  = (165, 168, 185)
CYAN   = ( 50, 210, 230)

# Player car
CAR_C  = (210,  60,  60)
CAR_D  = (145,  30,  30)
CAR_W  = (155, 205, 245)   # windows

# FOV cone
FOV_C  = ( 20, 165, 255)

# Vegetation
TREE_DARK  = ( 25, 115,  45)
TREE_MID   = ( 45, 165,  65)
TREE_HI    = ( 90, 210,  90)

# Lamp post
LAMP_POST  = (145, 148, 165)
LAMP_GLOW  = (255, 240, 165)

# Parked car body colours
PARKED_CAR_COLS = [
    ( 85,  95, 170),  # blue
    (165,  70,  60),  # red
    ( 60, 130, 100),  # green
    (145, 110,  50),  # yellow/brown
    ( 80,  90, 125),  # steel blue
    (160,  60, 125),  # pink/magenta
    (100, 165,  80),  # lime green
    ( 50, 115, 165),  # sky blue
    (175,  80,  50),  # orange-red
    (110,  55, 155),  # purple
    ( 55, 140, 155),  # teal
    (170, 130,  40),  # golden
]

# ═══════════════════════════════════════════════════════════════════════════════
#  WORLD / PARKING LOT
# ═══════════════════════════════════════════════════════════════════════════════
WORLD_W  = 1600
WORLD_H  = 1000
METER    = 30.0      # world units ≈ 1 real metre

SPOT_W   = 60
SPOT_H   = 100
N_SPOTS  = 20
ROW1_Y   = 100                       # top parking row start
ROW2_Y   = WORLD_H - 100 - SPOT_H   # bottom row start (= 800)
START_X  = 100
LANE_Y   = WORLD_H // 2             # main lane centre (= 500)

top_spots = [pygame.Rect(START_X + i*SPOT_W, ROW1_Y, SPOT_W, SPOT_H) for i in range(N_SPOTS)]
bot_spots = [pygame.Rect(START_X + i*SPOT_W, ROW2_Y, SPOT_W, SPOT_H) for i in range(N_SPOTS)]

_rng = random.Random(42)
occ_top = set(_rng.sample(range(N_SPOTS), 13))
occ_bot = set(_rng.sample(range(N_SPOTS), 12))

# Assign car colours deterministically
_crng = random.Random(99)
top_colors = [_crng.choice(PARKED_CAR_COLS) for _ in range(N_SPOTS)]
bot_colors = [_crng.choice(PARKED_CAR_COLS) for _ in range(N_SPOTS)]

# Handicapped spots (blue tint on minimap)
HANDICAP_TOP = {4}
HANDICAP_BOT = {15}

# ── Trees ──────────────────────────────────────────────────────────────────────
_trng = random.Random(555)
TREES = []
# Strip above top row
for _ in range(14):
    TREES.append((_trng.uniform(60, WORLD_W-60),
                  _trng.uniform(15, ROW1_Y - 15),
                  _trng.randint(14, 24)))
# Strip below bottom row
for _ in range(14):
    TREES.append((_trng.uniform(60, WORLD_W-60),
                  _trng.uniform(ROW2_Y + SPOT_H + 15, WORLD_H - 15),
                  _trng.randint(14, 24)))
# Left margin
for _ in range(7):
    TREES.append((_trng.uniform(20, START_X - 20),
                  _trng.uniform(ROW1_Y, ROW2_Y + SPOT_H),
                  _trng.randint(12, 20)))
# Right margin
for _ in range(7):
    TREES.append((_trng.uniform(START_X + N_SPOTS*SPOT_W + 20, WORLD_W - 20),
                  _trng.uniform(ROW1_Y, ROW2_Y + SPOT_H),
                  _trng.randint(12, 20)))

# ── Lamp posts ─────────────────────────────────────────────────────────────────
LAMPS = []
n_lamps = 6
for i in range(1, n_lamps + 1):
    lx = START_X + (i * N_SPOTS * SPOT_W) // (n_lamps + 1)
    LAMPS.append((lx, (ROW1_Y + SPOT_H + LANE_Y) // 2))   # between top row and lane
    LAMPS.append((lx, (LANE_Y + ROW2_Y) // 2))             # between lane and bottom row

# ═══════════════════════════════════════════════════════════════════════════════
#  CAMERA PROJECTION CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
CAM_FOV   = 160
FOCAL     = 420
HORIZON_Y = int(CAM_H * 0.40)   # = 300
GROUND_K  = FOCAL * 22           # ≈ 9240

# ── Pre-render sky with clouds ─────────────────────────────────────────────────
_sky_surf = pygame.Surface((CAM_W, HORIZON_Y))
for _y in range(HORIZON_Y):
    _t = _y / max(1, HORIZON_Y - 1)
    # Three-stop gradient: TOP→MID→BOT
    if _t < 0.5:
        _tt = _t * 2
        _c = tuple(int(SKY_TOP[i] + (SKY_MID[i] - SKY_TOP[i]) * _tt) for i in range(3))
    else:
        _tt = (_t - 0.5) * 2
        _c = tuple(int(SKY_MID[i] + (SKY_BOT[i] - SKY_MID[i]) * _tt) for i in range(3))
    pygame.draw.line(_sky_surf, _c, (0, _y), (CAM_W, _y))

# Sun
pygame.draw.circle(_sky_surf, (255, 248, 200), (int(CAM_W * 0.72), 22), 22)
pygame.draw.circle(_sky_surf, (255, 255, 230), (int(CAM_W * 0.72), 22), 15)
pygame.draw.circle(_sky_surf, (255, 255, 255), (int(CAM_W * 0.72), 22),  8)

# Clouds
_clrng = random.Random(77)
for _ in range(6):
    _cx = _clrng.randint(60, CAM_W - 60)
    _cy = _clrng.randint(15, HORIZON_Y - 35)
    for _ in range(5):
        _ex = _cx + _clrng.randint(-40, 40)
        _ey = _cy + _clrng.randint(-12, 12)
        _er = _clrng.randint(18, 48)
        pygame.draw.ellipse(_sky_surf, (225, 235, 252),
                            (_ex - _er, _ey - 14, _er * 2, 28))

# ── Pre-render ground gradient ─────────────────────────────────────────────────
_gnd_h    = CAM_H - HORIZON_Y
_gnd_surf = pygame.Surface((CAM_W, _gnd_h))
for _y in range(_gnd_h):
    _t = _y / max(1, _gnd_h - 1)
    pygame.draw.line(_gnd_surf, (
        int(GND_FAR[0] + (GND_NEAR[0] - GND_FAR[0]) * _t),
        int(GND_FAR[1] + (GND_NEAR[1] - GND_FAR[1]) * _t),
        int(GND_FAR[2] + (GND_NEAR[2] - GND_FAR[2]) * _t),
    ), (0, _y), (CAM_W, _y))


# ═══════════════════════════════════════════════════════════════════════════════
#  CAR (player)
# ═══════════════════════════════════════════════════════════════════════════════
class Car:
    W = 38
    L = 76

    def __init__(self):
        self.reset()

    def reset(self):
        self.x        = WORLD_W * 0.45
        self.y        = float(LANE_Y)
        self.angle    = 0.0
        self.speed    = 0.0
        self.collision = False
        self.col_timer = 0
        self.odometer  = 0.0

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
            (self.x + fx*hl + rx*hw, self.y + fy*hl + ry*hw),
            (self.x + fx*hl - rx*hw, self.y + fy*hl - ry*hw),
            (self.x - fx*hl - rx*hw, self.y - fy*hl - ry*hw),
            (self.x - fx*hl + rx*hw, self.y - fy*hl + ry*hw),
        ]

    def update(self, keys):
        MAX_FWD, MAX_REV = 5.0, 3.2
        ACC, FRIC, STEER = 0.14, 0.90, 2.6

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
#  PEDESTRIAN  (rich appearance)
# ═══════════════════════════════════════════════════════════════════════════════
class Pedestrian:
    R = 12

    _SKINS  = [(255,220,185),(240,200,160),(210,165,125),(175,125,85),(120,80,50)]
    _SHIRTS = [
        (220, 60, 60),(60,120,220),(50,185,80),(220,165,40),(160,60,225),
        (40,185,185),(225,100,165),(80,80,80),(255,140,30),(120,220,80),
        (255,80,140),(80,200,230),(240,200,50),(100,80,220),(60,180,130),
    ]
    _PANTS  = [(35,45,80),(55,42,28),(75,78,78),(28,65,48),(85,58,38),
               (40,40,40),(65,55,35),(30,35,70)]
    _HAIRS  = [(22,15,8),(65,42,12),(195,152,65),(205,55,50),(90,88,180),
               (195,195,195),(30,30,30),(180,120,50)]

    def __init__(self):
        self.x     = random.uniform(START_X + 20, START_X + N_SPOTS*SPOT_W - 20)
        self.y     = random.uniform(ROW1_Y + SPOT_H + 10, ROW2_Y - 10)
        self.skin  = random.choice(self._SKINS)
        self.shirt = random.choice(self._SHIRTS)
        self.pants = random.choice(self._PANTS)
        self.hair  = random.choice(self._HAIRS)
        self.color = self.shirt   # minimap colour
        self.dir   = random.uniform(0, 360)
        self.spd   = random.uniform(0.3, 0.9)
        self.timer = random.randint(60, 240)
        self.hit       = False
        self.hit_timer = 0
        # walking phase for leg animation
        self.walk_phase = random.uniform(0, math.pi * 2)

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.dir   = random.uniform(0, 360)
            self.spd   = random.uniform(0.3, 0.9)
            self.timer = random.randint(60, 240)

        self.walk_phase += self.spd * 0.18

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
#  PARKED CAR  (physical obstacle with OBB collision)
# ═══════════════════════════════════════════════════════════════════════════════
class ParkedCar:
    def __init__(self, cx, cy, w, h, angle_deg, color):
        self.x     = cx
        self.y     = cy
        self.w     = w          # width  (across)
        self.h     = h          # height (along heading)
        self.angle = angle_deg
        self.color = color
        self.collision = False
        self.col_timer = 0

    @property
    def fwd(self):
        a = math.radians(self.angle)
        return math.cos(a), math.sin(a)

    @property
    def rgt(self):
        fx, fy = self.fwd
        return -fy, fx

    def corners(self):
        fx, fy = self.fwd
        rx, ry = self.rgt
        hw, hl = self.w / 2, self.h / 2
        return [
            (self.x + fx*hl + rx*hw, self.y + fy*hl + ry*hw),
            (self.x + fx*hl - rx*hw, self.y + fy*hl - ry*hw),
            (self.x - fx*hl - rx*hw, self.y - fy*hl - ry*hw),
            (self.x - fx*hl + rx*hw, self.y - fy*hl + ry*hw),
        ]

    def update(self):
        if self.col_timer > 0:
            self.col_timer -= 1
            if self.col_timer == 0:
                self.collision = False


def build_parked_cars():
    """Build the list of physical parked car objects from occupied spots."""
    cars = []
    for i in occ_top:
        if i < N_SPOTS:
            cx = START_X + i * SPOT_W + SPOT_W // 2
            cy = ROW1_Y + SPOT_H // 2
            cars.append(ParkedCar(cx, cy, SPOT_W - 10, SPOT_H - 14, 90, top_colors[i]))
    for i in occ_bot:
        if i < N_SPOTS:
            cx = START_X + i * SPOT_W + SPOT_W // 2
            cy = ROW2_Y + SPOT_H // 2
            cars.append(ParkedCar(cx, cy, SPOT_W - 10, SPOT_H - 14, 270, bot_colors[i]))
    return cars


# ═══════════════════════════════════════════════════════════════════════════════
#  PROJECTION UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def world_to_cam(wx, wy, car):
    rx, ry = car.rear
    dx, dy = wx - rx, wy - ry
    a = math.radians(car.angle)
    cfx, cfy =  -math.cos(a), -math.sin(a)
    crx, cry =   math.sin(a), -math.cos(a)
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
    r = world_to_cam(wx, wy, car)
    if r is None:
        return None
    sx, _, depth = r
    sy = HORIZON_Y + int(GROUND_K / depth)
    return sx, sy


# ═══════════════════════════════════════════════════════════════════════════════
#  COLLISION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def sat_collide(corners_a, corners_b):
    """
    Separating Axis Theorem for two convex polygons.
    Returns (overlapping, penetration_depth, push_ax, push_ay).
    push axis is oriented to push A away from B.
    """
    min_pen = float('inf')
    best_ax = (1.0, 0.0)

    def project(corners, ax, ay):
        dots = [c[0] * ax + c[1] * ay for c in corners]
        return min(dots), max(dots)

    for corners in (corners_a, corners_b):
        n = len(corners)
        for i in range(n):
            ex = corners[(i + 1) % n][0] - corners[i][0]
            ey = corners[(i + 1) % n][1] - corners[i][1]
            length = math.hypot(ex, ey)
            if length < 1e-9:
                continue
            ax, ay = -ey / length, ex / length          # unit normal

            a_lo, a_hi = project(corners_a, ax, ay)
            b_lo, b_hi = project(corners_b, ax, ay)

            pen = min(a_hi, b_hi) - max(a_lo, b_lo)
            if pen <= 0:
                return False, 0.0, 0.0, 0.0
            if pen < min_pen:
                min_pen = pen
                best_ax = (ax, ay)

    # Ensure push axis points from B toward A
    cax = sum(c[0] for c in corners_a) / len(corners_a)
    cay = sum(c[1] for c in corners_a) / len(corners_a)
    cbx = sum(c[0] for c in corners_b) / len(corners_b)
    cby = sum(c[1] for c in corners_b) / len(corners_b)
    if (cax - cbx) * best_ax[0] + (cay - cby) * best_ax[1] < 0:
        best_ax = (-best_ax[0], -best_ax[1])

    return True, min_pen, best_ax[0], best_ax[1]


def check_car_collisions(car, parked_cars):
    """OBB-OBB collision between player car and each parked car."""
    for pc in parked_cars:
        pc.update()
        hit, pen, ax, ay = sat_collide(car.corners(), pc.corners())
        if hit and pen > 0.5:
            # Push player car out of the parked car
            car.x += ax * (pen + 1.0)
            car.y += ay * (pen + 1.0)
            if not car.collision:
                car.speed *= -0.35          # bounce
            car.collision = True
            car.col_timer = 60
            pc.collision  = True
            pc.col_timer  = 50


def nearest_rear_distance(car, peds, parked_cars):
    """
    Return world-unit distance (≥ 0) to the nearest obstacle visible in the
    rear camera arc, or None if nothing is in view.
    """
    min_d = None

    # Pedestrians
    for ped in peds:
        r = world_to_cam(ped.x, ped.y, car)
        if r:
            d = max(0.0, r[2] - ped.R)
            if min_d is None or d < min_d:
                min_d = d

    # Parked cars — check all 4 corners and the centre
    for pc in parked_cars:
        for wx, wy in pc.corners() + [(pc.x, pc.y)]:
            r = world_to_cam(wx, wy, car)
            if r:
                d = r[2]
                if min_d is None or d < min_d:
                    min_d = d

    return min_d   # world units; divide by METER to get metres


# ═══════════════════════════════════════════════════════════════════════════════
#  CAMERA VIEW  (left panel)
# ═══════════════════════════════════════════════════════════════════════════════
def draw_camera_view(surf, car, peds, parked_cars):
    surf.blit(_sky_surf, (0, 0))
    surf.blit(_gnd_surf, (0, HORIZON_Y))

    _cam_parking_lines(surf, car)
    _cam_parked_cars(surf, car, parked_cars)

    # Pedestrians: far → near (painter's algorithm)
    visible = []
    for ped in peds:
        r = world_to_cam(ped.x, ped.y, car)
        if r:
            visible.append((r[2], ped, r[0]))
    visible.sort(reverse=True)
    for depth, ped, sx in visible:
        _cam_pedestrian(surf, sx, depth, ped)

    nearest_d = nearest_rear_distance(car, peds, parked_cars)
    _cam_guidelines(surf, car)
    _cam_hud(surf, car, nearest_d)


# ── camera helpers ─────────────────────────────────────────────────────────────
def _cam_parking_lines(surf, car):
    dim   = (88, 91, 112)
    dim_y = (100, 90, 25)

    for row_y, row_h in [(ROW1_Y, SPOT_H), (ROW2_Y, SPOT_H)]:
        for edge_y in (row_y, row_y + row_h):
            pts = []
            for i in range(N_SPOTS + 1):
                p = cam_ground(START_X + i * SPOT_W, edge_y, car)
                if p:
                    pts.append(p)
            if len(pts) >= 2:
                pygame.draw.lines(surf, dim, False, pts, 1)
        for i in range(N_SPOTS + 1):
            wx = START_X + i * SPOT_W
            p1 = cam_ground(wx, row_y,         car)
            p2 = cam_ground(wx, row_y + row_h, car)
            if p1 and p2:
                pygame.draw.line(surf, dim, p1, p2, 1)

    # Handicapped spots (blue tint on ground)
    for i in HANDICAP_TOP:
        cx = START_X + i * SPOT_W + SPOT_W // 2
        for dy_off in range(0, SPOT_H, 15):
            p = cam_ground(cx, ROW1_Y + dy_off, car)
            if p:
                pygame.draw.circle(surf, (50, 100, 220), p, 2)

    # Lane dashes
    for xi in range(START_X, START_X + N_SPOTS * SPOT_W - 1, 50):
        p1 = cam_ground(xi,       LANE_Y, car)
        p2 = cam_ground(xi + 25,  LANE_Y, car)
        if p1 and p2:
            pygame.draw.line(surf, dim_y, p1, p2, 2)


def _cam_parked_cars(surf, car, parked_cars):
    for pc in parked_cars:
        col = RED_HI if pc.collision else pc.color
        _cam_box(surf, car, pc.x, pc.y, pc.w, pc.h, pc.angle, col)


def _cam_box(surf, car, wx, wy, ww, wh, hdg_deg, body_col):
    """3-D box (parked car) in camera view, with coloured body, glass strip and roof."""
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

    pts_bot, pts_top, pts_win_top, pts_win_bot, depths = [], [], [], [], []
    for bx, by in base_world:
        r = world_to_cam(bx, by, car)
        if r:
            sx_b, _, dep = r
            sy_b   = HORIZON_Y + int(GROUND_K / dep)
            px_h   = max(5, int(FOCAL * 1.55 * METER / dep))
            win_h  = int(px_h * 0.42)   # glass starts 10% from top, 42% tall
            pts_bot.append((sx_b, sy_b))
            pts_top.append((sx_b, sy_b - px_h))
            pts_win_top.append((sx_b, sy_b - px_h + int(px_h * 0.10)))
            pts_win_bot.append((sx_b, sy_b - px_h + int(px_h * 0.52)))
            depths.append(dep)

    n = min(len(pts_bot), len(pts_top))
    if n < 3:
        return

    try:
        shade  = tuple(max(0, c - 55) for c in body_col)
        roof_c = tuple(min(255, c + 20) for c in body_col)
        glass  = (120, 175, 220)
        glass2 = (100, 155, 200)

        # Side body
        sides = pts_bot[:n] + list(reversed(pts_top[:n]))
        pygame.draw.polygon(surf, shade, sides)

        # Window glass strip
        win_sides = pts_win_bot[:n] + list(reversed(pts_win_top[:n]))
        pygame.draw.polygon(surf, glass, win_sides)
        # Glass glare (lighter diagonal strip on first face)
        if n >= 2:
            glare_pts = [
                pts_win_top[0],
                (pts_win_top[0][0] + 4, pts_win_top[0][1]),
                (pts_win_bot[0][0] + 4, pts_win_bot[0][1]),
                pts_win_bot[0],
            ]
            pygame.draw.polygon(surf, (175, 220, 255), glare_pts)

        # Roof
        pygame.draw.polygon(surf, roof_c, pts_top[:n])

        # Outlines
        pygame.draw.polygon(surf, (20, 22, 32), sides,       1)
        pygame.draw.polygon(surf, (20, 22, 32), pts_top[:n], 1)
        pygame.draw.polygon(surf, (60, 70, 85), win_sides,   1)
    except Exception:
        pass


def _cam_pedestrian(surf, sx, depth, ped):
    """Detailed multi-part pedestrian: head/hair/eyes/neck/arms/torso/legs/shoes."""
    sy_gnd  = HORIZON_Y + int(GROUND_K / depth)
    scale   = max(0.18, min(4.5, 26.0 / depth))

    head_r  = max(2, int(10 * scale))
    torso_w = max(4, int(15 * scale))
    torso_h = max(3, int(20 * scale))
    hip_w   = max(3, int(11 * scale))
    leg_h   = max(3, int(24 * scale))
    arm_len = max(2, int(13 * scale))
    arm_w   = max(1, int(3  * scale))
    neck_h  = max(1, int(5  * scale))

    # Leg walk offset for animation
    loff = int(math.sin(ped.walk_phase) * max(1, int(3 * scale)))

    # Y positions bottom → top
    y_feet  = sy_gnd
    y_hip   = y_feet  - leg_h
    y_shldr = y_hip   - torso_h
    y_hcen  = y_shldr - neck_h - head_r

    if y_hcen - head_r > CAM_H + 20 or y_feet < HORIZON_Y - 20:
        return
    if sx < -80 or sx > CAM_W + 80:
        return

    c_skin  = ped.skin  if not ped.hit else RED_HI
    c_shirt = ped.shirt if not ped.hit else RED_HI
    c_pants = ped.pants if not ped.hit else (170, 25, 25)
    c_hair  = ped.hair

    # Shadow
    sw = max(5, int(20 * scale))
    pygame.draw.ellipse(surf, (15, 16, 28), (sx - sw, y_feet - 5, sw * 2, 8))

    # Legs (animated walk)
    lw = max(2, int(5 * scale))
    pygame.draw.rect(surf, c_pants,
                     (sx - hip_w//2, y_hip + loff, lw, leg_h - loff))
    pygame.draw.rect(surf, c_pants,
                     (sx + hip_w//2 - lw, y_hip - loff, lw, leg_h + loff))

    # Shoes
    shoe = max(3, int(7 * scale))
    shoe_col = (35, 25, 15)
    pygame.draw.ellipse(surf, shoe_col,
                        (sx - hip_w//2 - 2, y_feet + loff - shoe//3, shoe, shoe//3 + 3))
    pygame.draw.ellipse(surf, shoe_col,
                        (sx + hip_w//2 - shoe + 2, y_feet - loff - shoe//3, shoe, shoe//3 + 3))

    # Torso (trapezoid — wider at shoulders)
    if scale >= 0.35:
        t_pts = [
            (sx - torso_w//2 - 2, y_shldr),
            (sx + torso_w//2 + 2, y_shldr),
            (sx + hip_w//2,       y_hip),
            (sx - hip_w//2,       y_hip),
        ]
        pygame.draw.polygon(surf, c_shirt, t_pts)
        # Belt line
        if scale >= 0.6:
            pygame.draw.line(surf, tuple(max(0, c-40) for c in c_pants),
                             (sx - hip_w//2, y_hip),
                             (sx + hip_w//2, y_hip),
                             max(1, int(2 * scale)))
    else:
        pygame.draw.rect(surf, c_shirt, (sx - torso_w//2, y_shldr, torso_w, torso_h))

    # Arms
    if scale >= 0.42:
        arm_swing = int(math.sin(ped.walk_phase + math.pi) * arm_len * 0.35)
        pygame.draw.line(surf, c_skin,
                         (sx - torso_w//2 - 1, y_shldr + int(4 * scale)),
                         (sx - torso_w//2 - arm_len, y_shldr + torso_h//2 + arm_swing),
                         arm_w)
        pygame.draw.line(surf, c_skin,
                         (sx + torso_w//2 + 1, y_shldr + int(4 * scale)),
                         (sx + torso_w//2 + arm_len, y_shldr + torso_h//2 - arm_swing),
                         arm_w)

    # Neck
    if scale >= 0.45:
        nw = max(2, int(4 * scale))
        pygame.draw.rect(surf, c_skin,
                         (sx - nw//2, y_hcen + head_r, nw, neck_h + 1))

    # Head
    pygame.draw.circle(surf, c_skin, (sx, y_hcen), head_r)

    # Hair arc
    if head_r >= 4:
        try:
            pygame.draw.arc(surf, c_hair,
                            (sx - head_r, y_hcen - head_r, head_r * 2, head_r * 2),
                            math.radians(15), math.radians(165),
                            max(2, head_r // 2 + 1))
        except Exception:
            pass

    # Eyes (at large enough sizes)
    if head_r >= 5:
        er = max(1, head_r // 4)
        ex_off = head_r // 3
        # Whites
        if head_r >= 8:
            pygame.draw.circle(surf, (245, 245, 245),
                               (sx - ex_off, y_hcen - er), max(1, er))
            pygame.draw.circle(surf, (245, 245, 245),
                               (sx + ex_off, y_hcen - er), max(1, er))
        # Pupils
        pygame.draw.circle(surf, (25, 15, 10),
                           (sx - ex_off, y_hcen - er), max(1, er // 2 + 1))
        pygame.draw.circle(surf, (25, 15, 10),
                           (sx + ex_off, y_hcen - er), max(1, er // 2 + 1))

    # Mouth (smile) at large scale
    if head_r >= 10:
        try:
            pygame.draw.arc(surf, (160, 80, 60),
                            (sx - head_r//2, y_hcen, head_r, head_r // 2),
                            math.pi * 1.1, math.pi * 1.9, max(1, head_r // 5))
        except Exception:
            pass


def _cam_guidelines(surf, car):
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

    crx, cry = car.rgt
    fx, fy   = car.fwd
    hw       = car.W / 2
    for side in (-1, 1):
        near_x = rx + crx * hw * side - fx * 4
        near_y = ry + cry * hw * side - fy * 4
        far_x  = rx + crx * hw * side - fx * 4 * METER
        far_y  = ry + cry * hw * side - fy * 4 * METER
        p1 = cam_ground(near_x, near_y, car)
        p2 = cam_ground(far_x,  far_y,  car)
        if p1 and p2:
            pygame.draw.line(surf, YELLOW, p1, p2, 2)


def _cam_hud(surf, car, nearest_d=None):
    if car.collision:
        pygame.draw.rect(surf, RED,  (0, 0, CAM_W, CAM_H), 7)
    else:
        pygame.draw.rect(surf, DGRAY, (0, 0, CAM_W, CAM_H), 2)

    # Top bar
    pygame.draw.rect(surf, (5, 6, 16), (0, 0, CAM_W, 50))
    pygame.draw.rect(surf, CYAN, (0, 0, CAM_W, 3))
    surf.blit(font_lg.render("KAMERA COFANIA", True, WHITE), (18, 10))
    surf.blit(font_sm.render("● REC", True, RED_HI), (CAM_W - 65, 18))

    # Distance arc legend (bottom-right)
    for label, col, dy in [("4m", GREEN, 110), ("2m", ORANGE, 90), ("1m", RED, 70)]:
        pygame.draw.rect(surf, col, (CAM_W - 68, CAM_H - dy, 22, 8))
        surf.blit(font_sm.render(label, True, LGRAY),
                  (CAM_W - 42, CAM_H - dy - 2))

    # ── Nearest obstacle distance readout (bottom centre) ─────────────────────
    if nearest_d is not None:
        dm = nearest_d / METER   # convert to real metres
        if dm <= 0.5:
            d_col  = RED_HI
            d_text = "■  STOP!"
        elif dm < 1.0:
            d_col  = RED
            d_text = f"⬌  {dm:.1f} m"
        elif dm < 2.0:
            d_col  = ORANGE
            d_text = f"⬌  {dm:.1f} m"
        elif dm < 4.0:
            d_col  = YELLOW
            d_text = f"⬌  {dm:.1f} m"
        else:
            d_col  = GREEN
            d_text = f"⬌  {dm:.1f} m"

        d_surf = font_lg.render(d_text, True, d_col)
        dw     = d_surf.get_width()
        dx     = CAM_W // 2 - dw // 2
        dy_pos = CAM_H - 55
        # background pill
        pygame.draw.rect(surf, (8, 10, 20),
                         (dx - 14, dy_pos - 6, dw + 28, 42), border_radius=8)
        pygame.draw.rect(surf, d_col,
                         (dx - 14, dy_pos - 6, dw + 28, 42), 2, border_radius=8)
        surf.blit(d_surf, (dx, dy_pos))

    # Speed (bottom-left)
    kmh = int(abs(car.speed) * 15)
    surf.blit(font_md.render(f"{kmh} km/h", True, WHITE), (18, CAM_H - 36))

    # Gear indicator (bottom-right)
    if   car.speed < -0.08: gear, gc = "R", RED_HI
    elif car.speed >  0.08: gear, gc = "D", GREEN
    else:                   gear, gc = "P", YELLOW
    surf.blit(font_xl.render(gear, True, gc), (CAM_W - 65, CAM_H - 65))

    # Collision warning flash
    if car.collision and (pygame.time.get_ticks() // 280) % 2 == 0:
        warn = font_xl.render("⚠  UWAGA!  KOLIZJA!", True, RED_HI)
        wx   = CAM_W // 2 - warn.get_width() // 2
        pygame.draw.rect(surf, (50, 0, 0),
                         (wx - 14, CAM_H // 2 - 32, warn.get_width() + 28, 62))
        surf.blit(warn, (wx, CAM_H // 2 - 26))

    _draw_vignette(surf)


def _draw_vignette(surf):
    v = pygame.Surface((CAM_W, CAM_H), pygame.SRCALPHA)
    for i in range(14):
        alpha = 8 + i * 4
        pygame.draw.rect(v, (0, 0, 0, alpha),
                         (i, i, CAM_W - i*2, CAM_H - i*2), 1)
    surf.blit(v, (0, 0))


# ═══════════════════════════════════════════════════════════════════════════════
#  TOP-DOWN MAP  (right panel)
# ═══════════════════════════════════════════════════════════════════════════════
MAP_SCL = 0.40
MAP_X0  = CAM_W

def draw_topdown(surf, car, peds, parked_cars):
    cam_wx, cam_wy = car.x, car.y

    def w2s(wx, wy):
        sx = MAP_X0 + MAP_W // 2 + int((wx - cam_wx) * MAP_SCL)
        sy =          MAP_H // 2 + int((wy - cam_wy) * MAP_SCL)
        return sx, sy

    # Asphalt background
    pygame.draw.rect(surf, ASPHALT, (MAP_X0, 0, MAP_W, MAP_H))

    # Grass/green strips (above/below parking rows)
    for gy, gh in [(0, int(ROW1_Y * MAP_SCL)),
                   (int((ROW2_Y + SPOT_H) * MAP_SCL), MAP_H)]:
        pass   # will draw as world-space green strips below

    # World border region: draw green border strips
    _td_green_strip(surf, w2s)

    # Parking row backgrounds (slightly different tone)
    for row_y, row_h in [(ROW1_Y, SPOT_H), (ROW2_Y, SPOT_H)]:
        x1, y1 = w2s(START_X, row_y)
        x2, y2 = w2s(START_X + N_SPOTS * SPOT_W, row_y + row_h)
        if x2 > x1 and y2 > y1:
            pygame.draw.rect(surf, ASPHALT2, (x1, y1, x2 - x1, y2 - y1))

    # Lane area (slightly warmer shade)
    x1, y1 = w2s(START_X, ROW1_Y + SPOT_H)
    x2, y2 = w2s(START_X + N_SPOTS * SPOT_W, ROW2_Y)
    if x2 > x1 and y2 > y1:
        pygame.draw.rect(surf, ASPHALT3, (x1, y1, x2 - x1, y2 - y1))

    # Parking lines
    for i in range(N_SPOTS + 1):
        wx = START_X + i * SPOT_W
        for row_y, row_h in [(ROW1_Y, SPOT_H), (ROW2_Y, SPOT_H)]:
            pygame.draw.line(surf, LINE_WHITE,
                             w2s(wx, row_y), w2s(wx, row_y + row_h), 1)

    # Handicapped spots
    for i in HANDICAP_TOP:
        x1, y1 = w2s(START_X + i*SPOT_W + 2, ROW1_Y + 2)
        x2, y2 = w2s(START_X + i*SPOT_W + SPOT_W - 2, ROW1_Y + SPOT_H - 2)
        if x2 > x1 and y2 > y1:
            pygame.draw.rect(surf, (30, 60, 160), (x1, y1, x2-x1, y2-y1))
            pygame.draw.rect(surf, LINE_BLUE, (x1, y1, x2-x1, y2-y1), 1)
    for i in HANDICAP_BOT:
        x1, y1 = w2s(START_X + i*SPOT_W + 2, ROW2_Y + 2)
        x2, y2 = w2s(START_X + i*SPOT_W + SPOT_W - 2, ROW2_Y + SPOT_H - 2)
        if x2 > x1 and y2 > y1:
            pygame.draw.rect(surf, (30, 60, 160), (x1, y1, x2-x1, y2-y1))
            pygame.draw.rect(surf, LINE_BLUE, (x1, y1, x2-x1, y2-y1), 1)

    # Lane dashes
    for xi in range(START_X, START_X + N_SPOTS * SPOT_W - 1, 50):
        pygame.draw.line(surf, LINE_YELLOW,
                         w2s(xi, LANE_Y), w2s(xi + 25, LANE_Y), 1)

    # Direction arrows on lane
    _td_arrows(surf, w2s)

    # World border
    _td_border(surf, w2s)

    # Trees
    for tx, ty, tr in TREES:
        _td_tree(surf, w2s, tx, ty, tr)

    # Lamp posts
    for lx, ly in LAMPS:
        _td_lamp(surf, w2s, lx, ly)

    # Parked cars (from physical objects — flash red on collision)
    for pc in parked_cars:
        col = RED_HI if pc.collision else pc.color
        _td_car(surf, w2s, pc.x, pc.y, pc.w, pc.h, pc.angle, col)
        if pc.collision:
            # Extra highlight ring
            px, py = w2s(pc.x, pc.y)
            hw_s = max(5, int(pc.w / 2 * MAP_SCL))
            hl_s = max(5, int(pc.h / 2 * MAP_SCL))
            pygame.draw.ellipse(surf, RED_HI,
                                (px - hw_s - 3, py - hl_s - 3,
                                 (hw_s + 3)*2, (hl_s + 3)*2), 2)

    # FOV cone
    _td_fov_cone(surf, car, w2s)

    # Pedestrians
    for ped in peds:
        px, py = w2s(ped.x, ped.y)
        r  = max(3, int(ped.R * MAP_SCL))
        fc = RED_HI if ped.hit else ped.color
        # Shadow
        pygame.draw.ellipse(surf, (22, 24, 34),
                            (px - r, py - r//2, r*2, int(r*1.3)))
        pygame.draw.circle(surf, fc,    (px, py), r)
        pygame.draw.circle(surf, WHITE, (px, py), r, 1)
        # Shirt vs hair: tiny two-tone circle
        if r >= 5:
            pygame.draw.circle(surf, ped.shirt, (px, py), r // 2)

    # Player car
    cpts = [w2s(cx, cy) for cx, cy in car.corners()]
    pygame.draw.polygon(surf, RED_HI if car.collision else CAR_C,  cpts)
    pygame.draw.polygon(surf, CAR_D, cpts, 2)
    # Window on player car (top-down)
    fx, fy = car.fwd
    rx_v, ry_v = car.rgt
    hw_c, hl_c = car.W * 0.35, car.L * 0.25
    win_pts = [
        w2s(car.x + fx*hl_c + rx_v*hw_c, car.y + fy*hl_c + ry_v*hw_c),
        w2s(car.x + fx*hl_c - rx_v*hw_c, car.y + fy*hl_c - ry_v*hw_c),
        w2s(car.x - fx*hl_c - rx_v*hw_c, car.y - fy*hl_c - ry_v*hw_c),
        w2s(car.x - fx*hl_c + rx_v*hw_c, car.y - fy*hl_c + ry_v*hw_c),
    ]
    pygame.draw.polygon(surf, (155, 205, 245), win_pts)

    # Arrow on player car
    cx0, cy0 = w2s(car.x, car.y)
    ex = cx0 + int(fx * 18);  ey = cy0 + int(fy * 18)
    pygame.draw.line(surf, WHITE, (cx0, cy0), (ex, ey), 2)

    # Panel border + title bar
    pygame.draw.rect(surf, DGRAY, (MAP_X0, 0, MAP_W, MAP_H), 2)
    pygame.draw.rect(surf, (5, 6, 16), (MAP_X0, 0, MAP_W, 42))
    pygame.draw.rect(surf, ORANGE, (MAP_X0, 0, MAP_W, 3))   # accent stripe
    surf.blit(font_md.render("WIDOK Z GÓRY | Top View", True, WHITE),
              (MAP_X0 + 10, 11))

    _td_controls(surf)
    _td_info(surf, car)


def _td_green_strip(surf, w2s):
    """Draw green grass areas above/below the parking rows."""
    # Top grass strip (world y: 0 → ROW1_Y)
    p1 = w2s(0,       0)
    p2 = w2s(WORLD_W, ROW1_Y)
    r  = pygame.Rect(p1[0], p1[1], p2[0]-p1[0], p2[1]-p1[1])
    if r.width > 0 and r.height > 0:
        pygame.draw.rect(surf, (38, 90, 48), r)

    # Bottom grass strip (world y: ROW2_Y+SPOT_H → WORLD_H)
    p3 = w2s(0,       ROW2_Y + SPOT_H)
    p4 = w2s(WORLD_W, WORLD_H)
    r2 = pygame.Rect(p3[0], p3[1], p4[0]-p3[0], p4[1]-p3[1])
    if r2.width > 0 and r2.height > 0:
        pygame.draw.rect(surf, (38, 90, 48), r2)

    # Side strips (world x: 0→START_X and far end→WORLD_W)
    p5 = w2s(0,        ROW1_Y)
    p6 = w2s(START_X,  ROW2_Y + SPOT_H)
    r3 = pygame.Rect(p5[0], p5[1], p6[0]-p5[0], p6[1]-p5[1])
    if r3.width > 0 and r3.height > 0:
        pygame.draw.rect(surf, (38, 90, 48), r3)

    p7 = w2s(START_X + N_SPOTS*SPOT_W, ROW1_Y)
    p8 = w2s(WORLD_W,                  ROW2_Y + SPOT_H)
    r4 = pygame.Rect(p7[0], p7[1], p8[0]-p7[0], p8[1]-p7[1])
    if r4.width > 0 and r4.height > 0:
        pygame.draw.rect(surf, (38, 90, 48), r4)


def _td_border(surf, w2s):
    corners = [w2s(0, 0), w2s(WORLD_W, 0),
               w2s(WORLD_W, WORLD_H), w2s(0, WORLD_H)]
    pygame.draw.lines(surf, LGRAY, True, corners, 2)


def _td_arrows(surf, w2s):
    """Draw direction arrows on the main lane."""
    arrow_xs = range(START_X + 120, START_X + N_SPOTS*SPOT_W - 100, 250)
    for ax in arrow_xs:
        # Arrow pointing right (east)
        p_mid   = w2s(ax,     LANE_Y)
        p_tail  = w2s(ax - 30, LANE_Y)
        p_tip   = w2s(ax + 30, LANE_Y)
        p_ar    = w2s(ax + 10, LANE_Y - 15)
        p_al    = w2s(ax + 10, LANE_Y + 15)
        pygame.draw.line(surf, (90, 93, 115), p_tail, p_tip, 1)
        if p_tip != p_ar and p_tip != p_al:
            pygame.draw.polygon(surf, (90, 93, 115), [p_tip, p_ar, p_al])


def _td_car(surf, w2s, cx, cy, ww, wh, hdg_deg, col):
    """Detailed top-down car: body, roof, windshield, rear window, wheels, lights."""
    a      = math.radians(hdg_deg)
    fx, fy = math.cos(a), math.sin(a)
    rx, ry = -fy, fx
    hw, hl = ww / 2, wh / 2

    # Main body
    pts = [
        w2s(cx + fx*hl + rx*hw, cy + fy*hl + ry*hw),
        w2s(cx + fx*hl - rx*hw, cy + fy*hl - ry*hw),
        w2s(cx - fx*hl - rx*hw, cy - fy*hl - ry*hw),
        w2s(cx - fx*hl + rx*hw, cy - fy*hl + ry*hw),
    ]
    pygame.draw.polygon(surf, col, pts)

    # Roof (inner lighter rectangle, 60%×55% of body)
    rw, rl = hw * 0.60, hl * 0.55
    roof_pts = [
        w2s(cx + fx*rl + rx*rw, cy + fy*rl + ry*rw),
        w2s(cx + fx*rl - rx*rw, cy + fy*rl - ry*rw),
        w2s(cx - fx*rl - rx*rw, cy - fy*rl - ry*rw),
        w2s(cx - fx*rl + rx*rw, cy - fy*rl + ry*rw),
    ]
    roof_col = tuple(min(255, c + 28) for c in col)
    pygame.draw.polygon(surf, roof_col, roof_pts)

    # Windshield (front glass — lighter, near front)
    ws_start, ws_end = hl * 0.30, hl * 0.50
    ws_w = hw * 0.75
    wsh_pts = [
        w2s(cx + fx*ws_end   + rx*ws_w, cy + fy*ws_end   + ry*ws_w),
        w2s(cx + fx*ws_end   - rx*ws_w, cy + fy*ws_end   - ry*ws_w),
        w2s(cx + fx*ws_start - rx*ws_w, cy + fy*ws_start - ry*ws_w),
        w2s(cx + fx*ws_start + rx*ws_w, cy + fy*ws_start + ry*ws_w),
    ]
    pygame.draw.polygon(surf, (165, 215, 248), wsh_pts)

    # Rear window
    rw_start, rw_end = -hl * 0.50, -hl * 0.30
    rwh_pts = [
        w2s(cx + fx*rw_end   + rx*ws_w, cy + fy*rw_end   + ry*ws_w),
        w2s(cx + fx*rw_end   - rx*ws_w, cy + fy*rw_end   - ry*ws_w),
        w2s(cx + fx*rw_start - rx*ws_w, cy + fy*rw_start - ry*ws_w),
        w2s(cx + fx*rw_start + rx*ws_w, cy + fy*rw_start + ry*ws_w),
    ]
    pygame.draw.polygon(surf, (140, 190, 228), rwh_pts)

    # Side windows (narrow strips)
    for wd_hl_start, wd_hl_end in [(-0.28*hl, 0.28*hl)]:
        for side in (1, -1):
            sw_w1 = hw * side
            sw_w2 = hw * 0.72 * side
            sw_pts = [
                w2s(cx + fx*wd_hl_end   + rx*sw_w1, cy + fy*wd_hl_end   + ry*sw_w1),
                w2s(cx + fx*wd_hl_end   + rx*sw_w2, cy + fy*wd_hl_end   + ry*sw_w2),
                w2s(cx + fx*wd_hl_start + rx*sw_w2, cy + fy*wd_hl_start + ry*sw_w2),
                w2s(cx + fx*wd_hl_start + rx*sw_w1, cy + fy*wd_hl_start + ry*sw_w1),
            ]
            pygame.draw.polygon(surf, (145, 195, 235), sw_pts)

    # Wheels (dark circles at corners, slightly inset)
    wheel_r = max(2, int(5 * MAP_SCL))
    for fl, fr in [(0.78, 0.78), (-0.78, -0.78)]:
        for fs in (0.72, -0.72):
            wpx, wpy = w2s(cx + fx*(hl*fl) + rx*(hw*fs),
                           cy + fy*(hl*fr) + ry*(hw*fs))
            pygame.draw.circle(surf, (18, 18, 24), (wpx, wpy), wheel_r)
            pygame.draw.circle(surf, (45, 45, 55),  (wpx, wpy), max(1, wheel_r - 1))

    # Headlights (front, yellow-white)
    for fs in (0.70, -0.70):
        hpx, hpy = w2s(cx + fx*hl + rx*(hw*fs), cy + fy*hl + ry*(hw*fs))
        pygame.draw.circle(surf, (255, 250, 190), (hpx, hpy), max(1, int(3 * MAP_SCL)))

    # Tail-lights (rear, red)
    for fs in (0.70, -0.70):
        tpx, tpy = w2s(cx - fx*hl + rx*(hw*fs), cy - fy*hl + ry*(hw*fs))
        pygame.draw.circle(surf, (200, 50, 50), (tpx, tpy), max(1, int(3 * MAP_SCL)))

    # Outline
    pygame.draw.polygon(surf, (20, 22, 32), pts, 1)


def _td_tree(surf, w2s, tx, ty, tr):
    """Draw a stylised tree on the top-down map."""
    px, py = w2s(tx, ty)
    r = max(3, int(tr * MAP_SCL))

    # Shadow (offset ellipse)
    pygame.draw.ellipse(surf, (28, 48, 32),
                        (px - r + 2, py - r // 2 + 2, r * 2, int(r * 1.3)))
    # Dark outer canopy
    pygame.draw.circle(surf, TREE_DARK, (px, py), r)
    # Mid canopy
    pygame.draw.circle(surf, TREE_MID, (px - r//4, py - r//4), int(r * 0.72))
    # Highlight
    pygame.draw.circle(surf, TREE_HI,  (px - r//3, py - r//3), int(r * 0.40))


def _td_lamp(surf, w2s, lx, ly):
    """Draw a lamp post on the top-down map."""
    px, py = w2s(lx, ly)
    # Glow halo (alpha surface)
    glow = pygame.Surface((24, 24), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 240, 165, 55), (12, 12), 12)
    surf.blit(glow, (px - 12, py - 12))
    # Post dot
    pygame.draw.circle(surf, LAMP_POST, (px, py), max(2, int(3 * MAP_SCL)))
    pygame.draw.circle(surf, LAMP_GLOW, (px, py), max(1, int(2 * MAP_SCL)))


def _td_fov_cone(surf, car, w2s):
    rx, ry = car.rear
    a      = math.radians(car.angle)
    dist   = 5 * METER

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
    kmh    = int(abs(car.speed) * 15)
    dist_m = car.odometer * (1.0 / METER)
    for i, ln in enumerate([
        f"Prędkość: {kmh} km/h",
        f"Dystans:  {dist_m:.0f} m",
    ]):
        surf.blit(font_sm.render(ln, True, LGRAY),
                  (MAP_X0 + 12, 50 + i * 20))


# ═══════════════════════════════════════════════════════════════════════════════
#  PEDESTRIAN COLLISION DETECTION  (OBB vs circle)
# ═══════════════════════════════════════════════════════════════════════════════
def check_collisions(car, peds):
    fx, fy = car.fwd
    rx, ry = car.rgt
    for ped in peds:
        dx  = ped.x - car.x
        dy  = ped.y - car.y
        lon = dx * fx + dy * fy
        lat = dx * rx + dy * ry
        if abs(lon) < car.L / 2 + ped.R and abs(lat) < car.W / 2 + ped.R:
            if not car.collision:
                car.speed *= -0.5
            car.collision = True
            car.col_timer  = 90
            ped.hit       = True
            ped.hit_timer = 60
            d   = math.hypot(dx, dy) or 1
            ovr = (car.L / 2 + ped.R + 4) / d
            ped.x += dx * (ovr - 1) * 0.7
            ped.y += dy * (ovr - 1) * 0.7
            ped.x = max(START_X + 15,
                    min(START_X + N_SPOTS * SPOT_W - 15, ped.x))
            ped.y = max(ROW1_Y + SPOT_H + 5, min(ROW2_Y - 5, ped.y))


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    car = Car()

    peds = []
    random.seed(123)
    for _ in range(14):
        for _ in range(60):
            p = Pedestrian()
            if math.hypot(p.x - car.x, p.y - car.y) > 180:
                peds.append(p)
                break

    parked_cars = build_parked_cars()
    cam_surf    = pygame.Surface((CAM_W, CAM_H))

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    car.reset()

        keys = pygame.key.get_pressed()
        car.update(keys)
        for p in peds:
            p.update()
        check_collisions(car, peds)
        check_car_collisions(car, parked_cars)

        draw_camera_view(cam_surf, car, peds, parked_cars)
        screen.blit(cam_surf, (0, 0))

        draw_topdown(screen, car, peds, parked_cars)

        pygame.draw.line(screen, LGRAY, (CAM_W, 0), (CAM_W, SH), 2)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

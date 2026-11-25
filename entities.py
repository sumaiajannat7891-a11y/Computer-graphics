# src/entities.py
import random
import math
import pygame
from src.settings import (
    WIDTH, HEIGHT, GRAVITY, FRUIT_TYPES, POWERUP_TYPES,
    NEON_RED, NEON_ORANGE, WHITE, BG_DARK
)


def line_circle_intersect(p1, p2, center, radius):
    """Checks if line segment p1-p2 intersects a circle at center with given radius."""
    x1, y1 = p1
    x2, y2 = p2
    cx, cy = center

    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy

    if length_sq == 0:
        return math.hypot(cx - x1, cy - y1) <= radius

    t = max(0.0, min(1.0, ((cx - x1) * dx + (cy - y1) * dy) / length_sq))
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    return math.hypot(cx - closest_x, cy - closest_y) <= radius


class SlicedHalf:
    def __init__(self, x, y, vx, vy, radius, color, core_color, is_left, angle):
        self.x = x
        self.y = y
        self.vx = vx + (-3.5 if is_left else 3.5)
        self.vy = vy - 1.5
        self.radius = radius
        self.color = color
        self.core_color = core_color
        self.is_left = is_left
        self.angle = angle
        self.rot_speed = random.uniform(-8, -3) if is_left else random.uniform(3, 8)
        self.alpha = 255

    def update(self, time_scale=1.0):
        self.x += self.vx * time_scale
        self.y += self.vy * time_scale
        self.vy += GRAVITY * time_scale
        self.angle += self.rot_speed * time_scale
        self.alpha = max(0, self.alpha - 3)

    def draw(self, surface):
        if self.alpha <= 0:
            return
        size = self.radius * 3
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2

        # Draw full neon fruit then mask out one half
        pygame.draw.circle(surf, (*self.color, 60), (cx, cy), self.radius + 6)
        pygame.draw.circle(surf, (*self.color, int(self.alpha)), (cx, cy), self.radius, 4)
        pygame.draw.circle(surf, (*self.core_color, int(self.alpha * 0.85)), (cx, cy), int(self.radius * 0.65))

        if self.is_left:
            surf.fill((0, 0, 0, 0), rect=pygame.Rect(cx, 0, cx, size))
        else:
            surf.fill((0, 0, 0, 0), rect=pygame.Rect(0, 0, cx, size))

        rotated = pygame.transform.rotate(surf, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


class Entity:
    def __init__(self, x=None, y=None, vx=None, vy=None):
        self.x = x if x is not None else random.randint(150, WIDTH - 150)
        self.y = y if y is not None else HEIGHT + 50
        if vx is None:
            target_x = random.randint(WIDTH // 4, 3 * WIDTH // 4)
            self.vx = (target_x - self.x) / random.uniform(55, 75)
        else:
            self.vx = vx
        self.vy = vy if vy is not None else random.uniform(-19.5, -15.5)
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-4.5, 4.5)
        self.sliced = False
        self.missed = False
        self.entered_screen = False

    def update(self, time_scale=1.0):
        self.x += self.vx * time_scale
        self.y += self.vy * time_scale
        self.vy += GRAVITY * time_scale
        self.angle = (self.angle + self.rot_speed * time_scale) % 360

        if self.y < HEIGHT - 20:
            self.entered_screen = True

        if self.entered_screen and self.y > HEIGHT + 70:
            self.missed = True


class Fruit(Entity):
    def __init__(self, x=None, y=None, vx=None, vy=None):
        super().__init__(x, y, vx, vy)
        data = random.choice(FRUIT_TYPES)
        self.name = data["name"]
        self.color = data["color"]
        self.core_color = data.get("core", data["color"])
        self.points = data["points"]
        self.radius = data["radius"]

    def draw(self, surface):
        size = self.radius * 3
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2

        # Outer neon glow
        pygame.draw.circle(surf, (*self.color, 45), (cx, cy), self.radius + 10)
        pygame.draw.circle(surf, (*self.color, 90), (cx, cy), self.radius + 4)

        # Core & neon rim
        pygame.draw.circle(surf, BG_DARK, (cx, cy), self.radius)
        pygame.draw.circle(surf, (*self.core_color, 180), (cx, cy), int(self.radius * 0.65))
        pygame.draw.circle(surf, self.color, (cx, cy), self.radius, 4)

        # Rotating geometric detail lines inside fruit
        rad = math.radians(self.angle)
        for i in range(4):
            a = rad + i * (math.pi / 2)
            ex = cx + math.cos(a) * (self.radius * 0.6)
            ey = cy + math.sin(a) * (self.radius * 0.6)
            pygame.draw.line(surf, WHITE, (cx, cy), (ex, ey), 2)

        if self.x is not None and self.y is not None and math.isfinite(self.x) and math.isfinite(self.y):
            surface.blit(surf, (int(self.x - cx), int(self.y - cy)))

    def create_halves(self):
        left = SlicedHalf(self.x, self.y, self.vx, self.vy, self.radius, self.color, self.core_color, True, self.angle)
        right = SlicedHalf(self.x, self.y, self.vx, self.vy, self.radius, self.color, self.core_color, False, self.angle)
        return [left, right]


class Bomb(Entity):
    def __init__(self, x=None, y=None, vx=None, vy=None):
        super().__init__(x, y, vx, vy)
        self.radius = 36
        self.pulse = 0

    def update(self, time_scale=1.0):
        super().update(time_scale)
        self.pulse += 0.15

    def draw(self, surface):
        size = self.radius * 3
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        glow_r = self.radius + 8 + int(math.sin(self.pulse) * 4)

        # Danger red aura
        pygame.draw.circle(surf, (*NEON_RED, 70), (cx, cy), glow_r)
        pygame.draw.circle(surf, (25, 10, 15), (cx, cy), self.radius)
        pygame.draw.circle(surf, NEON_RED, (cx, cy), self.radius, 4)

        # Rotating hazard cross
        rad = math.radians(self.angle)
        for i in range(4):
            a = rad + i * (math.pi / 2)
            ex = cx + math.cos(a) * (self.radius * 0.55)
            ey = cy + math.sin(a) * (self.radius * 0.55)
            pygame.draw.line(surf, NEON_ORANGE, (cx, cy), (ex, ey), 4)

        pygame.draw.circle(surf, WHITE, (cx, cy), 6)
        if self.x is not None and self.y is not None and math.isfinite(self.x) and math.isfinite(self.y):
            surface.blit(surf, (int(self.x - cx), int(self.y - cy)))


class PowerUp(Entity):
    def __init__(self, x=None, y=None, vx=None, vy=None):
        super().__init__(x, y, vx, vy)
        data = random.choice(POWERUP_TYPES)
        self.name = data["name"]
        self.ptype = data["type"]
        self.color = data["color"]
        self.radius = data["radius"]

    def draw(self, surface):
        size = self.radius * 3
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2

        # Outer aura
        pygame.draw.circle(surf, (*self.color, 75), (cx, cy), self.radius + 10)
        pygame.draw.circle(surf, BG_DARK, (cx, cy), self.radius)

        # Rotating diamond & ring
        pts = []
        rad = math.radians(self.angle)
        for i in range(4):
            a = rad + i * (math.pi / 2)
            pts.append((cx + math.cos(a) * self.radius, cy + math.sin(a) * self.radius))
        pygame.draw.polygon(surf, self.color, pts, 3)
        pygame.draw.circle(surf, WHITE, (cx, cy), self.radius - 10, 2)

        if self.x is not None and self.y is not None and math.isfinite(self.x) and math.isfinite(self.y):
            surface.blit(surf, (int(self.x - cx), int(self.y - cy)))

_orig_fruit_init = Fruit.__init__

def _compat_fruit_init(self, *args, kind=None, **kwargs):
    if kind is not None:
        if isinstance(kind, dict) and "fruit_type" not in kwargs and "spec" not in kwargs and "data" not in kwargs:
            kwargs.setdefault("fruit_type", kind)
        elif isinstance(kind, str) and "name" not in kwargs:
            for ft in globals().get("FRUIT_TYPES", []):
                if ft.get("name") == kind:
                    kwargs.setdefault("fruit_type", ft)
                    break
    try:
        _orig_fruit_init(self, *args, **kwargs)
    except TypeError:
        if len(args) == 0 and kind is not None:
            _orig_fruit_init(self, kind, **kwargs)
        else:
            _orig_fruit_init(self, *args)

Fruit.__init__ = _compat_fruit_init

@property
def _fruit_alive(self):
    return not getattr(self, 'missed', False) and not getattr(self, 'sliced', False)

if not hasattr(Fruit, 'alive'):
    Fruit.alive = _fruit_alive

def _fruit_missed_bottom(self):
    return bool(getattr(self, 'missed', False))

if not hasattr(Fruit, 'missed_bottom'):
    Fruit.missed_bottom = _fruit_missed_bottom

import math
import random
import pygame
from src.settings import WIDTH, HEIGHT, NEON_CYAN, WHITE


class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, radius=4, life=0.5, gravity=250.0):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(60, 280)
        self.vx = float(vx) if vx is not None else math.cos(angle) * speed
        self.vy = float(vy) if vy is not None else math.sin(angle) * speed - 60
        self.radius = float(radius)
        self.life = float(life)
        self.max_life = float(life)
        self.gravity = float(gravity)

    @property
    def alpha(self):
        if self.max_life <= 0:
            return 0
        return max(0, min(255, int(255 * (self.life / self.max_life))))

    def update(self, dt=1 / 60):
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0 or self.radius <= 0:
            return
        r = max(1, int(self.radius * max(0.2, self.life / max(0.01, self.max_life))))
        alpha = self.alpha
        surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color[:3], max(20, alpha // 2)), (r * 2, r * 2), r * 2)
        pygame.draw.circle(surf, (*self.color[:3], alpha), (r * 2, r * 2), r)
        surface.blit(surf, (int(self.x - r * 2), int(self.y - r * 2)))


class FloatingText:
    def __init__(self, x, y, text, color=NEON_CYAN, font=None, life=0.9):
        self.x = float(x)
        self.y = float(y)
        self.text = str(text)
        self.color = color
        self.font = font or pygame.font.SysFont("arial", 28, bold=True)
        self.life = float(life)
        self.max_life = float(life)
        self.vy = -55.0

    @property
    def alpha(self):
        if self.max_life <= 0:
            return 0
        return max(0, min(255, int(255 * (self.life / self.max_life))))

    def update(self, dt=1 / 60):
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = self.alpha
        txt_surf = self.font.render(self.text, True, self.color[:3])
        txt_surf.set_alpha(alpha)
        rect = txt_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(txt_surf, rect)


class BladeTrail:
    def __init__(self, color=NEON_CYAN, max_points=18, width=10):
        self.color = color
        self.max_points = max_points
        self.width = width
        self.points = []

    def add_point(self, pos, *args, **kwargs):
        if pos is not None:
            self.points.append([float(pos[0]), float(pos[1]), 1.0])
            if len(self.points) > self.max_points:
                self.points.pop(0)

    def clear(self):
        self.points.clear()

    def update(self, dt=1 / 60, *args, **kwargs):
        updated = []
        for p in self.points:
            p[2] -= dt * 4.5
            if p[2] > 0:
                updated.append(p)
        self.points = updated

    def draw(self, surface, *args, **kwargs):
        if len(self.points) < 2:
            return
        trail_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(1, len(self.points)):
            p1 = self.points[i - 1]
            p2 = self.points[i]
            ratio = max(0.05, min(1.0, p2[2]))
            w = max(2, int(self.width * ratio))
            alpha = max(15, min(255, int(230 * ratio)))
            pygame.draw.line(
                trail_surf,
                (*self.color[:3], alpha),
                (int(p1[0]), int(p1[1])),
                (int(p2[0]), int(p2[1])),
                w,
            )
            pygame.draw.line(
                trail_surf,
                (*WHITE[:3], max(30, alpha // 2)),
                (int(p1[0]), int(p1[1])),
                (int(p2[0]), int(p2[1])),
                max(1, w // 3),
            )
        surface.blit(trail_surf, (0, 0))


class ScreenFlash:
    def __init__(self, color=WHITE, max_alpha=180, fade_speed=420):
        self.color = color
        self.max_alpha = max_alpha
        self.fade_speed = fade_speed
        self.alpha = 0.0

    def trigger(self, color=None, alpha=None, *args, **kwargs):
        if color is not None:
            self.color = color
        self.alpha = float(alpha if alpha is not None else self.max_alpha)

    def update(self, dt=1 / 60, *args, **kwargs):
        if self.alpha > 0:
            self.alpha = max(0.0, self.alpha - self.fade_speed * dt)

    def draw(self, surface, *args, **kwargs):
        if self.alpha > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((*self.color[:3], int(self.alpha)))
            surface.blit(flash_surf, (0, 0))


class ScreenShake:
    def __init__(self):
        self.magnitude = 0.0
        self.decay = 28.0
        self.offset = (0, 0)

    def trigger(self, magnitude=12.0, *args, **kwargs):
        self.magnitude = max(self.magnitude, float(magnitude))

    def update(self, dt=1 / 60, *args, **kwargs):
        if self.magnitude > 0.1:
            dx = random.uniform(-self.magnitude, self.magnitude)
            dy = random.uniform(-self.magnitude, self.magnitude)
            self.offset = (int(dx), int(dy))
            self.magnitude = max(0.0, self.magnitude - self.decay * dt)
        else:
            self.magnitude = 0.0
            self.offset = (0, 0)


class VFXManager:
    def __init__(self):
        self.particles = []
        self.floating_texts = []
        self.blade_trail = BladeTrail()
        self.flash = ScreenFlash()
        self.shake = ScreenShake()

    def spawn_particles(self, x, y, color, count=16):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def spawn_floating_text(self, x, y, text, color=NEON_CYAN, font=None):
        self.floating_texts.append(FloatingText(x, y, text, color, font))

    def update(self, dt=1 / 60):
        for p in self.particles[:]:
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)

        for ft in self.floating_texts[:]:
            ft.update(dt)
            if ft.life <= 0:
                self.floating_texts.remove(ft)

        self.blade_trail.update(dt)
        self.flash.update(dt)
        self.shake.update(dt)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
        for ft in self.floating_texts:
            ft.draw(surface)
        self.blade_trail.draw(surface)
        self.flash.draw(surface)

def _screen_shake_get_offset(self):
    return self.offset

ScreenShake.get_offset = _screen_shake_get_offset

import random
import sys
import pygame

from src.audio import SoundManager as SoundEngine
from src.entities import Fruit, SlicedHalf as HalfFruit, line_circle_intersect as line_intersects_circle
from src.settings import (
    BG_COLOR,
    BOMB_CHANCE_MAX,
    BOMB_CHANCE_START,
    COMBO_WINDOW,
    FPS,
    GRID_COLOR,
    HEIGHT,
    INITIAL_LIVES,
    MAX_SPAWN_INTERVAL,
    MIN_SPAWN_INTERVAL,
    NEON_CYAN,
    NEON_GOLD,
    NEON_GREEN,
    NEON_ORANGE,
    NEON_PINK,
    POWERUP_CHANCE,
    POWERUP_SCORE_BONUS,
    TITLE,
    WIDTH,
)
from src.storage import load_high_score, save_high_score
from src.vfx import BladeTrail, FloatingText, Particle, ScreenFlash, ScreenShake


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.font_title = pygame.font.SysFont("consolas", 56, bold=True)
        self.font_large = pygame.font.SysFont("consolas", 38, bold=True)
        self.font_med = pygame.font.SysFont("consolas", 26, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 20, bold=True)

        self.sound = SoundEngine()
        self.high_score = load_high_score()

        self.state = "MENU"  # MENU, PLAYING, GAMEOVER
        self.score = 0
        self.lives = INITIAL_LIVES
        self.spawn_timer = 0.0
        self.combo_count = 0
        self.combo_timer = 0.0

        self.fruits = []
        self.halves = []
        self.particles = []
        self.floating_texts = []
        self.blade = BladeTrail()
        self.shake = ScreenShake()
        self.flash = ScreenFlash()

        self.mouse_down = False
        self.prev_mouse_pos = None

        self.start_btn_rect = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 + 40, 280, 64)
        self.restart_btn_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 115, 300, 64)

    def reset_game(self):
        self.score = 0
        self.lives = INITIAL_LIVES
        self.spawn_timer = 0.35
        self.combo_count = 0
        self.combo_timer = 0.0
        self.fruits.clear()
        self.halves.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.blade.clear()
        self.mouse_down = False
        self.prev_mouse_pos = None

    def start_playing(self):
        self.reset_game()
        self.state = "PLAYING"

    def trigger_game_over(self):
        self.state = "GAMEOVER"
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self.high_score)

    def get_spawn_interval(self):
        progress = min(self.score / 300.0, 1.0)
        return MAX_SPAWN_INTERVAL - progress * (MAX_SPAWN_INTERVAL - MIN_SPAWN_INTERVAL)

    def get_bomb_chance(self):
        progress = min(self.score / 250.0, 1.0)
        return BOMB_CHANCE_START + progress * (BOMB_CHANCE_MAX - BOMB_CHANCE_START)

    def spawn_wave(self):
        count = 1 if self.score < 30 else random.randint(1, 3)
        for _ in range(count):
            roll = random.random()
            if roll < self.get_bomb_chance():
                kind = "bomb"
            elif roll < self.get_bomb_chance() + POWERUP_CHANCE:
                kind = "powerup"
            else:
                kind = "fruit"
            self.fruits.append(Fruit(kind=kind))

    def spawn_slice_effects(self, fruit):
        for _ in range(18):
            self.particles.append(Particle(fruit.x, fruit.y, fruit.color, speed_scale=1.0))

        left_half = HalfFruit(fruit.x, fruit.y, fruit.vx, fruit.vy, fruit.radius, fruit.color, side=-1)
        right_half = HalfFruit(fruit.x, fruit.y, fruit.vx, fruit.vy, fruit.radius, fruit.color, side=1)
        self.halves.extend([left_half, right_half])

    def spawn_bomb_effects(self, bomb):
        self.sound.play_explosion()
        self.shake.start(intensity=16, duration=0.35)
        self.flash.start(color=NEON_ORANGE, alpha=150, duration=0.18)
        for _ in range(42):
            col = random.choice([NEON_ORANGE, NEON_PINK, NEON_GOLD])
            self.particles.append(Particle(bomb.x, bomb.y, col, speed_scale=1.6))
        self.floating_texts.append(FloatingText(bomb.x, bomb.y, "BOMB HIT!", NEON_PINK, self.font_med))

    def handle_slice_collision(self, p1, p2):
        if self.state != "PLAYING":
            return

        sliced_any = False
        for fruit in self.fruits:
            if not fruit.alive:
                continue

            if line_intersects_circle(p1, p2, (fruit.x, fruit.y), fruit.radius * 0.92):
                fruit.alive = False
                sliced_any = True

                if fruit.kind == "bomb":
                    self.lives -= 1
                    self.spawn_bomb_effects(fruit)
                    if self.lives <= 0:
                        self.lives = 0
                        self.trigger_game_over()
                        return
                else:
                    self.sound.play_slice()
                    self.spawn_slice_effects(fruit)

                    pts = fruit.points
                    if fruit.kind == "powerup":
                        pts += POWERUP_SCORE_BONUS
                        self.flash.start(color=NEON_GOLD, alpha=80, duration=0.12)
                        self.floating_texts.append(
                            FloatingText(fruit.x, fruit.y - 18, f"+{pts} BONUS!", NEON_GOLD, self.font_med)
                        )
                    else:
                        self.floating_texts.append(
                            FloatingText(fruit.x, fruit.y - 12, f"+{pts}", fruit.color, self.font_small)
                        )

                    self.score += pts
                    self.combo_count += 1
                    self.combo_timer = COMBO_WINDOW

        if sliced_any and self.combo_count >= 3 and self.state == "PLAYING":
            bonus = self.combo_count * 2
            self.score += bonus
            self.floating_texts.append(
                FloatingText(
                    (p1[0] + p2[0]) * 0.5,
                    (p1[1] + p2[1]) * 0.5 - 26,
                    f"{self.combo_count}x COMBO +{bonus}!",
                    NEON_CYAN,
                    self.font_med,
                )
            )
            self.combo_count = 0
            self.combo_timer = 0.0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "PLAYING":
                        self.state = "MENU"
                    else:
                        self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self.state == "MENU":
                    if self.start_btn_rect.collidepoint(pos):
                        self.start_playing()
                elif self.state == "GAMEOVER":
                    if self.restart_btn_rect.collidepoint(pos):
                        self.start_playing()
                elif self.state == "PLAYING":
                    self.mouse_down = True
                    self.prev_mouse_pos = pos
                    self.blade.add_point(pos)
                    self.sound.play_swoosh()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.mouse_down = False
                self.prev_mouse_pos = None

            elif event.type == pygame.MOUSEMOTION:
                pos = event.pos
                if self.state == "PLAYING" and self.mouse_down:
                    self.blade.add_point(pos)
                    if self.prev_mouse_pos is not None:
                        self.handle_slice_collision(self.prev_mouse_pos, pos)
                    self.prev_mouse_pos = pos

    def update(self):
        dt = self.clock.get_time() / 1000.0
        dt = min(dt, 0.05)

        self.blade.update(dt)
        self.shake.update(dt)
        self.flash.update(dt)

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

        for ft in self.floating_texts:
            ft.update(dt)
        self.floating_texts = [ft for ft in self.floating_texts if ft.life > 0]

        for h in self.halves:
            h.update(dt)
        self.halves = [h for h in self.halves if not h.is_offscreen()]

        if self.state != "PLAYING":
            return

        if self.combo_count > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_count = 0
                self.combo_timer = 0.0

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_wave()
            self.spawn_timer = self.get_spawn_interval()

        for fruit in self.fruits:
            if not fruit.alive:
                continue
            fruit.update(dt * 60.0 if dt < 0.2 else 1.0)

            if fruit.missed_bottom():
                fruit.alive = False
                if fruit.kind != "bomb":
                    self.lives -= 1
                    self.shake.start(intensity=7, duration=0.18)
                    self.floating_texts.append(
                        FloatingText(fruit.x, HEIGHT - 55, "MISSED!", NEON_PINK, self.font_small)
                    )
                    if self.lives <= 0:
                        self.lives = 0
                        self.trigger_game_over()
                        return

        self.fruits = [f for f in self.fruits if f.alive and not f.missed_bottom()]

    def draw_background(self):
        self.screen.fill(BG_COLOR)
        step = 40
        for x in range(0, WIDTH, step):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, step):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WIDTH, y), 1)
        pygame.draw.rect(self.screen, NEON_CYAN, (4, 4, WIDTH - 8, HEIGHT - 8), 2, border_radius=8)

    def draw_hud(self):
        score_surf = self.font_med.render(f"SCORE: {self.score}", True, NEON_CYAN)
        best_surf = self.font_small.render(f"BEST: {self.high_score}", True, NEON_GOLD)
        lives_surf = self.font_med.render(f"LIVES: {self.lives}", True, NEON_GREEN if self.lives > 1 else NEON_PINK)

        self.screen.blit(score_surf, (24, 18))
        self.screen.blit(best_surf, (24, 52))
        self.screen.blit(lives_surf, (WIDTH - lives_surf.get_width() - 24, 18))

    def draw_button(self, rect, text, border_color, fill_color):
        mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos)
        bg = fill_color if not hovered else (35, 42, 72)
        pygame.draw.rect(self.screen, bg, rect, border_radius=12)
        pygame.draw.rect(self.screen, border_color, rect, width=3, border_radius=12)

        label = self.font_med.render(text, True, border_color)
        self.screen.blit(label, label.get_rect(center=rect.center))

    def draw_menu(self):
        title_surf = self.font_title.render("FRUIT NINJA", True, NEON_CYAN)
        sub_surf = self.font_large.render("NEON SLICE", True, NEON_PINK)
        best_surf = self.font_med.render(f"HIGH SCORE: {self.high_score}", True, NEON_GOLD)
        tip_surf = self.font_small.render("Hold Left Mouse & Drag to Slice | Avoid Bombs!", True, (210, 220, 240))

        self.screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 145)))
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 88)))
        self.screen.blit(best_surf, best_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 25)))
        self.screen.blit(tip_surf, tip_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 135)))

        self.draw_button(self.start_btn_rect, "START GAME", NEON_GREEN, (18, 24, 44))

    def draw_gameover(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 20, 185))
        self.screen.blit(overlay, (0, 0))

        over_surf = self.font_title.render("SYSTEM FAILURE", True, NEON_PINK)
        final_surf = self.font_large.render(f"FINAL SCORE: {self.score}", True, NEON_CYAN)
        best_surf = self.font_med.render(f"BEST SCORE: {self.high_score}", True, NEON_GOLD)

        self.screen.blit(over_surf, over_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 120)))
        self.screen.blit(final_surf, final_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
        self.screen.blit(best_surf, best_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25)))

        self.draw_button(self.restart_btn_rect, "PLAY AGAIN", NEON_CYAN, (18, 24, 44))

    def draw(self):
        self.draw_background()

        for fruit in self.fruits:
            if fruit.alive:
                fruit.draw(self.screen)

        for h in self.halves:
            h.draw(self.screen)

        for p in self.particles:
            p.draw(self.screen)

        self.blade.draw(self.screen)

        for ft in self.floating_texts:
            ft.draw(self.screen)

        if self.state == "PLAYING":
            self.draw_hud()
        elif self.state == "MENU":
            self.draw_menu()
        elif self.state == "GAMEOVER":
            self.draw_gameover()

        self.flash.draw(self.screen)

        offset = self.shake.get_offset()
        if offset != (0, 0):
            temp = self.screen.copy()
            self.screen.fill(BG_COLOR)
            self.screen.blit(temp, offset)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()

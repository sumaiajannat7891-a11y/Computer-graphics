# src/audio.py
import pygame
import numpy as np

class SoundManager:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
            self.enabled = True
        except Exception:
            self.enabled = False

    def play_slice(self):
        if not self.enabled:
            return
        try:
            duration = 0.08
            sample_rate = 22050
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            # High frequency swoosh sweep
            freq = np.linspace(1200, 300, len(t))
            wave = 0.3 * np.sin(2 * np.pi * freq * t) * np.linspace(1, 0, len(t))
            audio = (wave * 32767).astype(np.int16)
            sound = pygame.mixer.Sound(buffer=audio)
            sound.play()
        except Exception:
            pass

    def play_bomb(self):
        if not self.enabled:
            return
        try:
            duration = 0.5
            sample_rate = 22050
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            # Low rumble explosion with noise
            noise = np.random.uniform(-1, 1, len(t))
            wave = 0.5 * noise * np.linspace(1, 0, len(t))
            audio = (wave * 32767).astype(np.int16)
            sound = pygame.mixer.Sound(buffer=audio)
            sound.play()
        except Exception:
            pass

def _sm_play_swoosh(self, *args, **kwargs):
    for name in ('swoosh', 'play_slice', 'slice', 'play_sound'):
        fn = getattr(self, name, None)
        if callable(fn):
            try:
                return fn(*args, **kwargs)
            except TypeError:
                return fn()
    return None

if 'SoundManager' in globals() and not hasattr(SoundManager, 'play_swoosh'):
    SoundManager.play_swoosh = _sm_play_swoosh

"""Etapa 3 — easing, spring and the entry/exit/idle presets as pure functions of time.

Every preset returns a transform for one word at local time u (s since its entry
started): dict(dx, dy, scale, alpha, blur, blur_dir, mask). blur_dir 'v'/'h' is a
directional motion blur (px at 1x); 'g' a gaussian one. mask is the revealed
fraction for mask_reveal (1 = fully visible). No linear interpolation anywhere.
"""
import math


def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def ease_out_expo(p): p = clamp(p); return 1.0 if p >= 1 else 1 - 2 ** (-10 * p)
def ease_out_cubic(p): p = clamp(p); return 1 - (1 - p) ** 3
def ease_in_cubic(p): p = clamp(p); return p ** 3
def ease_in_out_sine(p): p = clamp(p); return -(math.cos(math.pi * p) - 1) / 2
def ease_out_back(p, s=1.5): p = clamp(p) - 1; return 1 + (s + 1) * p ** 3 + s * p ** 2


def bezier(x1, y1, x2, y2):
    """cubic-bezier(x1, y1, x2, y2) como no CSS/Remotion: x -> y por Newton sobre x(t)."""
    def f(p):
        p = clamp(p)
        if p in (0.0, 1.0): return p
        t = p
        for _ in range(8):
            x = 3 * x1 * t * (1 - t) ** 2 + 3 * x2 * t * t * (1 - t) + t ** 3 - p
            dx = 3 * x1 * (1 - t) ** 2 + 6 * (x2 - x1) * t * (1 - t) + 3 * (1 - x2) * t * t
            if abs(dx) < 1e-6: break
            t = clamp(t - x / dx)
        return 3 * y1 * t * (1 - t) ** 2 + 3 * y2 * t * t * (1 - t) + t ** 3
    return f


# Perfil de movimento (20/10/2026, EP 07): motion.perfil = editorial porta o perfil "editorial" do reel-motion (Remotion,
# aprovado na Andrea): curva que desacelera sem quique, entrada ~15% mais lenta, deslize e blur curtos, destaque sem
# mola e um movimento só por tipo de bloco. Sem perfil = motor de antes, idêntico.
_CURVES = {}
def _ease(cfg):
    c = cfg['motion'].get('curve')
    if not c: return ease_out_expo
    return _CURVES.setdefault(tuple(c), bezier(*c))
def _D(cfg, k=1.0): return cfg['timing']['enter'] * k * cfg['motion'].get('dur_k', 1.0)


def spring(t, stiffness=260.0, damping=18.0):
    """Damped spring 0 -> 1 (mass 1): slight overshoot, settles by ~0.4 s."""
    if t <= 0: return 0.0
    w0 = math.sqrt(stiffness); z = damping / (2 * w0)
    if z >= 1: return 1 - math.exp(-w0 * t) * (1 + w0 * t)
    wd = w0 * math.sqrt(1 - z * z)
    return 1 - math.exp(-z * w0 * t) * (math.cos(wd * t) + (z * w0 / wd) * math.sin(wd * t))


def _fade(u, d): return ease_out_cubic(u / max(1e-3, d))


def slide_blur(u, cfg):
    D = _D(cfg); m = cfg['motion']; e = _ease(cfg)(u / D)
    return dict(dx=0, dy=m['slide_px'] * (1 - e), scale=m['enter_scale_from'] + (1 - m['enter_scale_from']) * e,
                alpha=_fade(u, D * 0.7), blur=m['blur_px'] * (1 - e), blur_dir='v', mask=1.0)


def drop_blur(u, cfg):
    D = _D(cfg, 1.1); m = cfg['motion']; e = _ease(cfg)(u / D)
    return dict(dx=0, dy=-m['slide_px'] * 1.2 * (1 - e), scale=m['enter_scale_from'] + (1 - m['enter_scale_from']) * e,
                alpha=_fade(u, D * 0.6), blur=m['blur_px'] * 1.2 * (1 - e), blur_dir='v', mask=1.0)


def mask_reveal(u, cfg):
    D = _D(cfg, 1.15); m = cfg['motion']; e = _ease(cfg)(u / D)
    return dict(dx=-m['slide_px'] * 0.5 * (1 - e), dy=0, scale=1.0, alpha=_fade(u, D * 0.45),
                blur=m['blur_px'] * 0.6 * (1 - e), blur_dir='h', mask=e)


def pop_spring(u, cfg):
    m = cfg['motion']; sp = m['spring']; a = m.get('pop_from', 0.55)
    s = spring(u, sp['stiffness'], sp['damping']) if m.get('overshoot', 1) else _ease(cfg)(u / _D(cfg, 1.3))
    return dict(dx=0, dy=14 * (1 - s), scale=a + (1 - a) * s, alpha=_fade(u, 0.10), blur=0.0, blur_dir='g', mask=1.0)


def zoom_blur(u, cfg):
    m = cfg['motion']; a = m.get('zoom_from', 1.45)
    D = 0.30 * m.get('dur_k', 1.0); e = ease_out_back(u / D, 1.2) if m.get('overshoot', 1) else _ease(cfg)(u / D)
    return dict(dx=0, dy=0, scale=a - (a - 1) * e, alpha=_fade(u, 0.12),
                blur=10 * (1 - _ease(cfg)(u / D)), blur_dir='g', mask=1.0)


PRESETS = dict(slide_blur=slide_blur, drop_blur=drop_blur, mask_reveal=mask_reveal,
               pop_spring=pop_spring, zoom_blur=zoom_blur)


def preset(b, cfg):
    """motion.unico = {normal: x, highlight: y} troca a variação de presets por um movimento só por tipo de bloco."""
    return PRESETS[(cfg['motion'].get('unico') or {}).get(b['kind'], b['preset'])]


def exit_tf(v, cfg, dur=None):
    """v = s since the exit started. Opacity drops first (so the old block is already
    faint when the next one appears), with blur, slight shrink and a push upwards."""
    D = dur or cfg['timing']['exit']; m = cfg['motion']; p = clamp(v / D)
    e = ease_out_cubic(p)
    return dict(dy=-m['exit_push_px'] * e, scale=1 - (1 - m['exit_scale_to']) * e,
                alpha=1 - ease_out_expo(p), blur=6 * e)


def idle_tf(t_in, life, phase, cfg):
    """Micro-movement while on screen: slow breathe in scale + a few px of drift."""
    m = cfg['motion']
    s = 1 + m['idle_scale'] * ease_in_out_sine(t_in / max(0.8, life))
    dy = m['idle_drift_px'] * math.sin(2 * math.pi * t_in / 3.4 + phase)
    return s, dy

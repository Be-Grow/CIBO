"""Conta única da posição no Resolve (medida em 14/11/2026, ~/CIBO/tests/resolve_transform_teste.py --corr):
Pan/Tilt do clipe andam na medida do ARQUIVO da fonte, não da timeline. O davinci.py aplica a mesma razão (POSX, POSY)."""


def corrige(w, h, VW, VH, x, y, s, rot=0):
    """position x, y (em % da altura, como vai no FCPXML) e scale para o deslocamento VISTO ser o pedido"""
    return x * VW / w, y * VH / h, s

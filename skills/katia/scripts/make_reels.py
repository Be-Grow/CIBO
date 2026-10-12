#!/usr/bin/env python3
"""Katia = motor único `podcast-reels` + perfil da cliente (`../assets/profile.json`).

Antes esta pasta tinha uma cópia antiga do motor, que não recebia as correções (vídeo cortado
acima de 2 min, trilha em loop infinito travando o encode, frase sumindo da legenda). Agora só o
perfil é da Katia: fonte Montserrat Bold, capa mais baixa e sem barra, correções e ênfases.
Uso igual ao de antes:  JOB=job.json python3 make_reels.py [corte01 ...]
"""
import os, runpy, sys
H = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("PROFILE", os.path.join(H, "..", "assets", "profile.json"))
E = os.path.join(H, "..", "..", "podcast-reels", "scripts", "make_reels.py")
sys.argv[0] = E
sys.path.insert(0, os.path.dirname(E))
runpy.run_path(E, run_name="__main__")

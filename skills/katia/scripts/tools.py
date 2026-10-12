#!/usr/bin/env python3
"""Katia: `probe`/`sheet` do motor único podcast-reels (mesmos argumentos)."""
import os, runpy, sys
E = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "podcast-reels", "scripts", "tools.py")
sys.argv[0] = E
sys.path.insert(0, os.path.dirname(E))
runpy.run_path(E, run_name="__main__")

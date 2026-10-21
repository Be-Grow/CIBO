#!/usr/bin/env python3
"""Carga de contexto por pedido típico do CIBO (tokens ≈ bytes/3,6): o que entra sempre e o que cada pedido abre.
Base da tabela antes/depois de references/eficiencia.md. uso: carga.py"""
import os,glob,re,sys
H=os.path.expanduser; S=H('~/.claude/skills/')
def tk(*fs): return sum(os.path.getsize(f if f.startswith('/') else S+f) for f in fs)/3.6/1000
desc=sum(len((re.search(r'^description:\s*(.*?)\n(?:\w+:|---)',open(f).read(),re.S|re.M) or [0,''])[1].strip()) for f in glob.glob(S+'*/SKILL.md'))/3.6/1000
mem=glob.glob(H('~/.claude/projects/-Volumes-SSD-Movies-Edi--o-M-dia/memory/*.md'))
fixo=[('CLAUDE.md + memória',tk(H('~/.claude/CLAUDE.md'),*mem)),('descrições de skills',desc),('client-router SKILL',tk('client-router/SKILL.md')),
      ('regras-transversais',tk('client-router/references/regras-transversais.md')),('client-registry.md',tk('client-router/references/client-registry.md'))]
F=sum(v for _,v in fixo)
cen={'1 cliente novo (reel-motion)':['reel-motion/SKILL.md','briefing-criativo/SKILL.md','acervo/SKILL.md','fala-limpa/SKILL.md','talking-head-music/SKILL.md','lettering-motion/SKILL.md'],
     '2 Bombordo':['bombordo-boreste/SKILL.md','briefing-criativo/SKILL.md','acervo/SKILL.md','fala-limpa/SKILL.md','talking-head-music/SKILL.md'],
     '3 Katia':['katia/SKILL.md','podcast-reels/SKILL.md','briefing-criativo/SKILL.md','fala-limpa/SKILL.md','talking-head-music/SKILL.md'],
     '4 só legenda':['caption-quality-gate/SKILL.md','legenda-cruzada/SKILL.md'],
     '5 correção pontual (reel-motion)':['reel-motion/SKILL.md']}
out=['| Item | tokens (bytes/3,6) |','|---|---|']+[f'| {n} | {v:.1f}k |' for n,v in fixo]+[f'| **carga comum** | **{F:.1f}k** |','',
     '| Pedido típico | arquivos abertos além da carga comum | antes |','|---|---|---|']
for n,fs in cen.items(): out.append(f"| {n} | {', '.join(f.split('/')[0] for f in fs)} | {F+tk(*fs):.1f}k |")
print('\n'.join(out))

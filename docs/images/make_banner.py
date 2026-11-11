#!/usr/bin/env python3
"""Low-poly droopy banner (Meshgrove style): wordmark left, a low-poly droopy-eared dog with a droplet on the right."""
import math, random, sys, colorsys
import numpy as np
from scipy.spatial import Delaunay
random.seed(11)
W, H = 2304, 960
OUT = sys.argv[1] if len(sys.argv) > 1 else "banner.svg"
MODE = sys.argv[2] if len(sys.argv) > 2 else "banner"   # banner | logo

def hexrgb(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
def rgbhex(c): return '#%02x%02x%02x' % tuple(max(0,min(255,int(round(v*255)))) for v in c)
def shade(base, dl, ds=0.0):
    h,l,s = colorsys.rgb_to_hls(*hexrgb(base)); l=max(0,min(1,l+dl)); s=max(0,min(1,s+ds)); return rgbhex(colorsys.hls_to_rgb(h,l,s))
def inside(poly, p):
    x,y=p; n=len(poly); ins=False; j=n-1
    for i in range(n):
        xi,yi=poly[i]; xj,yj=poly[j]
        if ((yi>y)!=(yj>y)) and (x < (xj-xi)*(y-yi)/((yj-yi) or 1e-9)+xi): ins=not ins
        j=i
    return ins
def resample(poly, step):
    pts=[]
    for i in range(len(poly)):
        a=np.array(poly[i]); b=np.array(poly[(i+1)%len(poly)]); d=np.linalg.norm(b-a); n=max(1,int(d//step))
        for k in range(n): pts.append(tuple(a+(b-a)*k/n))
    return pts
def smooth(poly, iters=2):
    for _ in range(iters):
        out=[]
        for i in range(len(poly)):
            p=np.array(poly[i]); q=np.array(poly[(i+1)%len(poly)])
            out.append(tuple(p*0.75+q*0.25)); out.append(tuple(p*0.25+q*0.75))
        poly=out
    return poly
def lowpoly(poly, base, spacing=46, step=40, light=(-0.6,-0.8), amp=0.16, jitter=0.07, seed=0):
    rnd=random.Random(seed)
    pts=resample(poly, step)
    xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
    x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
    gy=y0
    while gy<y1:
        gx=x0+ (spacing/2 if int((gy-y0)/spacing)%2 else 0)
        while gx<x1:
            p=(gx+rnd.uniform(-0.3,0.3)*spacing, gy+rnd.uniform(-0.3,0.3)*spacing)
            if inside(poly,p): pts.append(p)
            gx+=spacing
        gy+=spacing*0.87
    P=np.array(pts); tri=Delaunay(P); out=[]
    cx=(x0+x1)/2; cy=(y0+y1)/2; r=max(x1-x0,y1-y0)/2
    for t in tri.simplices:
        a,b,c=P[t]; ctr=((a+b+c)/3)
        if not inside(poly, tuple(ctr)): continue
        # fake lighting: distance along light direction from the shape centre, plus jitter
        dl = ((ctr[0]-cx)*light[0] + (ctr[1]-cy)*light[1])/r*amp + rnd.uniform(-jitter,jitter)
        col=shade(base, dl)
        out.append(f'<polygon points="{a[0]:.1f},{a[1]:.1f} {b[0]:.1f},{b[1]:.1f} {c[0]:.1f},{c[1]:.1f}" fill="{col}" stroke="{col}" stroke-width="1" stroke-linejoin="round"/>')
    return "\n".join(out)
def ellipse(cx,cy,rx,ry,n=28,rot=0,squash=None):
    pts=[]
    for i in range(n):
        t=2*math.pi*i/n; x=rx*math.cos(t); y=ry*math.sin(t)
        if squash: y=y*(squash if y>0 else 1)
        xr=x*math.cos(rot)-y*math.sin(rot); yr=x*math.sin(rot)+y*math.cos(rot)
        pts.append((cx+xr,cy+yr))
    return pts

# ---- the dog (coordinates in banner space; the dog sits on the slab at y ~ 770) ----
OX = 0 if MODE=="banner" else -1210
BODY   = "#5d74a8"; BELLY="#b9c9e6"; EAR="#2d3f6e"; HEAD="#6a82b8"; MUZ="#c9d6ee"; NOSE="#141c33"; DROP="#3fd0ff"
parts=[]
# shadow on slab
parts.append(f'<ellipse cx="{1700+OX}" cy="772" rx="170" ry="16" fill="#0a0d18" opacity="0.7"/>')
# tail
tail=[(1835,700),(1905,640),(1945,650),(1930,690),(1870,735),(1850,750)]
parts.append(lowpoly([(x+OX,y) for x,y in smooth(tail,1)], BODY, spacing=30, step=26, seed=3))
# body: a sitting pear shape
body=smooth([(1600,470),(1800,470),(1860,560),(1880,680),(1850,760),(1560,760),(1525,680),(1545,560)],2)
parts.append(lowpoly([(x+OX,y) for x,y in body], BODY, spacing=52, step=44, seed=1))
# belly patch
belly=smooth([(1650,560),(1760,560),(1800,660),(1775,760),(1630,760),(1605,660)],2)
parts.append(lowpoly([(x+OX,y) for x,y in belly], BELLY, spacing=44, step=40, amp=0.10, seed=2))
# front paws
for px in (1615, 1745):
    paw=ellipse(px+OX, 752, 62, 24, n=18)
    parts.append(lowpoly(paw, BELLY, spacing=30, step=26, amp=0.08, seed=px))
    parts.append(f'<ellipse cx="{px+OX-26}" cy="762" rx="8" ry="5" fill="{shade(BELLY,-0.25)}"/><ellipse cx="{px+OX}" cy="765" rx="8" ry="5" fill="{shade(BELLY,-0.25)}"/><ellipse cx="{px+OX+26}" cy="762" rx="8" ry="5" fill="{shade(BELLY,-0.25)}"/>')
# ears: long, hanging, slightly swinging outward at the bottom (the droopy part)
earL=smooth([(1575,300),(1520,330),(1478,440),(1468,560),(1486,640),(1530,660),(1562,610),(1580,480),(1600,380)],2)
earR=smooth([(1825,300),(1880,330),(1922,440),(1932,560),(1914,640),(1870,660),(1838,610),(1820,480),(1800,380)],2)
parts.append(lowpoly([(x+OX,y) for x,y in earL], EAR, spacing=40, step=34, light=(-0.6,-0.8), seed=4))
parts.append(lowpoly([(x+OX,y) for x,y in earR], EAR, spacing=40, step=34, light=(-0.6,-0.8), seed=5))
# head: big, slightly wider than tall; droops a little
head=ellipse(1700+OX, 340, 178, 162, n=36)
parts.append(lowpoly(head, HEAD, spacing=50, step=44, seed=6))
# muzzle
muz=ellipse(1700+OX, 420, 108, 78, n=30)
parts.append(lowpoly(muz, MUZ, spacing=40, step=34, amp=0.10, seed=7))
# mouth line (a small sad-calm line)
parts.append(f'<path d="M {1668+OX} 462 Q {1700+OX} 478 {1732+OX} 462" fill="none" stroke="{shade(MUZ,-0.35)}" stroke-width="5" stroke-linecap="round"/>')
# nose
nose=[(1668,406),(1732,406),(1740,420),(1700,452),(1660,420)]
parts.append(lowpoly([(x+OX,y) for x,y in smooth(nose,1)], NOSE, spacing=22, step=18, amp=0.22, seed=8))
parts.append(f'<ellipse cx="{1686+OX}" cy="414" rx="9" ry="5" fill="#ffffff" opacity="0.35"/>')
# eyes: heavy droopy lids
for ex in (1644, 1756):
    parts.append(f'<ellipse cx="{ex+OX}" cy="318" rx="34" ry="30" fill="#f4f7ff"/>')
    parts.append(f'<circle cx="{ex+OX+2}" cy="330" r="13" fill="#141c33"/><circle cx="{ex+OX+7}" cy="325" r="4" fill="#ffffff"/>')
    # the lid: covers the top ~55 % of the eye, a low-poly wedge in head colour
    lid=[(ex-38,284),(ex+38,284),(ex+38,314+(10 if ex<1700 else 0)),(ex,318),(ex-38,314+(0 if ex<1700 else 10))]
    parts.append(lowpoly([(x+OX,y) for x,y in lid], shade(HEAD,-0.04), spacing=24, step=20, amp=0.12, seed=ex))
    parts.append(f'<path d="M {ex+OX-36} {314+(10 if ex<1700 else 0)} Q {ex+OX} 326 {ex+OX+36} {314+(0 if ex<1700 else 10)}" fill="none" stroke="{shade(HEAD,-0.30)}" stroke-width="4" stroke-linecap="round"/>')
# brows: slanted up-outward = worried / droopy
parts.append(f'<path d="M {1604+OX} 286 L {1664+OX} 268" stroke="{shade(HEAD,-0.32)}" stroke-width="9" stroke-linecap="round"/>')
parts.append(f'<path d="M {1796+OX} 286 L {1736+OX} 268" stroke="{shade(HEAD,-0.32)}" stroke-width="9" stroke-linecap="round"/>')
# collar with a droplet tag
parts.append(f'<path d="M {1598+OX} 480 Q {1700+OX} 530 {1802+OX} 480 L {1808+OX} 500 Q {1700+OX} 556 {1592+OX} 500 Z" fill="#ffb547"/>')
# the droplet: hovering above-left, glowing, low-poly teardrop
def teardrop(cx,cy,r,n=30):
    pts=[]
    for i in range(n):
        t=2*math.pi*i/n
        x=r*math.sin(t)*(1-0.5*math.cos(t))*0.9; y=-r*math.cos(t)*1.15
        pts.append((cx+x, cy+y))
    return pts
dcx, dcy = 1480+OX, 190
parts.append(f'<ellipse cx="{dcx}" cy="{dcy+10}" rx="150" ry="150" fill="url(#dropglow)"/>')
parts.append(lowpoly(teardrop(dcx,dcy,78), DROP, spacing=30, step=24, light=(-0.7,-0.7), amp=0.22, jitter=0.06, seed=9))
parts.append(f'<ellipse cx="{dcx-26}" cy="{dcy+6}" rx="12" ry="22" fill="#ffffff" opacity="0.55" transform="rotate(-20 {dcx-26} {dcy+6})"/>')
# two tiny drops
for (sx,sy,sr) in ((1575+OX, 118, 20), (1420+OX, 300, 15)):
    parts.append(lowpoly(teardrop(sx,sy,sr,n=14), DROP, spacing=14, step=12, amp=0.2, seed=int(sx)))

if MODE=="banner":
    bg = f'''<rect width="{W}" height="{H}" fill="#0f1322"/>
  <rect width="{W}" height="{H}" fill="url(#glow2)"/>
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
  <rect width="{W}" height="{H}" filter="url(#grain)"/>
  <text x="160" y="546" font-family="Red Hat Display" font-weight="600" font-size="190" letter-spacing="-2" fill="#ffffff">droopy</text>
  <text x="166" y="640" font-family="Red Hat Display" font-weight="500" font-size="44" letter-spacing="1" fill="#9fb0c8">drop files on your scripts</text>
  <rect x="1250" y="872" width="1054" height="44" fill="#000000" opacity="0.5" filter="url(#soft)"/>
  <polygon points="1296,748 2308,748 2308,800 1250,800" fill="#3a3b51"/>
  <polygon points="1250,800 2308,800 2308,872 1250,872" fill="#2a2b3b"/>
  <polygon points="1296,748 1302,748 1258,800 1250,800" fill="#525366"/>'''
    size=(W,H); vb=f"0 0 {W} {H}"
else:
    bg=''; size=(640,760); vb="140 40 640 760"
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{size[0]}" height="{size[1]}">
  <title>droopy</title>
  <defs>
    <radialGradient id="glow" cx="560" cy="470" r="620" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#3fd0ff" stop-opacity="0.42"/>
      <stop offset="0.45" stop-color="#4f8dff" stop-opacity="0.14"/>
      <stop offset="1" stop-color="#4f8dff" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glow2" cx="1850" cy="520" r="700" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#4f8dff" stop-opacity="0.10"/>
      <stop offset="1" stop-color="#4f8dff" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="dropglow">
      <stop offset="0" stop-color="#3fd0ff" stop-opacity="0.35"/>
      <stop offset="1" stop-color="#3fd0ff" stop-opacity="0"/>
    </radialGradient>
    <filter id="grain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7"/>
      <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.05 0"/>
    </filter>
    <filter id="soft" x="-10%" y="-200%" width="120%" height="500%"><feGaussianBlur stdDeviation="18"/></filter>
  </defs>
  {bg}
  {chr(10).join(parts)}
</svg>
'''
open(OUT,"w").write(svg); print("wrote", OUT, len(parts), "part groups")

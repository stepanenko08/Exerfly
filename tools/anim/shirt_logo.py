import numpy as np
from PIL import Image
d = np.load('muscles.png.geo.npz'); P, UV, reg, yh, T, zc, hw = d['P'], d['UV'], d['reg'], float(d['yh']), float(d['T']), d['zc'], d['hw']
src = '/home/claude/hy/tex_tan/texture_pbr_20250901.png'
tex = np.asarray(Image.open(src).convert('RGB')).astype(np.float32); S = tex.shape[0]
H = np.ptp(P[:, 1]); M = H/1.8                      # единиц сетки на метр
rel = (P[:, 1]-yh)/T; lat = P[:, 0]/np.maximum(hw, 1e-9); front = P[:, 2] > zc
# 1) убрать старые эмблемы на груди: насыщенные оранжевые пиксели в зоне груди
chest = front & (rel > 0.6) & (rel < 1.2) & (np.abs(lat) < 0.95)
hsv = np.asarray(Image.open(src).convert('HSV')).astype(np.float32)
sat = (tex[..., 0] > tex[..., 1]+18) & (tex[..., 0] > tex[..., 2]+18) & (tex[..., 0] > 45)
area = np.zeros(sat.shape, bool)
from PIL import ImageDraw
mask = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(mask)
for tri in d['I']:
    if chest[tri].all(): dr.polygon([(UV[v, 0]*S, UV[v, 1]*S) for v in tri], fill=255, outline=255)
area = np.asarray(mask) > 0
from scipy.ndimage import binary_dilation, label
cand0 = area & sat
lab, n = label(binary_dilation(cand0, iterations=2))
kill = np.zeros_like(cand0)
dark = tex.max(2) < 60
for i in range(1, n+1):
    comp = lab == i; sz = comp.sum()
    ring = binary_dilation(comp, iterations=4) & ~comp
    if sz < 4000 and dark[ring].mean() > 0.8: kill |= comp     # маленькое пятно в окружении тёмной ткани
kill = binary_dilation(kill, iterations=2) & area
shirt = np.median(tex[area & ~binary_dilation(sat, iterations=3)], 0)
tex[kill] = shirt
print('erased px', int(kill.sum()), 'shirt', shirt.round())
# 2) логотип на левой стороне груди (у персонажа левая = +X)
target = np.array([0.60, 0.93])                       # (lat, rel)
cand = front & np.isin(reg, [1, 2]) & (np.abs(lat-target[0]) < 0.25) & (np.abs(rel-target[1]) < 0.15)
xy = P[cand][:, :2]; uv = UV[cand]
med = np.median(uv, 0); ok = np.linalg.norm(uv-med, axis=1) < 0.05; xy, uv = xy[ok], uv[ok]
A, *_ = np.linalg.lstsq(np.c_[xy, np.ones(len(xy))], uv, rcond=None)   # uv = [x y 1] A
x0 = np.interp(target[0], [0, 1], [0, np.median(hw[cand])]); y0 = yh+target[1]*T
w = 0.085*M
logo = np.asarray(Image.open('wing.png').convert('RGBA')).astype(np.float32)/255; L = logo.shape[0]
corners = np.array([[x0-w/2, y0-w/2, 1], [x0+w/2, y0-w/2, 1], [x0-w/2, y0+w/2, 1], [x0+w/2, y0+w/2, 1]]) @ A
umin, vmin = (corners.min(0)*S).astype(int)-2; umax, vmax = (corners.max(0)*S).astype(int)+3
Ainv = np.linalg.inv(np.r_[A[:2].T.T, [[0, 0]]].T[:2, :2] if False else A[:2])   # 2x2
cnt = 0
for py in range(vmin, vmax):
    for px in range(umin, umax):
        uvp = np.array([(px+0.5)/S, (py+0.5)/S]) - A[2]
        x, y = uvp @ np.linalg.inv(A[:2])
        lx = (x-(x0-w/2))/w; ly = ((y0+w/2)-y)/w
        if 0 <= lx < 1 and 0 <= ly < 1:
            c = logo[int(ly*L), int(lx*L)]
            if c[3] > 0: tex[py, px] = tex[py, px]*(1-c[3]) + c[:3]*255*c[3]; cnt += 1
print('logo px', cnt, 'uv box', umin, vmin, umax, vmax)
import os; os.makedirs('/home/claude/hy/tex_final', exist_ok=True)
Image.fromarray(tex.clip(0, 255).astype(np.uint8)).save('/home/claude/hy/tex_final/texture_pbr_20250901.png')
import shutil; shutil.copy('/home/claude/hy/tex_tan/texture_pbr_20250901_normal.png', '/home/claude/hy/tex_final/')

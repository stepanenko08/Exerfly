"""Карта мышц в UV-пространстве персонажа: каждый тексель → индекс мышцы (0 = нет)."""
import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/home/claude/mx')
from lib import *
KEYS = ['chest', 'shoulders', 'biceps', 'triceps', 'forearms', 'abs', 'obliques', 'traps', 'lats', 'lower_back', 'glutes', 'quads', 'hamstrings', 'calves']
g = GLTF2().load(sys.argv[1]); b = g.binary_blob(); OUT = sys.argv[2]; SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
def rd(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
    dt = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a.componentType]
    v = np.frombuffer(b, dtype=dt, count=a.count*n, offset=bv.byteOffset+(a.byteOffset or 0)); return v.reshape(a.count, n) if n > 1 else v
p = [m for m in g.meshes if m.primitives[0].attributes.JOINTS_0 is not None][0].primitives[0]
P = rd(p.attributes.POSITION).astype(float); UV = rd(p.attributes.TEXCOORD_0).astype(float)
J = rd(p.attributes.JOINTS_0).astype(int); Wt = rd(p.attributes.WEIGHTS_0).astype(float); I = rd(p.indices).reshape(-1, 3)
sk = g.skins[0]; names = [short(g.nodes[j].name) for j in sk.joints]
IBM = rd(sk.inverseBindMatrices).reshape(-1, 4, 4).transpose(0, 2, 1)
BP = {n: np.linalg.inv(m)[:3, 3] for n, m in zip(names, IBM)}
dom = np.array([names[J[i, np.argmax(Wt[i])]] for i in range(len(P))])
H = P[:, 1].max()-P[:, 1].min(); y0 = P[:, 1].min()
x, y, z = P[:, 0], P[:, 1], P[:, 2]
yh = BP['Hips'][1]; ysh = (BP['LeftArm'][1]+BP['RightArm'][1])/2; T = ysh-yh
torso = np.isin(dom, ['Hips', 'Spine', 'Spine1', 'Spine2'])
bins = np.linspace(y.min(), y.max(), 60); zc = np.zeros(len(P)); hw = np.ones(len(P))
for i in range(len(bins)-1):
    sel = (y >= bins[i]) & (y < bins[i+1]); st = sel & torso
    if st.sum() > 5: zc[sel] = (z[st].max()+z[st].min())/2; hw[sel] = np.abs(x[st]).max()
reg = np.zeros(len(P), int); K = {k: i+1 for i, k in enumerate(KEYS)}
front = z > zc; lat = np.abs(x)/np.maximum(hw, 1e-9); rel = (y-yh)/T
for i in range(len(P)):
    d = dom[i]; s = 'Left' if x[i] > 0 else 'Right'
    if d in ('Spine', 'Spine1', 'Spine2') or (d == 'Hips' and rel[i] > -0.02):
        if front[i]:
            if rel[i] > 0.60: reg[i] = K['chest'] if lat[i] < 0.92 else K['shoulders']
            elif rel[i] > 0.08: reg[i] = K['abs'] if lat[i] < 0.5 else K['obliques']
        else:
            if rel[i] > 0.78: reg[i] = K['traps']
            elif rel[i] > 0.32: reg[i] = K['lats'] if lat[i] > 0.22 else K['traps'] if rel[i] > 0.6 else K['lats']
            elif rel[i] > -0.02: reg[i] = K['lower_back'] if lat[i] < 0.6 else K['obliques']
    elif d == 'Hips' or (d.endswith('UpLeg') and not front[i] and y[i] > yh-0.30*T):
        if not front[i]: reg[i] = K['glutes']
    if d.endswith('UpLeg') and reg[i] == 0:
        a0 = BP[s+'UpLeg']; a1 = BP[s+'Leg']; ax = a1-a0; t = np.clip(np.dot(P[i]-a0, ax)/np.dot(ax, ax), 0, 1)
        reg[i] = K['quads'] if P[i][2] > (a0+t*ax)[2] else K['hamstrings']
    elif d.endswith('Leg') and not d.endswith('UpLeg'):
        a0 = BP[s+'Leg']; a1 = BP[s+'Foot']; ax = a1-a0; t = np.clip(np.dot(P[i]-a0, ax)/np.dot(ax, ax), 0, 1)
        reg[i] = K['calves'] if P[i][2] < (a0+t*ax)[2] + 0.15*np.linalg.norm(ax)*0.1 else 0
    elif d.endswith('Shoulder'):
        reg[i] = K['traps'] if abs(x[i]) < abs(BP[s+'Arm'][0])*0.75 else K['shoulders']
    elif d.endswith('ForeArm'): reg[i] = K['forearms']
    elif d.endswith('Arm'):
        a0 = BP[s+'Arm']; a1 = BP[s+'ForeArm']; ax = a1-a0; t = np.dot(P[i]-a0, ax)/np.dot(ax, ax)
        c = a0+np.clip(t, 0, 1)*ax
        reg[i] = K['shoulders'] if t < 0.28 else (K['biceps'] if P[i][2] > c[2] else K['triceps'])
# растеризация треугольников в UV
img = Image.new('L', (SIZE, SIZE), 0); dr = ImageDraw.Draw(img)
for tri in I:
    r = np.bincount(reg[tri], minlength=16); k = int(np.argmax(r))
    if k == 0: continue
    pts = [(UV[v, 0]*SIZE, UV[v, 1]*SIZE) for v in tri]
    dr.polygon(pts, fill=k*16+8, outline=k*16+8)
img.save(OUT)
print('vertex counts', {k: int((reg == K[k]).sum()) for k in KEYS})
np.save(OUT+'.reg.npy', reg)
np.savez(OUT+'.geo.npz', P=P, UV=UV, reg=reg, I=I, yh=yh, T=T, zc=zc, hw=hw)

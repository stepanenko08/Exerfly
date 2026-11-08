"""Слой «подсветки мышц» по 2D-схеме мышц (tools/bodymap/muscle_colors.png).
Каждая точка тела (в позе покоя) проецируется на вид спереди или сзади, цвет схемы даёт мышцу.
Для каждой мышцы — своя маска в UV-развёртке персонажа (белые щели схемы = щели на теле) и своя
прозрачная сетка с материалом M_<ключ>; сайт меняет прозрачность материала.
python3 overlay2.py <in.glb> <out.glb> <muscle_colors.png> [debug.png]"""
import sys, io, numpy as np, cv2
from PIL import Image
sys.path.insert(0, '/home/claude/mx')
from lib import *
from pygltflib import Accessor, BufferView, Material, PbrMetallicRoughness, Mesh, Primitive, Attributes, Node, Texture, TextureInfo, Sampler
from pygltflib import Image as GImage
SRC, DST, MAP = sys.argv[1:4]; DEBUG = sys.argv[4] if len(sys.argv) > 4 else None
KEYS = ['chest', 'shoulders', 'biceps', 'triceps', 'forearms', 'abs', 'obliques', 'traps', 'lats', 'lower_back', 'glutes', 'quads', 'hamstrings', 'calves']
PAL = {'chest': '#E6194B', 'shoulders': '#F58231', 'biceps': '#FFE119', 'triceps': '#BFEF45', 'forearms': '#3CB44B', 'abs': '#42D4F4',
       'obliques': '#4363D8', 'traps': '#911EB4', 'lats': '#F032E6', 'lower_back': '#800000', 'glutes': '#9A6324', 'quads': '#000075',
       'hamstrings': '#469990', 'calves': '#DCBEFF', '_w': '#F8F8F8', '_n1': '#C0C0C0', '_n2': '#989898', '_n3': '#B8B8B8', '_n4': '#E8E8E8'}
TEX = 2048                                    # растр развёртки; маска каждой мышцы вырезается по её области (≤1024²)

# ---------- схема: метка мышцы для каждого пикселя ----------
img = np.array(Image.open(MAP).convert('RGB')); IH, IW, _ = img.shape
KS = IW/1024.0                                # ключевые точки заданы для картинки шириной 1024
pk = list(PAL); pc = np.array([[int(PAL[k][i:i+2], 16) for i in (1, 3, 5)] for k in pk], float)
# метка по ближайшему цвету палитры — через таблицу уникальных цветов (картинка большая)
packed = (img[:, :, 0].astype(np.int32) << 16) | (img[:, :, 1].astype(np.int32) << 8) | img[:, :, 2]
uniq, inv = np.unique(packed.ravel(), return_inverse=True)
ucol = np.stack([(uniq >> 16) & 255, (uniq >> 8) & 255, uniq & 255], 1).astype(float)
unear = ((ucol[:, None]-pc[None])**2).sum(-1).argmin(1)
lab_idx = unear[inv].reshape(IH, IW)
LAB = np.zeros((IH, IW), np.int16)                         # 0 — не мышца (фон, щель, кожа), 1..14 — мышца
for i, k in enumerate(KEYS): LAB[lab_idx == pk.index(k)] = i+1
del packed, inv, lab_idx, img

# ключевые точки на схеме (пиксели), вид спереди: слева на картинке — правая сторона тела
KP = {'front': dict(head=(255, 35), neck=(255, 112), pelvis=(255, 330),
                    Rsh=(170, 175), Rel=(150, 262), Rwr=(107, 338), Lsh=(340, 175), Lel=(360, 262), Lwr=(403, 338),
                    Rhip=(222, 335), Rkn=(218, 470), Ran=(224, 600), Lhip=(288, 335), Lkn=(292, 470), Lan=(286, 600)),
      'back': dict(head=(768, 32), neck=(768, 105), pelvis=(768, 330),
                   Lsh=(695, 175), Lel=(657, 268), Lwr=(628, 338), Rsh=(840, 175), Rel=(857, 268), Rwr=(888, 338),
                   Lhip=(735, 335), Lkn=(735, 475), Lan=(740, 600), Rhip=(800, 335), Rkn=(800, 475), Ran=(795, 600))}

# ---------- модель ----------
g = GLTF2().load(SRC); blob = bytearray(g.binary_blob())
def rd(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
    dt = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a.componentType]
    v = np.frombuffer(bytes(blob), dtype=dt, count=a.count*n, offset=bv.byteOffset+(a.byteOffset or 0)); return v.reshape(a.count, n) if n > 1 else v
def add_bytes(b, target=None):
    while len(blob) % 4: blob.append(0)
    off = len(blob); blob.extend(b); g.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=len(b), target=target)); return len(g.bufferViews)-1
def add_acc(arr, typ, comp, minmax=False, target=34962, norm=False):
    dt = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[comp]; arr = np.ascontiguousarray(arr, dtype=dt)
    a = Accessor(bufferView=add_bytes(arr.tobytes(), target), componentType=comp, count=int(arr.shape[0]), type=typ, normalized=norm or None)
    if minmax: a.min = [float(x) for x in arr.min(0)]; a.max = [float(x) for x in arr.max(0)]
    g.accessors.append(a); return len(g.accessors)-1
mi = [i for i, m in enumerate(g.meshes) if m.primitives[0].attributes.JOINTS_0 is not None][0]
p = g.meshes[mi].primitives[0]
P = rd(p.attributes.POSITION).astype(float); Nn = rd(p.attributes.NORMAL).astype(float); UV = rd(p.attributes.TEXCOORD_0).astype(float)
J = rd(p.attributes.JOINTS_0).astype(int); W = rd(p.attributes.WEIGHTS_0).astype(float)
if W.max() > 1.5: W = W/255.0
I = rd(p.indices).reshape(-1, 3).astype(np.int64)
skin = g.skins[0]; IBM = rd(skin.inverseBindMatrices).reshape(-1, 4, 4)
jname = [short(g.nodes[j].name) for j in skin.joints]
JP = {n: np.linalg.inv(IBM[i].T)[:3, 3] for i, n in enumerate(jname)}       # суставы в пространстве сетки
H = np.ptp(P[:, 1]); unit = H/1.8
def jp(n): return JP[n] if n in JP else None
# суставы, которых может не быть в списке скина (концевые), — по ближайшим
top = P[:, 1].max()
K3 = dict(head=np.array([0, top, 0]), neck=JP['Neck'], pelvis=JP['Hips'],
          Lsh=JP['LeftArm'], Lel=JP['LeftForeArm'], Lwr=JP['LeftHand'], Rsh=JP['RightArm'], Rel=JP['RightForeArm'], Rwr=JP['RightHand'],
          Lhip=JP['LeftUpLeg'], Lkn=JP['LeftLeg'], Lan=JP['LeftFoot'], Rhip=JP['RightUpLeg'], Rkn=JP['RightLeg'], Ran=JP['RightFoot'])

def view_xy(v3, view):                      # в координаты «как на картинке»: X вправо, Y вниз
    x, y = v3[..., 0], v3[..., 1]
    return np.stack([x if view == 'front' else -x, -y], -1)
def fit_affine(src, dst):                   # подобие+сдвиг: u = s*X + tx, v = s2*Y + ty (по осям отдельно)
    A = np.c_[src[:, 0], np.ones(len(src))]; ax = np.linalg.lstsq(A, dst[:, 0], rcond=None)[0]
    B = np.c_[src[:, 1], np.ones(len(src))]; ay = np.linalg.lstsq(B, dst[:, 1], rcond=None)[0]
    return lambda q: np.stack([q[..., 0]*ax[0]+ax[1], q[..., 1]*ay[0]+ay[1]], -1)
def chain_map(q, A, B, C, A2, B2, C2):
    """Точки q (N,2) рядом с цепочкой A-B-C → такая же точка у цепочки A2-B2-C2 (параметр вдоль + отступ)."""
    best = None
    for (a, b, a2, b2) in ((A, B, A2, B2), (B, C, B2, C2)):
        d = b-a; L = np.linalg.norm(d); u = d/L; n = np.array([-u[1], u[0]])
        t = (q-a)@u/L; off = (q-a)@n
        d2 = b2-a2; L2 = np.linalg.norm(d2); u2 = d2/L2; n2 = np.array([-u2[1], u2[0]])
        res = a2+np.clip(t, -0.3, 1.3)[:, None]*d2+(off*(L2/L))[:, None]*n2
        dist = np.abs(off)+np.maximum(0, -t)*L+np.maximum(0, t-1)*L
        if best is None: best = (res, dist)
        else:
            m = dist < best[1]; best[0][m] = res[m]; best[1][m] = dist[m]
    return best[0]

# веса костей: доля руки/ноги для каждой вершины
def bone_w(names):
    ids = [i for i, n in enumerate(jname) if any(n.startswith(x) for x in names)]
    return (W*np.isin(J, ids)).sum(1)
wLa = bone_w(['LeftArm', 'LeftForeArm', 'LeftHand']); wRa = bone_w(['RightArm', 'RightForeArm', 'RightHand'])
wLl = bone_w(['LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToe']); wRl = bone_w(['RightUpLeg', 'RightLeg', 'RightFoot', 'RightToe'])

def project(Pv, view):
    """3D-точки (N,3) → пиксели схемы для вида view; веса по вершинам передаются снаружи."""
    kp = {k: np.array(v, float)*KS for k, v in KP[view].items()}
    k3 = {k: view_xy(v, view) for k, v in K3.items()}
    q = view_xy(Pv, view)
    names = ['neck', 'pelvis', 'Lsh', 'Rsh', 'Lhip', 'Rhip']
    aff = fit_affine(np.array([k3[n] for n in names]), np.array([kp[n] for n in names]))
    base = aff(q)
    arms = {s: chain_map(q, k3[s+'sh'], k3[s+'el'], k3[s+'wr'], kp[s+'sh'], kp[s+'el'], kp[s+'wr']) for s in 'LR'}
    legs = {s: chain_map(q, k3[s+'hip'], k3[s+'kn'], k3[s+'an'], kp[s+'hip'], kp[s+'kn'], kp[s+'an']) for s in 'LR'}
    return base, arms, legs

# ---------- растеризация в UV ----------
nrm = Nn/np.linalg.norm(Nn, axis=1, keepdims=True)
tex_lab = np.zeros((TEX, TEX), np.int16); covered = np.zeros((TEX, TEX), bool)
uvp = np.c_[UV[:, 0]*TEX-0.5, UV[:, 1]*TEX-0.5]                 # glTF: v вниз от верха текстуры
# сначала соберём для каждого текселя 3D-точку, нормаль и веса, потом спроецируем всё разом
pts = []; nrms = []; wts = []; pix = []
for tri in I:
    a, b, c = uvp[tri]
    x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int); x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, TEX-1), min(y1, TEX-1)
    if x1 < x0 or y1 < y0: continue
    xs, ys = np.meshgrid(np.arange(x0, x1+1), np.arange(y0, y1+1)); q = np.c_[xs.ravel(), ys.ravel()].astype(float)
    T = np.array([[b[0]-a[0], c[0]-a[0]], [b[1]-a[1], c[1]-a[1]]]); det = np.linalg.det(T)
    if abs(det) < 1e-9: continue
    l12 = np.linalg.solve(T, (q-a).T).T; l0 = 1-l12.sum(1); bc = np.c_[l0, l12]
    m = (bc >= -0.02).all(1)
    if not m.any(): continue
    bc = bc[m]; q = q[m].astype(int)
    pts.append(bc@P[tri]); nrms.append(bc@nrm[tri]); wts.append(bc@np.c_[wLa[tri], wRa[tri], wLl[tri], wRl[tri]]); pix.append(q)
pts = np.concatenate(pts); nrms = np.concatenate(nrms); wts = np.concatenate(wts); pix = np.concatenate(pix)
covered[pix[:, 1], pix[:, 0]] = True
labels = np.zeros(len(pts), np.int16)
for view in ('front', 'back'):
    sel = (nrms[:, 2] >= 0) if view == 'front' else (nrms[:, 2] < 0)
    base, arms, legs = project(pts[sel], view)
    w = wts[sel]; uv = base.copy()
    for k, s in ((0, 'L'), (1, 'R')): uv += w[:, k:k+1]*(arms[s]-base)
    for k, s in ((2, 'L'), (3, 'R')): uv += w[:, k:k+1]*(legs[s]-base)
    ix = np.clip(np.round(uv[:, 0]).astype(int), 0, IW-1); iy = np.clip(np.round(uv[:, 1]).astype(int), 0, IH-1)
    labels[sel] = LAB[iy, ix]
tex_lab[pix[:, 1], pix[:, 0]] = labels

# ---------- маски мышц (с полями за края развёртки, чтобы не было швов) ----------
masks = {}
for i, k in enumerate(KEYS, 1):
    m = (tex_lab == i).astype(np.uint8)*255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))       # заделать точечные дырки
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))        # убрать одиночные точки
    pad = cv2.dilate(m, np.ones((9, 9), np.uint8)); m = np.where(covered, m, pad)
    masks[k] = cv2.GaussianBlur(m, (0, 0), 1.0)
if DEBUG:
    rgb = np.zeros((TEX, TEX, 3), np.uint8)
    for i, k in enumerate(KEYS): c = pc[pk.index(k)].astype(np.uint8); rgb[masks[k] > 127] = c
    rgb[~covered & (rgb.sum(2) == 0)] = 40
    Image.fromarray(rgb).resize((1024, 1024)).save(DEBUG)

# ---------- сетки слоя ----------
off = nrm*unit*0.005
Ppos = (P+off).astype('<f4')
g.extensionsUsed = sorted(set((g.extensionsUsed or []) + ['KHR_materials_unlit']))
g.samplers.append(Sampler(magFilter=9729, minFilter=9729, wrapS=33071, wrapT=33071)); smp = len(g.samplers)-1
prims = []
for k in KEYS:
    m = masks[k]
    if m.max() == 0: continue
    # треугольники, под которыми есть эта мышца
    tri_uv = uvp[I]; lo = np.floor(tri_uv.min(1)).astype(int).clip(0, TEX-1); hi = np.ceil(tri_uv.max(1)).astype(int).clip(0, TEX-1)
    integ = cv2.integral((m > 20).astype(np.uint8))
    cnt = integ[hi[:, 1]+1, hi[:, 0]+1]-integ[lo[:, 1], hi[:, 0]+1]-integ[hi[:, 1]+1, lo[:, 0]]+integ[lo[:, 1], lo[:, 0]]
    tri = I[cnt > 0]
    vs, inv = np.unique(tri.ravel(), return_inverse=True); tri2 = inv.reshape(-1, 3)
    # своя текстура только на область мышцы в развёртке (меньше памяти), UV пересчитываем в неё
    tuv = uvp[vs]; bx0, by0 = np.floor(tuv.min(0)).astype(int)-4; bx1, by1 = np.ceil(tuv.max(0)).astype(int)+4
    bx0, by0 = max(bx0, 0), max(by0, 0); bx1, by1 = min(bx1, TEX-1), min(by1, TEX-1)
    crop = m[by0:by1+1, bx0:bx1+1]; cw, ch = crop.shape[1], crop.shape[0]
    sc = min(1.0, 768/max(cw, ch))                     # ≤768² на мышцу: видеопамять телефона
    tw, th = max(4, int(round(cw*sc))), max(4, int(round(ch*sc)))
    crop = cv2.resize(crop, (tw, th), interpolation=cv2.INTER_AREA) if (tw, th) != (cw, ch) else crop
    uv_local = np.c_[(tuv[:, 0]+0.5-bx0)/cw, (tuv[:, 1]+0.5-by0)/ch]
    rgba = np.dstack([np.full((th, tw, 3), 255, np.uint8), crop]); buf = io.BytesIO(); Image.fromarray(rgba, 'RGBA').save(buf, 'PNG', optimize=True)
    g.images.append(GImage(bufferView=add_bytes(buf.getvalue()), mimeType='image/png')); g.textures.append(Texture(sampler=smp, source=len(g.images)-1))
    g.materials.append(Material(name='M_'+k, alphaMode='BLEND', doubleSided=False,
        pbrMetallicRoughness=PbrMetallicRoughness(baseColorFactor=[1.0, 0.3, 0.16, 0.0], baseColorTexture=TextureInfo(index=len(g.textures)-1), metallicFactor=0.0, roughnessFactor=1.0),
        extensions={'KHR_materials_unlit': {}}))
    w8 = np.round(W[vs]*255).astype(int); w8[:, 0] += 255-w8.sum(1)
    prims.append(Primitive(attributes=Attributes(POSITION=add_acc(Ppos[vs], 'VEC3', 5126, True), TEXCOORD_0=add_acc(uv_local, 'VEC2', 5126),
                                                 JOINTS_0=add_acc(J[vs].astype('u1'), 'VEC4', 5121), WEIGHTS_0=add_acc(w8.astype('u1'), 'VEC4', 5121, norm=True)),
                           indices=add_acc(tri2.astype('<u2').ravel(), 'SCALAR', 5123, target=34963), material=len(g.materials)-1, mode=4))
    print(f'{k:11s} {len(vs):6d} verts {len(tri2):6d} tris  tex {tw}x{th}  png {len(buf.getvalue())//1024} KB')
g.meshes.append(Mesh(name='MuscleOverlay', primitives=prims))
skin_node = [n for n in g.nodes if n.mesh == mi][0]
g.nodes.append(Node(name='MuscleOverlay', mesh=len(g.meshes)-1, skin=skin_node.skin))
par = [i for i, n in enumerate(g.nodes) if g.nodes.index(skin_node) in (n.children or [])][0]
g.nodes[par].children.append(len(g.nodes)-1)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save_binary(DST)
import os; print('SIZE %.2f MB' % (os.path.getsize(DST)/1e6))

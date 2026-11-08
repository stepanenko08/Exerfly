"""Собирает exercises.glb на новом персонаже (Mixamo auto-rig): текстура, снаряды, анимации.
python3 build2.py <персонаж.glb> <старая exercises.glb> <текстуры_dir> <выход.glb>"""
import sys, io, numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude/exerfly_src')
from props import Geo
from lib import *

CHAR, OLD, TEX, DST = sys.argv[1:5]
dst = GLTF2().load(CHAR); blob = bytearray(dst.binary_blob())
dst.animations = []
FLOOR = 0.025
def add_bytes(b, target=None):
    while len(blob) % 4: blob.append(0)
    off = len(blob); blob.extend(b)
    dst.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=len(b), target=target)); return len(dst.bufferViews)-1
def add_acc(arr, typ, minmax=False, comp=5126, target=None):
    arr = np.ascontiguousarray(arr, dtype={5126: '<f4', 5125: '<u4'}[comp]); bv = add_bytes(arr.tobytes(), target)
    a = Accessor(bufferView=bv, componentType=comp, count=int(arr.shape[0]), type=typ)
    if minmax:
        a.min = [float(x) for x in (arr.min(0) if arr.ndim > 1 else [arr.min()])]
        a.max = [float(x) for x in (arr.max(0) if arr.ndim > 1 else [arr.max()])]
    dst.accessors.append(a); return len(dst.accessors)-1
def mat(name, rgb, metal, rough):
    dst.materials.append(Material(name=name, pbrMetallicRoughness=PbrMetallicRoughness(baseColorFactor=list(rgb)+[1.0], metallicFactor=metal, roughnessFactor=rough)))
    return len(dst.materials)-1
def add_mesh(groups):
    prims = []
    for m, g in groups:
        P, N, I = g.arrays()
        prims.append(Primitive(attributes=Attributes(POSITION=add_acc(P, 'VEC3', True, target=34962), NORMAL=add_acc(N, 'VEC3', target=34962)),
                               indices=add_acc(I, 'SCALAR', False, 5125, 34963), material=m, mode=4))
    dst.meshes.append(Mesh(name='mesh', primitives=prims)); return len(dst.meshes)-1
HID = [1e-4]*3
def add_node(name, mesh=None, t=(0, 0, 0), children=None, top=True):
    dst.nodes.append(Node(name=name, mesh=mesh, translation=list(map(float, t)), scale=HID if top else None, children=children or []))
    i = len(dst.nodes)-1
    if top: dst.scenes[dst.scene or 0].nodes.append(i)
    return i
mid = {}

# ---------- подготовка персонажа ----------
rig = Rig(dst)
ROOT = 0
hips_rest = rig.world({}, 0)('Hips')[1, 3]
S_ROOT = 0.9606/hips_rest                       # рост как у старого персонажа (бёдра на 0.96 м)
dst.nodes[ROOT].scale = [float(S_ROOT)]*3
JOINTS = {short(dst.nodes[j].name): j for j in dst.skins[0].joints}
def img_bytes(path, size, fmt='JPEG', q=88):
    im = Image.open(path).convert('RGB')
    if im.size[0] > size: im = im.resize((size, size), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, fmt, quality=q, optimize=True); return buf.getvalue()
from pygltflib import Image as GImage, Texture, TextureInfo, NormalMaterialTexture, Sampler
dst.samplers = [Sampler(magFilter=9729, minFilter=9987, wrapS=10497, wrapT=10497)]
def add_tex(data):
    dst.images.append(GImage(bufferView=add_bytes(data), mimeType='image/jpeg'))
    dst.textures.append(Texture(sampler=0, source=len(dst.images)-1)); return len(dst.textures)-1
t_col = add_tex(img_bytes(TEX+'/texture_pbr_20250901.png', 2048))
t_nrm = add_tex(img_bytes(TEX+'/texture_pbr_20250901_normal.png', 2048, q=90))
m = dst.materials[0]; m.name = 'Athlete'
m.pbrMetallicRoughness = PbrMetallicRoughness(baseColorFactor=[1, 1, 1, 1], baseColorTexture=TextureInfo(index=t_col), metallicFactor=0.0, roughnessFactor=0.78)
m.normalTexture = NormalMaterialTexture(index=t_nrm, scale=1.0); m.extras = {}


def sphere(g, c, r, seg=24, rings=14):
    c = np.asarray(c, float); P = []; N = []; I = []
    for i in range(rings+1):
        th = np.pi*i/rings
        for j in range(seg+1):
            ph = 2*np.pi*j/seg; n = np.array([np.sin(th)*np.cos(ph), np.cos(th), np.sin(th)*np.sin(ph)]); P.append(c+r*n); N.append(n)
    for i in range(rings):
        for j in range(seg):
            a = i*(seg+1)+j; b = a+seg+1; I += [a, b, a+1, a+1, b, b+1]
    g._add(P, N, I)

# ---------- снаряды ----------
M_IRON = mat('Cast iron', (0.035, 0.035, 0.04), 0.6, 0.55)
M_RUBBER = mat('Rubber', (0.02, 0.02, 0.022), 0.0, 0.9)
M_BELT = mat('Belt', (0.03, 0.03, 0.033), 0.0, 0.85)
M_STRIPE = mat('Belt stripe', (0.10, 0.10, 0.11), 0.0, 0.8)
M_FRAME = mat('Treadmill frame', (0.045, 0.048, 0.055), 0.35, 0.45)
M_ACCENT = mat('Accent', (0.95, 0.27, 0.13), 0.1, 0.5)
M_SCREEN = mat('Screen', (0.01, 0.015, 0.02), 0.2, 0.2)


# ---------- снаряды из старой модели (скамья, штанга, турник) ----------
old = GLTF2().load(OLD); oblob = old.binary_blob()
def oacc(i):
    a = old.accessors[i]; bv = old.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]; dt = {5126: '<f4', 5125: '<u4', 5123: '<u2'}[a.componentType]
    v = np.frombuffer(oblob, dtype=dt, count=a.count*n, offset=bv.byteOffset+(a.byteOffset or 0))
    return v.reshape(a.count, n) if n > 1 else v
omat = {}
def copy_mat(i):
    if i in omat: return omat[i]
    m = old.materials[i]; p = m.pbrMetallicRoughness
    omat[i] = mat(m.name, p.baseColorFactor[:3], p.metallicFactor, p.roughnessFactor); mid[m.name] = omat[i]; return omat[i]
def copy_node(name):
    on = [n for n in old.nodes if n.name == name][0]; om = old.meshes[on.mesh]; prims = []
    for p in om.primitives:
        prims.append(Primitive(attributes=Attributes(POSITION=add_acc(oacc(p.attributes.POSITION), 'VEC3', True, target=34962),
                                                     NORMAL=add_acc(oacc(p.attributes.NORMAL), 'VEC3', target=34962)),
                               indices=add_acc(oacc(p.indices).astype('<u4'), 'SCALAR', False, 5125, 34963), material=copy_mat(p.material), mode=4))
    dst.meshes.append(Mesh(name=name, primitives=prims))
    return add_node(name, len(dst.meshes)-1, on.translation or (0, 0, 0))
BENCH = copy_node('Bench'); BAR = copy_node('Barbell'); PULL = copy_node('PullupBar')

# гантель: ось X, центр = хват
hd = Geo(); hd.cyl([0, 0, 0], [1, 0, 0], 0.015, 0.16)
hh = Geo()
for sg in (-1, 1): hh.cyl([sg*0.11, 0, 0], [1, 0, 0], 0.048, 0.07, seg=6)
DB = [add_node(n, add_mesh([(mid['Chrome'], hd), (M_RUBBER, hh)])) for n in ('DumbbellL', 'DumbbellR')]

# гиря: центр ручки = хват, тело ниже по -Y
kb_b = Geo(); sphere(kb_b, [0, -0.125, 0], 0.088)
kb_h = Geo(); kb_h.cyl([0, 0, 0], [1, 0, 0], 0.015, 0.13)
for sg in (-1, 1): kb_h.cyl([sg*0.065, -0.045, 0], [0, 1, 0], 0.015, 0.09)
KB = add_node('Kettlebell', add_mesh([(M_IRON, kb_b), (M_IRON, kb_h)]))

# беговая дорожка: бег по +Z, верх полотна на DECK
DECK = 0.17; BX = 0.30; Z0, Z1 = -0.95, 0.85
M_ALU = mat('Aluminium', (0.55, 0.57, 0.60), 0.9, 0.3)
M_GLASS = mat('Display', (0.02, 0.025, 0.03), 0.3, 0.08)
def obox(g, c, size, rx=0.0):
    """Коробка с центром c и размерами size, наклонённая на rx градусов вокруг X."""
    t = Geo(); h = np.asarray(size, float)/2; t.box(-h[0], h[0], -h[1], h[1], -h[2], h[2])
    a = np.radians(rx); R = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    off = 0
    for P, N, I in zip(t.P, t.N, t.I):
        g._add(P @ R.T + np.asarray(c, float), N @ R.T, I - off); off += len(P)
def tube(g, p0, p1, r, seg=20):
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float); d = p1-p0
    g.cyl((p0+p1)/2, d, r, np.linalg.norm(d), seg=seg)
top = FLOOR+DECK
tm = Geo(); tf = Geo(); ta = Geo(); ts = Geo(); tal = Geo(); tr = Geo(); tg = Geo()
tm.box(-BX, BX, FLOOR+0.03, top-0.004, Z0, Z1)                                         # полотно
for x in (-1, 1):
    tf.box(x*BX, x*(BX+0.10), FLOOR+0.03, top+0.004, Z0-0.04, Z1+0.06)                # корпус боковин
    tal.box(x*(BX+0.005), x*(BX+0.105), top+0.004, top+0.016, Z0-0.02, Z1+0.04)        # алюминиевые подножки
    ta.box(x*(BX+0.098), x*(BX+0.104), top-0.045, top-0.025, Z0+0.10, Z1-0.10)         # оранжевая линия сбоку
    for z in (Z0+0.02, Z1+0.10): tr.cyl([x*(BX+0.06), FLOOR+0.015, z], [0, 1, 0], 0.03, 0.03)   # ножки
tr.cyl([0, top-0.045, Z0+0.005], [1, 0, 0], 0.045, 2*BX)                              # задний ролик
obox(tf, [0, FLOOR+0.06, Z0-0.07], [2*BX+0.20, 0.07, 0.10])                            # задняя крышка
tf.cyl([0, FLOOR+0.095, Z0-0.07], [1, 0, 0], 0.035, 2*BX+0.20)
# кожух мотора: скошенный спереди
obox(tf, [0, top+0.03, Z1+0.16], [2*BX+0.20, 0.16, 0.26])
obox(tf, [0, top+0.07, Z1+0.33], [2*BX+0.20, 0.10, 0.16], rx=-35)
ta.box(-BX-0.101, BX+0.101, top+0.075, top+0.09, Z1+0.04, Z1+0.29)                     # полоса на кожухе
# стойки: наклонены назад к пользователю
for x in (-1, 1):
    tube(tf, [x*0.39, top+0.08, Z1+0.24], [x*0.37, FLOOR+1.15, Z1+0.10], 0.032)
    # поручни-петли
    tube(tf, [x*0.37, FLOOR+1.02, Z1+0.12], [x*0.40, FLOOR+1.02, Z1-0.40], 0.018)
    tube(tf, [x*0.40, FLOOR+1.02, Z1-0.40], [x*0.40, FLOOR+0.94, Z1-0.48], 0.018)
    tube(tg, [x*0.40, FLOOR+1.02, Z1-0.10], [x*0.40, FLOOR+1.02, Z1-0.34], 0.024)       # резиновые накладки
    tube(tal, [x*0.37, FLOOR+1.02, Z1+0.04], [x*0.38, FLOOR+1.02, Z1-0.08], 0.0245)     # датчики пульса
tube(tf, [-0.37, FLOOR+0.98, Z1+0.10], [0.37, FLOOR+0.98, Z1+0.10], 0.018)             # передний поручень
# консоль: панель, наклонённая к бегуну
obox(tf, [0, FLOOR+1.24, Z1+0.10], [0.84, 0.30, 0.07], rx=-28)
obox(ts, [0, FLOOR+1.255, Z1+0.068], [0.46, 0.17, 0.012], rx=-28)                      # экран
obox(ta, [0, FLOOR+1.215, Z1+0.050], [0.30, 0.012, 0.004], rx=-28)                     # строка на экране
obox(ta, [-0.10, FLOOR+1.29, Z1+0.078], [0.10, 0.03, 0.004], rx=-28)
obox(ta, [0.10, FLOOR+1.29, Z1+0.078], [0.10, 0.03, 0.004], rx=-28)
for i, x in enumerate((-0.34, -0.30, 0.30, 0.34)):
    obox(tg if i % 3 else ta, [x, FLOOR+1.20, Z1+0.055], [0.03, 0.03, 0.02], rx=-28)    # кнопки
for x in (-1, 1): tr.cyl([x*0.30, FLOOR+1.11, Z1+0.10], [0, 1, 0], 0.04, 0.06)          # подстаканники
TREAD = add_node('Treadmill', add_mesh([(M_BELT, tm), (M_FRAME, tf), (M_ACCENT, ta), (M_GLASS, ts), (M_ALU, tal), (M_RUBBER, tr), (M_RUBBER, tg)]))
# полосы на полотне (двигаются назад и повторяются)
SP = 0.15; stripes = Geo(); zs = np.arange(Z0+0.03, Z1-0.02, SP)
for z in zs: stripes.box(-BX+0.01, BX-0.01, FLOOR+DECK-0.005, FLOOR+DECK-0.002, z, z+0.025)
STRIPES = add_node('BeltStripes', add_mesh([(M_STRIPE, stripes)]))


# ---------- клипы ----------
def look(xdir, up=(0, 1, 0)):
    """Кватернион поворота, переводящий локальную X в xdir, а Y — как можно ближе к up."""
    x = xdir/np.linalg.norm(xdir); u = np.asarray(up, float); z = np.cross(x, u)
    if np.linalg.norm(z) < 1e-6: z = np.cross(x, [0, 0, 1])
    z /= np.linalg.norm(z); y = np.cross(z, x)
    return mat2q(np.stack([x, y, z], 1))
def fix_sign(q):
    q = np.array(q)
    for k in range(1, len(q)):
        if np.dot(q[k], q[k-1]) < 0: q[k] = -q[k]
    return q

def write(name, clip, N, props):
    times = np.arange(N)/FPS; T = times[-1]
    an = Animation(name=name, channels=[], samplers=[])
    tf_ = add_acc(times, 'SCALAR', True); tc = add_acc(np.array([0.0, T]), 'SCALAR', True)
    def ch(node, path, inp, out):
        an.samplers.append(AnimationSampler(input=inp, output=out, interpolation='LINEAR'))
        an.channels.append(AnimationChannel(sampler=len(an.samplers)-1, target=AnimationChannelTarget(node=node, path=path)))
    for bone, d in clip.items():
        if bone not in JOINTS: continue
        for path, v in d.items():
            if path == 'scale': continue
            v = v[:N]; v = fix_sign(v) if path == 'rotation' else v
            ch(JOINTS[bone], path, tf_, add_acc(v, 'VEC4' if path == 'rotation' else 'VEC3'))
    for node, path, v in props:
        if path == 'show': ch(node, 'scale', tc, add_acc(np.array([[1, 1, 1.], [1, 1, 1.]]), 'VEC3'))
        elif path == 'custom': ch(node, 'translation', add_acc(v[0], 'SCALAR', True), add_acc(v[1], 'VEC3'))
        else: ch(node, path, tf_, add_acc(np.array(v), 'VEC4' if path == 'rotation' else 'VEC3'))
    dst.animations.append(an)
    print('  +', name, f'{T:.2f}s', len(an.channels), 'channels')

GRIP = ['Index1', 'Index1', 'Index2']
def palm_axis(side):
    R = rig.world({}, 0)(side+'Hand')[:3, :3]
    k = int(np.argmax(np.abs(R[2]))); return k, np.sign(R[2, k])
AXL, AXR = palm_axis('Left'), palm_axis('Right')
def grips(clip, N):
    out = []
    for f in range(N):
        W = rig.world(clip, f); p = lambda n: W(n)[:3, 3]
        # точка хвата = центр сжатого кулака (по фалангам пальцев)
        fist = lambda sd: np.mean([p(sd+'Hand'+f) for f in GRIP], 0)
        gl = fist('Left'); gr = fist('Right')
        out.append(dict(gl=gl, gr=gr, al=W('LeftHand')[:3, AXL[0]]*AXL[1], ar=W('RightHand')[:3, AXR[0]]*AXR[1],
                        sh=(p('LeftArm')+p('RightArm'))/2, Wl=W('LeftHand')[:3, :3], Wr=W('RightHand')[:3, :3]))
    return out


# ---------- перенос анимаций ----------
OLDR = {short(n.name): np.array(n.rotation or [0, 0, 0, 1], float) for n in old.nodes if n.name}
NEWR = {k: np.array(dst.nodes[j].rotation or [0, 0, 0, 1], float) for k, j in JOINTS.items()}
def qinv(q): return np.array([-q[0], -q[1], -q[2], q[3]])
def fit(clip):
    """Клип в пространстве Mixamo (Y вверх, метры, риг Ch28) → новый персонаж."""
    clip['Hips']['translation'] = clip['Hips']['translation']/S_ROOT
    for k in list(clip):
        if 'Index' in k or 'Thumb' in k or 'Middle' in k or 'Ring' in k or 'Pinky' in k: del clip[k]
        elif k != 'Hips': clip[k] = {'rotation': clip[k]['rotation']} if 'rotation' in clip[k] else {}
    return clip

# палец-«варежка»: сгибаем вокруг оси ладони на заданный угол (кулак для снарядов, лёгкий сгиб без них)
def axis_angle(a, deg):
    a = a/np.linalg.norm(a); h = np.radians(deg)/2; return np.r_[a*np.sin(h), np.cos(h)]
REST = rig.world({}, 0)
PALM = {}
for side in ('Left', 'Right'):
    hand = REST(side+'Hand')[:3, 3]; tip = REST(side+'HandIndex3')[:3, 3]; d = (tip-hand)/np.linalg.norm(tip-hand)
    n = np.array([0, -1.0, 0]); n = n-np.dot(n, d)*d; PALM[side] = n/np.linalg.norm(n)
def curl(clip, N, angles):
    for side in ('Left', 'Right'):
        Rh = REST(side+'Hand')[:3, :3]
        palm = -Rh[:, 2] if False else None
        for i, ang in zip((1, 2, 3), angles):
            b = f'{side}HandIndex{i}'
            if b not in JOINTS: continue
            Rb = REST(b)[:3, :3]
            d = REST(f'{side}HandIndex{i+1}')[:3, 3]-REST(b)[:3, 3] if f'{side}HandIndex{i+1}' in rig.idx else Rb[:, 1]
            d = d/np.linalg.norm(d)
            n = PALM[side]                                   # нормаль ладони в мировых координатах (покой)
            ax_w = np.cross(d, n); ax_b = Rb.T @ ax_w        # ось сгиба в системе кости
            q = qmul(NEWR[b], axis_angle(ax_b, ang))
            clip[b] = {'rotation': np.repeat(q[None], N, 0)}
    return clip
R_FWD = np.array([np.sqrt(.5), 0, 0, np.sqrt(.5)])
def old_clip(name):
    """Анимация из старой exercises.glb (Hips в пространстве Armature, см) → клип Y-up."""
    a = [x for x in old.animations if x.name == name][0]; clip = {}; N = 0
    for ch in a.channels:
        nm = short(old.nodes[ch.target.node].name)
        if not old.nodes[ch.target.node].name or not old.nodes[ch.target.node].name.startswith('mixamorig'): continue
        smp = a.samplers[ch.sampler]; t = oacc(smp.input); v = oacc(smp.output).astype(float)
        times = np.arange(int(round(t[-1]*FPS))+1)/FPS
        v = np.stack([np.interp(times, t, v[:, i]) for i in range(v.shape[1])], 1)
        if ch.target.path == 'rotation': v /= np.linalg.norm(v, axis=1, keepdims=True)
        clip.setdefault(nm, {})[ch.target.path] = v; N = max(N, len(v))
    for d in clip.values():
        for k in d:
            if len(d[k]) < N: d[k] = np.repeat(d[k][-1:], N, 0) if len(d[k]) == 2 else d[k]
    h = clip['Hips']; h['rotation'] = qmul(np.broadcast_to(R_FWD, h['rotation'].shape), h['rotation'])
    t = h['translation']/100; h['translation'] = np.stack([t[:, 0], -t[:, 2], t[:, 1]], 1)
    return fit(clip), N

# выравнивание: убрать боковой наклон головы и перекос плеч, записанные в мокапе
def rot_between(a, b):
    a = a/np.linalg.norm(a); b = b/np.linalg.norm(b); v = np.cross(a, b); c = np.dot(a, b)
    if np.linalg.norm(v) < 1e-9: return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3)+vx+vx@vx*(1/(1+c))
def wrot(M):
    R = M[:3, :3]; return R/np.linalg.norm(R, axis=0)
def set_world_delta(clip, f, bone, Rd, W):
    """Повернуть кость на мировой поворот Rd (остальное тело ниже по иерархии следует за ней)."""
    P = wrot(W(short(dst.nodes[rig.parent[rig.idx[bone]]].name)))
    Rw = wrot(W(bone)); Rl = P.T @ Rd @ Rw
    clip[bone]['rotation'][f] = mat2q(Rl)
def level(clip, N, shoulders=True):
    for bone in ('Spine2', 'Head'):
        if bone in clip: clip[bone]['rotation'] = np.array(clip[bone]['rotation'], float)
    for f in range(N):
        if shoulders:
            W = rig.world(clip, f); sh = W('LeftArm')[:3, 3]-W('RightArm')[:3, 3]
            ang = np.arctan2(sh[1], np.hypot(sh[0], sh[2]))
            fwd = np.cross(sh, [0, 1, 0]); fwd /= np.linalg.norm(fwd)
            c, s_ = np.cos(-ang), np.sin(-ang); K = np.array([[0, -fwd[2], fwd[1]], [fwd[2], 0, -fwd[0]], [-fwd[1], fwd[0], 0]])
            set_world_delta(clip, f, 'Spine2', np.eye(3)+s_*K+(1-c)*K@K, W)
        W = rig.world(clip, f); v = W('HeadTop_End')[:3, 3]-W('Neck')[:3, 3]
        sh = W('LeftArm')[:3, 3]-W('RightArm')[:3, 3]; side = sh/np.linalg.norm(sh)
        v2 = v-np.dot(v, side)*side                     # убрать наклон к плечу, кивок вперёд/назад оставить
        set_world_delta(clip, f, 'Head', rot_between(v, v2), W)
    return clip

def load(fname, a=0, b=None, pingpong=False):
    clip, N = read_clip('glb/'+fname); fit(clip)
    b = N if b is None else b
    for d in clip.values():
        for k in d:
            v = d[k][a:b]
            d[k] = np.concatenate([v, v[-2::-1]]) if pingpong else v
    return clip, (2*(b-a)-1 if pingpong else b-a)

def barbell_props(G, drop=0.0):
    t = []; r = []
    for g in G:
        c = (g['gl']+g['gr'])/2; c[1] -= drop; t.append(c); r.append(look(g['gr']-g['gl']))
    return [(BAR, 'show', None), (BAR, 'translation', t), (BAR, 'rotation', fix_sign(r))]


FIST, RELAX, FLAT = (70, 85, 55), (15, 20, 10), (5, 5, 5)
import os
PROC_ONLY = bool(os.environ.get('PROC_ONLY'))
for name, hand in ([] if PROC_ONLY else (('pushup', FLAT), ('squat', RELAX), ('squat_arms_forward', RELAX))):
    clip, N = old_clip(name); curl(clip, N, hand); level(clip, N); write(name, clip, N, [])
if not PROC_ONLY:
    clip, N = old_clip('bench_press'); curl(clip, N, FIST); level(clip, N); G = grips(clip, N)
    write('bench_press', clip, N, [(BENCH, 'show', None)] + barbell_props(G))
    clip, N = old_clip('pullup'); curl(clip, N, FIST); level(clip, N); G = grips(clip, N)
    gm = np.mean([(g['gl']+g['gr'])/2 for g in G], 0)
    pb_pos = oacc(old.meshes[[n for n in old.nodes if n.name == 'PullupBar'][0].mesh].primitives[0].attributes.POSITION)
    BY = pb_pos[:, 1].max()-0.25
    spread = np.ptp(np.array([(g['gl']+g['gr'])/2 for g in G]), 0)
    print('  pullup hands spread (m):', spread.round(3))
    dst.nodes[PULL].translation = [0.0, float(gm[1]-BY), float(gm[2])]
    write('pullup', clip, N, [(PULL, 'show', None)])

    CLIPS = __import__('json').loads(open('clips.json').read())
    for c in CLIPS:
        clip, N = load(c['file'], c.get('from', 0), c.get('to'), c.get('pingpong', False))
        curl(clip, N, FIST if c['prop'] in ('barbell', 'dumbbells', 'kettlebell') else FLAT if c['name'] == 'plank' else RELAX)
        level(clip, N, shoulders=c.get('symmetric', True))
        G = grips(clip, N) if c['prop'] != 'none' and c['prop'] != 'treadmill' else None
        props = []
        if c['prop'] == 'barbell': props = barbell_props(G, c.get('drop', 0))
        elif c['prop'] == 'dumbbells':
            for node, side in ((DB[0], 'l'), (DB[1], 'r')):
                t = [g['g'+side] for g in G]; r = fix_sign([look(g['a'+side]) for g in G])
                props += [(node, 'show', None), (node, 'translation', t), (node, 'rotation', r)]
        elif c['prop'] == 'kettlebell':
            t = []; r = []
            for g in G:
                h = (g['gl']+g['gr'])/2; down = h-g['sh']; down /= np.linalg.norm(down)
                t.append(h); r.append(look(g['gr']-g['gl'], -down))
            props = [(KB, 'show', None), (KB, 'translation', t), (KB, 'rotation', fix_sign(r))]
        elif c['prop'] == 'treadmill':
            h = clip['Hips']['translation']          # Y вверх, единицы корня (м / S_ROOT)
            drift = (h[-1, 2]-h[0, 2])*np.arange(N)/(N-1)
            h[:, 2] -= drift + h[0, 2]               # убрать продвижение вперёд
            h[:, 1] += DECK/S_ROOT                    # поднять на полотно
            speed = drift[-1]*S_ROOT/((N-1)/FPS)      # м/с
            per = SP/speed; T = (N-1)/FPS; k = max(1, round(T/per)); per = T/k
            times = []; vals = []
            for i in range(k):
                times += [i*per, (i+1)*per-1e-4]; vals += [[0, 0, 0], [0, 0, -SP]]
            times.append(T); vals.append([0, 0, 0])
            props = [(TREAD, 'show', None), (STRIPES, 'show', None), (STRIPES, 'custom', (np.array(times), np.array(vals, float)))]
            print('  speed %.2f m/s' % speed)
        write(c['name'], clip, N, props)



exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proc.py')).read())

# ---------- сохранение ----------
dst.buffers[0].byteLength = len(blob); dst.set_binary_blob(bytes(blob)); dst.save_binary(DST)
import os; print('SIZE %.2f MB' % (os.path.getsize(DST)/1e6), [a.name for a in dst.animations])

# Процедурные анимации: позы задаются параметрами (положение таза, наклон корпуса,
# цели для кистей и стоп), между ключами — плавная интерполяция, конечности — IK.
# Выполняется внутри build2.py (exec), поэтому видит dst, rig, REST, JOINTS, write, grips, curl ...
import numpy as np

def nz(v): v = np.asarray(v, float); return v/np.linalg.norm(v)
def Rax(axis, deg):
    a = nz(axis); t = np.radians(deg); K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3)+np.sin(t)*K+(1-np.cos(t))*K@K
Rx = lambda d: Rax([1, 0, 0], d); Ry = lambda d: Rax([0, 1, 0], d); Rz = lambda d: Rax([0, 0, 1], d)
def euler(p=0, y=0, r=0): return Ry(y) @ Rx(p) @ Rz(r)
def frame(d, h):
    d = nz(d); h = np.asarray(h, float); h = nz(h-np.dot(h, d)*d); return np.stack([d, h, np.cross(d, h)], 1)
def signed_angle(a, b, axis):
    axis = nz(axis); a = a-np.dot(a, axis)*axis; b = b-np.dot(b, axis)*axis
    return np.degrees(np.arctan2(np.dot(np.cross(a, b), axis), np.dot(a, b)))

RW = {b: wrot(REST(b)) for b in JOINTS}; RP = {b: REST(b)[:3, 3].copy() for b in JOINTS}
PAR = {b: short(dst.nodes[rig.parent[rig.idx[b]]].name) for b in JOINTS}
def rwp(b): p = PAR[b]; return RW[p] if p in RW else np.eye(3)

LIMB = {}
for sd, sg in (('Left', 1), ('Right', -1)):
    for kind, (A, B, C), pole in (('arm', ('Arm', 'ForeArm', 'Hand'), (0, 0, -1)), ('leg', ('UpLeg', 'Leg', 'Foot'), (0, 0, 1))):
        a_, b_, c_ = sd+A, sd+B, sd+C
        u = nz(RP[b_]-RP[a_]); l = nz(RP[c_]-RP[b_]); pole = np.array(pole, float)
        LIMB[(sd, kind)] = dict(bones=(a_, b_, c_), la=np.linalg.norm(RP[b_]-RP[a_]), lb=np.linalg.norm(RP[c_]-RP[b_]),
                                Fu=frame(u, np.cross(pole, u)), Fl=frame(l, np.cross(pole, l)))
BALL_Y = (RP['LeftToeBase'][1]+RP['RightToeBase'][1])/2
ARM_LEN = LIMB[('Left', 'arm')]['la']+LIMB[('Left', 'arm')]['lb']
print('  proc: arm %.3f  leg %.3f  ball_y %.3f  hips %.3f' % (ARM_LEN, LIMB[('Left', 'leg')]['la']+LIMB[('Left', 'leg')]['lb'], BALL_Y, RP['Hips'][1]))

WARN = []
TW_PREV = {}
def ik(S, T, pole, la, lb, tag=''):
    d = T-S; L = np.linalg.norm(d); u = d/L
    if L > (la+lb)*1.002: WARN.append((tag, round(L-(la+lb), 3)))
    L = np.clip(L, abs(la-lb)+1e-4, (la+lb)*0.9995)
    v = np.asarray(pole, float); v = v-np.dot(v, u)*u
    if np.linalg.norm(v) < 1e-6: v = np.cross(u, [1, 0, 0])
    v = nz(v)
    ca = (la*la+L*L-lb*lb)/(2*la*L); sa = np.sqrt(max(0, 1-ca*ca))
    M = S+la*(ca*u+sa*v); T2 = S+u*L
    return nz(M-S), nz(T2-M), v

class Pose:
    """Сборка одной позы → локальные кватернионы костей."""
    def __init__(s):
        s.D = {}
    def local(s, b):
        Dp = s.D.get(PAR[b], np.eye(3)); Db = s.D[b]
        return rwp(b).T @ Dp.T @ Db @ RW[b]
    def clip(s, hips):
        c = {b: {'rotation': mat2q(s.local(b))[None]} for b in s.D}
        c.setdefault('Hips', {})['translation'] = (np.asarray(hips, float)/S_ROOT)[None]
        return c

def _palm_rest(sd):
    ax = AXL if sd == 'Left' else AXR
    T = RW[sd+'Hand'][:, ax[0]]*ax[1]                              # ось хвата (поперёк кулака)
    Hd = nz(RP[sd+'HandIndex1']-RP[sd+'Hand'])
    n = nz(np.cross(Hd, T)); n = n if np.dot(n, PALM[sd]) > 0 else -n
    return n
PALM_REST = {sd: _palm_rest(sd) for sd in ('Left', 'Right')}

def solve(P):
    """P: параметры позы (см. ключи ниже). Возвращает (clip одного кадра, pose)."""
    po = Pose(); D = po.D
    Rp = euler(*P.get('pelvis', (0, 0, 0)))
    sp = P.get('spine', (0, 0, 0)); Rs = euler(sp[0]/3, sp[1]/3, sp[2]/3)
    D['Hips'] = Rp; D['Spine'] = Rp@Rs; D['Spine1'] = D['Spine']@Rs; D['Spine2'] = D['Spine1']@Rs
    D['Neck'] = D['Spine2']@Rx(P.get('neck', 0)); D['Head'] = D['Neck']@Rx(P.get('head', 0))
    cl = P.get('clav', (0, 0))
    D['LeftShoulder'] = D['Spine2']@Rz(cl[0]); D['RightShoulder'] = D['Spine2']@Rz(-cl[1])
    hips = np.asarray(P['hips'], float)
    # ноги: положение подушечки стопы, подъём пятки, разворот носка
    for sd in ('Left', 'Right'):
        f = P['foot'+sd[0]]
        ball = np.array([f[0], BALL_Y+(f[3] if len(f) > 3 else 0), f[1]], float)
        heel = f[2] if len(f) >= 3 else 0; yaw = P.get('toe', 8)*(1 if sd == 'Left' else -1)
        Df = Ry(yaw)@Rx(heel); D[sd+'Foot'] = Df; D[sd+'ToeBase'] = Ry(yaw)
        ankle = ball - Df@(RP[sd+'ToeBase']-RP[sd+'Foot'])
        P['_ankle'+sd[0]] = ankle
    W = rig.world(po.clip(hips), 0)
    for sd in ('Left', 'Right'):
        Lm = LIMB[(sd, 'leg')]; a_, b_, c_ = Lm['bones']
        S = W(a_)[:3, 3]; T = P['_ankle'+sd[0]]
        kp = P.get('knee'+sd[0], None)
        if kp is None:
            kp = Ry(P.get('toe', 8)*(1 if sd == 'Left' else -1)+P.get('kneeout', 0)*(1 if sd == 'Left' else -1))@np.array([0, 0, 1.0])
        u, l, v = ik(S, T, kp, Lm['la'], Lm['lb'], 'leg')
        h = np.cross(v, u)
        D[a_] = frame(u, h)@Lm['Fu'].T; D[b_] = frame(l, h)@Lm['Fl'].T
    # руки
    W = rig.world(po.clip(hips), 0)
    for sd in ('Left', 'Right'):
        k = sd[0]; Lm = LIMB[(sd, 'arm')]; a_, b_, c_ = Lm['bones']
        if 'hand'+k not in P: continue
        S = W(a_)[:3, 3]; T = np.asarray(P['hand'+k], float)
        u, l, v = ik(S, T, P['elbow'+k], Lm['la'], Lm['lb'], 'arm')
        h = np.cross(v, u)
        Du = frame(u, h)@Lm['Fu'].T; Dl = frame(l, h)@Lm['Fl'].T
        tw = 0
        if 'axis'+k in P:
            # ось хвата (поперёк кулака) — вдоль грифа/рукояти; ладонь лишь выбирает из двух вариантов
            ax_ = AXL if sd == 'Left' else AXR; Tw = Dl@(RW[sd+'Hand'][:, ax_[0]]*ax_[1]); av = np.asarray(P['axis'+k], float)
            cands = [signed_angle(Tw, av, l), signed_angle(Tw, -av, l)]
            hint = np.asarray(P.get('palm'+k, -l), float)
            prev = TW_PREV.get(k)
            if prev is None:
                tw = max(cands, key=lambda t_: np.dot(Rax(l, t_)@Dl@PALM_REST[sd], hint))
            else:                                                      # непрерывно: ближайший к прошлому кадру
                cands = [c_+360*np.round((prev-c_)/360) for c_ in cands]
                tw = min(cands, key=lambda t_: abs(t_-prev))
            TW_PREV[k] = tw
        elif 'palm'+k in P:
            tw = signed_angle(Dl@PALM_REST[sd], np.asarray(P['palm'+k], float), l)
            prev = TW_PREV.get(k)
            if prev is not None: tw += 360*np.round((prev-tw)/360)        # без скачка через ±180°
            TW_PREV[k] = tw
        tw += P.get('twist'+k, 0)
        D[a_] = Du; D[b_] = Rax(l, tw*0.5)@Dl
        Dh = Rax(l, tw)@Dl
        pn = Dh@PALM_REST[sd]; fl = P.get('wrist'+k, 0)
        if fl: Dh = Rax(np.cross(l, pn), fl)@Dh
        D[c_] = Dh
    return po.clip(hips), po

FIST_OFF = {}
def solve_grip(P, iters=10):
    """Как solve, но P['gripL'/'gripR'] — где должен быть центр кулака (а не запястье)."""
    P = dict(P)
    for k in 'LR':
        if 'grip'+k in P: P['hand'+k] = np.asarray(P['grip'+k], float) - FIST_OFF.get(k, 0)
    n0 = len(WARN)
    for _ in range(iters):
        c, po = solve(P); W = rig.world(c, 0)
        for k, sd in (('L', 'Left'), ('R', 'Right')):
            if 'grip'+k not in P: continue
            fist = np.mean([W(sd+'Hand'+g)[:3, 3] for g in GRIP], 0); wr = W(sd+'Hand')[:3, 3]
            new = np.asarray(P['grip'+k], float)-(fist-wr)
            P['hand'+k] = new if _ == 0 else P['hand'+k]*0.4+new*0.6     # с затуханием, чтобы не раскачивалось
    del WARN[n0:]
    return solve(P)

def ease(x): return 0.5-0.5*np.cos(np.pi*x)
def lerp(a, b, t):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)): return a+(b-a)*t
    return tuple(np.asarray(a, float)+(np.asarray(b, float)-np.asarray(a, float))*t)

def animate(name, keys, props_fn=None, hand=None, grip=False, fn=None):
    """keys: [(время, {параметры})]; недостающие параметры наследуются от предыдущего ключа.
    Последний ключ должен совпадать с первым (петля)."""
    full = []; cur = {}
    for t, p in keys:
        cur = {**cur, **p}; full.append((t, dict(cur)))
    T = full[-1][0]; N = int(round(T*FPS))+1
    frames = []; TW_PREV.clear()
    for f in range(N):
        t = f/FPS; i = max(j for j in range(len(full)) if full[j][0] <= t+1e-9); i = min(i, len(full)-2)
        (t0, a), (t1, b) = full[i], full[i+1]
        x = ease((t-t0)/(t1-t0)) if t1 > t0 else 0
        P = {k: lerp(a[k], b[k], x) if k in b else a[k] for k in a}
        for k in P:
            if isinstance(P[k], tuple) and len(P[k]) == 3 and k.startswith(('hand', 'grip', 'elbow', 'palm', 'hips')): P[k] = np.array(P[k])
        if fn: P = fn(P)
        c, _ = (solve_grip if grip else solve)(P); frames.append(c)
    clip = {}
    for b in frames[0]:
        clip[b] = {k: np.concatenate([fr[b][k] for fr in frames]) for k in frames[0][b]}
    curl(clip, N, hand or FIST)
    props = props_fn(clip, N) if props_fn else []
    write(name, clip, N, props)
    if WARN: print('   ! reach exceeded', {k: (sum(1 for w in WARN if w[0] == k), max([w[1] for w in WARN if w[0] == k], default=0)) for k in ('leg', 'arm')})
    WARN.clear()
    return clip, N

def bar_track(clip, N):
    return barbell_props(grips(clip, N))
def dumbbell_track(clip, N):
    G = grips(clip, N); out = []
    for node, side in ((DB[0], 'l'), (DB[1], 'r')):
        t = [g['g'+side] for g in G]; r = fix_sign([look(g['a'+side]) for g in G])
        out += [(node, 'show', None), (node, 'translation', t), (node, 'rotation', r)]
    return out

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proc_ex.py')).read())
import os as _o
if _o.environ.get('DBG'): exec(open(_o.environ['DBG']).read())

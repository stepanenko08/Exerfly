# Упражнения, собранные из поз (см. proc.py)
import numpy as np

def mid_shoulder_rel(P):
    """Середина плечевых суставов относительно таза для данного наклона корпуса."""
    Q = {k: v for k, v in P.items() if not k.startswith(('hand', 'grip'))}
    Q['hips'] = np.zeros(3); Q.setdefault('footL', (0.12, 0.0)); Q.setdefault('footR', (-0.12, 0.0))
    n = len(WARN); c, _ = solve(Q); W = rig.world(c, 0); del WARN[n:]
    return (W('LeftArm')[:3, 3]+W('RightArm')[:3, 3])/2

FIST_D = np.linalg.norm(np.mean([RP['LeftHand'+g] for g in GRIP], 0)-RP['LeftHand'])
_c, _ = solve({**dict(hips=(0, RP['Hips'][1], 0), footL=(0.12, 0), footR=(-0.12, 0)), 'handL': np.array([0.2, -1.0, 0.0]), 'elbowL': (0, 0, -1), 'palmL': (0, 0, -1)})
_W = rig.world(_c, 0)
REACH = np.linalg.norm(np.mean([_W('LeftHand'+g)[:3, 3] for g in GRIP], 0)-_W('LeftArm')[:3, 3])
print('  fist offset %.3f, straight reach to fist %.3f' % (FIST_D, REACH)); WARN.clear()
STAND = dict(hips=(0, RP['Hips'][1], 0), pelvis=(0, 0, 0), spine=(0, 0, 0), neck=0, head=0, toe=8)
FL, FR = (0.11, 0.06), (-0.11, 0.06)

# ---------------- становая тяга ----------------
DL_GRIP = 0.25                        # половина ширины хвата
PLATE_R = 0.225
DL_FEET = dict(footL=(0.13, 0.17), footR=(-0.13, 0.17), toe=10)
DL_BAR_Z = 0.11                       # гриф над серединой стопы
def dl_pose(s, th, P=None):
    P = dict(P or {}); P['s'] = s
    P.update(pelvis=(th*0.85, 0, 0), spine=(th*0.15+3*(1-s), 0, 0), neck=-th*0.3, head=-th*0.25, kneeout=6, **DL_FEET)
    rel = mid_shoulder_rel(P)
    hang = REACH*0.99
    dx = DL_GRIP-abs(RP['LeftArm'][0])
    dz = 0.05-0.17*s**1.6                                     # внизу плечи чуть впереди грифа, вверху — гриф у бёдер
    sh_stand = mid_shoulder_rel({**STAND, **DL_FEET})+np.array(STAND['hips'])
    top = sh_stand[1]-np.sqrt(hang**2-dx**2-0.12**2)
    by = PLATE_R+(top-PLATE_R)*s
    bar = np.array([0, by, DL_BAR_Z])
    sh = np.array([0, by+np.sqrt(hang**2-dx**2-dz**2), DL_BAR_Z+dz])
    P['hips'] = sh-rel
    P.update(gripL=bar+[DL_GRIP, 0, 0], gripR=bar-[DL_GRIP, 0, 0], elbowL=(0.3, 0, -1), elbowR=(-0.3, 0, -1),
             palmL=(0, 0, -1), palmR=(0, 0, -1), axisL=(1, 0, 0), axisR=(1, 0, 0))
    return P, bar
def seg_dist(p, a, b):
    ab = b-a; t = np.clip(np.dot(p-a, ab)/np.dot(ab, ab), 0, 1); return np.linalg.norm(p-(a+t*ab))
def dl_clear(s, th):
    """Насколько гриф отстоит от голени/колена/бедра (в плоскости YZ), минус нужный зазор."""
    P, bar = dl_pose(s, th); c, _ = solve(P); W = rig.world(c, 0); m = 1
    yz = lambda v: np.array([v[1], v[2]])
    for sd in ('Left', 'Right'):
        h, k, a = (yz(W(sd+b)[:3, 3]) for b in ('UpLeg', 'Leg', 'Foot'))
        m = min(m, seg_dist(yz(bar), k, a)-0.055*BODY, np.linalg.norm(yz(bar)-k)-0.075*BODY)
        if s < 0.8: m = min(m, seg_dist(yz(bar), h, k)-0.08*BODY)
    return m
DL_S = np.linspace(0, 1, 26)
BODY = REACH/0.661                                           # толщина конечностей ~ пропорциональна росту
def dl_need():
    need = []
    for s_ in DL_S:
        th = 50*(1-s_**1.35)
        while dl_clear(s_, th) < 0 and th < 80: th += 1.0
        need.append(th)
    return need
# гриф над серединой стопы; если корпус внизу получается почти горизонтальным — чуть вперёд (для другой анатомии)
while True:
    need = dl_need()
    if max(need[:4]) <= 60 or DL_BAR_Z > 0.16: break
    DL_BAR_Z += 0.01
print('  deadlift bar z %.2f' % DL_BAR_Z)
need = np.array(need)
need = np.maximum.accumulate(need[::-1])[::-1]+1.0           # монотонно: чем выше гриф, тем прямее корпус
need = np.convolve(np.r_[need[0], need, need[-1]], [1/3, 1/3, 1/3], 'valid')
print('  deadlift trunk angle by height:', need[::5].round(1))
WARN.clear()
def deadlift_fn(P):
    s = P['s']; th = float(np.interp(s, DL_S, need)) if s < 1 else 0.0
    P, _ = dl_pose(s, th, P)
    return P

animate('deadlift', [(0, dict(s=1)), (0.4, dict(s=1)), (1.7, dict(s=0)), (2.0, dict(s=0)), (3.1, dict(s=1)), (3.4, dict(s=1))],
        props_fn=bar_track, grip=True, fn=deadlift_fn)

def shoulder(P, side='Left'):
    Q = dict(P); Q.setdefault('footL', FL); Q.setdefault('footR', FR)
    Q = {k: v for k, v in Q.items() if not k.startswith(('hand', 'grip'))}
    c, _ = solve(Q); return rig.world(c, 0)(side+'Arm')[:3, 3]

# ---------------- выпады вперёд (поочерёдно) ----------------
def arms_relaxed(P):
    """Руки свободно висят вдоль тела, чуть согнуты; P['swing'] — лёгкий мах (+ левая вперёд)."""
    sw = P.get('swing', 0)
    for k, sd, sg in (('L', 'Left', 1), ('R', 'Right', -1)):
        S = shoulder(P, sd)
        d = nz(np.array([sg*0.10, -1, 0.06+sg*sw]))
        P['grip'+k] = S+d*REACH*0.95
        P['elbow'+k] = np.array([sg*0.25, 0, -1.0])
        P['palm'+k] = np.array([-sg*1.0, 0, -0.15])
    return P
def lunge_keys(front):
    sg = 1 if front == 'L' else -1; F, B = 'foot'+front, 'foot'+('R' if front == 'L' else 'L')
    fx, bx = sg*0.115, -sg*0.11; Hy = RP['Hips'][1]
    stand = {F: (fx, 0.06, 0, 0), B: (bx, 0.06, 0, 0), 'hips': (0, Hy, 0), 'pelvis': (0, 0, 0), 'spine': (0, 0, 0), 'neck': 0, 'swing': 0}
    return [  # (время от начала шага, поза)
        (0.00, stand),
        (0.30, {F: (fx, 0.34, -6, 0.08), B: (bx, 0.06, 6, 0), 'hips': (sg*0.01, Hy-0.04, 0.12), 'pelvis': (3, 0, 0), 'swing': -sg*0.10}),
        (0.55, {F: (fx, 0.72, 0, 0), B: (bx, 0.06, 22, 0), 'hips': (sg*0.02, Hy-0.13, 0.27), 'pelvis': (6, -sg*3, 0), 'spine': (2, 0, 0), 'swing': -sg*0.06}),
        (1.05, {F: (fx, 0.72, 0, 0), B: (bx, 0.06, 52, 0), 'hips': (sg*0.02, 0.585, 0.32), 'pelvis': (9, -sg*4, 0), 'spine': (1, 0, 0), 'neck': -6, 'swing': 0}),
        (1.25, {F: (fx, 0.72, 0, 0), B: (bx, 0.06, 52, 0), 'hips': (sg*0.02, 0.59, 0.32)}),
        (1.65, {F: (fx, 0.70, 4, 0), B: (bx, 0.06, 24, 0), 'hips': (sg*0.015, Hy-0.12, 0.20), 'pelvis': (5, -sg*2, 0), 'spine': (1, 0, 0), 'neck': -2}),
        (1.95, {F: (fx, 0.32, -4, 0.07), B: (bx, 0.06, 6, 0), 'hips': (sg*0.005, Hy-0.03, 0.06), 'pelvis': (2, 0, 0), 'spine': (0, 0, 0), 'neck': 0, 'swing': sg*0.04}),
        (2.25, stand),
        (2.55, stand)]
keys = []
for i, (t, p) in enumerate(lunge_keys('L')): keys.append((t, {**p, 'toe': 8} if i == 0 else p))
for t, p in lunge_keys('R')[1:]: keys.append((2.55+t, p))
animate('lunge', keys, hand=RELAX, grip=True, fn=arms_relaxed)

# ---------------- жим штанги стоя ----------------
OHP_FEET = dict(footL=(0.13, 0.06), footR=(-0.13, 0.06), toe=10)
OHP_GRIP = 0.27
def ohp_fn(P):
    s = P['s']; P.update(**OHP_FEET)
    face = np.sin(np.pi*np.clip(s/0.6, 0, 1))                  # гриф проходит лицо — голова уходит назад
    under = np.clip((s-0.45)/0.55, 0, 1)                       # после лба — корпус «под гриф»
    P.update(hips=(0, RP['Hips'][1]-0.005, -0.012*face+0.02*under), pelvis=(-2*face, 0, 0), spine=(-2*face+2*under, 0, 0),
             neck=-12*face+4*under, head=-6*face, clav=(14*under, 14*under))
    sh = (shoulder(P, 'Left')+shoulder(P, 'Right'))/2
    dx = OHP_GRIP-abs(shoulder(P, 'Left')[0]-sh[0])
    rack = sh+np.array([0, -0.02, 0.16])
    top = sh+np.array([0, np.sqrt((REACH*0.985)**2-dx**2), 0.0])
    y = rack[1]+(top[1]-rack[1])*s
    z = rack[2]+(top[2]-rack[2])*ease(under)
    bar = np.array([0, y, z])
    P.update(gripL=bar+[OHP_GRIP, 0, 0], gripR=bar-[OHP_GRIP, 0, 0], axisL=(1, 0, 0), axisR=(1, 0, 0))
    e = np.clip(s*1.15, 0, 1)
    P.update(elbowL=nz(lerp((0.55, -1, 0.0), (1, 0.1, -0.25), e)), elbowR=nz(lerp((-0.55, -1, 0.0), (-1, 0.1, -0.25), e)),
             palmL=nz(lerp((0, 0.45, 1), (0, 1, 0.3), e)), palmR=nz(lerp((0, 0.45, 1), (0, 1, 0.3), e)),
             wristL=-30*(1-e)-8, wristR=-30*(1-e)-8)
    for k in ('elbowL', 'elbowR', 'palmL', 'palmR'): P[k] = np.array(P[k])
    return P
animate('overhead_press', [(0, dict(s=0)), (0.45, dict(s=0)), (1.25, dict(s=1)), (1.6, dict(s=1)), (2.9, dict(s=0))],
        props_fn=bar_track, grip=True, fn=ohp_fn)

# ---------------- махи гантелями в стороны ----------------
def lateral_fn(P):
    a = P['a']; P.update(footL=(0.12, 0.06), footR=(-0.12, 0.06), toe=8, hips=(0, RP['Hips'][1]-0.015, -0.01),
                         pelvis=(5-1.5*a, 0, 0), spine=(4-1*a, 0, 0), neck=-5, head=-2, clav=(4*a, 4*a))
    for k, sd, sg in (('L', 'Left', 1), ('R', 'Right', -1)):
        S = shoulder(P, sd); r = REACH*0.94
        ang = np.radians(10+78*a)                              # отведение: от бедра до уровня плеча
        fwd = np.radians(20)                                   # плоскость лопатки — чуть вперёд
        d = np.array([sg*np.sin(ang)*np.cos(fwd), -np.cos(ang), np.sin(ang)*np.sin(fwd)+0.04])
        P['grip'+k] = S+r*nz(d)
        P['elbow'+k] = nz(np.array([sg*0.3, 0.6*a, -1.0]))    # локоть ведёт движение, смотрит назад-вверх
        P['palm'+k] = nz(np.array([-sg*(1-a)*1.0, -0.2-0.8*a, 0.0])); P['axis'+k] = np.array([0, 0, 1.0])
        P['wrist'+k] = -6*a
    return P
animate('lateral_raise', [(0, dict(a=0)), (0.35, dict(a=0)), (1.2, dict(a=1)), (1.45, dict(a=1)), (2.8, dict(a=0))],
        props_fn=dumbbell_track, grip=True, fn=lateral_fn)

# ---------------- снаряды: общие детали ----------------
def rbox(g, c, size, r, R=np.eye(3), n=6):
    """Коробка со скруглёнными рёбрами (подушки, сиденья)."""
    h = np.asarray(size, float)/2; r = min(r, *(h*0.999)); inner = h-r
    for ax in range(3):
        for sgn in (-1, 1):
            u_ax, v_ax = [i for i in range(3) if i != ax]
            P = []; N = []
            for i in range(n+1):
                for j in range(n+1):
                    p = np.zeros(3); p[ax] = sgn; p[u_ax] = -1+2*i/n; p[v_ax] = -1+2*j/n
                    # плотнее к краям, чтобы скругление было гладким
                    p[u_ax] = np.sign(p[u_ax])*abs(p[u_ax])**0.6; p[v_ax] = np.sign(p[v_ax])*abs(p[v_ax])**0.6
                    q = p*h; cq = np.clip(q, -inner, inner); d = q-cq
                    nn = d/np.linalg.norm(d) if np.linalg.norm(d) > 1e-9 else np.eye(3)[ax]*sgn
                    P.append(R@(cq+r*nn)+c); N.append(R@nn)
            I = []
            for i in range(n):
                for j in range(n):
                    a = i*(n+1)+j; b = a+n+1
                    tri = [a, b, a+1, a+1, b, b+1]
                    # ориентация треугольников наружу
                    if (np.cross(np.array(P[b])-P[a], np.array(P[a+1])-P[a]) @ N[a]) < 0: tri = [a, a+1, b, a+1, b+1, b]
                    I += tri
            g._add(P, N, I)
def rtube(g, p0, p1, w, h, up=(0, 1, 0), r=0.008):
    """Прямоугольная профильная труба от p0 до p1."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float); d = p1-p0; L = np.linalg.norm(d)
    x = nz(d); y = np.asarray(up, float); y = y-np.dot(y, x)*x
    if np.linalg.norm(y) < 1e-6: y = np.array([0, 0, 1.0])-x[2]*x
    y = nz(y); z = np.cross(x, y)
    rbox(g, (p0+p1)/2, (L, h, w), r, np.stack([x, y, z], 1), n=3)

M_STEEL = mat('Powder steel', (0.05, 0.052, 0.058), 0.55, 0.38)
M_PAD = mat('Vinyl pad', (0.028, 0.028, 0.03), 0.0, 0.62)
M_CHROME2 = mid.get('Chrome', mat('Chrome2', (0.8, 0.8, 0.82), 1.0, 0.18))

# ---------------- жим гантелей на наклонной скамье ----------------
INC = 32                                                     # наклон спинки, градусов от пола
INC_SEAT_Y = 0.45
INC_BASE = dict(hips=(0, 0.585, 0.0), pelvis=(-(90-INC)*0.84, 0, 0), spine=(-(90-INC)*0.16, 0, 0), neck=14, head=10,
                footL=(0.25, 0.66), footR=(-0.25, 0.66), toe=14, kneeout=12)
_c, _ = solve(INC_BASE); _W = rig.world(_c, 0)
HP = _W('Hips')[:3, 3]; S2 = _W('Spine2')[:3, 3]; U = nz(S2-HP); NB = nz(np.cross(U, [1, 0, 0]))   # NB — от спины к скамье
print('  incline: trunk angle from floor %.1f' % np.degrees(np.arcsin(U[1])))
def incline_fn(P):
    s = P['s']; P.update(INC_BASE)
    for k, sd, sg in (('L', 'Left', 1), ('R', 'Right', -1)):
        S = shoulder(P, sd)
        de = nz(np.array([sg*0.7, -0.6, 0.3]))                  # плечо: в сторону-вниз, локоть чуть к ногам
        E = S+de*LIMB[(sd, 'arm')]['la']
        bottom = E+np.array([0, LIMB[(sd, 'arm')]['lb']+0.07, 0])  # предплечье вертикально, гантель над локтем
        top = S+np.array([-sg*0.035, REACH*0.965, 0.0])          # руки перпендикулярно полу, гантели не касаются
        g = bottom+(top-bottom)*s+np.array([sg*0.03, 0, 0])*np.sin(np.pi*s)
        P['grip'+k] = g
        P['elbow'+k] = nz(lerp(tuple(de), (sg*1.0, -0.1, 0.1), s))
        P['palm'+k] = nz(-U+np.array([0, 0.25, 0])); P['axis'+k] = np.array([1.0, 0, 0])
        P['wrist'+k] = -12
    return P

def incline_bench():
    seat, pad, fr, rub, acc = Geo(), Geo(), Geo(), Geo(), Geo()
    # спинка: поверхность — по спине персонажа
    BACK_D = 0.118; L = 0.80; T = 0.065
    Rb = np.stack([np.array([1., 0, 0]), -NB, U], 1)          # x — ширина, y — наружу (к спине), z — вдоль спины
    pad_c = HP+U*(L/2-0.12)+NB*(BACK_D+T/2)
    rbox(pad, pad_c, (0.27, T, L), 0.028, Rb)
    # сиденье
    sz = HP[2]+0.10
    seat_c = np.array([0, INC_SEAT_Y-0.035, sz])
    rbox(seat, seat_c, (0.29, 0.07, 0.33), 0.028)
    # подложки (фанера) под подушками
    rbox(fr, seat_c-[0, 0.045, 0], (0.24, 0.02, 0.29), 0.004)
    rbox(fr, pad_c+NB*(T/2+0.01), (0.22, 0.02, L-0.06), 0.004, Rb)
    # рама: центральная балка, стабилизаторы
    FZ, RZ = 0.42, pad_c[2]-np.cos(np.radians(INC))*L*0.42
    by = 0.13
    rtube(fr, [0, by, FZ], [0, by, RZ], 0.06, 0.09)
    for z, w in ((FZ, 0.56), (RZ, 0.60)):
        tube(fr, [-w/2, 0.045, z], [w/2, 0.045, z], 0.035)
        for sg in (-1, 1):
            rbox(rub, [sg*(w/2-0.02), 0.012, z], (0.06, 0.024, 0.075), 0.01)
            tube(rub, [sg*(w/2+0.004), 0.045, z], [sg*(w/2+0.02), 0.045, z], 0.037)
        rtube(fr, [0, 0.07, z], [0, by, z], 0.06, 0.05, up=(0, 0, 1))
    # колёса спереди
    for sg in (-1, 1): rub.cyl([sg*0.30, 0.05, FZ+0.05], [1, 0, 0], 0.05, 0.035)
    # стойка сиденья
    rtube(fr, [0, by, sz], [0, INC_SEAT_Y-0.09, sz], 0.06, 0.06, up=(0, 0, 1))
    # опора спинки: балка под подушкой + шарнир у сиденья + регулируемый упор
    bb0 = pad_c-U*(L/2-0.05)+NB*(T/2+0.05); bb1 = pad_c+U*(L/2-0.12)+NB*(T/2+0.05)
    rtube(fr, bb0, bb1, 0.06, 0.05, up=-NB)
    hinge = np.array([0, INC_SEAT_Y-0.10, bb0[2]])
    tube(fr, hinge-[0.045, 0, 0], hinge+[0.045, 0, 0], 0.03)
    rtube(fr, hinge, bb0, 0.05, 0.05)
    rtube(fr, [0, by, hinge[2]], hinge, 0.06, 0.06, up=(0, 0, 1))
    strut_top = pad_c+NB*(T/2+0.05)
    strut_bot = np.array([0, by+0.05, strut_top[2]-0.18])
    for sg in (-1, 1): rtube(fr, strut_bot+[sg*0.04, 0, 0], strut_top+[sg*0.04, 0, 0], 0.016, 0.04)
    tube(acc, strut_bot-[0.06, 0, 0], strut_bot+[0.06, 0, 0], 0.013)                # фиксатор
    # «лестница» регулировки
    for i in range(6):
        z = strut_bot[2]+0.05-i*0.055
        rbox(fr, [0, by+0.065, z], (0.07, 0.03, 0.018), 0.004)
    # ручка для перемещения и акцент
    tube(fr, [0, by, RZ], [0, by+0.10, RZ-0.08], 0.017)
    tube(acc, [-0.02, by+0.10, RZ-0.08], [0.02, by+0.10, RZ-0.08], 0.02)
    rbox(acc, [0, by+0.047, (FZ+RZ)/2], (0.062, 0.004, 0.25), 0.002)
    return add_node('InclineBench', add_mesh([(M_PAD, pad), (M_PAD, seat), (M_STEEL, fr), (M_RUBBER, rub), (M_ACCENT, acc)]))
IBENCH = incline_bench()
animate('incline_dumbbell_press', [(0, dict(s=0)), (0.35, dict(s=0)), (1.15, dict(s=1)), (1.4, dict(s=1)), (2.8, dict(s=0))],
        props_fn=lambda c, N: [(IBENCH, 'show', None)]+dumbbell_track(c, N), grip=True, fn=incline_fn)

# ================= партия 2: румынская тяга, тяга штанги в наклоне, подъёмы на бицепс, молотки, скручивания =================
def hang_grip(P, half, side):
    """Кулак прямо под плечом (руки висят вертикально), хват на расстоянии half от центра."""
    S = shoulder(P, side); sg = 1 if side == 'Left' else -1
    dx = half-abs(S[0]); dy = np.sqrt(max(1e-6, (REACH*0.985)**2-dx**2))
    return np.array([sg*half, S[1]-dy, S[2]])

def body_W(P):
    n = len(WARN); c, _ = solve({k: v for k, v in P.items() if not k.startswith(('hand', 'grip'))}); del WARN[n:]
    return rig.world(c, 0)
def clear_bar(P, bar, side_legs=('Left', 'Right'), clr=0.085):
    """Сдвигает гриф вперёд (по +Z), пока он не отойдёт от бёдер/колен на clr (в плоскости YZ)."""
    W = body_W(P); yz = lambda v: np.array([v[1], v[2]])
    segs = [(yz(W(sd+'UpLeg')[:3, 3]), yz(W(sd+'Leg')[:3, 3])) for sd in side_legs]
    segs += [(yz(W(sd+'Leg')[:3, 3]), yz(W(sd+'Foot')[:3, 3])) for sd in side_legs]
    dz = 0.0
    for _ in range(60):
        q = np.array([bar[1], bar[2]+dz])
        if min(seg_dist(q, a, b) for a, b in segs) >= clr*BODY: break
        dz += 0.004
    return dz

# ---------------- румынская тяга ----------------
RDL_FEET = dict(footL=(0.12, 0.08), footR=(-0.12, 0.08), toe=8)
def rdl_fn(P):
    s = P['s']                                                  # 0 — стоя, 1 — внизу
    th = 72*s                                                   # наклон корпуса: таз уходит назад, спина прямая
    P.update(**RDL_FEET, pelvis=(th*0.9, 0, 0), spine=(th*0.1, 0, 0), neck=-th*0.35, head=-th*0.2, kneeout=4,
             hips=(0, RP['Hips'][1]-0.075*s-0.012, -0.30*s))
    gl = hang_grip(P, 0.24, 'Left'); dz = clear_bar(P, gl, clr=0.13)          # гриф скользит по бёдрам, не сквозь них
    for k, sd in (('L', 'Left'), ('R', 'Right')):
        P['grip'+k] = hang_grip(P, 0.24, sd)+np.array([0, 0, dz])
        P['elbow'+k] = np.array([0.3 if k == 'L' else -0.3, 0, -1.0]); P['palm'+k] = np.array([0, 0, -1.0]); P['axis'+k] = np.array([1.0, 0, 0])
    return P
animate('romanian_deadlift', [(0, dict(s=0)), (0.4, dict(s=0)), (1.9, dict(s=1)), (2.15, dict(s=1)), (3.25, dict(s=0))],
        props_fn=bar_track, grip=True, fn=rdl_fn)

# ---------------- тяга штанги в наклоне ----------------
ROW_BASE = dict(footL=(0.17, 0.05), footR=(-0.17, 0.05), toe=10, kneeout=6,
                pelvis=(52, 0, 0), spine=(8, 0, 0), neck=-24, head=-10, hips=(0, 0.84, -0.20))
_c, _ = solve(ROW_BASE); _W = rig.world(_c, 0)
ROW_H = _W('Hips')[:3, 3]; ROW_U = nz(_W('Spine2')[:3, 3]-ROW_H); ROW_F = nz(np.cross([1, 0, 0], ROW_U))   # вперёд от груди
ROW_TF = 0.33
def row_fn(P):
    s = P['s']; P.update(ROW_BASE)
    # корпус не застывший: на подъёме чуть выпрямляется и подаётся, голова следует, колени пружинят
    P.update(pelvis=(52-6*s, 0, 0), spine=(8-3*s+1.5*np.sin(np.pi*s), 0, 0), neck=-24+4*s, head=-10+2*s,
             hips=(0, 0.84+0.012*s, -0.20+0.015*s))
    W = body_W(P); H = W('Hips')[:3, 3]; U_ = nz(W('Spine2')[:3, 3]-H); F_ = nz(np.cross([1, 0, 0], U_))
    for k, sd, sg in (('L', 'Left', 1), ('R', 'Right', -1)):
        bottom = hang_grip(P, 0.26, sd)
        top = H+U_*0.20+F_*ROW_TF+np.array([sg*0.26, 0, 0])                     # к животу; локти не выше линии спины
        g = bottom+(top-bottom)*s+np.array([0, 0, -0.03])*np.sin(np.pi*s)
        P['grip'+k] = g
        P['elbow'+k] = nz(lerp((sg*0.35, 0.0, -1.0), (sg*0.45, 0.45, -1.0), s))
        P['palm'+k] = np.array([0, 0, -1.0]); P['axis'+k] = np.array([1.0, 0, 0])
    return P
animate('barbell_row', [(0, dict(s=0)), (0.35, dict(s=0)), (1.0, dict(s=1)), (1.25, dict(s=1)), (2.25, dict(s=0))],
        props_fn=bar_track, grip=True, fn=row_fn)

# ---------------- подъём штанги / гантелей на бицепс ----------------
CURL_BASE = dict(footL=(0.16, 0.06), footR=(-0.16, 0.06), toe=10, hips=(0, RP['Hips'][1]-0.01, 0), pelvis=(0, 0, 0), spine=(0, 0, 0))
def curl_arm(P, k, phi, width):
    """Плечо висит у корпуса, предплечье поднимается на угол phi (0 — рука прямая)."""
    sd = 'Left' if k == 'L' else 'Right'; sg = 1 if k == 'L' else -1
    S = shoulder(P, sd); Lm = LIMB[(sd, 'arm')]
    E = S+Lm['la']*nz(np.array([sg*0.10, -1, 0.06+0.22*(phi/140)**2]))   # локоть у бока, вверху чуть выходит вперёд
    a = np.radians(max(phi, 4))
    W_ = E+Lm['lb']*np.array([sg*(width-abs(E[0]))/Lm['lb']*np.cos(a)*0.0, -np.cos(a), np.sin(a)])
    W_[0] = sg*max(abs(W_[0]), width)
    P['hand'+k] = W_; P['elbow'+k] = np.array([sg*0.15, -0.2, -1.0])
def fist_clear(P, k='L'):
    c, _ = solve(P); W = rig.world(c, 0); sd = 'Left' if k == 'L' else 'Right'
    f = np.mean([W(sd+'Hand'+g)[:3, 3] for g in GRIP], 0); yz = lambda v: np.array([v[1], v[2]])
    return min(seg_dist(yz(f), yz(W(s_+'UpLeg')[:3, 3]), yz(W(s_+'Leg')[:3, 3])) for s_ in ('Left', 'Right'))
CURL_PHI0 = 8
for _ph in range(8, 46, 2):                                    # внизу гриф перед бёдрами, а не в них
    _P = dict(CURL_BASE)
    for _k in 'LR': curl_arm(_P, _k, _ph, 0.20); _P['axis'+_k] = np.array([1.0, 0, 0])
    CURL_PHI0 = _ph
    if fist_clear(_P) >= 0.13*BODY: break
print('  curl start angle', CURL_PHI0)
def barbell_curl_fn(P):
    s = P['s']; P.update(CURL_BASE); P['spine'] = (-3*s, 0, 0)
    phi = CURL_PHI0+(125-CURL_PHI0)*s                          # вверху гриф у плеч, не в груди
    for k in 'LR':
        curl_arm(P, k, phi, 0.20)
        P['axis'+k] = np.array([1.0, 0, 0]); P['palm'+k] = nz(np.array([0, np.sin(np.radians(phi)), np.cos(np.radians(phi))]))  # ладони вперёд/вверх
        P['wrist'+k] = 6*s
    return P
animate('barbell_curl', [(0, dict(s=0)), (0.35, dict(s=0)), (1.35, dict(s=1)), (1.6, dict(s=1)), (2.85, dict(s=0))],
        props_fn=bar_track, fn=barbell_curl_fn)

def heavy_dumbbells():
    hd = Geo(); hd.cyl([0, 0, 0], [1, 0, 0], 0.016, 0.17)
    hh = Geo()
    for sg in (-1, 1): hh.cyl([sg*0.125, 0, 0], [1, 0, 0], 0.062, 0.09, seg=6)
    return [add_node(n, add_mesh([(mid['Chrome'], hd), (M_RUBBER, hh)])) for n in ('DumbbellHeavyL', 'DumbbellHeavyR')]
DBH = heavy_dumbbells()
def hammer_fn(P):
    a, b = P['a'], P['b']; t = P.get('t', 0)
    w = a-b                                                       # куда смещён вес: к рабочей руке
    P.update(footL=(0.17, 0.07), footR=(-0.17, 0.05), toe=12, kneeout=4,
             hips=(0.012*w, RP['Hips'][1]-0.008+0.003*np.sin(t*2.1), 0.004*np.sin(t*1.3)),
             pelvis=(2.5, 2.5*w, -1.8*w), spine=(1.5+0.8*np.sin(t*2.1), -3*w, 1.2*w), neck=-2, head=-3+2*(a+b))
    for k, key in (('L', 'a'), ('R', 'b')):
        phi = 10+124*P[key]
        curl_arm(P, k, phi, 0.205)
        P['palm'+k] = np.array([-1.0 if k == 'L' else 1.0, 0, 0.15])                       # нейтральный хват: ладони к телу
    return P
animate('hammer_curl', [(0, dict(a=0, b=0)), (0.3, dict(a=0, b=0)), (1.3, dict(a=1, b=0)), (1.5, dict(a=1, b=0)), (2.55, dict(a=0, b=0)),
                        (2.85, dict(a=0, b=0)), (3.85, dict(a=0, b=1)), (4.05, dict(a=0, b=1)), (5.1, dict(a=0, b=0))],
        props_fn=lambda c, N: dumbbell_track(c, N, DBH), fn=hammer_fn)

# ---------------- скручивания на коврике ----------------
CR_HIP_Y = 0.105
CR_BASE = dict(hips=(0, CR_HIP_Y, 0), pelvis=(-90, 0, 0), toe=4, neck=0, head=0,
               footL=(0.14, 0.50), footR=(-0.14, 0.50), kneeL=(0, 1, 0.2), kneeR=(0, 1, 0.2))
def crunch_fn(P):
    s = P['s']; P.update(CR_BASE); P.update(spine=(34*s, 0, 0), neck=14+10*s, head=4)
    c, _ = solve({k: v for k, v in P.items() if not k.startswith(('hand', 'grip'))}); W = rig.world(c, 0)
    Hd = W('Head')[:3, 3]; R = wrot(W('Head'))
    for k, sg in (('L', 1), ('R', -1)):
        P['hand'+k] = Hd+R@np.array([sg*0.075, 0.07, -0.085])                # ладони за затылком
        P['elbow'+k] = np.array([sg*1.0, 0.25, 0.0]); P['palm'+k] = R@np.array([0, 0, 1.0])
    return P
def exercise_mat():
    g_, edge = Geo(), Geo()
    rbox(g_, [0, 0.006, -0.05], (0.62, 0.012, 1.80), 0.006, n=4)
    for sg in (-1, 1): rbox(edge, [sg*0.3125, 0.0065, -0.05], (0.004, 0.0105, 1.78), 0.002, n=3)
    M_MAT = mat('Mat', (0.035, 0.036, 0.04), 0.0, 0.85)
    return add_node('Mat', add_mesh([(M_MAT, g_), (M_ACCENT, edge)]))
MAT = exercise_mat()
animate('crunch', [(0, dict(s=0)), (0.35, dict(s=0)), (0.95, dict(s=1)), (1.25, dict(s=1)), (2.05, dict(s=0))],
        props_fn=lambda c, N: [(MAT, 'show', None)], hand=RELAX, fn=crunch_fn)

# ================= партия 3: упражнения с горизонтальной скамьёй =================
FB_TOP = 0.44                                                   # верх подушки скамьи
def flat_bench_mesh():
    pad, fr, rub, acc = Geo(), Geo(), Geo(), Geo()
    L = 1.20
    rbox(pad, [0, FB_TOP-0.035, 0], (0.28, 0.07, L), 0.028)
    rbox(fr, [0, FB_TOP-0.08, 0], (0.24, 0.02, L-0.06), 0.004)
    by = 0.30
    rtube(fr, [0, by, -L/2+0.08], [0, by, L/2-0.08], 0.07, 0.08)              # продольная балка
    rtube(fr, [0, by+0.04, -0.3], [0, FB_TOP-0.09, -0.3], 0.05, 0.03, up=(0, 0, 1))
    rtube(fr, [0, by+0.04, 0.3], [0, FB_TOP-0.09, 0.3], 0.05, 0.03, up=(0, 0, 1))
    for z, w in ((-L/2+0.12, 0.50), (L/2-0.12, 0.46)):
        rtube(fr, [0, 0.07, z], [0, by, z], 0.06, 0.06, up=(0, 0, 1))         # стойка
        tube(fr, [-w/2, 0.045, z], [w/2, 0.045, z], 0.035)                     # опора
        for sg in (-1, 1):
            rbox(rub, [sg*(w/2-0.02), 0.012, z], (0.06, 0.024, 0.075), 0.01)
            tube(rub, [sg*(w/2+0.004), 0.045, z], [sg*(w/2+0.02), 0.045, z], 0.037)
    rub.cyl([0, 0.05, L/2-0.02], [1, 0, 0], 0.045, 0.06)                     # колесо для перемещения
    for sg in (-1, 1): rbox(acc, [sg*0.0362, by, 0], (0.004, 0.012, L-0.30), 0.002)
    return add_mesh([(M_PAD, pad), (M_STEEL, fr), (M_RUBBER, rub), (M_ACCENT, acc)])
FB_MESH = flat_bench_mesh()
def flat_bench(name, x=0.0, z=0.0, across=False):
    i = add_node(name, FB_MESH, (x, 0, z))
    if across: dst.nodes[i].rotation = [0.0, float(np.sqrt(.5)), 0.0, float(np.sqrt(.5))]
    return i

def ez_bar():
    """Короткий гриф с небольшими блинами (для разгибаний лёжа). Ось X, центр — середина грифа."""
    b, pl, cl = Geo(), Geo(), Geo()
    b.cyl([0, 0, 0], [1, 0, 0], 0.0135, 0.98)
    for sg in (-1, 1):
        b.cyl([sg*0.55, 0, 0], [1, 0, 0], 0.024, 0.16)
        cl.cyl([sg*0.475, 0, 0], [1, 0, 0], 0.032, 0.025)
        pl.cyl([sg*0.515, 0, 0], [1, 0, 0], 0.115, 0.032, seg=40)
        pl.cyl([sg*0.55, 0, 0], [1, 0, 0], 0.095, 0.03, seg=40)
    return add_node('EZBar', add_mesh([(mid['Chrome'], b), (M_RUBBER, pl), (M_ACCENT, cl)]))
EZB = ez_bar()
def ez_track(clip, N):
    t = []; r = []
    for g in grips(clip, N): t.append((g['gl']+g['gr'])/2); r.append(look(g['gl']-g['gr']))
    return [(EZB, 'show', None), (EZB, 'translation', t), (EZB, 'rotation', fix_sign(r))]

# ---------------- лёжа на скамье: база ----------------
SUP = dict(hips=(0, FB_TOP+0.093, 0), pelvis=(-90, 0, 0), spine=(0, 0, 0), neck=4, head=0,
           footL=(0.27, 0.56), footR=(-0.27, 0.56), toe=14, kneeout=10)
FB_SUP = flat_bench('FlatBench', z=-0.33)

# ---------------- разведение гантелей лёжа ----------------
def fly_fn(P):
    s = P['s']; P.update(SUP); P['spine'] = (-3*s, 0, 0)          # внизу грудь чуть раскрыта
    for k, sd, sg in (('L', 'Left', 1), ('R', 'Right', -1)):
        S = shoulder(P, sd)
        a = np.radians(-9+82*s)                                   # от «над грудью» до уровня плеч
        r = REACH*(0.95-0.07*s)                                    # локти мягко согнуты, внизу — сильнее
        P['grip'+k] = S+r*np.array([sg*np.sin(a), np.cos(a), 0.0])+np.array([0, 0.0, 0.05])
        P['elbow'+k] = nz(lerp((sg*1.0, 0.1, 0.1), (sg*0.15, -1.0, 0.15), s))
        P['palm'+k] = nz(np.array([-sg*np.cos(a), np.sin(a), 0.0])); P['axis'+k] = np.array([0, 0, 1.0])
    return P
animate('dumbbell_fly', [(0, dict(s=0)), (0.35, dict(s=0)), (1.5, dict(s=1)), (1.7, dict(s=1)), (2.8, dict(s=0))],
        props_fn=lambda c, N: [(FB_SUP, 'show', None)]+dumbbell_track(c, N), grip=True, fn=fly_fn)

# ---------------- французский жим лёжа ----------------
SK_TILT = 14; SK_BEND = 94
def skull_fn(P):
    s = P['s']; P.update(SUP)
    for k, sd, sg in (('L', 'Left', 1), ('R', 'Right', -1)):
        S = shoulder(P, sd); Lm = LIMB[(sd, 'arm')]
        b = np.radians(SK_TILT); u = nz(np.array([-sg*0.10, np.cos(b), -np.sin(b)]))    # плечо почти вертикально, к голове
        E = S+Lm['la']*u
        f = np.radians(SK_TILT+6+(SK_BEND-6)*s); fa = np.array([0, np.cos(f), -np.sin(f)])
        Wr = E+Lm['lb']*fa
        P['hand'+k] = Wr
        P['elbow'+k] = nz(np.array([sg*0.12, 0.85, 0.5]))            # постоянный полюс — без рывков у верхней точки
        P['axis'+k] = np.array([1.0, 0, 0]); P['palm'+k] = np.array([0, np.sin(f), np.cos(f)])
        P['wrist'+k] = 10*s
    return P
animate('skull_crusher', [(0, dict(s=0)), (0.35, dict(s=0)), (1.45, dict(s=1)), (1.65, dict(s=1)), (2.7, dict(s=0))],
        props_fn=lambda c, N: [(FB_SUP, 'show', None)]+ez_track(c, N), fn=skull_fn)

# ---------------- тяга гантели одной рукой с упором в скамью ----------------
def foot_on_bench(ankle, heel, side, yaw):
    """Параметры стопы, у которой голеностоп в точке ankle (стопа подъёмом на скамье, носок назад)."""
    Df = Ry(yaw*(1 if side == 'Left' else -1))@Rx(heel)
    ball = ankle+Df@(RP[side+'ToeBase']-RP[side+'Foot'])
    return (ball[0], ball[2], heel, ball[1]-BALL_Y)
DR_X = 0.14                                                      # скамья под левым коленом и левой рукой
FB_ROW = flat_bench('FlatBenchRow', x=DR_X, z=0.16)
DR_KA = 34                                                       # бедро опорной ноги наклонено назад — таз ниже
def dr_base(th):
    P = dict(pelvis=(th, 0, 0), spine=(2, 0, 0), neck=-18, head=-6, toe=6, footR=(-0.21, 0.10), hips=(0, 0, 0))
    P['footL'] = (0.12, -0.3, 160, 0.4)
    W = body_W(P); hj = W('LeftUpLeg')[:3, 3]; la = LIMB[('Left', 'leg')]['la']; lb = LIMB[('Left', 'leg')]['lb']
    knee = np.array([DR_X-0.01, FB_TOP+0.066, 0.0]); ka = np.radians(DR_KA)
    hy = knee[1]+la*0.995*np.cos(ka)-hj[1]
    P['hips'] = (DR_X-0.01-hj[0], hy, knee[2]-hj[2]+la*0.995*np.sin(ka))
    ank = np.array([knee[0], FB_TOP+0.055, knee[2]-np.sqrt(lb**2-0.011**2)*0.995])
    P['footL'] = foot_on_bench(ank, 145, 'Left', 6); P['kneeL'] = np.array([0, -1.0, 0.25]); P['toefollowL'] = True
    hr = body_W(P)('RightUpLeg')[:3, 3]
    P['footR'] = (hr[0]-0.08, hr[2]+0.12)                          # стоящая нога — под тазом, чуть в сторону
    return P
ARM_W = LIMB[('Left', 'arm')]['la']+LIMB[('Left', 'arm')]['lb']           # плечо → запястье
for _th in range(60, 110):                                       # корпус почти параллельно полу, опорная рука прямая
    _W = body_W(dr_base(_th))
    if _W('LeftArm')[1, 3]-(FB_TOP+0.06) <= ARM_W*0.95: break
DR_TH = _th; _S = _W('LeftArm')[:3, 3]; print('  dumbbell row: pelvis pitch', DR_TH, 'shoulder y %.3f hips y %.3f' % (_S[1], _W('Hips')[1, 3]))
DR_TF = 0.30
_W = body_W(dr_base(DR_TH)); _SL = _W('LeftArm')[:3, 3]
_dy = _SL[1]-(FB_TOP+0.06); _dz = np.sqrt(max(0, (ARM_W*0.975)**2-_dy**2-0.02**2))
DR_HAND = np.array([_SL[0]+0.02, FB_TOP+0.06, min(_SL[2]+_dz, 0.16+0.6-0.07)])
DR_WRIST = -75
def drow_fn(P):
    s = P['s']; P.update(dr_base(DR_TH))
    # небольшое, почти параллельное полу движение корпуса: чуть поднимается и раскрывается к рабочей руке
    h = np.array(P['hips']); P['hips'] = tuple(h+np.array([-0.008*s, 0.018*s, -0.012*s]))
    P['pelvis'] = (DR_TH-2.5*s, -2*s, -2*s); P['spine'] = (2-1.5*s, -5*s, -4*s)
    W = body_W(P); H = W('Hips')[:3, 3]; U_ = nz(W('Spine2')[:3, 3]-H); F_ = nz(np.cross([1, 0, 0], U_))
    P['handL'] = DR_HAND                                          # опорная ладонь неподвижно лежит на скамье
    P['elbowL'] = np.array([0.3, 0, -1.0]); P['palmL'] = np.array([0, -1.0, 0]); P['wristL'] = DR_WRIST
    SR = W('RightArm')[:3, 3]
    bottom = np.array([SR[0]-0.03, SR[1]-(REACH*0.97), SR[2]+0.04])
    top = H+U_*0.14+F_*DR_TF+np.array([-0.21, 0, 0])
    P['gripR'] = bottom+(top-bottom)*s
    P['elbowR'] = nz(lerp((-0.25, 0.0, -1.0), (-0.3, 0.5, -1.0), s))
    P['palmR'] = np.array([1.0, 0, 0]); P['axisR'] = np.array([0, 0, 1.0])
    return P
def one_db(clip, N):
    out = dumbbell_track(clip, N)
    return [x for x in out if x[0] == DB[1]]
animate('dumbbell_row', [(0, dict(s=0)), (0.3, dict(s=0)), (1.0, dict(s=1)), (1.25, dict(s=1)), (2.3, dict(s=0))],
        props_fn=lambda c, N: [(FB_ROW, 'show', None)]+one_db(c, N), grip=True, hand={'Left': FLAT, 'Right': FIST}, fn=drow_fn)

# ---------------- болгарские выпады ----------------
BSS_FX = 0.12
FB_BSS = flat_bench('FlatBenchSplit', x=-0.10, z=-1.06)
def bss_fn(P):
    s = P['s']
    P.update(toe=8, kneeout=4, pelvis=(6+12*s, 0, 0), spine=(3+3*s, 0, 0), neck=-6-8*s, head=-2,
             hips=(0.02, 0.80-0.27*s, -0.04-0.06*s), footL=(BSS_FX, 0.36))
    lb = LIMB[('Right', 'leg')]['lb']
    P['footR'] = foot_on_bench(np.array([-0.10, FB_TOP+0.07, -0.43]), 150, 'Right', 8); P['kneeR'] = np.array([0, -1.0, 0.35]); P['toefollowR'] = True
    for k, sd, sg in (('L', 'Left', 1), ('R', 'Right', -1)):
        S = shoulder(P, sd)
        P['grip'+k] = S+REACH*0.97*nz(np.array([sg*0.06, -1, 0.03]))
        P['elbow'+k] = np.array([sg*0.2, 0, -1.0]); P['palm'+k] = np.array([-sg*1.0, 0, 0]); P['axis'+k] = np.array([0, 0, 1.0])
    return P
animate('bulgarian_split_squat', [(0, dict(s=0)), (0.35, dict(s=0)), (1.5, dict(s=1)), (1.7, dict(s=1)), (2.8, dict(s=0))],
        props_fn=lambda c, N: [(FB_BSS, 'show', None)]+dumbbell_track(c, N), grip=True, fn=bss_fn)

# ---------------- ягодичный мост со штангой (hip thrust) ----------------
HT_ZB = -0.40                                                    # центр скамьи (стоит поперёк)
FB_HT = flat_bench('FlatBenchThrust', z=HT_ZB, across=True)
HT_C = np.array([0, FB_TOP-0.01, HT_ZB+0.14])                    # край скамьи под лопатками
def ht_body(s, feet=None):
    tilt = 38*(1-s)
    P = dict(pelvis=(-(90-tilt)+4*s, 0, 0), spine=(-4*s, 0, 0), neck=12+22*s, head=6, toe=12, kneeout=8, hips=(0, 0, 0))
    P['footL'] = feet or (0.18, 0.6); P['footR'] = (-P['footL'][0], P['footL'][1])
    W = body_W(P); H = W('Hips')[:3, 3]; S2 = W('Spine2')[:3, 3]; U_ = nz(S2-H); F_ = nz(np.cross([1, 0, 0], U_))
    P['hips'] = tuple(HT_C+F_*0.105-U_*0.04-(S2-H))
    return P
_P = ht_body(1.0); _W = body_W(_P); _hj = _W('LeftUpLeg')[:3, 3]; _la = LIMB[('Left', 'leg')]['la']
_knee_z = _hj[2]+_la*0.97
HT_FEET = (0.19, _knee_z+0.10)
print('  hip thrust: hips top', np.round(_P['hips'], 3), 'feet z %.2f' % HT_FEET[1])
def ht_fn(P):
    s = P['s']; P.update(ht_body(s, HT_FEET))
    Rp = euler(*P['pelvis']); H = np.array(P['hips'])
    bar = H+Rp@np.array([0, -0.07, 0.205+0.035*(1-s)])                       # гриф лежит в тазобедренном сгибе
    P['_bar'] = bar
    for k, sg in (('L', 1), ('R', -1)):
        P['grip'+k] = bar+np.array([sg*0.34, 0, 0])
        P['elbow'+k] = np.array([sg*0.6, -1.0, 0.0]); P['axis'+k] = np.array([1.0, 0, 0]); P['palm'+k] = np.array([0, -1.0, 0.3])
    return P
_b0 = ht_fn(dict(s=0.0))['_bar']; print('  hip thrust bar bottom y %.3f (plates %.3f)' % (_b0[1], _b0[1]-PLATE_R))
animate('hip_thrust', [(0, dict(s=0)), (0.3, dict(s=0)), (1.1, dict(s=1)), (1.5, dict(s=1)), (2.6, dict(s=0))],
        props_fn=lambda c, N: [(FB_HT, 'show', None)]+bar_track(c, N), grip=True, fn=ht_fn)

# ================= партия 4: блочная стойка, брусья, турник =================
M_IRON2 = mat('Stack iron', (0.03, 0.03, 0.034), 0.5, 0.5)
M_CABLE = mat('Cable', (0.02, 0.02, 0.022), 0.3, 0.5)
def dyn_cyl(name, r, m, seg=10):
    """Цилиндр вдоль X от 0 до 1: анимируется положением начала, поворотом и длиной (scale.x)."""
    g = Geo(); g.cyl([0.5, 0, 0], [1, 0, 0], r, 1.0, seg=seg)
    return add_node(name, add_mesh([(m, g)]))
def stretch(node, A, B):
    t, r, sc = [], [], []
    for a, b in zip(A, B):
        d = np.asarray(b)-np.asarray(a); L = max(np.linalg.norm(d), 1e-4)
        t.append(np.asarray(a, float)); r.append(look(d, (0, 0, 1) if abs(d[1]) > 0.9*L else (0, 1, 0))); sc.append([L, 1, 1])
    return [(node, 'translation', t), (node, 'rotation', fix_sign(r)), (node, 'scale', sc)]

def cable_tower(name, ZT, PY, seat=None):
    """Блочная стойка: центр на z=ZT, блок на высоте PY смотрит к персонажу (к -Z)."""
    fr, acc, rub, st, pad, chr_ = Geo(), Geo(), Geo(), Geo(), Geo(), Geo()
    H = 2.32; zf = ZT-0.20                                              # передняя колонна с кареткой
    rbox(fr, [0, 0.03, ZT], (0.76, 0.06, 0.62), 0.01, n=3)
    for sg in (-1, 1):
        rtube(fr, [sg*0.30, 0.06, ZT+0.14], [sg*0.30, H, ZT+0.14], 0.07, 0.07, up=(0, 0, 1))
        tube(chr_, [sg*0.09, 0.12, ZT+0.10], [sg*0.09, 1.25, ZT+0.10], 0.007)         # направляющие стека
    rtube(fr, [-0.34, H, ZT+0.14], [0.34, H, ZT+0.14], 0.08, 0.08, up=(0, 1, 0))
    rtube(fr, [0, H, ZT+0.14], [0, H, zf], 0.07, 0.07)
    rtube(fr, [0, 0.06, zf], [0, H, zf], 0.07, 0.07, up=(0, 0, 1))
    for i in range(14): rbox(acc, [0, 0.35+i*0.13, zf-0.036], (0.03, 0.012, 0.004), 0.001, n=2)   # отметки высоты
    rbox(fr, [0, PY+0.07, zf-0.035], (0.13, 0.20, 0.07), 0.015)                      # каретка
    rub.cyl([0, PY, zf-0.12], [1, 0, 0], 0.055, 0.035, seg=28)                       # ролик
    rbox(fr, [0, PY, zf-0.095], (0.06, 0.06, 0.08), 0.01)
    for i in range(5): rbox(st, [0, 0.13+i*0.062+0.028, ZT+0.10], (0.30, 0.056, 0.12), 0.008, n=3)
    rbox(rub, [0, 0.07, ZT+0.10], (0.30, 0.03, 0.12), 0.01, n=2)
    tube(chr_, [0, 0.62, ZT+0.10], [0, H-0.03, ZT+0.10], 0.005)
    groups = [(M_STEEL, fr), (M_ACCENT, acc), (M_RUBBER, rub), (M_IRON2, st), (mid['Chrome'], chr_)]
    if seat is not None:
        sz, sy, kz, ky = seat
        rtube(fr, [0, 0.05, ZT-0.25], [0, 0.05, sz-0.05], 0.07, 0.05)
        rtube(fr, [0, 0.05, sz], [0, sy-0.07, sz], 0.07, 0.07, up=(0, 0, 1))
        rbox(pad, [0, sy-0.035, sz], (0.36, 0.07, 0.38), 0.03)
        tube(fr, [-0.32, 0.03, sz], [0.32, 0.03, sz], 0.03)
        rtube(fr, [0, sy-0.07, sz+0.06], [0, ky, kz], 0.06, 0.05, up=(0, 0, 1))
        for sg in (-1, 1): pad.cyl([sg*0.13, ky, kz], [1, 0, 0], 0.055, 0.20, seg=24)
        tube(fr, [-0.03, ky, kz], [0.03, ky, kz], 0.03)
        groups.append((M_PAD, pad))
    node = add_node(name, add_mesh(groups))
    top = Geo()
    for i in range(3): rbox(top, [0, i*0.062, 0], (0.30, 0.056, 0.12), 0.008, n=3)
    top.cyl([0, 0.0, -0.065], [0, 0, 1], 0.012, 0.03)                          # штифт под рабочим весом
    stack = add_node(name+'Stack', add_mesh([(M_IRON2, top)]), (0, 0, 0))
    return dict(node=node, stack=stack, pulley=np.array([0, PY-0.055, zf-0.12]), stack0=np.array([0, 0.13+5*0.062+0.028, ZT+0.10]))
CABLE = dyn_cyl('Cable', 0.0055, M_CABLE)
def cable_props(T, ends):
    """Трос от ролика к рукояти + подъём верхней плиты стека на величину вытянутого троса."""
    P0 = [T['pulley']]*len(ends); L = np.array([np.linalg.norm(e-T['pulley']) for e in ends])
    lift = L-L.min()+0.02
    st = [T['stack0']+np.array([0, l, 0]) for l in lift]
    return [(T['node'], 'show', None), (T['stack'], 'show', None), (T['stack'], 'translation', st)]+stretch(CABLE, P0, ends)

def handle_bar(name, half, bend=0.0):
    g, gr = Geo(), Geo()
    g.cyl([0, 0, 0], [1, 0, 0], 0.013, 2*half-(0.16 if bend else 0))
    if bend:
        for sg in (-1, 1):
            a = np.array([sg*(half-0.08), 0, 0]); b = a+np.array([sg*0.14, -0.06, 0])
            g.cyl((a+b)/2, b-a, 0.013, np.linalg.norm(b-a))
    for sg in (-1, 1): gr.cyl([sg*(half-0.12 if bend else half*0.65), 0, 0], [1, 0, 0], 0.017, 0.12 if bend else half*0.6)
    g.cyl([0, 0.025, 0], [0, 1, 0], 0.012, 0.05); g.cyl([0, 0.055, 0], [0, 0, 1], 0.018, 0.012)
    return add_node(name, add_mesh([(mid['Chrome'], g), (M_RUBBER, gr)]))
def bar_handle_props(node, clip, N, T, up_off=0.0):
    G = grips(clip, N); t, r, ends = [], [], []
    for g in G:
        c = (g['gl']+g['gr'])/2; d = nz(g['gl']-g['gr'])
        toward = nz(T['pulley']-c); upv = toward-np.dot(toward, d)*d
        t.append(c); r.append(look(d, upv)); ends.append(c+nz(upv)*0.06)
    return [(node, 'show', None), (node, 'translation', t), (node, 'rotation', fix_sign(r))]+cable_props(T, ends)

# ---------------- разгибания на блоке (трицепс) ----------------
TPD = cable_tower('CableTowerTPD', 0.78, 2.05)
PDBAR = handle_bar('PushdownBar', 0.25)
def pushdown_fn(P):
    s = P['s']                                                       # 0 — предплечья вверх, 1 — руки выпрямлены
    b = np.sin(np.pi*s)                                              # корпус чуть «дожимает» вес и пружинит
    P.update(footL=(0.19, 0.04), footR=(-0.19, 0.04), toe=12, kneeout=5, hips=(0, RP['Hips'][1]-0.03-0.012*s, -0.02-0.02*s),
             pelvis=(8+5*s, 0, 0), spine=(4+4*s+1.5*b, 0, 0), neck=-10-5*s, head=-2)
    phi = 92-84*s
    for k in 'LR':
        curl_arm(P, k, phi, 0.115)
        P['axis'+k] = np.array([1.0, 0, 0]); P['palm'+k] = nz(np.array([0, -np.sin(np.radians(phi)), -np.cos(np.radians(phi))]))
        P['wrist'+k] = 8*(1-s)
    return P
animate('triceps_pushdown', [(0, dict(s=0)), (0.3, dict(s=0)), (1.0, dict(s=1)), (1.25, dict(s=1)), (2.25, dict(s=0))],
        props_fn=lambda c, N: bar_handle_props(PDBAR, c, N, TPD), fn=pushdown_fn)

# ---------------- тяга каната к лицу ----------------
FPT = cable_tower('CableTowerFP', 1.30, 1.62)
ROPE = [dyn_cyl('RopeL', 0.014, M_RUBBER, 12), dyn_cyl('RopeR', 0.014, M_RUBBER, 12)]
def facepull_fn(P):
    s = P['s']
    P.update(footL=(0.16, 0.10), footR=(-0.16, -0.02), toe=10, kneeout=4, hips=(0, RP['Hips'][1]-0.03, -0.03-0.015*s),
             pelvis=(-3-2*s, 0, 0), spine=(-2-3*s, 0, 0), neck=3*s, head=0, clav=(4*s, 4*s))
    W = body_W(P); Sm = (W('LeftArm')[:3, 3]+W('RightArm')[:3, 3])/2
    for k, sg in (('L', 1), ('R', -1)):
        a = Sm+np.array([sg*0.07, 0.03, REACH*0.93]); b = Sm+np.array([sg*0.20, 0.15, 0.22])
        P['grip'+k] = a+(b-a)*s+np.array([sg*0.05, 0.05, 0])*np.sin(np.pi*s)
        P['elbow'+k] = nz(lerp((sg*0.7, -0.7, -0.2), (sg*1.0, 0.1, -0.15), s))
        P['axis'+k] = np.array([0, 1.0, 0]); P['palm'+k] = np.array([-sg*1.0, 0, 0.3])
    return P
def facepull_props(clip, N):
    G = grips(clip, N); J, ends = [], {'l': [], 'r': []}
    for g in G:
        c = (g['gl']+g['gr'])/2; j = c+nz(FPT['pulley']-c)*0.16; J.append(j)
        for sd in 'lr': ends[sd].append(g['g'+sd]-np.array([0, 0.05, 0]))
    return cable_props(FPT, J)+stretch(ROPE[0], J, ends['l'])+stretch(ROPE[1], J, ends['r'])
animate('face_pull', [(0, dict(s=0)), (0.4, dict(s=0)), (1.5, dict(s=1)), (1.85, dict(s=1)), (3.2, dict(s=0))],
        props_fn=facepull_props, grip=True, fn=facepull_fn)

# ---------------- тяга верхнего блока ----------------
LP_SEAT = 0.48; LP_SZ = 0.0
LP_BASE = dict(hips=(0, LP_SEAT+0.13, LP_SZ-0.06), footL=(0.20, 0.47), footR=(-0.20, 0.47), toe=12, kneeout=8)
def lp_body(s):
    lean = 12+12*np.sin(np.pi/2*min(1, s*1.4))
    return dict(LP_BASE, pelvis=(-lean*0.7, 0, 0), spine=(-lean*0.3-2*s, 0, 0), neck=lean*0.75, head=-3*s, clav=(10*(1-s), 10*(1-s)))
_W = body_W(lp_body(0)); _kn = (_W('LeftLeg')[:3, 3]+_W('RightLeg')[:3, 3])/2
LPT = cable_tower('CableTowerLP', 0.62, 2.33, seat=(LP_SZ, LP_SEAT, _kn[2]-0.07, _kn[1]+0.12))
LPBAR = handle_bar('LatBar', 0.58, bend=1)
def lp_fn(P):
    s = P['s']; P.update(lp_body(s))
    W = body_W(P); Sm = (W('LeftArm')[:3, 3]+W('RightArm')[:3, 3])/2
    H = W('Hips')[:3, 3]; U_ = nz(W('Spine2')[:3, 3]-H); F_ = nz(np.cross([1, 0, 0], U_))
    for k, sg in (('L', 1), ('R', -1)):
        S = W(('Left' if k == 'L' else 'Right')+'Arm')[:3, 3]; dx = 0.40-abs(S[0])
        top = np.array([sg*0.40, S[1]+np.sqrt((REACH*0.975)**2-dx**2-0.17**2), S[2]+0.17])
        bot = Sm+F_*0.21-U_*0.05+np.array([sg*0.40, 0, 0])
        P['grip'+k] = top+(bot-top)*s
        P['elbow'+k] = nz(lerp((sg*1.0, -0.2, -0.2), (sg*0.6, -1.0, -0.4), s))
        P['axis'+k] = np.array([1.0, 0, 0]); P['palm'+k] = nz(np.array([0, 0.3, 1.0]))
    return P
animate('lat_pulldown', [(0, dict(s=0)), (0.35, dict(s=0)), (1.15, dict(s=1)), (1.4, dict(s=1)), (2.5, dict(s=0))],
        props_fn=lambda c, N: bar_handle_props(LPBAR, c, N, LPT), grip=True, fn=lp_fn)

# ---------------- отжимания на брусьях ----------------
DIP_Y = 1.24; DIP_X = 0.30; DIP_Z = 0.10
def dip_station():
    fr, acc, rub, gr = Geo(), Geo(), Geo(), Geo()
    for sg in (-1, 1):
        x = sg*DIP_X
        tube(fr, [x, DIP_Y, DIP_Z-0.32], [x, DIP_Y, DIP_Z+0.30], 0.02)                    # перекладина
        gr.cyl([x, DIP_Y, DIP_Z+0.0], [0, 0, 1], 0.024, 0.30, seg=24)                     # прорезиненный хват
        for z in (DIP_Z-0.30, DIP_Z+0.28):
            rtube(fr, [x+sg*0.02, 0.05, z], [x+sg*0.02, DIP_Y-0.02, z], 0.055, 0.055, up=(0, 0, 1))
        rtube(fr, [x+sg*0.02, 0.04, DIP_Z-0.55], [x+sg*0.02, 0.04, DIP_Z+0.50], 0.07, 0.06)  # опора
        for z in (DIP_Z-0.55, DIP_Z+0.50): rbox(rub, [x+sg*0.02, 0.012, z], (0.08, 0.024, 0.06), 0.01, n=2)
        rbox(acc, [x+sg*0.05, 0.75, DIP_Z+0.28], (0.004, 0.25, 0.04), 0.002, n=2)
    rtube(fr, [-DIP_X-0.02, 0.35, DIP_Z-0.30], [DIP_X+0.02, 0.35, DIP_Z-0.30], 0.05, 0.05, up=(0, 1, 0))
    rtube(fr, [-DIP_X-0.02, 0.04, DIP_Z-0.30], [DIP_X+0.02, 0.04, DIP_Z-0.30], 0.05, 0.05, up=(0, 1, 0))
    return add_node('DipStation', add_mesh([(M_STEEL, fr), (M_ACCENT, acc), (M_RUBBER, rub), (M_RUBBER, gr)]))
DIPS = dip_station()
def legs_tucked(P, bend=1.0):
    """Голени скрещены сзади: бедро чуть вперёд, колени согнуты ~90°."""
    W = body_W(P); a = np.radians(28*bend)
    for k, sd, sg in (('L', 'Left', 1), ('R', 'Right', -1)):
        hj = W(sd+'UpLeg')[:3, 3]; Lm = LIMB[(sd, 'leg')]
        dth = W('Hips')[:3, :3]@np.array([0, 0, 1.0]); dth = nz(np.array([0, -1, 0])+nz(dth)*np.tan(np.radians(14)))
        kn = hj+Lm['la']*nz(dth+np.array([sg*0.02, 0, 0]))
        ank = kn+Lm['lb']*nz(np.array([sg*0.03, -np.cos(a), -np.sin(a)*1.6]))
        P['foot'+k] = foot_on_bench(ank, 55, sd, 4)
        P['knee'+k] = np.array([0, 0.0, 1.0])
    return P
RT_DIP = 12                                                      # плечи раскрыты, лопатки сведены
def dip_fn(P):
    s = P['s']                                                    # 0 — руки прямые, 1 — внизу
    P.update(pelvis=(8+24*s, 0, 0), spine=(4+8*s, 0, 0), neck=-10-16*s, head=-4, clav=(-3, -3), retract=RT_DIP*s, toe=4,
             footL=(0.1, 0), footR=(-0.1, 0), hips=(0, 0, 0))
    rel = mid_shoulder_rel(P)
    hand_y = DIP_Y+0.01
    top = np.array([0, hand_y+np.sqrt((REACH*0.975)**2-(DIP_X-0.19)**2), DIP_Z+0.0])
    bot = np.array([0, hand_y+LIMB[('Left', 'arm')]['lb']*0.95+LIMB[('Left', 'arm')]['la']*0.22, DIP_Z+0.09])   # плечо ≈ параллельно полу, локоть ~90°
    P['hips'] = top+(bot-top)*s-rel
    P = legs_tucked(P)
    for k, sg in (('L', 1), ('R', -1)):
        P['grip'+k] = np.array([sg*DIP_X, hand_y, DIP_Z+0.0])
        P['elbow'+k] = np.array([sg*0.5, -0.1, -1.0]); P['axis'+k] = np.array([0, 0, 1.0]); P['palm'+k] = np.array([-sg*1.0, -0.5, 0])
    return P
animate('dips', [(0, dict(s=0)), (0.35, dict(s=0)), (1.4, dict(s=1)), (1.6, dict(s=1)), (2.5, dict(s=0))],
        props_fn=lambda c, N: [(DIPS, 'show', None)], grip=True, fn=dip_fn)

# ---------------- подъём ног в висе ----------------
HB_Y = 2.32
def pull_frame():
    fr, rub, acc, gr = Geo(), Geo(), Geo(), Geo()
    tube(fr, [-0.62, HB_Y, 0], [0.62, HB_Y, 0], 0.016)
    for sg in (-1, 1):
        gr.cyl([sg*0.24, HB_Y, 0], [1, 0, 0], 0.02, 0.16, seg=24)
        rtube(fr, [sg*0.66, 0.05, -0.05], [sg*0.66, HB_Y+0.06, -0.05], 0.07, 0.07, up=(0, 0, 1))
        rtube(fr, [sg*0.66, HB_Y, -0.05], [sg*0.60, HB_Y, 0.0], 0.05, 0.05)
        rtube(fr, [sg*0.66, 0.04, -0.65], [sg*0.66, 0.04, 0.55], 0.08, 0.06)
        for z in (-0.65, 0.55): rbox(rub, [sg*0.66, 0.012, z], (0.09, 0.024, 0.06), 0.01, n=2)
        rtube(fr, [sg*0.66, 0.05, -0.55], [sg*0.66, 1.0, -0.05], 0.05, 0.05, up=(1, 0, 0))
        rbox(acc, [sg*0.66, 1.6, 0.0-0.012], (0.04, 0.3, 0.004), 0.002, n=2)
    rtube(fr, [-0.66, HB_Y+0.06, -0.05], [0.66, HB_Y+0.06, -0.05], 0.06, 0.06, up=(0, 1, 0))
    return add_node('PullFrame', add_mesh([(M_STEEL, fr), (M_RUBBER, rub), (M_ACCENT, acc), (M_RUBBER, gr)]))
PFRAME = pull_frame()
def hlr_fn(P):
    s = P['s']; al = 95*s                                         # угол подъёма ног
    P.update(pelvis=(-0.30*al, 0, 0), spine=(0.20*al, 0, 0), neck=-4+0.14*al, head=0, clav=(14, 14), toe=4,
             footL=(0.1, 0), footR=(-0.1, 0), hips=(0, 0, 0))
    rel = mid_shoulder_rel(P)
    dy = np.sqrt((REACH*0.975)**2-(0.24-0.19)**2)
    P['hips'] = np.array([0, HB_Y-dy, -0.04*np.sin(np.pi/2*s)])-rel
    W = body_W(P)
    for k, sd, sg in (('L', 'Left', 1), ('R', 'Right', -1)):
        hj = W(sd+'UpLeg')[:3, 3]; Lm = LIMB[(sd, 'leg')]; a = np.radians(al)
        a_ = np.radians(92*s)                                         # угол ног относительно вертикали (в мире)
        d = np.array([-sg*0.015, -np.cos(a_), np.sin(a_)])
        bend = 0.985-0.02*np.sin(np.pi*s)                               # колени чуть мягче в середине подъёма
        P['foot'+k] = foot_on_bench(hj+d*(Lm['la']+Lm['lb'])*bend, 30-np.degrees(a_), sd, 4)
        P['knee'+k] = np.array([0, np.sin(a_), np.cos(a_)])
        P['grip'+k] = np.array([sg*0.24, HB_Y, 0.0])
        P['elbow'+k] = np.array([sg*1.0, 0, -0.3]); P['axis'+k] = np.array([1.0, 0, 0]); P['palm'+k] = np.array([0, 0.2, 1.0])
    return P
animate('hanging_leg_raise', [(0, dict(s=0)), (0.35, dict(s=0)), (1.25, dict(s=1)), (1.5, dict(s=1)), (2.6, dict(s=0))],
        props_fn=lambda c, N: [(PFRAME, 'show', None)], grip=True, fn=hlr_fn)

# ================= партия 5: жим ногами, подъёмы на носки, гиперэкстензия =================
def heel_ball(ball, heel, side, yaw):
    """Голеностоп для стопы с подушечкой в точке ball и наклоном heel."""
    Df = Ry(yaw*(1 if side == 'Left' else -1))@Rx(heel)
    return ball-Df@(RP[side+'ToeBase']-RP[side+'Foot'])

# ---------------- подъёмы на носки (на степ-платформе) ----------------
STEP_H = 0.15; CR_BZ = 0.05
def calf_step():
    g, rub, acc = Geo(), Geo(), Geo()
    rbox(g, [0, STEP_H/2+0.01, CR_BZ+0.11], (0.86, STEP_H-0.02, 0.34), 0.03)
    rbox(rub, [0, STEP_H-0.002, CR_BZ+0.11], (0.80, 0.008, 0.30), 0.004, n=3)
    for sg in (-1, 1):
        rbox(acc, [sg*0.43, STEP_H*0.55, CR_BZ+0.11], (0.006, 0.03, 0.30), 0.002, n=2)
        rbox(rub, [sg*0.36, 0.01, CR_BZ+0.11], (0.10, 0.02, 0.30), 0.006, n=2)
    return add_node('Step', add_mesh([(M_PAD, g), (M_RUBBER, rub), (M_ACCENT, acc)]))
STEP = calf_step()
_ank0 = heel_ball(np.array([0.11, BALL_Y, 0.0]), 0, 'Left', 10)
def calf_fn(P):
    s = P['s']; heel = -14+44*s                                   # пятки ниже края → высоко на носках
    P.update(toe=10, kneeout=2, pelvis=(1, 0, 0), spine=(0, 0, 0), neck=-1, head=0)
    for k, sd, sg in (('L', 'Left', 1), ('R', 'Right', -1)):
        ball = np.array([sg*0.11, BALL_Y+STEP_H, CR_BZ]); P['foot'+k] = (ball[0], ball[2], heel, STEP_H)
    ank = heel_ball(np.array([0.11, BALL_Y+STEP_H, CR_BZ]), heel, 'Left', 10)
    P['hips'] = (0, RP['Hips'][1]-0.006+(ank[1]-_ank0[1]), ank[2]-_ank0[2]-0.01)
    P['swing'] = 0
    return arms_relaxed(P)                                        # руки свободно вдоль тела
animate('calf_raise', [(0, dict(s=0.3)), (0.25, dict(s=0)), (0.55, dict(s=0)), (1.2, dict(s=1)), (1.6, dict(s=1)), (2.2, dict(s=0.3))],
        props_fn=lambda c, N: [(STEP, 'show', None)], hand=RELAX, grip=True, fn=calf_fn)

# ---------------- жим ногами (платформа под 45°) ----------------
LP_R = nz(np.array([0, 1.0, 1.0]))                                # направление салазок
LP_N = nz(np.array([0, 1.0, -1.0]))                               # «вверх» по платформе
LP_BA = 42                                                        # спинка, градусов от пола
LP_BASE2 = dict(hips=(0, 0.47, 0.0), pelvis=(-(90-LP_BA)*0.85, 0, 0), spine=(-(90-LP_BA)*0.15, 0, 0), neck=24, head=8, toe=12)
_W = body_W({**LP_BASE2, 'footL': (0.15, 0.6), 'footR': (-0.15, 0.6)})
LPH = (_W('LeftUpLeg')[:3, 3]+_W('RightUpLeg')[:3, 3])/2
_LL = LIMB[('Left', 'leg')]['la']+LIMB[('Left', 'leg')]['lb']
LPU = nz(_W('Spine2')[:3, 3]-_W('Hips')[:3, 3]); LPB = nz(np.cross(LPU, [1, 0, 0]))   # к спинке
LP_OFF = LP_N*0.10                                                 # стопы чуть выше линии таза
def lp_ankles(D):
    return [LPH+LP_R*D+LP_OFF+np.array([sg*0.17, 0, 0]) for sg in (1, -1)]
LP_DTOP = np.sqrt(max(0, (_LL*0.965)**2-0.10**2)); LP_DBOT = _LL*0.50
SOLE = 0.105                                                       # от голеностопа до подошвы
def leg_press_machine():
    fr, pad, acc, rub = Geo(), Geo(), Geo(), Geo()
    H = np.array(LP_BASE2['hips'])
    rbox(pad, [0, 0.40-0.035, H[2]+0.10], (0.40, 0.07, 0.40), 0.03)
    Wd = LPU; rbox(pad, H+LPU*0.33+LPB*0.16, (0.42, 0.07, 0.72), 0.03, np.stack([np.array([1., 0, 0]), -LPB, LPU], 1))
    rtube(fr, [0, 0.05, H[2]-0.70], [0, 0.05, H[2]+1.90], 0.10, 0.08)
    rtube(fr, [0, 0.05, H[2]+0.10], [0, 0.33, H[2]+0.10], 0.08, 0.08, up=(0, 0, 1))
    rtube(fr, [0, 0.05, H[2]-0.35], H+LPU*0.33+LPB*0.21, 0.07, 0.06)
    for sg in (-1, 1):
        a = LPH+LP_R*0.45+np.array([sg*0.34, 0, 0])-LP_N*0.25; b = a+LP_R*1.10
        rtube(fr, a, b, 0.06, 0.08, up=LP_N)
        rtube(fr, [sg*0.34, 0.05, b[2]], b, 0.06, 0.06, up=(0, 0, 1))
        rtube(fr, [sg*0.34, 0.05, a[2]], a, 0.06, 0.06, up=(0, 0, 1))
        tube(fr, [sg*0.30, 0.40, H[2]-0.10], [sg*0.30, 0.40, H[2]+0.16], 0.016); rub.cyl([sg*0.30, 0.40, H[2]+0.04], [0, 0, 1], 0.022, 0.12)
        rtube(fr, [sg*0.30, 0.40, H[2]-0.10], [sg*0.20, 0.36, H[2]-0.10], 0.03, 0.03)
        rbox(acc, a+LP_R*0.55+np.array([sg*0.032, 0, 0])-LP_N*0.0, (0.004, 0.05, 0.8), 0.002, np.stack([np.array([1., 0, 0]), LP_N, LP_R], 1), n=2)
    tube(fr, [-0.36, 0.05, H[2]+1.90], [0.36, 0.05, H[2]+1.90], 0.03)
    machine = add_node('LegPress', add_mesh([(M_STEEL, fr), (M_PAD, pad), (M_ACCENT, acc), (M_RUBBER, rub)]))
    # салазки: начало координат — центр поверхности платформы
    s_fr, s_pl, s_rb = Geo(), Geo(), Geo()
    Rm = np.stack([np.array([1., 0, 0]), -LP_N, -LP_R], 1)
    rbox(s_fr, LP_R*0.025, (0.62, 0.58, 0.05), 0.01, Rm)
    rbox(s_rb, -LP_R*0.002, (0.56, 0.52, 0.006), 0.003, Rm, n=3)
    for sg in (-1, 1):
        rtube(s_fr, LP_R*0.05+np.array([sg*0.30, 0, 0])-LP_N*0.20, LP_R*0.05+np.array([sg*0.34, 0, 0])-LP_N*0.25, 0.05, 0.05)
        rtube(s_fr, LP_R*0.05+np.array([sg*0.34, 0, 0])+LP_N*0.20, LP_R*0.16+np.array([sg*0.34, 0, 0])-LP_N*0.25, 0.06, 0.05)   # ползун на рельсе
        h0 = np.array([sg*0.40, 0, 0])+LP_R*0.13-LP_N*0.04                   # рог для блинов на каретке
        s_fr.cyl(h0+np.array([sg*0.12, 0, 0]), [1, 0, 0], 0.025, 0.26)
        s_fr.cyl(h0+np.array([sg*0.015, 0, 0]), [1, 0, 0], 0.045, 0.03)
        for i, r_ in enumerate((0.20, 0.20, 0.14)):
            s_pl.cyl(h0+np.array([sg*(0.055+i*0.048), 0, 0]), [1, 0, 0], r_, 0.044, seg=40)
    tube(s_fr, LP_R*0.13-LP_N*0.04-np.array([0.40, 0, 0]), LP_R*0.13-LP_N*0.04+np.array([0.40, 0, 0]), 0.03)   # поперечина каретки
    for sg in (-1, 1): rtube(s_fr, LP_R*0.05+np.array([sg*0.22, 0, 0])-LP_N*0.04, LP_R*0.13+np.array([sg*0.22, 0, 0])-LP_N*0.04, 0.05, 0.05)
    sled = add_node('LegPressSled', add_mesh([(M_STEEL, s_fr), (M_RUBBER, s_pl), (M_RUBBER, s_rb)]))
    return machine, sled
LPM, LPS = leg_press_machine()
def legpress_fn(P):
    s = P['s']; D = LP_DTOP+(LP_DBOT-LP_DTOP)*s                    # 0 — ноги почти прямые, 1 — колени ~90°
    P.update(LP_BASE2); P['neck'] = 24+6*s
    for (k, sd, sg), A in zip((('L', 'Left', 1), ('R', 'Right', -1)), lp_ankles(D)):
        Df = Ry(12*sg)@Rx(-135); ball = A+Df@(RP[sd+'ToeBase']-RP[sd+'Foot'])
        P['foot'+k] = (ball[0], ball[2], -135, ball[1]-BALL_Y); P['toefollow'+k] = True
        P['knee'+k] = np.array([sg*0.35, 0.7, -0.7])
        P['grip'+k] = np.array([sg*0.30, 0.40, 0.04]); P['elbow'+k] = np.array([sg*0.6, 0, -1.0])
        P['axis'+k] = np.array([0, 0, 1.0]); P['palm'+k] = np.array([-sg*1.0, 0, 0])
    P['_sled'] = LPH+LP_R*(D+SOLE)+LP_OFF
    return P
_LPK = [(0, dict(s=0)), (0.35, dict(s=0)), (1.45, dict(s=1)), (1.7, dict(s=1)), (2.6, dict(s=0))]
def lp_track(clip, N):
    # положение салазок = по подошвам: середина голеностопов + подошва
    t = []
    for f in range(N):
        W = rig.world(clip, f); A = (W('LeftFoot')[:3, 3]+W('RightFoot')[:3, 3])/2
        t.append(LPH+LP_R*(np.dot(A-LPH-LP_OFF, LP_R)+SOLE)+LP_OFF)
    return [(LPM, 'show', None), (LPS, 'show', None), (LPS, 'translation', t)]
animate('leg_press', _LPK, props_fn=lp_track, grip=True, fn=legpress_fn)

# ---------------- гиперэкстензия (тренажёр 45°) ----------------
HX_D = nz(np.array([0, 1.0, 1.0]))                                # линия ног
HX_F = nz(np.array([0, -1.0, 1.0]))                               # перед тела (к полу)
HX_ANK = np.array([0, 0.27, 0.0])
HX_LL = LIMB[('Left', 'leg')]['la']+LIMB[('Left', 'leg')]['lb']
HX_HJ = HX_ANK+HX_D*HX_LL*0.99
def hyper_machine():
    fr, pad, acc, rub = Geo(), Geo(), Geo(), Geo()
    Rm = np.stack([np.array([1., 0, 0]), -HX_F, HX_D], 1)
    # опора для стоп (перпендикулярно ногам)
    fp = HX_ANK-HX_D*0.115
    rbox(rub, fp, (0.46, 0.30, 0.04), 0.01, np.stack([np.array([1., 0, 0]), HX_F, -HX_D], 1)@np.diag([1, 1, 1]))
    # валики за голенью
    rl = HX_ANK+HX_D*0.10-HX_F*0.085
    for sg in (-1, 1): pad.cyl(rl+np.array([sg*0.11, 0, 0]), [1, 0, 0], 0.05, 0.18, seg=24)
    tube(fr, rl-np.array([0.02, 0, 0]), rl+np.array([0.02, 0, 0]), 0.025)
    # подушка под бёдрами (ниже тазобедренного сустава)
    hp = HX_HJ-HX_D*0.16+HX_F*0.135
    rbox(pad, hp, (0.40, 0.08, 0.26), 0.035, Rm)
    # рама
    beam0 = fp-HX_F*0.10-HX_D*0.05; beam1 = hp+HX_F*0.07-HX_D*0.10
    rtube(fr, beam0, beam1, 0.08, 0.08, up=-HX_F)
    rtube(fr, rl, beam0+HX_D*0.25, 0.05, 0.05)
    rtube(fr, [0, 0.05, beam0[2]-0.25], [0, 0.05, hp[2]+0.25], 0.10, 0.08)
    rtube(fr, [0, 0.05, beam0[2]], beam0, 0.07, 0.07, up=(0, 0, 1))
    rtube(fr, [0, 0.05, hp[2]+0.05], beam1, 0.07, 0.07, up=(0, 0, 1))
    for z in (beam0[2]-0.25, hp[2]+0.25):
        tube(fr, [-0.33, 0.05, z], [0.33, 0.05, z], 0.03)
        for sg in (-1, 1): rbox(rub, [sg*0.32, 0.015, z], (0.07, 0.03, 0.07), 0.01, n=2)
    for sg in (-1, 1):
        a = hp+HX_F*0.02+np.array([sg*0.24, 0, 0])-HX_D*0.05; tube(fr, a, a-HX_F*0.0+np.array([0, 0.18, 0])+HX_D*0.05, 0.016)
    rbox(acc, (beam0+beam1)/2+np.array([0.042, 0, 0]), (0.004, 0.03, np.linalg.norm(beam1-beam0)*0.7), 0.002,
         np.stack([np.array([1., 0, 0]), -HX_F, nz(beam1-beam0)], 1), n=2)
    return add_node('HyperBench', add_mesh([(M_STEEL, fr), (M_PAD, pad), (M_ACCENT, acc), (M_RUBBER, rub)]))
HYP = hyper_machine()
def hyper_fn(P):
    s = P['s']; th = 70*s                                         # 0 — корпус на одной линии с ногами, 1 — наклон вниз
    P.update(pelvis=(45+th*0.85, 0, 0), spine=(th*0.15, 0, 0), neck=-12+0.1*th, head=-4, toe=8, hips=(0, 0, 0))
    for k, sd, sg in (('L', 'Left', 1), ('R', 'Right', -1)):
        A = HX_ANK+np.array([sg*0.10, 0, 0])
        Df = Ry(8*sg)@Rx(45); ball = A+Df@(RP[sd+'ToeBase']-RP[sd+'Foot'])
        P['foot'+k] = (ball[0], ball[2], 45, ball[1]-BALL_Y); P['toefollow'+k] = True
    W = body_W(P); hj = (W('LeftUpLeg')[:3, 3]+W('RightUpLeg')[:3, 3])/2
    P['hips'] = HX_HJ-hj
    W = body_W(P); Hd = W('Head')[:3, 3]; R = wrot(W('Head'))
    for k, sg in (('L', 1), ('R', -1)):                           # руки скрещены на груди
        U_ = nz(W('Spine2')[:3, 3]-W('Hips')[:3, 3]); X_ = np.array([1.0, 0, 0]); F_ = nz(np.cross(X_, U_))
        So = W(('Right' if k == 'L' else 'Left')+'Arm')[:3, 3]
        lay = 0.03 if k == 'L' else 0.0                              # левое предплечье поверх правого
        P['hand'+k] = So+X_*sg*0.14-U_*(0.10+lay)+F_*(0.13+lay)       # запястье у груди, пальцы на противоположном плече
        P['elbow'+k] = nz(-U_+F_*0.6+X_*sg*0.2); P['palm'+k] = -F_
    return P
animate('back_extension', [(0, dict(s=0)), (0.35, dict(s=0)), (1.5, dict(s=1)), (1.75, dict(s=1)), (2.85, dict(s=0))],
        props_fn=lambda c, N: [(HYP, 'show', None)], hand=RELAX, fn=hyper_fn)

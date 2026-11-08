# Упражнения, собранные из поз (см. proc.py)
import numpy as np

def mid_shoulder_rel(P):
    """Середина плечевых суставов относительно таза для данного наклона корпуса."""
    Q = {k: v for k, v in P.items() if not k.startswith(('hand', 'grip'))}
    Q['hips'] = np.zeros(3); Q.setdefault('footL', (0.12, 0.0)); Q.setdefault('footR', (-0.12, 0.0))
    c, _ = solve(Q); W = rig.world(c, 0)
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

"""Выравнивает нижний край шорт в одну ровную линию (перерисовывает текстуру вокруг подола).
python3 shorts_hem.py <персонаж ath.glb> <папка текстур> <выходная папка> [t_hem=0.53] [выходной персонаж .glb]

Подол = плоскость, перпендикулярная бедру (кость UpLeg -> Leg), на доле t_hem длины бедра от тазобедренного сустава
(0.53 — чуть короче, чем у мужской модели, у неё край на ~0.58). Выше — ткань, ниже — кожа; меняются только пиксели
бедра в полосе t = 0.30..0.78. Если указан выходной персонаж, бедро в этой полосе ещё и сглаживается, чтобы не было
видно «ступенек» старых краёв шорт (в исходной модели шорты — утолщение на ноге, его край был неровный).
"""
import sys, os, shutil, numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import GLTF2, short

CHAR, TEX, OUT = sys.argv[1:4]     # [5-й аргумент — куда сохранить персонажа со сглаженным бедром]
T_HEM = float(sys.argv[4]) if len(sys.argv) > 4 else 0.53
BAND = (0.30, 0.78)       # где вообще можно менять пиксели (доля длины бедра)
SOFT = 0.006              # ширина сглаживания края (~2.5 мм)
COL = 'texture_pbr_20250901.png'; NRM = 'texture_pbr_20250901_normal.png'

g = GLTF2().load(CHAR); blob = g.binary_blob()
def rd(i):
    ac = g.accessors[i]; bv = g.bufferViews[ac.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[ac.type]
    dt = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[ac.componentType]
    return np.frombuffer(blob, dt, ac.count*n, bv.byteOffset+(ac.byteOffset or 0)).reshape(ac.count, n).astype(float)
pr = g.meshes[0].primitives[0]
P = rd(pr.attributes.POSITION); UV = rd(pr.attributes.TEXCOORD_0); F = rd(pr.indices).astype(int).reshape(-1, 3)
J = rd(pr.attributes.JOINTS_0).astype(int); W = rd(pr.attributes.WEIGHTS_0)
names = [short(g.nodes[j].name) for j in g.skins[0].joints]
IBM = rd(g.skins[0].inverseBindMatrices).reshape(-1, 4, 4).transpose(0, 2, 1)
JP = {n: np.linalg.inv(IBM[i])[:3, 3] for i, n in enumerate(names)}

col = np.asarray(Image.open(os.path.join(TEX, COL)).convert("RGB")).astype(np.float32)
nrm = np.asarray(Image.open(os.path.join(TEX, NRM)).convert("RGB")).astype(np.float32)
S = col.shape[0]
lum = col.mean(2)
is_orange = (col[..., 0] > col[..., 1] + 90) & (col[..., 0] > 140)

# покрытие текстуры треугольниками (нужно для «подтяжки» краёв островов)

def raster(tri_uv):
    """Пиксели внутри UV-треугольника и барицентрики."""
    x = tri_uv[:, 0]*S - 0.5; y = tri_uv[:, 1]*S - 0.5
    x0, x1 = int(np.floor(x.min())), int(np.ceil(x.max())); y0, y1 = int(np.floor(y.min())), int(np.ceil(y.max()))
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, S-1), min(y1, S-1)
    if x1 < x0 or y1 < y0: return None
    gx, gy = np.meshgrid(np.arange(x0, x1+1), np.arange(y0, y1+1))
    gx = gx.ravel(); gy = gy.ravel()
    d = (y[1]-y[2])*(x[0]-x[2]) + (x[2]-x[1])*(y[0]-y[2])
    if abs(d) < 1e-12: return None
    a = ((y[1]-y[2])*(gx-x[2]) + (x[2]-x[1])*(gy-y[2]))/d
    b = ((y[2]-y[0])*(gx-x[2]) + (x[0]-x[2])*(gy-y[2]))/d
    c = 1-a-b; e = -0.02
    m = (a >= e) & (b >= e) & (c >= e)
    return gx[m], gy[m], np.stack([a[m], b[m], c[m]], 1)

TMAP = np.full((S, S), np.nan)          # доля длины бедра для каждого пикселя бедра (NaN — не бедро)
for side in ['Left', 'Right']:
    A = JP[side+'UpLeg']; B = JP[side+'Leg']; ax = B-A; L = np.linalg.norm(ax); ax /= L
    ji = [names.index(side+'UpLeg'), names.index(side+'Leg')]
    wl = sum(W[:, k]*np.isin(J[:, k], ji) for k in range(4))
    tv = (P-A)@ax/L
    tri = F[(wl[F].max(1) > 0.5) & (tv[F].max(1) > BAND[0]) & (tv[F].min(1) < BAND[1])]
    print(side, 'L', round(L, 5), 'tris', len(tri))
    for f in tri:
        res = raster(UV[f])
        if res is None: continue
        gx, gy, bc = res
        TMAP[gy, gx] = ((bc@P[f])-A)@ax/L

def push_pull(img, known):
    """Заполняет неизвестные пиксели плавным продолжением известных (многоуровневое усреднение)."""
    w = known.astype(np.float32); c = img.astype(np.float32)*w[..., None]; levels = []
    while w.shape[0] > 1:
        levels.append((c, w))
        h = w.shape[0]//2
        w = w.reshape(h, 2, h, 2).sum((1, 3)); c = c.reshape(h, 2, h, 2, 3).sum((1, 3))
    out = c/np.maximum(w, 1e-9)[..., None]
    for c, w in reversed(levels):
        up = np.repeat(np.repeat(out, 2, 0), 2, 1)
        a = np.minimum(w, 1)[..., None]
        out = np.where(w[..., None] > 0, c/np.maximum(w, 1e-9)[..., None], up)*a + up*(1-a)
    return out

# пиксели, которые реально лежат на треугольниках (остальное — поля между островами)
from PIL import ImageDraw
cov = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cov)
for f in F:
    dr.polygon([tuple(q) for q in (UV[f]*S - 0.5)], fill=255)
covered = np.asarray(cov) > 0

band = ~np.isnan(TMAP) & (TMAP > BAND[0]) & (TMAP < BAND[1])
T = np.where(band, TMAP, 0)
inner = ndimage.binary_erosion(~np.isnan(TMAP), iterations=2)     # без пикселей на самом краю островов
old_cloth = inner & (lum < 85) & (col[..., 0]-col[..., 2] < 25) & ~is_orange                       # тёмная ткань в исходной текстуре
near_cloth = ndimage.binary_dilation(old_cloth, iterations=30)   # ткань + тень от неё на коже
want_cloth = band & (T < T_HEM + 2*SOFT)
want_skin = band & (T > T_HEM - 2*SOFT)
# кожа: заполняем бывшую ткань (и её размытый край) продолжением соседней кожи
skinlike = (col[..., 0] > col[..., 1]) & (col[..., 1] > col[..., 2]) & (col[..., 0]-col[..., 2] > 40)
skin_known = band & (lum > 100) & skinlike & ~is_orange & ~near_cloth
skin_img = push_pull(col, skin_known)
# ткань: заполняем бывшую кожу продолжением соседней ткани
cloth_known = band & old_cloth & ~ndimage.binary_dilation(lum >= 85, iterations=2)
cloth_img = np.broadcast_to(np.median(col[cloth_known], 0).astype(np.float32), col.shape)   # ровный цвет ткани
k = np.clip((T-(T_HEM-SOFT))/(2*SOFT), 0, 1); k = k*k*(3-2*k)          # 0 — ткань, 1 — кожа
# + тёмные остатки старого края (коричневатая тень ткани на коже)
resid = want_skin & (T < T_HEM + 0.12) & (lum < 0.8*skin_img.mean(2))
M = want_skin & (near_cloth | ndimage.binary_dilation(resid, iterations=8))
Z = want_skin & ~M                                          # настоящая кожа рядом
fa = (M*np.clip(ndimage.distance_transform_edt(~Z)/15.0, 0, 1))[..., None]   # мягкий переход только к настоящей коже (15 px), у подола — полная замена
skin_layer = col*(1-fa) + skin_img*fa
keep_or = is_orange & (T < 0.45)                                    # оранжевый кант оставляем, обрывки у старого края — нет
# вся ткань шорт на бедре (от t=0.30 до подола) перекрашивается одним ровным слоем: мягкая светотень без пятен и старых краёв
cl_smooth = ndimage.gaussian_filter(push_pull(col, cloth_known & (lum < 60)), sigma=(30, 30, 0))
cl_smooth = np.minimum(cl_smooth, np.median(col[cloth_known], 0)*0.95)
g_top = np.clip((T-0.30)/0.05, 0, 1); g_top = (g_top*g_top*(3-2*g_top))[..., None]   # плавный переход к нетронутой ткани выше
fc = (want_cloth[..., None]*g_top)*(~keep_or)[..., None]
cloth_layer = col*(1-fc) + cl_smooth*fc
out = cloth_layer*(1-k[..., None]) + skin_layer*k[..., None]
upd = band & (want_cloth | want_skin)
new_col = np.where(upd[..., None], out, col)
changed = upd & (np.abs(new_col-col).sum(2) > 6)
flat = np.array([128, 128, 255.0])
# нормали: под новой тканью оставляем как есть, там где ткань стала кожей — плоские (без «рубца» старого подола)
new_nrm = nrm*(1-fa) + flat*fa
fcn = 0.0   # рисунок ткани в нормалях оставляем (без него ткань выглядит светлее)
new_nrm = new_nrm*(1-fcn) + flat*fcn
# старый край ткани внутри новых шорт: сглаживаем нормали, чтобы не было видно «рубца»
old_edge = want_cloth & (T < T_HEM - 2*SOFT) & ndimage.binary_dilation(~old_cloth & inner, iterations=20) & ndimage.binary_dilation(old_cloth, iterations=20)
fe = np.clip(ndimage.gaussian_filter(old_edge.astype(np.float32), 4)*2, 0, 1)[..., None]
new_nrm = new_nrm*(1-fe) + flat*fe
changed |= old_edge
del skin_img, cloth_img, skin_layer, cloth_layer, out

# подтягиваем изменённые цвета на 4 пикселя за край островов (чтобы не было тёмной каймы на мип-уровнях)
grow = ndimage.binary_dilation(changed, iterations=6) & ~covered
# + крайние пиксели тех же треугольников, не попавшие в растр (дают светлую «строчку» по шву)
grow |= ndimage.binary_dilation(changed, iterations=5) & covered & ~band
if grow.any():
    _, (iy, ix) = ndimage.distance_transform_edt(~changed, return_indices=True)
    new_col[grow] = new_col[iy[grow], ix[grow]]; new_nrm[grow] = new_nrm[iy[grow], ix[grow]]
print('changed px', int(changed.sum()), 'padding px', int(grow.sum()))
os.makedirs(OUT, exist_ok=True)
Image.fromarray(new_col.clip(0, 255).astype(np.uint8)).save(os.path.join(OUT, COL))
Image.fromarray(new_nrm.clip(0, 255).astype(np.uint8)).save(os.path.join(OUT, NRM))

# ---------- геометрия (если указана 5-я папка/файл): убираем «ступеньки» старых краёв шорт на бедре ----------
# В модели шорты чуть толще ноги, и край этой «манжеты» не совпадает с новой линией.
# Радиус бедра в полосе t = 0.28..0.70 заменяем плавным профилем (квадратичная подгонка по секторам вокруг бедра).
if len(sys.argv) > 5:
    NPOS = P.copy(); moved = np.zeros(len(P), bool)
    for side in ['Left', 'Right']:
        A = JP[side+'UpLeg']; B = JP[side+'Leg']; ax = B-A; L = np.linalg.norm(ax); ax /= L
        ji = [names.index(side+'UpLeg'), names.index(side+'Leg')]
        wl = sum(W[:, k]*np.isin(J[:, k], ji) for k in range(4))
        t = (P-A)@ax/L; r = P-A-np.outer((P-A)@ax, ax); rad = np.linalg.norm(r, axis=1)
        up = np.array([0, 0, 1.0]); e1 = up-ax*(up@ax); e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1)
        ang = np.arctan2(r@e2, r@e1)
        leg = (wl > 0.5) & (t > 0.26) & (t < 0.72)
        NB = 24; fb = (ang+np.pi)/(2*np.pi)*NB
        fit = []
        for b in range(NB):
            d = np.abs(((fb-b-0.5+NB/2) % NB)-NB/2)
            mm = leg & (d < 1.5)
            fit.append(np.polyfit(t[mm], rad[mm], 2) if mm.sum() > 12 else None)
        ok = [f for f in fit if f is not None]; fit = np.array([f if f is not None else np.mean(ok, 0) for f in fit])
        b0 = np.floor(fb-0.5).astype(int); fr = fb-0.5-b0
        k0 = fit[b0 % NB]; k1 = fit[(b0+1) % NB]
        rs = np.polyval(k0.T, t)*(1-fr) if False else (k0[:, 0]*t*t+k0[:, 1]*t+k0[:, 2])*(1-fr) + (k1[:, 0]*t*t+k1[:, 1]*t+k1[:, 2])*fr
        def ss(x): x = np.clip(x, 0, 1); return x*x*(3-2*x)
        w = ss((t-0.28)/0.06)*ss((0.70-t)/0.06)*(wl > 0.5)
        w[~leg] = 0
        newr = rad + w*(rs-rad)
        sel = w > 0
        NPOS[sel] = A + np.outer(t[sel]*L, ax) + r[sel]/rad[sel, None]*newr[sel, None]
        moved |= sel
        print(side, 'smoothed verts', int(sel.sum()), 'max shift mm', round(float(np.abs(newr-rad)[sel].max()/L*400), 1))
    key = np.round(P/1e-7).astype(np.int64)
    _, grp = np.unique(key, axis=0, return_inverse=True); grp = grp.ravel()
    fn = np.cross(NPOS[F[:, 1]]-NPOS[F[:, 0]], NPOS[F[:, 2]]-NPOS[F[:, 0]])
    acc = np.zeros((grp.max()+1, 3))
    for c in range(3): np.add.at(acc, grp[F[:, c]], fn)
    touch = np.zeros(len(P), bool); touch[F[moved[F].any(1)].ravel()] = True
    NN = rd(pr.attributes.NORMAL).copy()
    nn = acc[grp[touch]]; NN[touch] = nn/np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-20)
    data = bytearray(g.binary_blob())
    for ai, arr in [(pr.attributes.POSITION, NPOS), (pr.attributes.NORMAL, NN)]:
        ac = g.accessors[ai]; bv = g.bufferViews[ac.bufferView]
        assert bv.byteStride in (None, 0, 12)
        off = bv.byteOffset+(ac.byteOffset or 0); b = np.ascontiguousarray(arr, '<f4').tobytes(); data[off:off+len(b)] = b
    ap = g.accessors[pr.attributes.POSITION]; ap.min = NPOS.min(0).tolist(); ap.max = NPOS.max(0).tolist()
    g.set_binary_blob(bytes(data)); g.save(sys.argv[5]); print('saved', sys.argv[5])

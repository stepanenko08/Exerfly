"""Цветная карта мышц (PNG) → контуры SVG для каждой группы мышц, спереди и сзади."""
import numpy as np, cv2, json
from PIL import Image
im = np.array(Image.open('muscle_colors.png').convert('RGB')).astype(float)
H, W, _ = im.shape
PAL = {
 'chest': '#E6194B', 'shoulders': '#F58231', 'biceps': '#FFE119', 'triceps': '#BFEF45', 'forearms': '#3CB44B',
 'abs': '#42D4F4', 'obliques': '#4363D8', 'traps': '#911EB4', 'lats': '#F032E6', 'lower_back': '#800000',
 'glutes': '#9A6324', 'quads': '#000075', 'hamstrings': '#469990', 'calves': '#DCBEFF',
 '_white': '#F8F8F8', '_n1': '#C0C0C0', '_n2': '#989898', '_n3': '#B8B8B8', '_n4': '#E8E8E8'}
keys = list(PAL); cols = np.array([[int(PAL[k][i:i+2], 16) for i in (1, 3, 5)] for k in keys], float)
d = ((im[:, :, None, :]-cols[None, None])**2).sum(-1); lab = d.argmin(-1)
UP = 4; S = 0.25                                  # апскейл для гладких контуров; масштаб в единицы SVG
def path_of(mask):
    m = cv2.resize(mask.astype(np.uint8)*255, (W*UP, H*UP), interpolation=cv2.INTER_NEAREST)
    m = cv2.GaussianBlur(m, (0, 0), UP*0.9); m = (m > 127).astype(np.uint8)
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cs:
        if cv2.contourArea(c) < (UP*UP)*25: continue
        a = cv2.approxPolyDP(c, UP*0.55, True)[:, 0, :].astype(float)/UP*S
        if len(a) < 3: continue
        # гладкая кривая: квадратичные Безье через середины рёбер
        mids = (a+np.roll(a, -1, 0))/2
        f = lambda p: f'{p[0]:.1f} {p[1]:.1f}'
        s = 'M' + f(mids[-1])
        for i in range(len(a)): s += 'Q' + f(a[i]) + ' ' + f(mids[i])
        out.append(s+'Z')
    return ''.join(out)
res = {'front': {}, 'back': {}}
neutral = np.isin(lab, [keys.index(k) for k in ('_n1', '_n2', '_n3')])
for side, sl in (('front', np.s_[:, :W//2]), ('back', np.s_[:, W//2:])):
    sel = np.zeros((H, W), bool); sel[sl] = True
    for k in keys:
        if k.startswith('_'): continue
        mk = (lab == keys.index(k)) & sel
        mk = cv2.morphologyEx(mk.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)).astype(bool)
        if mk.sum() < 60: continue
        res[side][k] = path_of(mk)
    nm = cv2.morphologyEx((neutral & sel).astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)).astype(bool)
    res[side]['_body'] = path_of(nm)
ys, xs = np.where(lab != keys.index('_white'))
res['bbox'] = [float(xs.min()*S), float(ys.min()*S), float(xs.max()*S), float(ys.max()*S)]
json.dump(res, open('paths.json', 'w'))
print({s: {k: len(v) for k, v in res[s].items()} for s in ('front', 'back')}, res['bbox'])
print('total chars', sum(len(v) for s in ('front', 'back') for v in res[s].values()))

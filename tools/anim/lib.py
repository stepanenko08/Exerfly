"""Общие функции: чтение клипов Mixamo, перенос на риг exercises.glb, прямая кинематика."""
import numpy as np
from pygltflib import (GLTF2, Accessor, BufferView, Animation, AnimationChannel, AnimationChannelTarget,
                       AnimationSampler, Material, PbrMetallicRoughness, Mesh, Primitive, Attributes, Node)

FPS = 30
short = lambda n: n.split(':', 1)[1] if n and ':' in n else n

# ---------- кватернионы (x, y, z, w) ----------
def qmul(a, b):
    ax, ay, az, aw = np.moveaxis(np.asarray(a, float), -1, 0)
    bx, by, bz, bw = np.moveaxis(np.asarray(b, float), -1, 0)
    return np.stack([aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx,
                     aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz], -1)
def qmat(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
def mat2q(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t+1)*2; return np.array([(m[2,1]-m[1,2])/s, (m[0,2]-m[2,0])/s, (m[1,0]-m[0,1])/s, s/4])
    i = np.argmax(np.diag(m))
    if i == 0:
        s = np.sqrt(1+m[0,0]-m[1,1]-m[2,2])*2; return np.array([s/4, (m[0,1]+m[1,0])/s, (m[0,2]+m[2,0])/s, (m[2,1]-m[1,2])/s])
    if i == 1:
        s = np.sqrt(1+m[1,1]-m[0,0]-m[2,2])*2; return np.array([(m[0,1]+m[1,0])/s, s/4, (m[1,2]+m[2,1])/s, (m[0,2]-m[2,0])/s])
    s = np.sqrt(1+m[2,2]-m[0,0]-m[1,1])*2; return np.array([(m[0,2]+m[2,0])/s, (m[1,2]+m[2,1])/s, s/4, (m[1,0]-m[0,1])/s])
def trs(t, r, s):
    M = np.eye(4); M[:3, :3] = qmat(r) * np.asarray(s); M[:3, 3] = t; return M

# поворот Armature в exercises.glb: +90° вокруг X, масштаб 0.01
R_INV = np.array([-np.sqrt(.5), 0, 0, np.sqrt(.5)])

def read_clip(path):
    """Клип Mixamo → {имя кости: {'rotation': (N,4), 'translation': (N,3)}}, число кадров."""
    g = GLTF2().load(path); blob = g.binary_blob(); a = g.animations[0]
    def rd(i, n):
        ac = g.accessors[i]; bv = g.bufferViews[ac.bufferView]
        return np.frombuffer(blob, dtype='<f4', count=ac.count*n, offset=bv.byteOffset+(ac.byteOffset or 0)).reshape(ac.count, n).copy()
    out = {}; N = 0
    for ch in a.channels:
        s = a.samplers[ch.sampler]; name = short(g.nodes[ch.target.node].name)
        n = {'rotation': 4, 'translation': 3, 'scale': 3}[ch.target.path]
        v = rd(s.output, n); out.setdefault(name, {})[ch.target.path] = v; N = max(N, len(v))
    return out, N

def to_rig(clip):
    """Переводит корень (Hips) из пространства Mixamo (Y вверх, метры) в пространство Armature (повёрнуто, см)."""
    h = clip['Hips']
    h['rotation'] = qmul(np.broadcast_to(R_INV, h['rotation'].shape), h['rotation'])
    t = h['translation']; h['translation'] = np.stack([t[:, 0], t[:, 2], -t[:, 1]], 1) * 100
    return clip

class Rig:
    """Прямая кинематика по иерархии exercises.glb."""
    def __init__(s, g):
        s.g = g; s.parent = {c: i for i, n in enumerate(g.nodes) for c in (n.children or [])}
        s.idx = {short(n.name): i for i, n in enumerate(g.nodes) if n.name}
    def rest(s, i):
        n = s.g.nodes[i]
        return (np.array(n.translation or [0, 0, 0], float), np.array(n.rotation or [0, 0, 0, 1], float), np.array(n.scale or [1, 1, 1], float))
    def world(s, clip, f):
        cache = {}
        def W(i):
            if i in cache: return cache[i]
            t, r, sc = s.rest(i); nm = short(s.g.nodes[i].name)
            if nm in clip:
                if 'rotation' in clip[nm]: r = clip[nm]['rotation'][min(f, len(clip[nm]['rotation'])-1)]
                if 'translation' in clip[nm]: t = clip[nm]['translation'][min(f, len(clip[nm]['translation'])-1)]
            M = trs(t, r, sc)
            if i in s.parent: M = W(s.parent[i]) @ M
            cache[i] = M; return M
        return lambda name: W(s.idx[name])
    def pos(s, clip, f, names):
        W = s.world(clip, f); return {n: W(n)[:3, 3] for n in names}

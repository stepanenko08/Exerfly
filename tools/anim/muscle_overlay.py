"""Добавляет в модель полупрозрачный «слой мышц»: по одной сетке на мышцу, привязанной к тому же скелету.
Каждая мышца — свой материал M_<ключ> (unlit, прозрачный), сайт меняет ему прозрачность."""
import sys, numpy as np
sys.path.insert(0, '/home/claude/mx')
from lib import *
from pygltflib import Accessor, BufferView, Material, PbrMetallicRoughness, Mesh, Primitive, Attributes, Node
SRC, DST = sys.argv[1], sys.argv[2]
KEYS = ['chest', 'shoulders', 'biceps', 'triceps', 'forearms', 'abs', 'obliques', 'traps', 'lats', 'lower_back', 'glutes', 'quads', 'hamstrings', 'calves']
g = GLTF2().load(SRC); blob = bytearray(g.binary_blob())
def rd(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
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
P = rd(p.attributes.POSITION).astype(float); Nn = rd(p.attributes.NORMAL).astype(float)
J = rd(p.attributes.JOINTS_0); W = rd(p.attributes.WEIGHTS_0); I = rd(p.indices).reshape(-1, 3).astype(np.int64)
reg = np.load('/home/claude/mus/muscles.png.geo.npz')['reg']; assert len(reg) == len(P)
H = np.ptp(P[:, 1]); unit = H/1.8
# сварка вершин по позиции (швы развёртки), чтобы сглаживание шло через швы
key = np.round(P/(unit*0.002)).astype(np.int64); _, weld = np.unique(key, axis=0, return_inverse=True); weld = weld.ravel(); NW = weld.max()+1
edges = np.concatenate([I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]]); ew = weld[edges]; ew = ew[ew[:, 0] != ew[:, 1]]
deg = np.bincount(np.r_[ew[:, 0], ew[:, 1]], minlength=NW).astype(float)+1
off = Nn/np.linalg.norm(Nn, axis=1, keepdims=True)*unit*0.006            # слой на 6 мм над кожей/тканью
Ppos = (P+off).astype('<f4')
mats = []
g.extensionsUsed = sorted(set((g.extensionsUsed or []) + ['KHR_materials_unlit']))
prims = []
for k, name in enumerate(KEYS, start=1):
    m = np.zeros(NW); np.maximum.at(m, weld[reg == k], 1.0)
    for _ in range(3):                                                      # мягкий край: несколько шагов усреднения по соседям
        s = m.copy(); np.add.at(s, ew[:, 0], m[ew[:, 1]]); np.add.at(s, ew[:, 1], m[ew[:, 0]]); m = np.maximum(m*0.0+s/deg, (m >= 1)*0.0+m*0)
        m = np.clip(m, 0, 1)
    core = np.zeros(NW); np.maximum.at(core, weld[reg == k], 1.0)
    a = np.where(core > 0, 1.0, np.clip(m*1.6, 0, 1))                            # внутри — ровно, к краю — затухание
    av = a[weld]
    tri = I[av[I].max(1) > 0.05]
    vs, inv = np.unique(tri.ravel(), return_inverse=True); tri2 = inv.reshape(-1, 3)
    col = np.c_[np.full((len(vs), 3), 255), np.round(av[vs]*255)].astype('u1')
    w8 = np.round(W[vs]*255).astype(int); w8[:, 0] += 255-w8.sum(1)
    g.materials.append(Material(name='M_'+name, alphaMode='BLEND', doubleSided=False,
        pbrMetallicRoughness=PbrMetallicRoughness(baseColorFactor=[1.0, 0.35, 0.21, 0.0], metallicFactor=0.0, roughnessFactor=1.0),
        extensions={'KHR_materials_unlit': {}}))
    prims.append(Primitive(attributes=Attributes(POSITION=add_acc(Ppos[vs], 'VEC3', 5126, True), JOINTS_0=add_acc(J[vs].astype('u1'), 'VEC4', 5121),
                                                 WEIGHTS_0=add_acc(w8.astype('u1'), 'VEC4', 5121, norm=True), COLOR_0=add_acc(col, 'VEC4', 5121, norm=True)),
                           indices=add_acc(tri2.astype('<u2').ravel(), 'SCALAR', 5123, target=34963), material=len(g.materials)-1, mode=4))
    print(name, len(vs), 'verts', len(tri2), 'tris')
g.meshes.append(Mesh(name='MuscleOverlay', primitives=prims))
skin_node = [n for n in g.nodes if n.mesh == mi][0]
g.nodes.append(Node(name='MuscleOverlay', mesh=len(g.meshes)-1, skin=skin_node.skin))
par = [i for i, n in enumerate(g.nodes) if g.nodes.index(skin_node) in (n.children or [])][0]
g.nodes[par].children.append(len(g.nodes)-1)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save_binary(DST)
import os; print('SIZE %.2f MB' % (os.path.getsize(DST)/1e6))

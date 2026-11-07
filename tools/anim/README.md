# Добавление анимаций Mixamo в models/exercises.glb

1. Mixamo → Download: FBX Binary, Without Skin, 30 FPS, Keyframe Reduction: none.
2. Конвертация в GLB (FBX2glTF, npm-пакет `fbx2gltf`):
   `FBX2glTF -b --anim-framerate bake30 -i "Back Squat.fbx" -o glb/Back_Squat`
3. Описать клип в `clips.json`:
   - `name` — имя анимации в модели (используется в js/data.js → model.variants[].anim)
   - `file` — файл из папки glb/
   - `prop` — снаряд: `barbell`, `dumbbells`, `kettlebell`, `treadmill` или `none`
   - `from` / `to` — обрезка по кадрам (30 кадров = 1 с), `pingpong` — проиграть туда и обратно
   - `drop` — опустить штангу относительно хвата (м)
4. Сборка (нужны `pip install pygltflib numpy`):
   `python3 build.py ../../models/exercises.glb ../../models/exercises.glb`
   Скрипт добавляет клипы к уже существующим, поэтому запускать его на исходной модели без этих клипов.

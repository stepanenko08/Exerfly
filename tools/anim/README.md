# Сборка models/exercises.glb и models/exercises_f.glb

Исходники (персонажи, текстуры, старая модель со снарядами, клипы Mixamo, инструменты проверки кадрами)
лежат в `D:\Exerfly\sources-3d` — вне git. Подробная инструкция по восстановлению и сборке: `sources-3d/README.md`.

## Файлы здесь
- `build_character.py` — сборка персонажа: текстуры (3072 px), снаряды, старые клипы и клипы Mixamo (clips.json), затем запускает proc.py
- `proc.py` — решатель поз: IK рук и ног, хват за снаряд, ключи с плавной интерполяцией, короткие паузы (HOLD = 0.1 с), лёгкое «дыхание»
- `proc_ex.py` — все процедурные упражнения и снаряды (скамьи, блочная стойка, брусья, турник, жим ногами, степ, гиперэкстензия)
- `lib.py`, `props.py` — вспомогательное (чтение клипов, геометрия)
- `clips.json` — какие клипы Mixamo брать и как обрезать
- `muscle_overlay.py` — слои подсветки мышц (сейчас подсветка выключена и в модель не входит)

## Команда (из облачного окружения Claude, пути — см. sources-3d/README.md)
```
python3 build2.py <персонаж ath.glb> <old_model/exercises.glb> <папка текстур> <выход.glb>
```

## Новые клипы Mixamo
1. Mixamo → Download: FBX Binary, Without Skin, 30 FPS, Keyframe Reduction: none.
2. FBX → GLB: `FBX2glTF -b --anim-framerate bake30 -i "Back Squat.fbx" -o glb/Back_Squat`
3. Описать клип в clips.json: name, file, prop, from / to (кадры), pingpong.

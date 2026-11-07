# Сборка models/exercises.glb

## Текущий персонаж (build_character.py)
Персонаж создан в Hunyuan3D (геометрия + текстура), скелет поставлен в Mixamo Auto-Rigger.
`python3 build_character.py <персонаж_из_mixamo.glb> <старая_модель_со_снарядами.glb> <папка_с_текстурами> <выход.glb>`
- персонаж из Mixamo (FBX → GLB через FBX2glTF), масштабируется так, чтобы бёдра были на 0.96 м
- текстуры: цвет и карта нормалей сжимаются до 2048 px JPEG
- скамья, штанга и турник копируются из старой модели
- анимации pushup, squat, squat_arms_forward, bench_press, pullup переносятся из старой модели
- анимации Mixamo — по списку clips.json (папка glb/ с конвертированными клипами)

## Добавление анимаций Mixamo
1. Mixamo → Download: FBX Binary, Without Skin, 30 FPS, Keyframe Reduction: none.
2. FBX → GLB: `FBX2glTF -b --anim-framerate bake30 -i "Back Squat.fbx" -o glb/Back_Squat`
3. Описать клип в clips.json: name, file, prop (barbell / dumbbells / kettlebell / treadmill / none), from / to (кадры), pingpong.
4. Пересобрать модель командой выше.

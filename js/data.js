/* Exerfly — база упражнений (данные без текста).
   Тексты (названия, описание, техника, ошибки) лежат в js/lang/<язык>.js под тем же id.
   Чтобы добавить упражнение: добавьте объект сюда и тексты в каждый языковой файл.

   muscles.primary / secondary — ключи мышц (см. MUSCLE_KEYS)
   reps     — строка с числами; repsType: 'perSide' (на каждую сторону), 'sec' (секунды), 'min' (минуты), 'max' (до отказа)
   rest     — отдых в секундах: число или [от, до]; null — без отдыха
   model    — только если есть анимация в models/exercises.glb */

window.EXERFLY = { LANG: {} };

EXERFLY.MUSCLE_KEYS = ['chest', 'shoulders', 'biceps', 'triceps', 'forearms', 'abs', 'obliques', 'traps', 'lats', 'lower_back', 'glutes', 'quads', 'hamstrings', 'calves'];
EXERFLY.GROUP_KEYS = ['legs', 'back', 'chest', 'shoulders', 'arms', 'core', 'fullbody', 'cardio'];
EXERFLY.EQUIPMENT_KEYS = ['bodyweight', 'dumbbells', 'barbell', 'bench', 'bar', 'dips', 'machine', 'cable', 'rack', 'kettlebell', 'treadmill'];

EXERFLY.EXERCISES = [
  /* ---------- ноги и ягодицы ---------- */
  { id: 'squat', group: 'legs', level: 1, equipment: ['bodyweight'], sets: '3', reps: '15–20', rest: 60,
    muscles: { primary: ['quads', 'glutes'], secondary: ['hamstrings', 'lower_back', 'abs'] },
    model: { target: '0m 0.8m 0m', orbit: '35deg 78deg 4.2m', max: '6m', variants: [{ anim: 'squat', label: 'classic' }, { anim: 'squat_arms_forward', label: 'armsForward' }] } },
  { id: 'back-squat', group: 'legs', level: 2, equipment: ['barbell', 'rack'], sets: '4', reps: '6–10', rest: [120, 180],
    muscles: { primary: ['quads', 'glutes'], secondary: ['hamstrings', 'lower_back', 'abs', 'calves'] },
    model: { target: '0m 0.95m 0m', orbit: '18deg 82deg 4.6m', max: '8m', variants: [{ anim: 'back_squat', label: 'classic' }] } },
  { id: 'deadlift', group: 'legs', level: 3, equipment: ['barbell'], sets: '3–4', reps: '4–6', rest: 180,
    muscles: { primary: ['glutes', 'hamstrings', 'lower_back'], secondary: ['quads', 'traps', 'lats', 'forearms'] } },
  { id: 'romanian-deadlift', group: 'legs', level: 2, equipment: ['barbell', 'dumbbells'], sets: '3', reps: '8–12', rest: 90,
    muscles: { primary: ['hamstrings', 'glutes'], secondary: ['lower_back', 'forearms'] } },
  { id: 'lunge', group: 'legs', level: 1, equipment: ['bodyweight', 'dumbbells'], sets: '3', reps: '10–12', repsType: 'perSide', rest: 60,
    muscles: { primary: ['quads', 'glutes'], secondary: ['hamstrings', 'calves'] } },
  { id: 'bulgarian-split-squat', group: 'legs', level: 2, equipment: ['bench', 'dumbbells'], sets: '3', reps: '8–10', repsType: 'perSide', rest: 90,
    muscles: { primary: ['quads', 'glutes'], secondary: ['hamstrings', 'abs'] } },
  { id: 'hip-thrust', group: 'legs', level: 2, equipment: ['barbell', 'bench'], sets: '3–4', reps: '8–12', rest: 90,
    muscles: { primary: ['glutes'], secondary: ['hamstrings', 'quads'] } },
  { id: 'leg-press', group: 'legs', level: 1, equipment: ['machine'], sets: '3–4', reps: '10–15', rest: 90,
    muscles: { primary: ['quads', 'glutes'], secondary: ['hamstrings', 'calves'] } },
  { id: 'calf-raise', group: 'legs', level: 1, equipment: ['bodyweight', 'machine'], sets: '3–4', reps: '15–20', rest: 45,
    muscles: { primary: ['calves'], secondary: [] } },

  { id: 'overhead-squat', group: 'legs', level: 3, equipment: ['barbell'], sets: '3–4', reps: '5–8', rest: 120,
    muscles: { primary: ['quads', 'glutes', 'shoulders'], secondary: ['abs', 'traps', 'lower_back', 'hamstrings'] },
    model: { target: '0m 1.05m 0m', orbit: '30deg 80deg 5.2m', max: '9m', variants: [{ anim: 'overhead_squat', label: 'classic' }] } },
  { id: 'pistol-squat', group: 'legs', level: 3, equipment: ['bodyweight'], sets: '3', reps: '5–8', repsType: 'perSide', rest: 90,
    muscles: { primary: ['quads', 'glutes'], secondary: ['hamstrings', 'calves', 'abs'] },
    model: { target: '0m 0.8m 0m', orbit: '70deg 80deg 4.4m', max: '8m', variants: [{ anim: 'pistol_squat', label: 'classic' }] } },
  { id: 'kettlebell-deadlift', group: 'legs', level: 1, equipment: ['kettlebell'], sets: '3', reps: '10–15', rest: 60,
    muscles: { primary: ['glutes', 'hamstrings'], secondary: ['lower_back', 'quads', 'forearms'] },
    model: { target: '0m 0.75m 0m', orbit: '60deg 80deg 4m', max: '7m', variants: [{ anim: 'kettlebell_deadlift', label: 'classic' }] } },

  /* ---------- спина ---------- */
  { id: 'pullup', group: 'back', level: 2, equipment: ['bar'], sets: '3–4', reps: '', repsType: 'max', rest: 120,
    muscles: { primary: ['lats', 'biceps'], secondary: ['traps', 'forearms', 'shoulders', 'abs'] },
    model: { target: '0m 1.2m 0m', orbit: '35deg 82deg 7.4m', max: '10m', variants: [{ anim: 'pullup', label: 'overhand' }] } },
  { id: 'lat-pulldown', group: 'back', level: 1, equipment: ['cable', 'machine'], sets: '3–4', reps: '10–12', rest: 90,
    muscles: { primary: ['lats'], secondary: ['biceps', 'traps', 'shoulders'] } },
  { id: 'barbell-row', group: 'back', level: 2, equipment: ['barbell'], sets: '3–4', reps: '8–10', rest: 120,
    muscles: { primary: ['lats', 'traps'], secondary: ['biceps', 'lower_back', 'shoulders', 'forearms'] } },
  { id: 'dumbbell-row', group: 'back', level: 1, equipment: ['dumbbells', 'bench'], sets: '3', reps: '10–12', repsType: 'perSide', rest: 60,
    muscles: { primary: ['lats'], secondary: ['traps', 'biceps', 'shoulders'] } },
  { id: 'back-extension', group: 'back', level: 1, equipment: ['machine'], sets: '3', reps: '12–15', rest: 60,
    muscles: { primary: ['lower_back', 'glutes'], secondary: ['hamstrings'] } },

  /* ---------- грудь ---------- */
  { id: 'pushup', group: 'chest', level: 1, equipment: ['bodyweight'], sets: '3', reps: '10–20', rest: 60,
    muscles: { primary: ['chest', 'triceps'], secondary: ['shoulders', 'abs'] },
    model: { target: '0m 0.25m 0m', orbit: '40deg 75deg 3.8m', max: '6m', variants: [{ anim: 'pushup', label: 'classic' }] } },
  { id: 'bench-press', group: 'chest', level: 2, equipment: ['barbell', 'bench'], sets: '4', reps: '6–10', rest: [120, 180],
    muscles: { primary: ['chest'], secondary: ['triceps', 'shoulders'] },
    model: { target: '0m 0.6m 0.3m', orbit: '50deg 68deg 6.2m', max: '9m', variants: [{ anim: 'bench_press', label: 'classic' }] } },
  { id: 'incline-dumbbell-press', group: 'chest', level: 2, equipment: ['dumbbells', 'bench'], sets: '3–4', reps: '8–12', rest: 90,
    muscles: { primary: ['chest', 'shoulders'], secondary: ['triceps'] } },
  { id: 'dumbbell-fly', group: 'chest', level: 1, equipment: ['dumbbells', 'bench'], sets: '3', reps: '12–15', rest: 60,
    muscles: { primary: ['chest'], secondary: ['shoulders'] } },
  { id: 'dips', group: 'chest', level: 2, equipment: ['dips'], sets: '3', reps: '8–12', rest: 90,
    muscles: { primary: ['chest', 'triceps'], secondary: ['shoulders'] } },

  /* ---------- плечи ---------- */
  { id: 'overhead-press', group: 'shoulders', level: 2, equipment: ['barbell'], sets: '4', reps: '6–10', rest: 120,
    muscles: { primary: ['shoulders'], secondary: ['triceps', 'traps', 'abs'] } },
  { id: 'lateral-raise', group: 'shoulders', level: 1, equipment: ['dumbbells'], sets: '3–4', reps: '12–15', rest: 60,
    muscles: { primary: ['shoulders'], secondary: ['traps'] } },
  { id: 'face-pull', group: 'shoulders', level: 1, equipment: ['cable'], sets: '3', reps: '15', rest: 60,
    muscles: { primary: ['shoulders'], secondary: ['traps'] } },

  /* ---------- руки ---------- */
  { id: 'barbell-curl', group: 'arms', level: 1, equipment: ['barbell'], sets: '3', reps: '10–12', rest: 60,
    muscles: { primary: ['biceps'], secondary: ['forearms'] } },
  { id: 'hammer-curl', group: 'arms', level: 1, equipment: ['dumbbells'], sets: '3', reps: '10–12', rest: 60,
    muscles: { primary: ['biceps', 'forearms'], secondary: [] } },
  { id: 'skull-crusher', group: 'arms', level: 2, equipment: ['barbell', 'bench'], sets: '3', reps: '10–12', rest: 60,
    muscles: { primary: ['triceps'], secondary: [] } },
  { id: 'triceps-pushdown', group: 'arms', level: 1, equipment: ['cable'], sets: '3', reps: '12–15', rest: 60,
    muscles: { primary: ['triceps'], secondary: [] } },

  { id: 'dumbbell-curl', group: 'arms', level: 1, equipment: ['dumbbells'], sets: '3', reps: '10–12', repsType: 'perSide', rest: 60,
    muscles: { primary: ['biceps'], secondary: ['forearms'] },
    model: { target: '0m 1m 0m', orbit: '30deg 82deg 3.8m', max: '7m', variants: [{ anim: 'dumbbell_curl', label: 'classic' }] } },

  /* ---------- пресс и кор ---------- */
  { id: 'plank', group: 'core', level: 1, equipment: ['bodyweight'], sets: '3', reps: '30–60', repsType: 'sec', rest: 45,
    muscles: { primary: ['abs'], secondary: ['obliques', 'shoulders', 'glutes'] },
    model: { target: '0m 0.35m 0m', orbit: '75deg 75deg 3.8m', max: '7m', variants: [{ anim: 'plank', label: 'classic' }] } },
  { id: 'crunch', group: 'core', level: 1, equipment: ['bodyweight'], sets: '3', reps: '15–20', rest: 45,
    muscles: { primary: ['abs'], secondary: ['obliques'] } },
  { id: 'hanging-leg-raise', group: 'core', level: 3, equipment: ['bar'], sets: '3', reps: '8–12', rest: 90,
    muscles: { primary: ['abs'], secondary: ['obliques', 'forearms'] } },
  { id: 'bicycle-crunch', group: 'core', level: 1, equipment: ['bodyweight'], sets: '3', reps: '15–20', repsType: 'perSide', rest: 45,
    muscles: { primary: ['abs', 'obliques'], secondary: [] },
    model: { target: '0m 0.3m 0m', orbit: '65deg 70deg 3.6m', max: '7m', variants: [{ anim: 'bicycle_crunch', label: 'classic' }] } },

  /* ---------- всё тело ---------- */
  { id: 'clean-and-jerk', group: 'fullbody', level: 3, equipment: ['barbell'], sets: '5', reps: '1–3', rest: [120, 180],
    muscles: { primary: ['quads', 'glutes', 'shoulders', 'traps'], secondary: ['hamstrings', 'triceps', 'lower_back', 'abs', 'calves'] },
    model: { target: '0m 1m 0.2m', orbit: '35deg 80deg 5.6m', max: '9m', variants: [{ anim: 'clean_and_jerk', label: 'classic' }] } },

  /* ---------- кардио ---------- */
  { id: 'treadmill-run', group: 'cardio', level: 1, equipment: ['treadmill'], sets: '1', reps: '20–30', repsType: 'min', rest: null,
    muscles: { primary: ['quads', 'hamstrings', 'calves'], secondary: ['glutes', 'abs'] },
    model: { target: '0m 0.8m 0m', orbit: '55deg 76deg 6.2m', max: '10m', variants: [{ anim: 'treadmill_run', label: 'classic' }] } }
];

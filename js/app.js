/* Exerfly — каталог, поиск/фильтры, страница упражнения, смена языка.
   Маршруты: пустой хеш = каталог, #<id упражнения> = страница упражнения. */
(function () {
  const D = window.EXERFLY;
  const MODELS = window.EXERFLY_MODELS || { m: 'models/exercises.glb', f: 'models/exercises_f.glb' };
  const LANGS = ['sk', 'en', 'uk', 'ru'];
  const DEFAULT_LANG = 'sk';
  const app = document.getElementById('app');
  const byId = Object.fromEntries(D.EXERCISES.map(e => [e.id, e]));
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  /* ---------- состояние ---------- */
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* хранилище недоступно */ } }
  };
  const S = {
    lang: LANGS.includes(store.get('exerfly-lang')) ? store.get('exerfly-lang') : DEFAULT_LANG,
    q: '', group: null, speed: 1, who: store.get('exerfly-character') === 'f' ? 'f' : 'm', glow: false, /* подсветка мышц временно выключена */ muscles: new Set(), equipment: new Set(), levels: new Set(), only3d: false, panel: false
  };
  const L = () => D.LANG[S.lang];
  const T = () => L().ui;
  const exText = ex => L().ex[ex.id] || D.LANG.en.ex[ex.id];
  const mName = k => L().muscles[k];

  /* ---------- форматирование ---------- */
  function plural(n, forms) {
    const key = new Intl.PluralRules(L().locale).select(n);
    return forms[key] || forms.other;
  }
  function fmtRest(r) {
    if (r == null) return '—';
    const t = T(), [a, b] = Array.isArray(r) ? r : [r, r];
    if (b < 120) return `${a === b ? a : a + '–' + b} ${t.sec}`;
    const m = x => String(+(x / 60).toFixed(1)).replace('.', L().locale === 'en' ? '.' : ',');
    return `${a === b ? m(a) : m(a) + '–' + m(b)} ${t.min}`;
  }
  function fmtReps(ex) {
    const t = T();
    if (ex.repsType === 'max') return { v: t.max, note: '' };
    if (ex.repsType === 'sec') return { v: `${ex.reps} ${t.sec}`, note: '' };
    if (ex.repsType === 'min') return { v: `${ex.reps} ${t.min}`, note: '' };
    if (ex.repsType === 'perSide') return { v: ex.reps, note: t.perSide };
    return { v: ex.reps, note: '' };
  }

  /* ---------- схема мышц ---------- */
  function bodyMap(primary, secondary, opts = {}) {
    const pri = new Set(primary), sec = new Set(secondary || []);
    const m = k => `class="m ${pri.has(k) ? 'pri' : sec.has(k) ? 'sec' : ''}" data-m="${k}"${opts.interactive ? ` role="button" tabindex="0" aria-pressed="${pri.has(k)}" aria-label="${esc(mName(k))}"` : ''}`;
    const tip = k => opts.interactive ? `<title>${esc(mName(k))}</title>` : '';
    const pair = (cx, dx, f) => f(cx - dx, -1) + f(cx + dx, 1);
    const fig = (cx, view) => {
      let s = '';
      s += `<circle class="skin" cx="${cx}" cy="16" r="10"/>`;
      s += `<rect class="skin" x="${cx - 5}" y="24" width="10" height="10"/>`;
      s += `<rect class="base" x="${cx - 21}" y="33" width="42" height="70" rx="10"/>`;
      s += `<rect class="base" x="${cx - 19}" y="96" width="38" height="20" rx="8"/>`;
      s += pair(cx, 34, x => `<circle class="skin" cx="${x}" cy="113" r="4.5"/>`);
      s += pair(cx, 10, x => `<ellipse class="skin" cx="${x}" cy="204" rx="7" ry="3.5"/>`);
      s += pair(cx, 25, x => `<ellipse ${m('shoulders')} cx="${x}" cy="42" rx="8.5" ry="8.5">${tip('shoulders')}</ellipse>`);
      s += pair(cx, 34, x => `<rect ${m('forearms')} x="${x - 4}" y="80" width="8" height="28" rx="4">${tip('forearms')}</rect>`);
      if (view === 'front') {
        s += pair(cx, 31.5, x => `<rect ${m('biceps')} x="${x - 4.5}" y="51" width="9" height="27" rx="4.5">${tip('biceps')}</rect>`);
        s += pair(cx, 10.5, x => `<rect ${m('chest')} x="${x - 9.5}" y="36" width="19" height="20" rx="7">${tip('chest')}</rect>`);
        s += `<rect ${m('abs')} x="${cx - 7.5}" y="59" width="15" height="38" rx="5">${tip('abs')}</rect>`;
        s += pair(cx, 14, x => `<rect ${m('obliques')} x="${x - 4}" y="61" width="8" height="33" rx="4">${tip('obliques')}</rect>`);
        s += pair(cx, 10, x => `<rect ${m('quads')} x="${x - 8}" y="116" width="16" height="45" rx="8">${tip('quads')}</rect>`);
        s += pair(cx, 10, x => `<rect ${m('calves')} x="${x - 6}" y="165" width="12" height="35" rx="6">${tip('calves')}</rect>`);
      } else {
        s += pair(cx, 31.5, x => `<rect ${m('triceps')} x="${x - 4.5}" y="51" width="9" height="27" rx="4.5">${tip('triceps')}</rect>`);
        s += `<polygon ${m('traps')} points="${cx - 5},28 ${cx + 5},28 ${cx + 18},38 ${cx + 6},62 ${cx - 6},62 ${cx - 18},38">${tip('traps')}</polygon>`;
        s += pair(cx, 0, (x, sg) => { const p = (dx, y) => `${cx + sg * dx},${y}`;
          return `<polygon ${m('lats')} points="${p(20, 47)} ${p(8, 62)} ${p(7, 90)} ${p(15, 87)} ${p(20, 66)}">${tip('lats')}</polygon>`; });
        s += `<rect ${m('lower_back')} x="${cx - 5.5}" y="65" width="11" height="31" rx="3">${tip('lower_back')}</rect>`;
        s += pair(cx, 9.5, x => `<ellipse ${m('glutes')} cx="${x}" cy="108" rx="9.5" ry="10">${tip('glutes')}</ellipse>`);
        s += pair(cx, 10, x => `<rect ${m('hamstrings')} x="${x - 8}" y="121" width="16" height="40" rx="8">${tip('hamstrings')}</rect>`);
        s += pair(cx, 10, x => `<rect ${m('calves')} x="${x - 6.5}" y="165" width="13" height="34" rx="6.5">${tip('calves')}</rect>`);
      }
      return s;
    };
    const labels = opts.labels === false ? '' :
      `<text x="50" y="223" text-anchor="middle">${esc(T().front)}</text><text x="150" y="223" text-anchor="middle">${esc(T().back)}</text>`;
    const h = opts.labels === false ? 210 : 228;
    const aria = opts.interactive ? `aria-label="${esc(T().fMusclesHint)}"` : `role="img" aria-label="${esc(primary.map(mName).join(', '))}"`;
    return `<svg class="bm${opts.interactive ? ' interactive' : ''}" viewBox="0 0 200 ${h}" ${aria}>${fig(50, 'front')}${fig(150, 'back')}${labels}</svg>`;
  }

  const levelHTML = n => `<span class="level">${esc(L().levels[n])}<span class="bars" aria-hidden="true"><i class="${n >= 1 ? 'on' : ''}"></i><i class="${n >= 2 ? 'on' : ''}"></i><i class="${n >= 3 ? 'on' : ''}"></i></span></span>`;
  const chips = (keys, cls = '') => keys.map(k => `<span class="chip ${cls}">${esc(mName(k))}</span>`).join('');

  /* ---------- тема ---------- */
  const themeBtn = document.getElementById('theme');
  const darkMQ = matchMedia('(prefers-color-scheme: dark)');
  const currentTheme = () => document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  function applyTheme(theme, save) {
    document.documentElement.setAttribute('data-theme', theme);
    if (save) store.set('exerfly-theme', theme);
    themeBtn.setAttribute('aria-checked', String(theme === 'dark'));
    const fav = document.getElementById('favicon');
    if (fav) fav.href = `assets/logo/favicon-${theme}.svg`;
  }
  themeBtn.addEventListener('click', () => applyTheme(currentTheme() === 'dark' ? 'light' : 'dark', true));
  // пока пользователь сам не выбрал тему, следуем за системой
  darkMQ.addEventListener && darkMQ.addEventListener('change', e => { if (!store.get('exerfly-theme')) applyTheme(e.matches ? 'dark' : 'light', false); });
  applyTheme(currentTheme(), false);

  /* ---------- шапка и выбор языка ---------- */
  const langBox = document.getElementById('lang');
  // глобус: контур, экватор, меридиан, две параллели и центральная ось
  const globe = '<svg class="globe" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="9.2"/><ellipse cx="12" cy="12" rx="4.4" ry="9.2"/><path d="M12 2.8v18.4M2.8 12h18.4M4.6 6.9c4.6 2.4 10.2 2.4 14.8 0M4.6 17.1c4.6-2.4 10.2-2.4 14.8 0"/></svg>';
  const chev = '<svg class="chev" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
  const check = '<svg class="check" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 5 5 9-10"/></svg>';
  function renderHeader() {
    const t = T();
    document.documentElement.lang = S.lang;
    const nav = document.getElementById('nav');
    nav.setAttribute('aria-label', t.mainNav);
    nav.innerHTML = `<ul>
        <li><a href="#" aria-current="page">${esc(t.navExercises)}</a></li>
        ${[t.navPrograms, t.navQuiz, t.navProfile].map(x => `<li><span class="soon" aria-disabled="true">${esc(x)}<small>${esc(t.soon)}</small></span></li>`).join('')}
      </ul>`;
    document.getElementById('skip').textContent = t.skip;
    document.getElementById('logo-link').setAttribute('aria-label', t.homeLabel);
    const md = document.querySelector('meta[name="description"]'); if (md) md.content = t.metaDesc;
    themeBtn.setAttribute('aria-label', t.darkMode);
    themeBtn.title = t.darkMode;
    langBox.innerHTML = `
      <button type="button" class="lang-btn" id="lang-btn" aria-haspopup="listbox" aria-expanded="false" aria-label="${esc(t.language)}: ${esc(L().name)}">${globe}${L().short}${chev}</button>
      <ul class="lang-menu" id="lang-menu" role="listbox" aria-label="${esc(t.language)}" hidden>
        ${LANGS.map(k => `<li><button type="button" role="option" data-lang="${k}" aria-selected="${k === S.lang}"><span class="code">${D.LANG[k].short}</span>${esc(D.LANG[k].name)}${check}</button></li>`).join('')}
      </ul>`;
    document.getElementById('footer-note').textContent = 'Exerfly · ' + t.footer;
    requestAnimationFrame(syncHeaderHeight);
  }
  // высота шапки нужна липкой панели фильтров и боковой колонке
  const headerEl = document.getElementById('site-header');
  function syncHeaderHeight() { document.documentElement.style.setProperty('--header-h', headerEl.offsetHeight + 'px'); }
  if (window.ResizeObserver) new ResizeObserver(syncHeaderHeight).observe(headerEl); else window.addEventListener('resize', syncHeaderHeight);
  document.getElementById('skip').addEventListener('click', () => { app.focus(); app.scrollIntoView(); });
  function setMenu(open, focusFirst) {
    const btn = document.getElementById('lang-btn'), menu = document.getElementById('lang-menu');
    menu.hidden = !open; btn.setAttribute('aria-expanded', String(open));
    if (open && focusFirst) (menu.querySelector('[aria-selected="true"]') || menu.querySelector('button')).focus();
  }
  langBox.addEventListener('click', e => {
    if (e.target.closest('#lang-btn')) { setMenu(document.getElementById('lang-menu').hidden, e.detail === 0); return; }
    const b = e.target.closest('[data-lang]'); if (!b) return;
    S.lang = b.dataset.lang; store.set('exerfly-lang', S.lang);
    renderHeader(); route(true);
    document.getElementById('lang-btn').focus();
  });
  langBox.addEventListener('keydown', e => {
    const items = [...langBox.querySelectorAll('[data-lang]')], i = items.indexOf(document.activeElement);
    if (e.key === 'Escape') { setMenu(false); document.getElementById('lang-btn').focus(); }
    else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (document.getElementById('lang-menu').hidden) { setMenu(true, true); return; }
      const n = items[(i + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]; n && n.focus();
    }
  });
  document.addEventListener('click', e => { if (!langBox.contains(e.target)) setMenu(false); });

  /* ---------- фильтрация ---------- */
  const norm = s => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ё/g, 'е').replace(/[’']/g, '');
  function haystack(ex) {
    const parts = LANGS.map(k => D.LANG[k].ex[ex.id] ? D.LANG[k].ex[ex.id].name : '');
    [...ex.muscles.primary, ...ex.muscles.secondary].forEach(k => LANGS.forEach(l => parts.push(D.LANG[l].muscles[k])));
    parts.push(L().groups[ex.group]);
    ex.equipment.forEach(k => parts.push(L().equipment[k]));
    return norm(parts.join(' | '));
  }
  const activeCount = () => (S.group ? 1 : 0) + S.muscles.size + S.equipment.size + S.levels.size + (S.only3d ? 1 : 0);
  const panelCount = () => S.equipment.size + S.levels.size + (S.only3d ? 1 : 0);
  function filtered() {
    const words = norm(S.q.trim()).split(/\s+/).filter(Boolean);
    let list = D.EXERCISES.filter(ex => {
      if (S.group && ex.group !== S.group) return false;
      if (S.only3d && !ex.model) return false;
      if (S.levels.size && !S.levels.has(ex.level)) return false;
      if (S.equipment.size && !ex.equipment.some(k => S.equipment.has(k))) return false;
      if (S.muscles.size && ![...ex.muscles.primary, ...ex.muscles.secondary].some(k => S.muscles.has(k))) return false;
      if (words.length) { const h = haystack(ex); if (!words.every(w => h.includes(w))) return false; }
      return true;
    });
    if (S.muscles.size) {
      const score = ex => ex.muscles.primary.filter(k => S.muscles.has(k)).length * 2 + ex.muscles.secondary.filter(k => S.muscles.has(k)).length;
      list = list.slice().sort((a, b) => score(b) - score(a));
    }
    return list;
  }

  /* ---------- каталог ---------- */
  function renderCatalog() {
    const t = T();
    document.title = 'Exerfly';
    const [a, ...b] = t.heroTitle.split('. ');
    const with3d = D.EXERCISES.filter(e => e.model).length;
    app.innerHTML = `
      <section class="wrap hero" aria-labelledby="hero-title">
        <div>
          <p class="eyebrow">${esc(t.heroEyebrow)}</p>
          <h1 id="hero-title" tabindex="-1">${esc(a)}.${b.length ? `<br><em>${esc(b.join('. '))}</em>` : ''}</h1>
          <p class="lead">${esc(t.heroLead)}</p>
          <form class="search" role="search" id="search-form">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
            <input id="q" type="search" autocomplete="off" placeholder="${esc(t.search)}" aria-label="${esc(t.search)}" value="${esc(S.q)}">
            <button type="button" class="clear" data-act="clear-q" aria-label="${esc(t.clearSearch)}" ${S.q ? '' : 'hidden'}>×</button>
          </form>
          <ul class="stats">
            <li><b>${D.EXERCISES.length}</b><span>${esc(plural(D.EXERCISES.length, t.count))}</span></li>
            <li><b>${D.GROUP_KEYS.length}</b><span>${esc(t.statGroups)}</span></li>
            <li><b>${with3d}</b><span>${esc(t.stat3d)}</span></li>
          </ul>
        </div>
        <section class="mapcard" aria-labelledby="map-title">
          <div class="mapcard-head"><h2 class="eyebrow" id="map-title">${esc(t.fMuscles)}</h2><p class="hint">${esc(t.fMusclesHint)}</p></div>
          <div id="heromap"></div>
        </section>
      </section>
      <section class="toolbar" aria-label="${esc(t.filters)}"><div class="wrap" id="toolbar"></div></section>
      <section class="wrap results" id="results"></section>`;
    document.getElementById('search-form').addEventListener('submit', e => e.preventDefault());
    const q = document.getElementById('q');
    q.addEventListener('input', () => { S.q = q.value; app.querySelector('[data-act="clear-q"]').hidden = !S.q; refresh(); });
    refresh();
  }

  function refresh() {
    const t = T(), list = filtered(), n = activeCount() + (S.q.trim() ? 1 : 0);
    document.getElementById('heromap').innerHTML = bodyMap([...S.muscles], [], { interactive: true });

    const groupTabs = `<div class="tabs" role="group" aria-label="${esc(t.fGroup)}">
        <button type="button" class="pill" data-act="group" data-v="" aria-pressed="${!S.group}">${esc(t.all)} <span class="n">${D.EXERCISES.length}</span></button>
        ${D.GROUP_KEYS.map(g => `<button type="button" class="pill" data-act="group" data-v="${g}" aria-pressed="${S.group === g}">${esc(L().groups[g])} <span class="n">${D.EXERCISES.filter(e => e.group === g).length}</span></button>`).join('')}
      </div>`;
    const pc = panelCount();
    const row = `<div class="toolrow">
        <button type="button" class="pill filter-btn" data-act="panel" aria-expanded="${S.panel}" aria-controls="panel">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 6h16M7 12h10M10 18h4"/></svg>
          ${esc(t.filters)}${pc ? ` <span class="dotn">${pc}</span>` : ''}
        </button>
        ${[...S.muscles].map(k => `<button type="button" class="pill muscle" data-act="muscle" data-v="${k}" aria-pressed="true">${esc(mName(k))} <span class="x" aria-hidden="true">×</span></button>`).join('')}
        ${n ? `<button type="button" class="linkbtn" data-act="reset">${esc(t.reset)}</button>` : ''}
        <span class="count" role="status">${esc(t.found)}: ${list.length}</span>
      </div>`;
    const panel = !S.panel ? '' : `<div class="panel" id="panel">
        <fieldset><legend>${esc(t.fEquipment)}</legend><div class="opts">${D.EQUIPMENT_KEYS.map(k => `<button type="button" class="pill" data-act="equip" data-v="${k}" aria-pressed="${S.equipment.has(k)}">${esc(L().equipment[k])}</button>`).join('')}</div></fieldset>
        <fieldset><legend>${esc(t.fLevel)}</legend><div class="opts">${[1, 2, 3].map(k => `<button type="button" class="pill" data-act="level" data-v="${k}" aria-pressed="${S.levels.has(k)}">${levelHTML(k)}</button>`).join('')}</div>
          <label class="switch"><input type="checkbox" id="only3d" data-act="only3d" ${S.only3d ? 'checked' : ''}>${esc(t.only3d)}</label></fieldset>
        <fieldset><legend>${esc(t.fMuscles)}</legend><div class="opts">${D.MUSCLE_KEYS.map(k => `<button type="button" class="pill muscle" data-act="muscle" data-v="${k}" aria-pressed="${S.muscles.has(k)}">${esc(mName(k))}</button>`).join('')}</div></fieldset>
      </div>`;
    document.getElementById('toolbar').innerHTML = groupTabs + row + panel;

    const res = document.getElementById('results');
    if (!list.length) {
      res.innerHTML = `<div class="empty"><h2>${esc(t.nothing)}</h2><p>${esc(t.nothingHint)}</p><button type="button" class="pill" data-act="reset">${esc(t.reset)}</button></div>`;
    } else if (n) {
      res.innerHTML = `<h2 class="sr-only">${esc(t.found)}: ${list.length}</h2><ul class="grid">${list.map(card).join('')}</ul>`;
    } else {
      res.innerHTML = D.GROUP_KEYS.map(g => {
        const items = list.filter(e => e.group === g);
        return `<section aria-labelledby="g-${g}"><div class="group-head"><h2 id="g-${g}">${esc(L().groups[g])}</h2><span class="n">${items.length}</span></div><ul class="grid">${items.map(card).join('')}</ul></section>`;
      }).join('');
    }
  }

  function card(ex) {
    const x = exText(ex);
    return `<li><a class="card" href="#${ex.id}">
      <div class="card-fig">${ex.model ? '<span class="tag3d"><i aria-hidden="true"></i>3D</span>' : ''}${bodyMap(ex.muscles.primary, ex.muscles.secondary, { labels: false })}</div>
      <div class="card-body">
        <h3>${esc(x.name)}</h3>
        <p>${esc(x.short)}</p>
        <div class="chips">${chips(ex.muscles.primary, 'hot')}</div>
        <div class="card-foot"><span>${esc(ex.equipment.map(k => L().equipment[k]).join(' · '))}</span>${levelHTML(ex.level)}</div>
      </div>
    </a></li>`;
  }

  function toggle(set, v) { set.has(v) ? set.delete(v) : set.add(v); }
  function onCatalogAction(el) {
    const act = el.dataset.act, v = el.dataset.v;
    if (act === 'group') S.group = v || null;
    else if (act === 'muscle') toggle(S.muscles, v);
    else if (act === 'equip') toggle(S.equipment, v);
    else if (act === 'level') toggle(S.levels, +v);
    else if (act === 'only3d') S.only3d = el.checked;
    else if (act === 'panel') S.panel = !S.panel;
    else if (act === 'clear-q') { S.q = ''; const q = document.getElementById('q'); q.value = ''; el.hidden = true; q.focus(); }
    else if (act === 'reset') { S.q = ''; S.group = null; S.muscles.clear(); S.equipment.clear(); S.levels.clear(); S.only3d = false; renderCatalog(); return; }
    else return;
    refresh();
    // вернуть фокус на ту же кнопку после перерисовки
    const same = app.querySelector(`[data-act="${act}"]${v !== undefined ? `[data-v="${v}"]` : ''}`);
    if (same && act !== 'clear-q') same.focus({ preventScroll: true });
  }
  app.addEventListener('click', e => {
    if (location.hash.slice(1)) return;
    const m = e.target.closest('.bm.interactive [data-m]');
    if (m) { toggle(S.muscles, m.dataset.m); refresh(); return; }
    const el = e.target.closest('[data-act]');
    if (el && el.dataset.act !== 'only3d') onCatalogAction(el);
  });
  app.addEventListener('change', e => { if (e.target.dataset.act === 'only3d') onCatalogAction(e.target); });
  app.addEventListener('keydown', e => {
    const m = e.target.closest && e.target.closest('.bm.interactive [data-m]');
    if (m && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault(); const k = m.dataset.m; toggle(S.muscles, k); refresh();
      const again = app.querySelector(`.bm.interactive [data-m="${k}"]`); if (again) again.focus();
    }
  });

  /* ---------- страница упражнения ---------- */
  function renderDetail(ex) {
    const t = T(), x = exText(ex), en = D.LANG.en.ex[ex.id];
    document.title = x.name + ' · Exerfly';
    const md = ex.model, reps = fmtReps(ex);
    const stage = md ? `<div class="stage">
        <model-viewer id="mv" src="${MODELS[S.who]}" animation-name="${md.variants[0].anim}" autoplay camera-controls
          environment-image="neutral" exposure="1.05" shadow-intensity="1.1" shadow-softness="0.9" field-of-view="28deg"
          camera-target="${md.target}" camera-orbit="${md.orbit}" min-camera-orbit="auto 20deg 1.5m" max-camera-orbit="auto 88deg ${md.max}"
          interaction-prompt="none" touch-action="pan-y" alt="${esc(x.name)}"></model-viewer>
        <span class="hint" aria-hidden="true">${esc(t.drag)}</span>
        <div class="stage-top">
          <div class="seg who" role="group" aria-label="${esc(t.character)}">
            ${['m', 'f'].map(v => `<button type="button" data-who="${v}" aria-pressed="${S.who === v}">${esc(v === 'm' ? t.male : t.female)}</button>`).join('')}
          </div>
          ${md.variants.length > 1 ? `<div class="seg variants" role="group" aria-label="${esc(t.variant)}">${md.variants.map((v, i) =>
            `<button type="button" data-anim="${v.anim}" aria-pressed="${i === 0}">${esc(t.variants[v.label] || v.label)}</button>`).join('')}</div>` : ''}
        </div>
        <div class="player">
          <button type="button" class="pbtn" id="pp" aria-label="${esc(t.pause)}" title="${esc(t.pause)}">
            <svg class="i-pause" viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>
            <svg class="i-play" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z"/></svg>
          </button>
          <input type="range" id="scrub" min="0" max="1" step="0.001" value="0" aria-label="${esc(t.phase)}">
          <div class="speed" role="group" aria-label="${esc(t.speed)}">
            ${[1, 0.5, 0.25].map(v => `<button type="button" data-speed="${v}" aria-pressed="${v === S.speed}">${v === 1 ? '1×' : v === 0.5 ? '0.5×' : '0.25×'}</button>`).join('')}
          </div>
          <button type="button" class="glow-btn" id="glow" aria-pressed="false" disabled title="${esc(t.soon)}">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v2M12 19v2M5 12H3M21 12h-2M6.3 6.3 4.9 4.9M19.1 19.1l-1.4-1.4M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4"/><circle cx="12" cy="12" r="4"/></svg>
            <span>${esc(t.glow)}</span>
          </button>
        </div>
      </div>`
      : `<div class="stage flat"><div class="inner">${bodyMap(ex.muscles.primary, ex.muscles.secondary)}<span class="note">${esc(t.no3d)}</span></div></div>`;

    app.innerHTML = `<article class="wrap" aria-labelledby="ex-title">
      <nav class="crumbs" aria-label="${esc(t.breadcrumbs)}"><a class="back" href="#"><span aria-hidden="true">←</span> ${esc(t.backToAll)}</a></nav>
      <header class="ex-head">
        <p class="eyebrow">${esc(L().groups[ex.group])}</p>
        <h1 id="ex-title" tabindex="-1">${esc(x.name)}</h1>
        ${S.lang !== 'en' && en ? `<p class="sub" lang="en">${esc(en.name)}</p>` : ''}
        <p class="lead">${esc(x.short)}</p>
      </header>
      ${stage}
      <div class="ex-body">
        <div>
          <section class="box"><h2>${esc(t.technique)}</h2>
            <ol class="steps">${x.steps.map(s => `<li><span>${esc(s)}</span></li>`).join('')}</ol></section>
          <section class="box"><h2>${esc(t.mistakes)}</h2>
            <ul class="mistakes">${x.mistakes.map(s => `<li><span>${esc(s)}</span></li>`).join('')}</ul></section>
        </div>
        <div class="aside">
          <section class="box" aria-labelledby="facts-title">
            <h2 class="sr-only" id="facts-title">${esc(t.sets)}, ${esc(t.reps)}, ${esc(t.rest)}</h2>
            <dl class="facts">
              <div><dt>${esc(t.sets)}</dt><dd><b>${esc(ex.sets)}</b></dd></div>
              <div><dt>${esc(t.reps)}</dt><dd><b>${esc(reps.v)}</b>${reps.note ? ` <small>${esc(reps.note)}</small>` : ''}</dd></div>
              <div><dt>${esc(t.rest)}</dt><dd><b>${esc(fmtRest(ex.rest))}</b></dd></div>
            </dl>
          </section>
          <section class="box"><h2>${esc(t.muscles)}</h2>
            <div class="mus">
              ${bodyMap(ex.muscles.primary, ex.muscles.secondary)}
              <div class="mlist">
                <div><div class="lbl"><span class="sw pri"></span>${esc(t.primary)}</div><div class="chips">${chips(ex.muscles.primary, 'hot')}</div></div>
                ${ex.muscles.secondary.length ? `<div><div class="lbl"><span class="sw sec"></span>${esc(t.secondary)}</div><div class="chips">${chips(ex.muscles.secondary)}</div></div>` : ''}
              </div>
            </div>
          </section>
          <section class="box"><h2>${esc(t.equipLevel)}</h2>
            <div class="metarow">${ex.equipment.map(k => `<span class="chip">${esc(L().equipment[k])}</span>`).join('')}<span class="chip">${levelHTML(ex.level)}</span></div>
          </section>
        </div>
      </div>
    </article>`;
    const mv = document.getElementById('mv');
    if (mv) setupPlayer(mv, ex);
  }

  /* ---------- плеер: пауза, скорость, фаза, подсветка мышц ---------- */
  // слой мышц в модели: материалы M_<мышца>, у каждого меняем прозрачность
  const GLOW = [1.0, 0.35, 0.21];
  const glowAlpha = (ex, key) => ex.muscles.primary.includes(key) ? 0.88 : ex.muscles.secondary.includes(key) ? 0.38 : 0;

  function setupPlayer(mv, ex) {
    const t = T(), pp = document.getElementById('pp'), scrub = document.getElementById('scrub'), glowBtn = document.getElementById('glow');
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    let dragging = false;
    const setPaused = paused => {
      pp.classList.toggle('paused', paused);
      pp.setAttribute('aria-label', paused ? t.play : t.pause); pp.title = paused ? t.play : t.pause;
    };
    pp.addEventListener('click', () => { if (mv.paused) mv.play(); else mv.pause(); setPaused(mv.paused); });
    scrub.addEventListener('input', () => {
      dragging = true; mv.pause(); setPaused(true);
      mv.currentTime = +scrub.value * (mv.duration || 0);
    });
    scrub.addEventListener('change', () => { dragging = false; });
    app.querySelectorAll('.speed button').forEach(b => b.addEventListener('click', () => {
      S.speed = +b.dataset.speed; mv.timeScale = S.speed;
      app.querySelectorAll('.speed button').forEach(o => o.setAttribute('aria-pressed', String(o === b)));
    }));
    app.querySelectorAll('.variants button').forEach(b => b.addEventListener('click', () => {
      mv.animationName = b.dataset.anim; mv.play(); setPaused(false);
      app.querySelectorAll('.variants button').forEach(o => o.setAttribute('aria-pressed', String(o === b)));
    }));
    // персонаж: мужчина / женщина, выбор запоминается для следующих упражнений
    app.querySelectorAll('.who button').forEach(b => b.addEventListener('click', () => {
      if (S.who === b.dataset.who) return;
      S.who = b.dataset.who; store.set('exerfly-character', S.who);
      app.querySelectorAll('.who button').forEach(o => o.setAttribute('aria-pressed', String(o === b)));
      overlay = []; body = null; mv.src = MODELS[S.who]; setPaused(false);
    }));

    let overlay = [], body = null, bodyDim = -1;
    glowBtn.addEventListener('click', () => {
      S.glow = !S.glow; store.set('exerfly-glow', S.glow ? '1' : '0');
      glowBtn.setAttribute('aria-pressed', String(S.glow));
    });
    mv.addEventListener('load', () => {
      mv.timeScale = S.speed;
      const mats = mv.model ? mv.model.materials : [];
      overlay = mats.filter(m => m.name && m.name.startsWith('M_')).map(m => ({ m, key: m.name.slice(2), a: -1 }));
      body = mats.find(m => m.name === 'Athlete') || null; bodyDim = -1;

    });

    (function tick(now) {
      if (!mv.isConnected) return;
      const d = mv.duration || 0;
      if (d && !dragging) scrub.value = ((mv.currentTime % d) / d).toFixed(3);
      if (overlay.length) {
        const k = S.glow ? (reduce ? 1 : 0.78 + 0.22 * Math.sin(now / 320)) : 0;
        // в режиме подсветки тело приглушается, чтобы мышцы читались лучше
        const dim = S.glow ? 0.42 : 1;
        if (body && dim !== bodyDim) { body.pbrMetallicRoughness.setBaseColorFactor([dim, dim, dim * 1.04, 1]); bodyDim = dim; }
        for (const o of overlay) {
          const a = Math.round(glowAlpha(ex, o.key) * k * 100) / 100;
          if (a !== o.a) { o.m.pbrMetallicRoughness.setBaseColorFactor([GLOW[0], GLOW[1], GLOW[2], a]); o.a = a; }
        }
      }
      requestAnimationFrame(tick);
    })(performance.now());
  }

  /* ---------- роутер ---------- */
  let catalogScroll = 0, onCatalog = true, firstRoute = true;
  function route(keepScroll) {
    const id = decodeURIComponent(location.hash.slice(1));
    if (id && byId[id]) {
      if (onCatalog) catalogScroll = window.scrollY;
      onCatalog = false; renderDetail(byId[id]);
      if (keepScroll !== true) window.scrollTo(0, 0);
    } else {
      const y = keepScroll === true ? window.scrollY : catalogScroll;
      onCatalog = true; renderCatalog(); window.scrollTo(0, y);
    }
    // после перехода переносим фокус на заголовок, чтобы экранный диктор прочитал новую страницу
    if (!firstRoute && keepScroll !== true) { const h = app.querySelector('h1'); if (h) h.focus({ preventScroll: true }); }
    firstRoute = false;
  }
  window.addEventListener('hashchange', () => route());
  renderHeader();
  route();
})();

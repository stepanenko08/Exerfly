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
    q: '', group: null, speed: 1, who: store.get('exerfly-character') === 'f' ? 'f' : 'm', glow: false, /* подсветка мышц временно выключена */ muscles: new Set(), equipment: new Set(), levels: new Set(), only3d: false, panel: false, tbCollapsed: null, favOnly: false
  };
  /* избранное — в браузере, как тема и язык */
  const FAV = new Set((() => { try { return JSON.parse(store.get('exerfly-fav') || '[]'); } catch (e) { return []; } })());
  const saveFav = () => store.set('exerfly-fav', JSON.stringify([...FAV]));
  const HEART = '<svg class="heart" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.3s-7.6-4.6-9.2-9.4C1.7 7.6 3.9 4.5 7.2 4.5c2 0 3.6 1.1 4.8 2.8 1.2-1.7 2.8-2.8 4.8-2.8 3.3 0 5.5 3.1 4.4 6.4-1.6 4.8-9.2 9.4-9.2 9.4Z"/></svg>';
  function toast(msg) {
    let el = document.getElementById('toast');
    if (!el) { el = document.createElement('div'); el.id = 'toast'; el.className = 'toast'; el.setAttribute('role', 'status'); document.body.appendChild(el); }
    el.textContent = msg; el.classList.add('show');
    clearTimeout(toast.t); toast.t = setTimeout(() => el.classList.remove('show'), 2200);
  }
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
  /* схема мышц: одна общая копия контуров (symbol), карточки ссылаются на неё через <use> и красят мышцы CSS-переменными;
     интерактивная схема на главной — со своими контурами, чтобы по каждой мышце можно было нажать */
  const BODY = D.BODY;
  const BM_VIEWS = ['front', 'back'];
  (function injectBodySymbol() {
    let s = '';
    for (const v of BM_VIEWS) for (const [k, d] of Object.entries(BODY[v]))
      s += k === '_body' ? `<path d="${d}" style="fill:var(--body)"/>` : `<path d="${d}" style="fill:var(--bm-${k},var(--bm-idle))"/>`;
    document.body.insertAdjacentHTML('afterbegin', `<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><symbol id="bm-sym" viewBox="0 0 ${BODY.w} ${BODY.h}">${s}</symbol></svg>`);
  })();
  function bodyMap(primary, secondary, opts = {}) {
    const pri = new Set(primary), sec = new Set(secondary || []);
    const labels = opts.labels === false ? '' :
      `<text x="${BODY.cx.front}" y="${BODY.h + 9}" text-anchor="middle">${esc(T().front)}</text><text x="${BODY.cx.back}" y="${BODY.h + 9}" text-anchor="middle">${esc(T().back)}</text>`;
    const vb = `0 0 ${BODY.w} ${BODY.h + (opts.labels === false ? 0 : 12)}`;
    if (!opts.interactive) {
      const vars = [...pri].map(k => `--bm-${k}:var(--heat)`).concat([...sec].filter(k => !pri.has(k)).map(k => `--bm-${k}:var(--heat-2)`)).join(';');
      return `<svg class="bm" viewBox="${vb}" style="${vars}" role="img" aria-label="${esc(primary.map(mName).join(', '))}"><use href="#bm-sym" width="${BODY.w}" height="${BODY.h}"/>${labels}</svg>`;
    }
    let s = '';
    for (const v of BM_VIEWS) for (const [k, d] of Object.entries(BODY[v])) {
      if (k === '_body') { s += `<path class="bm-body" d="${d}"/>`; continue; }
      s += `<path class="m ${pri.has(k) ? 'pri' : sec.has(k) ? 'sec' : ''}" data-m="${k}" role="button" tabindex="0" aria-pressed="${pri.has(k)}" aria-label="${esc(mName(k))}" d="${d}"></path>`;
    }
    return `<svg class="bm interactive" viewBox="${vb}" aria-label="${esc(T().fMusclesHint)}">${s}${labels}</svg>`;
  }

  const levelHTML = n => `<span class="level">${esc(L().levels[n])}<span class="bars" aria-hidden="true"><i class="${n >= 1 ? 'on' : ''}"></i><i class="${n >= 2 ? 'on' : ''}"></i><i class="${n >= 3 ? 'on' : ''}"></i></span></span>`;
  const chips = (keys, cls = '') => keys.map(k => `<span class="chip ${cls}">${esc(mName(k))}</span>`).join('');

  /* ---------- тема ---------- */
  const themeBtn = document.getElementById('theme');
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
  const activeCount = () => (S.favOnly ? 1 : 0) + (S.group ? 1 : 0) + S.muscles.size + S.equipment.size + S.levels.size + (S.only3d ? 1 : 0);
  const panelCount = () => S.equipment.size + S.levels.size + (S.only3d ? 1 : 0);
  function filtered() {
    const words = norm(S.q.trim()).split(/\s+/).filter(Boolean);
    let list = D.EXERCISES.filter(ex => {
      if (S.favOnly && !FAV.has(ex.id)) return false;
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
          <div class="mapcard-head"><h2 class="eyebrow" id="map-title">${esc(t.fMuscles)}</h2><span class="map-hover" id="map-hover" aria-hidden="true"></span><p class="hint">${esc(t.fMusclesHint)}</p></div>
          <div id="heromap"></div>
        </section>
      </section>
      <section class="toolbar" id="tbar" aria-label="${esc(t.filters)}"><div class="wrap">
        <div class="tb-row">
          <div class="mini-search" role="search">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
            <input id="q2" type="search" autocomplete="off" placeholder="${esc(t.search)}" aria-label="${esc(t.search)}" value="${esc(S.q)}">
            <button type="button" class="clear" data-act="clear-q" aria-label="${esc(t.clearSearch)}" ${S.q ? '' : 'hidden'}>×</button>
          </div>
          <div class="tb-filter" id="tb-filter"></div>
          <div class="tb-scroll" id="tb-scroll">
            <button type="button" class="tb-arrow prev" data-dir="-1" tabindex="-1" aria-hidden="true" hidden><svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg></button>
            <div class="tabs" id="tb-tabs" role="group" aria-label="${esc(t.fGroup)}"></div>
            <button type="button" class="tb-arrow next" data-dir="1" tabindex="-1" aria-hidden="true" hidden><svg viewBox="0 0 24 24"><path d="m9 6 6 6-6 6"/></svg></button>
          </div>
        </div>
        <div id="toolbar" class="tb-extra"></div>
        <button type="button" class="tb-toggle" id="tb-toggle" aria-controls="tb-filter tb-scroll toolbar" aria-expanded="true" aria-label="${esc(t.collapse)}" title="${esc(t.collapse)}">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 15 6-6 6 6"/></svg>
        </button>
      </div></section>
      <section class="wrap results" id="results"></section>
      <div id="sheet-root"></div>`;
    document.getElementById('search-form').addEventListener('submit', e => e.preventDefault());
    const q = document.getElementById('q');
    const q2 = document.getElementById('q2');
    const onType = src => { S.q = src.value; (src === q ? q2 : q).value = S.q; app.querySelectorAll('[data-act="clear-q"]').forEach(b => { b.hidden = !S.q; }); refresh(); };
    q.addEventListener('input', () => onType(q));
    q2.addEventListener('input', () => onType(q2));
    // стрелка: на телефоне сворачивает панель, на компьютере закрывает открытые фильтры
    document.getElementById('tb-toggle').addEventListener('click', () => {
      if (narrowMQ.matches) { S.tbCollapsed = !tbCollapsed(); syncStuck(); }
      else closePanel();
    });
    // стрелки прокрутки групп мышц
    const tabs = document.getElementById('tb-tabs');
    document.querySelectorAll('.tb-arrow').forEach(btn => btn.addEventListener('click', () => {
      tabs.scrollBy({ left: +btn.dataset.dir * tabs.clientWidth * 0.7, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    }));
    tabs.addEventListener('scroll', syncArrows, { passive: true });
    if (window.ResizeObserver) new ResizeObserver(syncArrows).observe(tabs);
    refresh();
    syncStuck();
  }

  /* панель фильтров «прилипла» к шапке → показываем мини-поиск и стрелку сворачивания.
     S.tbCollapsed: null — авто (на телефоне свёрнута, на компьютере раскрыта), иначе выбор пользователя */
  const narrowMQ = matchMedia('(max-width: 767px)');
  const tbCollapsed = () => S.tbCollapsed === null ? narrowMQ.matches : S.tbCollapsed;
  function syncStuck() {
    const bar = document.getElementById('tbar');
    if (!bar) return;
    const top = parseFloat(getComputedStyle(bar).top) || 0;
    const stuck = getComputedStyle(bar).position === 'sticky' && bar.getBoundingClientRect().top <= top + 0.5 && window.scrollY > 0;
    const narrow = narrowMQ.matches, collapsed = narrow && stuck && tbCollapsed() && !S.panel;   // открытые фильтры не прячем
    bar.classList.toggle('stuck', stuck);
    bar.classList.toggle('collapsed', collapsed);
    const btn = document.getElementById('tb-toggle'), t = T();
    bar.classList.toggle('panel-open', S.panel);
    // открытые фильтры в прилипшей панели: ограничиваем высоту экраном, чтобы листались сами фильтры, а не страница
    const pnl = document.getElementById('panel');
    if (pnl && !pnl.classList.contains('sheet')) {
      const vh = window.visualViewport ? window.visualViewport.height : window.innerHeight;
      pnl.style.maxHeight = stuck ? Math.max(160, vh - pnl.getBoundingClientRect().top - 12) + 'px' : '';
    }
    if (btn) {
      const label = narrow ? (collapsed ? t.expand : t.collapse) : t.collapseFilters;
      btn.setAttribute('aria-controls', narrow ? 'tb-filter tb-scroll toolbar' : 'panel');
      btn.setAttribute('aria-expanded', String(narrow ? !collapsed : S.panel));
      btn.setAttribute('aria-label', label); btn.title = label;
    }
    // если фокус был в мини-поиске, а панель отлипла — переносим его в большой поиск
    if (!stuck && document.activeElement && document.activeElement.id === 'q2') document.getElementById('q').focus({ preventScroll: true });
  }
  function syncArrows() {
    const tabs = document.getElementById('tb-tabs'), box = document.getElementById('tb-scroll');
    if (!tabs || !box) return;
    const max = tabs.scrollWidth - tabs.clientWidth;
    const canPrev = tabs.scrollLeft > 2, canNext = tabs.scrollLeft < max - 2;
    box.querySelector('.prev').hidden = !canPrev;
    box.querySelector('.next').hidden = !canNext;
    tabs.style.setProperty('--fl', canPrev ? '56px' : '0px');
    tabs.style.setProperty('--fr', canNext ? '56px' : '0px');
  }
  // показать выбранную/сфокусированную группу целиком, если она за краем
  function revealTab(el) {
    const tabs = document.getElementById('tb-tabs');
    if (!tabs || !el || !tabs.contains(el)) return;
    const pad = 48, l = el.offsetLeft - tabs.offsetLeft, r = l + el.offsetWidth;
    if (l < tabs.scrollLeft + pad) tabs.scrollLeft = Math.max(0, l - pad);
    else if (r > tabs.scrollLeft + tabs.clientWidth - pad) tabs.scrollLeft = r - tabs.clientWidth + pad;
  }
  document.addEventListener('focusin', e => { if (e.target.closest && e.target.closest('#tb-tabs')) revealTab(e.target); });

  function closePanel() {
    if (!S.panel) return;
    S.panel = false; refresh();
    const fb = app.querySelector('[data-act="panel"]'); if (fb) fb.focus({ preventScroll: true });
  }
  // клик вне панели фильтров (и не по кнопке «Фильтры») — закрыть её
  document.addEventListener('click', e => {
    if (!S.panel || location.hash.slice(1)) return;
    const inside = e.composedPath().some(el => el.id === 'panel' || el.id === 'tb-toggle' || (el.dataset && el.dataset.act === 'panel'));
    if (!inside) closePanel();
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && S.panel && !location.hash.slice(1)) closePanel(); });

  let stuckRAF = 0;
  addEventListener('scroll', () => { if (!stuckRAF) stuckRAF = requestAnimationFrame(() => { stuckRAF = 0; syncStuck(); }); }, { passive: true });
  addEventListener('resize', syncStuck);
  if (window.visualViewport) visualViewport.addEventListener('resize', syncStuck);

  let sheetOpen = false;
  function renderSheet(open, fields, n) {
    const root = document.getElementById('sheet-root'); if (!root) return;
    const t = T(), body = root.querySelector('.sheet-body'), keep = body ? body.scrollTop : 0;
    document.documentElement.classList.toggle('sheet-open', open);
    if (!open) { root.innerHTML = ''; sheetOpen = false; return; }
    root.innerHTML = `<div class="sheet-backdrop" data-act="panel" aria-hidden="true"></div>
      <div class="panel sheet${sheetOpen ? '' : ' enter'}" id="panel" role="dialog" aria-modal="true" aria-labelledby="sheet-title">
        <div class="sheet-head"><span class="sheet-grip" aria-hidden="true"></span><h2 id="sheet-title">${esc(t.filters)}</h2>
          <button type="button" class="sheet-x" data-act="panel" aria-label="${esc(t.collapseFilters)}">×</button></div>
        <div class="sheet-body">${fields}</div>
        <div class="sheet-foot">
          <button type="button" class="linkbtn" data-act="reset">${esc(t.reset)}</button>
          <button type="button" class="pill sheet-go" data-act="panel">${esc(t.showResults)} · ${n}</button>
        </div>
      </div>`;
    root.querySelector('.sheet-body').scrollTop = keep;
    if (!sheetOpen) root.querySelector('.sheet-x').focus({ preventScroll: true });
    sheetOpen = true;
  }
  narrowMQ.addEventListener && narrowMQ.addEventListener('change', () => { if (!location.hash.slice(1) && document.getElementById('tbar')) refresh(); });

  function refresh() {
    const t = T(), list = filtered(), n = activeCount() + (S.q.trim() ? 1 : 0);
    document.getElementById('heromap').innerHTML = bodyMap([...S.muscles], [], { interactive: true });

    const groupTabs = `<button type="button" class="pill" data-act="group" data-v="" aria-pressed="${!S.group}">${esc(t.all)} <span class="n">${D.EXERCISES.length}</span></button>
        <button type="button" class="pill fav-pill" data-act="favonly" aria-pressed="${S.favOnly}">${HEART}${esc(t.favorites)} <span class="n">${FAV.size}</span></button>
        ${D.GROUP_KEYS.map(g => `<button type="button" class="pill" data-act="group" data-v="${g}" aria-pressed="${S.group === g}">${esc(L().groups[g])} <span class="n">${D.EXERCISES.filter(e => e.group === g).length}</span></button>`).join('')}`;
    const pc = panelCount();
    const filterBtn = `<button type="button" class="pill filter-btn" data-act="panel" aria-expanded="${S.panel}" aria-controls="panel">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 6h16M7 12h10M10 18h4"/></svg>
          ${esc(t.filters)}${pc ? ` <span class="dotn">${pc}</span>` : ''}
        </button>`;
    const count = `<span class="count" role="status">${esc(t.found)}: ${list.length}</span>`;
    // строка с выбранными мышцами и сбросом — только когда что-то выбрано; иначе счётчик только для скринридера
    const row = n ? `<div class="toolrow">
        ${[...S.muscles].map(k => `<button type="button" class="pill muscle" data-act="muscle" data-v="${k}" aria-pressed="true">${esc(mName(k))} <span class="x" aria-hidden="true">×</span></button>`).join('')}
        <button type="button" class="linkbtn" data-act="reset">${esc(t.reset)}</button>
        ${count}
      </div>` : `<div class="sr-only">${count}</div>`;
    const fields = `        <fieldset><legend>${esc(t.fEquipment)}</legend><div class="opts">${D.EQUIPMENT_KEYS.map(k => `<button type="button" class="pill" data-act="equip" data-v="${k}" aria-pressed="${S.equipment.has(k)}">${esc(L().equipment[k])}</button>`).join('')}</div></fieldset>
        <fieldset><legend>${esc(t.fLevel)}</legend><div class="opts">${[1, 2, 3].map(k => `<button type="button" class="pill" data-act="level" data-v="${k}" aria-pressed="${S.levels.has(k)}">${levelHTML(k)}</button>`).join('')}</div>
          <label class="switch"><input type="checkbox" id="only3d" data-act="only3d" ${S.only3d ? 'checked' : ''}>${esc(t.only3d)}</label></fieldset>
        <fieldset><legend>${esc(t.fMuscles)}</legend><div class="opts">${D.MUSCLE_KEYS.map(k => `<button type="button" class="pill muscle" data-act="muscle" data-v="${k}" aria-pressed="${S.muscles.has(k)}">${esc(mName(k))}</button>`).join('')}</div></fieldset>`;
    // телефон: фильтры во всплывающем окне снизу; компьютер — панелью под строкой групп
    const sheet = S.panel && narrowMQ.matches;
    const panel = !S.panel || sheet ? '' : `<div class="panel" id="panel">${fields}</div>`;
    document.getElementById('tb-filter').innerHTML = filterBtn;
    const tabsEl = document.getElementById('tb-tabs'), keep = tabsEl.scrollLeft;
    tabsEl.innerHTML = groupTabs;
    tabsEl.scrollLeft = keep;
    document.getElementById('toolbar').innerHTML = row + panel;
    renderSheet(sheet, fields, list.length);
    syncArrows(); syncStuck();

    const res = document.getElementById('results');
    if (!list.length) {
      const favEmpty = S.favOnly && !FAV.size;
      res.innerHTML = favEmpty ? `<div class="empty fav-empty">${HEART}<h2>${esc(t.favEmptyTitle)}</h2><p>${esc(t.favEmptyHint)}</p><button type="button" class="pill" data-act="favonly">${esc(t.all)}</button></div>` : `<div class="empty"><h2>${esc(t.nothing)}</h2><p>${esc(t.nothingHint)}</p><button type="button" class="pill" data-act="reset">${esc(t.reset)}</button></div>`;
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
    </a>${favBtn(ex, 'fav-btn')}</li>`;
  }
  function favBtn(ex, cls) {
    const on = FAV.has(ex.id), t = T(), name = exText(ex).name;
    return `<button type="button" class="${cls}" data-act="fav" data-v="${ex.id}" aria-pressed="${on}" aria-label="${esc((on ? t.removeFav : t.addFav) + ': ' + name)}" title="${esc(on ? t.removeFav : t.addFav)}">${HEART}${cls === 'fav-big' ? `<span>${esc(on ? t.inFav : t.addFav)}</span>` : ''}</button>`;
  }
  function toggleFav(id) { FAV.has(id) ? FAV.delete(id) : FAV.add(id); saveFav(); }

  function toggle(set, v) { set.has(v) ? set.delete(v) : set.add(v); }
  function onCatalogAction(el) {
    const act = el.dataset.act, v = el.dataset.v;
    if (act === 'group') S.group = v || null;
    else if (act === 'muscle') toggle(S.muscles, v);
    else if (act === 'equip') toggle(S.equipment, v);
    else if (act === 'level') toggle(S.levels, +v);
    else if (act === 'only3d') S.only3d = el.checked;
    else if (act === 'panel') S.panel = !S.panel;
    else if (act === 'fav') toggleFav(v);
    else if (act === 'favonly') S.favOnly = !S.favOnly;
    else if (act === 'clear-q') {
      S.q = ''; const inMini = !!el.closest('.mini-search');
      ['q', 'q2'].forEach(id => { const i = document.getElementById(id); if (i) i.value = ''; });
      app.querySelectorAll('[data-act="clear-q"]').forEach(b => { b.hidden = true; });
      document.getElementById(inMini ? 'q2' : 'q').focus({ preventScroll: inMini });
    }
    else if (act === 'reset') { S.q = ''; S.favOnly = false; S.group = null; S.muscles.clear(); S.equipment.clear(); S.levels.clear(); S.only3d = false; renderCatalog(); return; }
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
  // подпись группы мышц над схемой при наведении (и при фокусе с клавиатуры)
  function mapHover(k) {
    const el = document.getElementById('map-hover'); if (!el) return;
    if (k) el.textContent = mName(k);
    el.classList.toggle('on', !!k);
    app.querySelectorAll('.bm.interactive .m.hov').forEach(x => x.classList.remove('hov'));
    if (k) app.querySelectorAll(`.bm.interactive [data-m="${k}"]`).forEach(x => x.classList.add('hov'));
  }
  app.addEventListener('pointerover', e => { const m = e.target.closest && e.target.closest('.bm.interactive [data-m]'); if (m && e.pointerType !== 'touch') mapHover(m.dataset.m); });
  app.addEventListener('pointerout', e => { const m = e.target.closest && e.target.closest('.bm.interactive [data-m]'); if (m && !(e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest(`[data-m="${m.dataset.m}"]`))) mapHover(null); });
  app.addEventListener('focusin', e => { const m = e.target.closest && e.target.closest('.bm.interactive [data-m]'); if (m) mapHover(m.dataset.m); });
  app.addEventListener('focusout', e => { if (e.target.closest && e.target.closest('.bm.interactive [data-m]')) mapHover(null); });
  // мышью/пальцем мышца не получает фокус — иначе браузер на миг рисует рамку фокуса (клавиатурой фокус остаётся)
  app.addEventListener('mousedown', e => { if (e.target.closest && e.target.closest('.bm.interactive [data-m]')) e.preventDefault(); });
  app.addEventListener('keydown', e => {
    const m = e.target.closest && e.target.closest('.bm.interactive [data-m]');
    if (m && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault(); const k = m.dataset.m; toggle(S.muscles, k); refresh();
      const again = app.querySelector(`.bm.interactive [data-m="${k}"]`); if (again) again.focus();
    }
  });

  /* камера: на телефоне чуть дальше, чтобы кнопки поверх 3D не закрывали модель */
  const phoneMQ = matchMedia('(max-width: 640px)');
  const CAM_PHONE = 1.55;
  const CAM_DESK = 1.25;                            // и на компьютере чуть дальше: плеер и кнопки не должны закрывать модель
  const camFactor = md => phoneMQ.matches ? (md.phone || CAM_PHONE) : (md.desk || CAM_DESK);
  const camOrbit = md => {
    const p = md.orbit.trim().split(/\s+/); p[2] = (parseFloat(p[2]) * camFactor(md)).toFixed(2) + 'm'; return p.join(' ');
  };
  const camMax = md => (Math.max(parseFloat(md.max), parseFloat(camOrbit(md).split(/\s+/)[2]) + 1)).toFixed(1) + 'm';
  phoneMQ.addEventListener && phoneMQ.addEventListener('change', () => {
    const mv = document.getElementById('mv'), ex = byId[decodeURIComponent(location.hash.slice(1))];
    if (!mv || !ex || !ex.model) return;
    mv.maxCameraOrbit = `auto 88deg ${camMax(ex.model)}`; mv.cameraOrbit = camOrbit(ex.model);
  });

  // знак логотипа — для экрана загрузки
  const WING = document.querySelector('.logo-mark') ? document.querySelector('.logo-mark').innerHTML.replace(/class="hot"/g, '') : '';

  /* соседние упражнения: в пределах текущей выборки каталога, если упражнение в ней есть, иначе по всему списку */
  function neighbours(ex) {
    let list = filtered(); if (!list.includes(ex)) list = D.EXERCISES;
    const i = list.indexOf(ex), n = list.length;
    return n < 2 ? null : { prev: list[(i - 1 + n) % n], next: list[(i + 1) % n] };
  }
  function exNav(ex) {
    const nb = neighbours(ex), t = T(); if (!nb) return '';
    return `<nav class="ex-nav" aria-label="${esc(t.exNav)}">
      <a class="ex-nav-link prev" href="#${nb.prev.id}" rel="prev"><span class="dir"><span aria-hidden="true">←</span> ${esc(t.prevEx)}</span><span class="nm">${esc(exText(nb.prev).name)}</span></a>
      <a class="ex-nav-link next" href="#${nb.next.id}" rel="next"><span class="dir">${esc(t.nextEx)} <span aria-hidden="true">→</span></span><span class="nm">${esc(exText(nb.next).name)}</span></a>
    </nav>`;
  }
  function setupDetail(ex) {
    const t = T(), x = exText(ex);
    // избранное
    const fb = app.querySelector('.fav-big');
    fb.addEventListener('click', () => { toggleFav(ex.id); fb.outerHTML = favBtn(ex, 'fav-big'); setupFavBig(); });
    function setupFavBig() { const b = app.querySelector('.fav-big'); b.focus({ preventScroll: true }); b.addEventListener('click', () => { toggleFav(ex.id); b.outerHTML = favBtn(ex, 'fav-big'); setupFavBig(); }); }
    // поделиться: системное меню на телефоне, иначе — копирование ссылки
    const shareBtn = document.getElementById('share');   // кнопка временно убрана
    if (shareBtn) shareBtn.addEventListener('click', async () => {
      const url = location.href, data = { title: x.name + ' · Exerfly', text: x.short, url };
      if (navigator.share && matchMedia('(pointer: coarse)').matches) { try { await navigator.share(data); } catch (e) { /* закрыли меню */ } return; }
      try { await navigator.clipboard.writeText(url); }
      catch (e) { const ta = document.createElement('textarea'); ta.value = url; ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (e2) {} ta.remove(); }
      toast(t.linkCopied);
    });
  }

  /* клавиши на странице упражнения: пробел — пауза, ← → — перемотка */
  document.addEventListener('keydown', e => {
    const mv = document.getElementById('mv'); if (!mv || e.altKey || e.ctrlKey || e.metaKey) return;
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable) return;
    if (e.key === ' ' || e.code === 'Space') {
      if (tag === 'button' || tag === 'a') return;                 // пробел на кнопке — нажимает кнопку
      e.preventDefault(); document.getElementById('pp').click();
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      const d = mv.duration || 0; if (!d) return;
      e.preventDefault();
      const step = (e.shiftKey ? 1 : 0.25) * (e.key === 'ArrowLeft' ? -1 : 1);
      mv.currentTime = ((mv.currentTime + step) % d + d) % d;
    }
  });

  /* ---------- страница упражнения ---------- */
  function renderDetail(ex) {
    const t = T(), x = exText(ex), en = D.LANG.en.ex[ex.id];
    document.title = x.name + ' · Exerfly';
    const md = ex.model, reps = fmtReps(ex);
    const stage = md ? `<div class="stage">
        <div class="loader" id="loader" role="progressbar" aria-label="${esc(t.loading3d)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
          <svg class="ld-mark" viewBox="0 0 128 128" aria-hidden="true">
            <defs><clipPath id="ld-clip"><rect id="ld-rect" x="0" y="0" width="0" height="128"/></clipPath></defs>
            <g class="ld-base">${WING}</g><g class="ld-fill" clip-path="url(#ld-clip)">${WING}</g>
          </svg>
          <div class="ld-txt"><span>${esc(t.loading3d)}</span><b id="ld-pct">0%</b></div>
        </div>
        <model-viewer id="mv" src="${MODELS[S.who]}" animation-name="${md.variants[0].anim}" autoplay camera-controls
          environment-image="neutral" exposure="1.05" shadow-intensity="1.1" shadow-softness="0.9" field-of-view="28deg"
          camera-target="${md.target}" camera-orbit="${camOrbit(md)}" min-camera-orbit="auto 20deg 1.5m" max-camera-orbit="auto 88deg ${camMax(md)}"
          interaction-prompt="none" touch-action="pan-y" alt="${esc(x.name)}"></model-viewer>
        <span class="hint" aria-hidden="true">${esc(t.drag)} · ${esc(t.keysHint)}</span>
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
        <div class="ex-actions">${favBtn(ex, 'fav-big')}
        </div>
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
      ${exNav(ex)}
    </article>`;
    const mv = document.getElementById('mv');
    if (mv) setupPlayer(mv, ex);
    setupDetail(ex);
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
      pp.setAttribute('aria-label', paused ? t.play : t.pause); pp.title = (paused ? t.play : t.pause) + ' (Space)';
    };
    pp.addEventListener('click', () => { if (mv.paused) mv.play(); else mv.pause(); setPaused(mv.paused); });
    // клик/тап по 3D-окну — пауза/продолжить; перетаскивание по-прежнему поворачивает модель
    let down = null;
    mv.addEventListener('pointerdown', e => { down = { x: e.clientX, y: e.clientY, t: performance.now() }; });
    mv.addEventListener('pointerup', e => {
      if (!down) return; const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y), dt = performance.now() - down.t; down = null;
      if (moved < 6 && dt < 350) pp.click();
    });
    mv.addEventListener('pointercancel', () => { down = null; });
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
      overlay = []; body = null; ldDone = false; ld.hidden = false; ld.classList.remove('done'); showProgress(0); mv.src = MODELS[S.who]; setPaused(false);
    }));

    let overlay = [], body = null, bodyDim = -1;
    glowBtn.addEventListener('click', () => {
      S.glow = !S.glow; store.set('exerfly-glow', S.glow ? '1' : '0');
      glowBtn.setAttribute('aria-pressed', String(S.glow));
    });
    // экран загрузки: крылья логотипа заполняются по мере загрузки модели
    const ld = document.getElementById('loader'), ldRect = document.getElementById('ld-rect'), ldPct = document.getElementById('ld-pct');
    let ldTimer = 0, ldDone = false;                  // после загрузки модели прогресс окружения/текстур уже не показываем
    const showProgress = p => {
      const v = Math.max(0, Math.min(1, p)), pc = Math.round(v * 100);
      ldRect.setAttribute('width', (v * 128).toFixed(1)); ldPct.textContent = pc + '%'; ld.setAttribute('aria-valuenow', pc);
    };
    mv.addEventListener('progress', e => {
      const p = e.detail.totalProgress;
      if (ldDone) return;
      if (p < 1) { clearTimeout(ldTimer); ld.classList.remove('done'); ld.hidden = false; }
      showProgress(p);
    });
    mv.addEventListener('load', () => {
      ldDone = true; showProgress(1); clearTimeout(ldTimer);
      ldTimer = setTimeout(() => { ld.classList.add('done'); ldTimer = setTimeout(() => { ld.hidden = true; }, 400); }, 250);
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
  // логотип: сброс всех фильтров и поиска + главная страница сверху
  document.getElementById('logo-link').addEventListener('click', e => {
    e.preventDefault();
    Object.assign(S, { q: '', group: null, only3d: false, panel: false, tbCollapsed: null, favOnly: false });
    S.muscles.clear(); S.equipment.clear(); S.levels.clear();
    catalogScroll = 0;
    if (location.hash.slice(1)) location.hash = '';               // hashchange → route() → каталог
    else { renderCatalog(); window.scrollTo(0, 0); }
  });
  renderHeader();
  route();
})();

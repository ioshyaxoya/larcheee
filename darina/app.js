/* ===========================================================================
 * Darina Danilyuk — механика главной страницы.
 *
 * Две независимые части:
 *   1. Deck      — постраничная прокрутка на весь экран (как fullPage.js
 *                  на референсе alextakacs.com: autoScrolling, 700 мс,
 *                  якоря #1..#N).
 *   2. CutEngine — «нарезка»: фильм делится на 29 равных кусков, движок
 *                  прыгает по их началам и играет каждый кусок со
 *                  скоростью ×1.28.
 * =========================================================================== */

(function () {
  'use strict';

  var CFG = Object.assign(
    { CUTS: 29, RATE: 1.28, CUT_SECONDS: 1.6, SCROLL_SPEED: 700 },
    window.MONTAGE || {}
  );
  var FILMS = window.FILMS || [];

  /* ── язык ──────────────────────────────────────────────────────────── */

  var I18N = window.I18N || {};
  var ORDER = window.I18N_ORDER || Object.keys(I18N);
  var FALLBACK = window.I18N_FALLBACK || [];
  var STORE_KEY = 'darina.lang';

  /** Сохранённый выбор, иначе язык браузера, иначе первый в списке. */
  function pickLocale() {
    try {
      var saved = localStorage.getItem(STORE_KEY);
      if (saved && I18N[saved]) return saved;
    } catch (e) { /* приватный режим — просто идём дальше */ }

    var langs = navigator.languages || [navigator.language || ''];
    for (var i = 0; i < langs.length; i++) {
      var tag = String(langs[i]);
      if (I18N[tag]) return tag;
      var base = tag.split('-')[0].toLowerCase();
      for (var j = 0; j < ORDER.length; j++) {
        if (ORDER[j].split('-')[0].toLowerCase() === base) return ORDER[j];
      }
    }
    return ORDER[0];
  }

  var locale = pickLocale();
  var dict = function (code) { return I18N[code] || {}; };

  /** Строка с откатом на запасные языки. */
  function t(key) {
    var chain = [locale].concat(FALLBACK);
    for (var i = 0; i < chain.length; i++) {
      var v = dict(chain[i])[key];
      if (v !== undefined && v !== '') return v;
    }
    return '';
  }

  /** Строка из вложенной группы (kinds, films). */
  function tin(group, key) {
    if (!key) return '';
    var chain = [locale].concat(FALLBACK);
    for (var i = 0; i < chain.length; i++) {
      var g = dict(chain[i])[group];
      if (g && g[key] !== undefined && g[key] !== '') return g[key];
    }
    return '';
  }

  /** Массив строк с откатом (aboutText, shots). */
  function tlist(key) {
    var chain = [locale].concat(FALLBACK);
    for (var i = 0; i < chain.length; i++) {
      var v = dict(chain[i])[key];
      if (Array.isArray(v) && v.length) return v;
    }
    return [];
  }

  function each(sel, fn) {
    Array.prototype.forEach.call(document.querySelectorAll(sel), fn);
  }

  var REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var SEEK_EPS = 0.04;   // чтобы попасть в декодируемый кадр, а не на стык
  var FLASH_MS = 90;     // длительность затемнения на склейке
  var MIME = { mp4: 'video/mp4', webm: 'video/webm', ogv: 'video/ogg', mov: 'video/quicktime' };
  var LOAD_TIMEOUT = 8000; // сколько ждём метаданные, прежде чем считать файл битым

  /* ======================================================================
   * 1. Разметка экранов с фильмами
   * ==================================================================== */

  var deckEl = document.getElementById('deck');

  function buildFilmSection(film, i) {
    var s = document.createElement('section');
    s.className = 'section section--film';
    s.dataset.anchor = String(i + 2);          // #1 — герой, фильмы с #2

    var media = document.createElement('div');
    media.className = 'film-media';

    var poster = document.createElement('img');
    poster.className = 'film-poster';
    poster.src = film.poster || 'assets/hero.jpg';
    poster.alt = '';
    media.appendChild(poster);

    var v = document.createElement('video');
    v.muted = true;
    v.defaultMuted = true;
    v.playsInline = true;
    v.setAttribute('playsinline', '');
    v.setAttribute('webkit-playsinline', '');
    v.setAttribute('muted', '');
    v.preload = 'metadata';
    // у готовой нарезки склейки уже вшиты — она просто крутится по кругу;
    // у исходного фильма цикл ведёт CutEngine
    v.loop = !!film.prerendered;

    // film.src — строка или массив: браузер берёт первый формат, который умеет
    var srcs = Array.isArray(film.src) ? film.src : [film.src];
    srcs.forEach(function (url) {
      if (!url) return;
      var so = document.createElement('source');
      so.src = url;
      var type = MIME[(url.split('.').pop() || '').toLowerCase()];
      if (type) so.type = type;
      v.appendChild(so);
    });
    media.appendChild(v);

    s.appendChild(media);

    var flash = document.createElement('div');
    flash.className = 'cut-flash';
    s.appendChild(flash);

    var grain = document.createElement('div');
    grain.className = 'grain';
    s.appendChild(grain);

    var vign = document.createElement('div');
    vign.className = 'vignette';
    s.appendChild(vign);

    var title = document.createElement('div');
    title.className = 'film-title';
    var tt = document.createElement(film.link ? 'a' : 'span');
    tt.className = 't';
    tt.dataset.tFilm = film.id || '';
    if (film.link) { tt.href = film.link; tt.target = '_blank'; tt.rel = 'noopener'; }
    title.appendChild(tt);

    var sub = document.createElement('span');
    sub.className = 's';
    sub.dataset.tKind = film.kind || '';
    if (film.year) sub.dataset.year = String(film.year);
    title.appendChild(sub);

    if (creditsFor(film).length || tin('synopsis', film.id) || (film.bts && film.bts.length)) {
      var cr = document.createElement('button');
      cr.type = 'button';
      cr.className = 'film-credits';
      cr.dataset.t = 'aboutFilm';
      cr.addEventListener('click', function () { openCredits(film); });
      title.appendChild(cr);
    }
    s.appendChild(title);

    return s;
  }

  /** Экран-анонс: без видео и без нарезки — только типографика поверх свечения. */
  function buildSoonSection(film, i) {
    var s = document.createElement('section');
    s.className = 'section section--soon' + (film.id ? '' : ' soon-untitled');
    s.dataset.anchor = String(i + 2);

    if (film.poster) {
      var ph = document.createElement('img');
      ph.className = 'soon-poster';
      ph.src = film.poster;
      ph.alt = '';
      s.appendChild(ph);
    }

    // подложка из бэкстейджа: крутится сама, без нарезки
    if (film.src) {
      var sv = document.createElement('video');
      sv.className = 'soon-video';
      sv.muted = true;
      sv.defaultMuted = true;
      sv.playsInline = true;
      sv.setAttribute('playsinline', '');
      sv.setAttribute('webkit-playsinline', '');
      sv.setAttribute('muted', '');
      sv.loop = true;
      sv.preload = 'metadata';
      (Array.isArray(film.src) ? film.src : [film.src]).forEach(function (url) {
        if (!url) return;
        var so = document.createElement('source');
        so.src = url;
        var type = MIME[(url.split('.').pop() || '').toLowerCase()];
        if (type) so.type = type;
        sv.appendChild(so);
      });
      s.appendChild(sv);
    }

    var glow = document.createElement('div');
    glow.className = 'soon-glow';
    s.appendChild(glow);

    var grain = document.createElement('div');
    grain.className = 'grain';
    s.appendChild(grain);

    var inner = document.createElement('div');
    inner.className = 'soon-inner';

    // Сверху вниз: «скоро» крупно над всем, название — оно же открывает страницу
    // клипа, — и мелко «by …» с исполнителями. Режиссёры и подробности живут на
    // странице клипа; на экране анонса их нет, чтобы он не был перегружен.
    var badge = document.createElement('div');
    badge.className = 'soon-badge';
    badge.dataset.t = 'soon';
    inner.appendChild(badge);

    var opener = badge;                 // пока названия нет, страницу открывает «скоро»
    if (film.id) {
      var st = document.createElement('button');
      st.type = 'button';
      st.className = 'soon-title';
      st.dataset.tFilm = film.id;
      inner.appendChild(st);
      opener = st;
    }

    // у работы есть что показать — открывающий элемент становится нажимаемым
    if ((film.bts && film.bts.length) || (film.posts && film.posts.length) || film.story || film.creditsKey) {
      opener.addEventListener('click', function () { openCredits(film); });
      if (opener === badge) {
        badge.setAttribute('role', 'button');
        badge.tabIndex = 0;
        badge.style.cursor = 'pointer';
        badge.addEventListener('keydown', function (e) {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openCredits(film); }
        });
      }
    }

    // под названием — кто исполняет: «by …». Регистр имён не трогаем: он взят со
    // страницы трека. dir=ltr — имена латиницей, и в арабской раскладке они не плывут.
    if (film.artists) {
      var by = document.createElement('div');
      by.className = 'soon-by';
      by.dir = 'ltr';
      var bw = document.createElement('span');
      bw.className = 'soon-by-word';
      bw.dataset.t = 'soonBy';
      by.appendChild(bw);
      by.appendChild(document.createTextNode(' '));
      var bn = document.createElement('span');
      bn.className = 'soon-by-names';
      bn.textContent = film.artists;
      by.appendChild(bn);
      inner.appendChild(by);
    } else {
      var kicker = document.createElement('div');
      kicker.className = 'soon-kicker';
      kicker.dataset.tKind = film.kind || '';
      inner.appendChild(kicker);
    }

    if (film.note) {
      var nt = document.createElement('div');
      nt.className = 'soon-note';
      nt.textContent = film.note;
      inner.appendChild(nt);
    }

    // появятся после премьеры: VK Видео первым, YouTube вторым
    if (film.links && film.links.length) {
      var row = document.createElement('div');
      row.className = 'soon-links';
      film.links.forEach(function (l) {
        if (!l || !l.url) return;
        var a = document.createElement('a');
        a.href = l.url;
        a.target = '_blank';
        a.rel = 'noopener';
        a.textContent = l.label || l.url;
        row.appendChild(a);
      });
      if (row.children.length) inner.appendChild(row);
    }

    s.appendChild(inner);
    return s;
  }

  /** Подвал: контакты, правовые ссылки и имя, уходящее в тень. */
  function buildFooterSection(i) {
    var s = document.createElement('section');
    s.className = 'section section--footer';
    s.dataset.anchor = String(i + 2);

    var f = document.createElement('div');
    f.className = 'foot';

    // верх: куда писать
    var top = document.createElement('div');
    top.className = 'foot-top';
    (window.CONTACTS || []).forEach(function (c) {
      var a = document.createElement('a');
      a.className = 'foot-pill';
      a.href = c.url;
      a.textContent = c.text;
      if (c.url.indexOf('mailto:') !== 0) { a.target = '_blank'; a.rel = 'noopener'; }
      top.appendChild(a);
    });
    var upper = document.createElement('div');
    upper.className = 'foot-upper';
    upper.appendChild(top);

    var rule = document.createElement('div');
    rule.className = 'foot-rule';
    upper.appendChild(rule);
    f.appendChild(upper);

    var lower = document.createElement('div');
    lower.className = 'foot-lower';

    // правовые документы — открываются оверлеем, как «о себе»
    var nav = document.createElement('nav');
    nav.className = 'foot-links';
    LEGAL_DOCS.forEach(function (key) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.dataset.t = key;
      btn.addEventListener('click', function () { openLegal(key); });
      nav.appendChild(btn);
    });
    lower.appendChild(nav);

    var who = document.createElement('p');
    who.className = 'foot-who';
    who.dataset.t = 'footWho';
    lower.appendChild(who);

    var copy = document.createElement('p');
    copy.className = 'foot-copy';
    copy.dataset.year = String(new Date().getFullYear());
    lower.appendChild(copy);
    f.appendChild(lower);

    // имя во всю ширину, уходит вниз в тень
    var mark = document.createElement('div');
    mark.className = 'foot-mark';
    var mi = document.createElement('img');
    mi.src = 'assets/logo-darina.svg';
    mi.alt = '';
    mark.appendChild(mi);

    s.appendChild(f);
    s.appendChild(mark);
    return s;
  }

  var LEGAL_DOCS = ['legalTerms', 'legalPrivacy', 'legalCookies', 'legalNotice'];

  FILMS.forEach(function (film, i) {
    deckEl.appendChild((film.soon ? buildSoonSection : buildFilmSection)(film, i));
  });
  deckEl.appendChild(buildFooterSection(FILMS.length));

  var sections = Array.prototype.slice.call(deckEl.querySelectorAll('.section'));

  /* ======================================================================
   * 2. CutEngine — нарезка одного фильма на CUTS кусков
   * ==================================================================== */

  function CutEngine(section, film, onCut) {
    this.section = section;
    this.video = section.querySelector('video');
    this.onCut = onCut || function () {};

    // prerendered — файл уже собран из CUTS кусков и ускорен при кодировании:
    // движку остаётся только крутить его и считать текущий кусок по таймкоду
    this.prerendered = !!film.prerendered;
    this.cuts = film.cuts || CFG.CUTS;
    this.rate = this.prerendered ? 1 : (film.rate || CFG.RATE);
    this.cutSeconds = film.cutSeconds || CFG.CUT_SECONDS;

    this.index = 0;
    this.duration = 0;
    this.segLen = 0;
    this.hold = 0;
    this.ready = false;
    this.active = false;
    this.failed = false;
    this.raf = null;
    this._flashTimer = null;
    this._loadTimer = null;

    var self = this;

    this.video.addEventListener('loadedmetadata', function () {
      clearTimeout(self._loadTimer);
      self.measure();
      if (self.active) self.start();
    });

    this.video.addEventListener('error', function () { self.fail(); });

    // ни один <source> не подошёл — браузер оставляет networkState = NO_SOURCE
    Array.prototype.forEach.call(this.video.querySelectorAll('source'), function (so) {
      so.addEventListener('error', function () {
        if (self.video.networkState === 3 /* NETWORK_NO_SOURCE */) self.fail();
      });
    });

    // некоторые браузеры сбрасывают playbackRate после seek/загрузки
    this.video.addEventListener('ratechange', function () {
      if (self.active && Math.abs(self.video.playbackRate - self.rate) > 0.001) {
        self.video.playbackRate = self.rate;
      }
    });

    if (this.video.readyState >= 1) this.measure();
  }

  /** Считает геометрию нарезки: длина куска и сколько его показывать. */
  CutEngine.prototype.measure = function () {
    var d = this.video.duration;
    if (!isFinite(d) || d <= 0) return;
    this.duration = d;
    this.segLen = d / this.cuts;
    // показываем либо CUT_SECONDS, либо весь кусок — что короче
    this.hold = Math.min(this.cutSeconds, this.segLen);
    this.ready = true;
  };

  /** Время начала куска i в исходнике. */
  CutEngine.prototype.segStart = function (i) {
    return i * this.segLen;
  };

  CutEngine.prototype.fail = function () {
    if (this.failed) return;
    this.failed = true;
    this.section.classList.remove('is-playing');
    if (!this.section.querySelector('.film-missing')) {
      var m = document.createElement('div');
      m.className = 'film-missing';
      m.dataset.t = 'missing';
      m.textContent = t('missing');
      this.section.appendChild(m);
    }
  };

  CutEngine.prototype.flash = function () {
    if (REDUCED) return;
    var s = this.section;
    s.classList.add('is-cutting');
    clearTimeout(this._flashTimer);
    this._flashTimer = setTimeout(function () {
      s.classList.remove('is-cutting');
    }, FLASH_MS);
  };

  /** Переход на кусок i: перемотка в его начало + склейка. */
  CutEngine.prototype.goTo = function (i, silent) {
    if (!this.ready) return;
    this.index = ((i % this.cuts) + this.cuts) % this.cuts;
    var target = this.segStart(this.index) + SEEK_EPS;
    if (target > this.duration - 0.05) target = Math.max(0, this.duration - 0.05);
    try { this.video.currentTime = target; } catch (e) { /* not seekable yet */ }
    if (this.video.playbackRate !== this.rate) this.video.playbackRate = this.rate;
    if (!silent) this.flash();
    this.onCut(this.index, this.cuts);
  };

  CutEngine.prototype.advance = function () {
    this.goTo(this.index + 1);
  };

  CutEngine.prototype.tick = function () {
    var self = this;
    this.raf = requestAnimationFrame(function () { self.tick(); });

    if (!this.active || !this.ready || this.failed) return;
    if (this.video.paused || this.video.seeking) return;
    if (REDUCED) return;                       // без нарезки — играем подряд

    var pos = this.video.currentTime;

    if (this.prerendered) {
      // склейки уже в файле: ничего не трогаем, только ведём индикатор
      var idx = Math.min(this.cuts - 1, Math.max(0, Math.floor(pos / this.segLen)));
      if (idx !== this.index) {
        this.index = idx;
        this.onCut(idx, this.cuts);
      }
      return;
    }

    var start = this.segStart(this.index);

    // кусок доиграл — режем на следующий;
    // ушли назад (loop/сбой перемотки) — тоже пересобираемся
    if (pos >= start + this.hold || pos < start - 0.5) this.advance();
  };

  CutEngine.prototype.start = function () {
    this.active = true;
    this.section.classList.add('is-active');
    if (this.failed) return;

    if (!this.ready) {                          // метаданные ещё едут
      if (this.video.preload !== 'auto') this.video.preload = 'auto';
      // NETWORK_LOADING — загрузка уже идёт, второй load() её только собьёт
      if (this.video.networkState !== 2) this.video.load();
      var self0 = this;
      clearTimeout(this._loadTimer);
      this._loadTimer = setTimeout(function () {
        if (!self0.ready) self0.fail();         // файла нет / формат не тот
      }, LOAD_TIMEOUT);
      return;
    }

    this.video.playbackRate = this.rate;
    if (!this.prerendered) this.goTo(this.index, true);

    var self = this;
    var p = this.video.play();
    if (p && p.then) {
      p.then(function () {
        self.video.playbackRate = self.rate;
        self.section.classList.add('is-playing');
      }).catch(function () { /* autoplay заблокирован — остаётся постер */ });
    } else {
      this.section.classList.add('is-playing');
    }

    if (this.raf === null) this.tick();
  };

  CutEngine.prototype.stop = function () {
    this.active = false;
    this.section.classList.remove('is-active');
    this.video.pause();
    if (this.raf !== null) { cancelAnimationFrame(this.raf); this.raf = null; }
  };

  /** Прогрев соседнего экрана, чтобы не ловить паузу на перелистывании. */
  CutEngine.prototype.warm = function () {
    if (this.failed || this.ready) return;
    if (this.video.preload !== 'auto') {
      this.video.preload = 'auto';
      if (this.video.networkState !== 2) this.video.load();
    }
  };

  /* ======================================================================
   * 2b. Плеер экрана-анонса — без нарезки, просто цикл
   * ==================================================================== */

  function SoonMedia(section) {
    this.section = section;
    this.video = section.querySelector('video');
  }

  SoonMedia.prototype.start = function () {
    if (!this.video) return;
    var self = this;
    var p = this.video.play();
    if (p && p.then) {
      p.then(function () { self.section.classList.add('is-playing'); })
       .catch(function () { /* автоплей заблокирован — остаётся постер */ });
    } else {
      this.section.classList.add('is-playing');
    }
  };

  SoonMedia.prototype.stop = function () {
    if (this.video) this.video.pause();
  };

  SoonMedia.prototype.warm = function () {
    if (this.video && this.video.preload !== 'auto') {
      this.video.preload = 'auto';
      if (this.video.networkState !== 2) this.video.load();
    }
  };

  /* ======================================================================
   * 3. Индикатор нарезки (29 рисок)
   * ==================================================================== */

  var cutsEl = document.getElementById('cuts');
  var ticks = [];

  function buildTicks(n) {
    if (ticks.length === n) return;
    cutsEl.textContent = '';
    ticks = [];
    for (var i = 0; i < n; i++) {
      var tick = document.createElement('i');
      cutsEl.appendChild(tick);
      ticks.push(tick);
    }
  }

  function paintTicks(index, total) {
    buildTicks(total);
    for (var i = 0; i < ticks.length; i++) {
      ticks[i].className = i === index ? 'now' : (i < index ? 'done' : '');
    }
  }

  /* ======================================================================
   * 4. Deck — постраничная прокрутка
   * ==================================================================== */

  // engineBySection — только фильмы, нужен индикатору нарезки;
  // playersBySection — всё, что надо включать и глушить при листании
  var engineBySection = [];
  var playersBySection = [];
  FILMS.forEach(function (film, i) {
    var si = i + 1;
    if (film.soon) {
      engineBySection[si] = null;
      playersBySection[si] = sections[si].querySelector('video') ? new SoonMedia(sections[si]) : null;
      return;
    }
    var eng = new CutEngine(sections[si], film, function (index, total) {
      if (current === si) paintTicks(index, total);
    });
    engineBySection[si] = eng;
    playersBySection[si] = eng;
  });
  var engines = engineBySection.filter(Boolean);

  var current = 0;
  var locked = false;
  var cueEl = document.getElementById('cue');

  deckEl.style.setProperty('--speed', CFG.SCROLL_SPEED + 'ms');

  function go(i, instant) {
    i = Math.max(0, Math.min(sections.length - 1, i));
    if (i === current && !instant) return;

    var prev = current;
    current = i;

    if (instant) {
      deckEl.classList.add('is-instant');
      // форсируем reflow, чтобы transition не проиграл на возврате класса
      void deckEl.offsetHeight;
    }
    deckEl.style.transform = 'translate3d(0,-' + (i * 100) + '%,0)';
    if (instant) {
      requestAnimationFrame(function () { deckEl.classList.remove('is-instant'); });
    }

    sections.forEach(function (s, n) { s.classList.toggle('is-active', n === i); });

    // список покинутого экрана отматываем наверх, чтобы вернуться к началу
    if (prev !== i) {
      var leftBehind = sections[prev] && sections[prev].querySelector('.js-scroll');
      if (leftBehind) leftBehind.scrollTop = 0;
    }

    // видео: играет только активный экран, соседи — прогреваются
    playersBySection.forEach(function (pl, si) {
      if (!pl) return;
      if (si === i) { pl.start(); return; }
      pl.stop();
      if (Math.abs(si - i) === 1) pl.warm();
    });

    if (i === 0) heroStart(); else heroStop();

    // индикатор нарезки — только там, где реально есть фильм
    var eng = engineBySection[i] || null;
    cutsEl.classList.toggle('is-on', !!eng);
    if (eng) paintTicks(eng.index, eng.cuts);

    cueEl.classList.toggle('is-hidden', i === sections.length - 1);

    var anchor = sections[i].dataset.anchor;
    if (('#' + anchor) !== location.hash) {
      history.replaceState(null, '', '#' + anchor);
    }

    locked = true;
    setTimeout(function () { locked = false; }, CFG.SCROLL_SPEED + 120);
  }

  function next() { if (!locked) go(current + 1); }
  function prev() { if (!locked) go(current - 1); }

  /* — экраны с прокручиваемым содержимым (стена) —
     жест сначала отдаётся списку и только на его краю листает деку */

  /** Прокручиваемая область под точкой события, если она есть. */
  function scrollHost(node) {
    while (node && node !== document.body) {
      if (node.classList && node.classList.contains('js-scroll')) return node;
      node = node.parentNode;
    }
    return null;
  }

  /** Может ли область ещё прокрутиться в эту сторону. */
  function canScroll(el, dy) {
    if (!el || el.scrollHeight <= el.clientHeight + 1) return false;
    return dy < 0 ? el.scrollTop > 1
                  : el.scrollTop + el.clientHeight < el.scrollHeight - 1;
  }

  /* — колесо / трекпад — */
  window.addEventListener('wheel', function (e) {
    if (panelOpen) return;
    var host = scrollHost(e.target);
    if (canScroll(host, e.deltaY)) return;     // колесо уходит содержимому
    e.preventDefault();
    if (locked || Math.abs(e.deltaY) < 8) return;
    if (e.deltaY > 0) next(); else prev();
  }, { passive: false });

  /* — тач — */
  var touchY = null;
  var touchHost = null;

  window.addEventListener('touchstart', function (e) {
    touchY = e.touches[0].clientY;
    touchHost = scrollHost(e.target);
  }, { passive: true });

  window.addEventListener('touchmove', function (e) {
    if (panelOpen) return;
    if (touchHost && canScroll(touchHost, touchY - e.touches[0].clientY)) return;
    e.preventDefault();
  }, { passive: false });

  window.addEventListener('touchend', function (e) {
    if (panelOpen || touchY === null) return;
    var dy = touchY - e.changedTouches[0].clientY;
    var host = touchHost;
    touchY = null;
    touchHost = null;
    if (canScroll(host, dy)) return;
    if (Math.abs(dy) < 50 || locked) return;
    if (dy > 0) next(); else prev();
  }, { passive: true });

  /* — клавиатура — */
  window.addEventListener('keydown', function (e) {
    // просмотрщик кадра выше панели: пока он открыт, клавиши его, не наши,
    // иначе Escape закрывал бы заодно и описание под ним
    if (lb.root && !lb.root.hidden) return;
    if (panelOpen) {
      if (e.key === 'Escape') { closePanel(); return; }
      if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && creditsUI && panelOpen.id === 'panel-credits') {
        var car = creditsUI.activeCar();
        if (car) {
          e.preventDefault();
          car.step((e.key === 'ArrowRight') !== document.body.classList.contains('is-rtl') ? 1 : -1);
        }
      }
      return;
    }
    switch (e.key) {
      case 'ArrowDown': case 'PageDown': case ' ':
        if (canScroll(sections[current].querySelector('.js-scroll'), 1)) return;
        e.preventDefault(); next(); break;
      case 'ArrowUp': case 'PageUp':
        if (canScroll(sections[current].querySelector('.js-scroll'), -1)) return;
        e.preventDefault(); prev(); break;
      case 'Home':
        e.preventDefault(); go(0); break;
      case 'End':
        e.preventDefault(); go(sections.length - 1); break;
    }
  });

  cueEl.addEventListener('click', function () {
    if (current === sections.length - 1) go(0); else next();
  });

  /* — якоря #1..#N — */
  function fromHash() {
    var m = /^#(\d+)$/.exec(location.hash);
    if (!m) return -1;
    var n = parseInt(m[1], 10) - 1;
    return (n >= 0 && n < sections.length) ? n : -1;
  }

  window.addEventListener('hashchange', function () {
    var n = fromHash();
    if (n >= 0 && n !== current) go(n);
  });

  /* ======================================================================
   * 5. Оверлеи about / contact
   * ==================================================================== */

  var panelOpen = null;

  function openPanel(name) {
    var el = document.getElementById('panel-' + name);
    if (!el) return;
    el.hidden = false;
    void el.offsetHeight;
    el.classList.add('is-open');
    panelOpen = el;
  }

  function closePanel() {
    if (!panelOpen) return;
    var el = panelOpen;
    panelOpen = null;
    el.classList.remove('is-open');
    Array.prototype.forEach.call(el.querySelectorAll('video'), function (v) { v.pause(); });
    setTimeout(function () { if (!el.classList.contains('is-open')) el.hidden = true; }, 320);
  }

  Array.prototype.forEach.call(document.querySelectorAll('[data-panel]'), function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      openPanel(a.dataset.panel);
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll('.panel'), function (p) {
    p.addEventListener('click', function (e) {
      if (e.target === p || e.target.classList.contains('panel-close')) closePanel();
    });
  });

  /* ── первый экран: фотография макета и портреты, сменяющие друг друга ── */

  var heroTimer = null;
  var heroIdx = 0;
  var heroSlides = [];

  function buildHero() {
    var hero = sections[0];
    var first = hero && hero.querySelector('.hero-photo');
    if (!first) return;

    var cfg = window.HERO || {};
    var photos = cfg.photos || (Array.isArray(cfg) ? cfg : [first.getAttribute('src')]);
    var sets = cfg.sets || photos.map(function (_, i) { return [i]; });

    // Первый экран — склейки: в каждой один, два или три кадра. Кадры стоят
    // в ряд во всю высоту, ширина по пропорции, поэтому ничего не обрезается.
    // Белые поля на снимках сами работают промежутком между ними.
    var blur = document.createElement('div');
    blur.className = 'hero-blur';
    blur.style.backgroundImage = 'url("' + photos[sets[0][0]] + '")';
    hero.insertBefore(blur, first);

    heroSlides = [];
    var frag = document.createDocumentFragment();

    sets.forEach(function (set, n) {
      var box = document.createElement('div');
      box.className = 'hero-set' + (n === 0 ? ' is-on' : '');

      set.forEach(function (idx, k) {
        var im;
        if (n === 0 && k === 0) {
          im = first;                 // кадр из разметки переиспользуем
          im.src = photos[idx];
        } else {
          im = document.createElement('img');
          im.src = photos[idx];
          im.alt = '';
          // первые две склейки грузим сразу, остальные по мере показа
          if (n > 1) im.loading = 'lazy';
        }
        im.className = 'hero-photo';
        box.appendChild(im);
      });

      frag.appendChild(box);
      heroSlides.push(box);
    });

    // порядок в разметке: подложка, за ней склейки по порядку
    hero.insertBefore(frag, blur.nextSibling);
  }

  function heroStart() {
    if (REDUCED || heroSlides.length < 2 || heroTimer) return;
    heroTimer = setInterval(function () {
      heroSlides[heroIdx].classList.remove('is-on');
      heroIdx = (heroIdx + 1) % heroSlides.length;
      heroSlides[heroIdx].classList.add('is-on');
    }, 6500);
  }

  function heroStop() { clearInterval(heroTimer); heroTimer = null; }

  /** Контакты из CONTACTS: пустые пропускаем, пока ссылки нет. */
  function buildContacts() {
    var box = document.querySelector('#panel-contact .contacts');
    if (!box) return;
    box.textContent = '';
    (window.CONTACTS || []).forEach(function (c) {
      if (!c || !c.url) return;
      var a = document.createElement('a');
      a.href = c.url;
      a.textContent = c.text || c.url;
      if (c.url.indexOf('mailto:') !== 0) { a.target = '_blank'; a.rel = 'noopener'; }
      box.appendChild(a);
    });
  }

  /** Титры на языке посетителя: русские для русского, латиница для прочих. */
  function creditsFor(film) {
    var c = film && film.credits;
    if (!c) return [];
    if (Array.isArray(c)) return c;                  // старый плоский формат
    var variant = (locale === 'ru' ? c.ru : c.en) || c.en || c.ru;
    return Array.isArray(variant) ? variant : [];
  }

  /* ── просмотр кадра: большой кадр, счётчик, автопрокрутка ──────────────── */

  var LB_STEP = 3800;  // пауза между кадрами в автопрокрутке
  var lb = {
    root: null, img: null, cap: null, count: null, play: null,
    shots: [], i: 0, timer: 0, playing: false, prev: null,
  };

  function lbStop() {
    if (lb.timer) { clearInterval(lb.timer); lb.timer = 0; }
    lb.playing = false;
    if (lb.play) {
      lb.play.textContent = '\u25B6';
      lb.play.setAttribute('aria-label', t('play'));
    }
  }

  function lbStart() {
    lbStop();
    lb.playing = true;
    lb.play.textContent = '\u275A\u275A';
    lb.play.setAttribute('aria-label', t('pause'));
    lb.timer = setInterval(function () { lbGo(lb.i + 1); }, LB_STEP);
  }

  function lbGo(n) {
    if (!lb.shots.length) return;
    // по кругу: с последнего кадра возвращаемся к первому
    lb.i = (n % lb.shots.length + lb.shots.length) % lb.shots.length;
    var shot = lb.shots[lb.i];
    lb.img.src = shot.cover;
    lb.count.textContent = (lb.i + 1) + ' / ' + lb.shots.length;
    if (shot.shot !== undefined) {
      lb.cap.dataset.tShot = String(shot.shot);
      lb.cap.textContent = tlist('shots')[shot.shot] || '';
      lb.cap.hidden = false;
    } else {
      delete lb.cap.dataset.tShot;
      lb.cap.textContent = '';
      lb.cap.hidden = true;
    }
  }

  function openLightbox(shots, i) {
    if (!lb.root || !shots || !shots.length) return;
    lb.shots = shots;
    lb.prev = document.activeElement;
    lb.root.hidden = false;
    document.body.classList.add('is-lightbox');
    lbGo(i || 0);
    lbStop();
    lb.root.focus();
  }

  function closeLightbox() {
    if (!lb.root || lb.root.hidden) return;
    lbStop();
    lb.root.hidden = true;
    document.body.classList.remove('is-lightbox');
    if (lb.prev && lb.prev.focus) lb.prev.focus();
  }

  function buildLightbox() {
    lb.root = document.getElementById('lightbox');
    if (!lb.root) return;
    lb.img = lb.root.querySelector('.lightbox-stage img');
    lb.cap = lb.root.querySelector('.lightbox-stage figcaption');
    lb.count = lb.root.querySelector('.lightbox-count');
    lb.play = lb.root.querySelector('.lb-play');
    lb.root.tabIndex = -1;

    each('.lb-prev', function (b) {
      b.addEventListener('click', function () { lbStop(); lbGo(lb.i - 1); });
    });
    each('.lb-next', function (b) {
      b.addEventListener('click', function () { lbStop(); lbGo(lb.i + 1); });
    });
    lb.root.querySelector('.lb-restart').addEventListener('click', function () {
      lbStop(); lbGo(0);
    });
    lb.play.addEventListener('click', function () {
      lb.playing ? lbStop() : lbStart();
    });
    lb.root.querySelector('.lightbox-close').addEventListener('click', closeLightbox);
    // клик мимо кадра закрывает, по самому кадру — нет
    lb.root.addEventListener('click', function (e) {
      if (e.target === lb.root) closeLightbox();
    });

    document.addEventListener('keydown', function (e) {
      if (lb.root.hidden) return;
      // Событие нужно погасить здесь. Иначе оно дойдёт до общего обработчика,
      // а тот увидит уже закрытый просмотрщик и закроет заодно описание под ним.
      if (e.key === 'Escape') { e.stopPropagation(); closeLightbox(); return; }
      // в RTL стрелки меняются местами вместе с лентой
      var back = document.body.classList.contains('is-rtl') ? 'ArrowRight' : 'ArrowLeft';
      var fwd = back === 'ArrowLeft' ? 'ArrowRight' : 'ArrowLeft';
      if (e.key === back || e.key === fwd || e.key === ' ') {
        e.preventDefault();
        e.stopPropagation();
      }
      if (e.key === back) { lbStop(); lbGo(lb.i - 1); }
      else if (e.key === fwd) { lbStop(); lbGo(lb.i + 1); }
      else if (e.key === ' ') { lb.playing ? lbStop() : lbStart(); }
    });
  }

  /** Правовой документ: заголовок и абзацы из словаря. */
  function openLegal(key) {
    var panel = document.getElementById('panel-legal');
    if (!panel) return;
    panel.querySelector('h2').textContent = t(key);
    var body = panel.querySelector('.panel-body');
    body.textContent = '';
    tlist(key + 'Text').forEach(function (para) {
      var p = document.createElement('p');
      p.textContent = para;
      body.appendChild(p);
    });
    panel.dataset.doc = key;
    openPanel('legal');
  }

  /* ── листалка ─────────────────────────────────────────────────────────────
     Ряд кадров, который переходит стрелками, а не прокручивается. Нативная
     полоса прокрутки на тёмной странице выглядела грубо и выдавала, что блок
     «с прокруткой». Ряд лежит в окне с overflow:hidden и сдвигается на целый
     кадр; под ним стрелки и счётчик, как в референсе. Тянется мышью и пальцем,
     листается колесом вбок и стрелками клавиатуры. */

  var DRAG_PX = 6;

  function buildCarousel(items) {
    var root = document.createElement('div');
    root.className = 'car';

    var view = document.createElement('div');
    view.className = 'car-view';
    var track = document.createElement('div');
    track.className = 'car-track';
    items.forEach(function (it) { track.appendChild(it); });
    view.appendChild(track);
    root.appendChild(view);

    var bar = document.createElement('div');
    bar.className = 'car-bar';
    var prev = document.createElement('button');
    prev.type = 'button';
    prev.className = 'car-arrow car-prev';
    var count = document.createElement('span');
    count.className = 'car-count';
    var next = document.createElement('button');
    next.type = 'button';
    next.className = 'car-arrow car-next';
    bar.appendChild(prev);
    bar.appendChild(count);
    bar.appendChild(next);
    root.appendChild(bar);

    var starts = [];      // где начинается каждый кадр, считая от начала ряда
    var idx = 0;          // кадр, с которого сейчас показан ряд
    var last = 0;         // последняя позиция: дальше ряд упирается в край окна
    var maxOff = 0;       // на сколько ряд длиннее окна
    var cur = 0;          // текущий сдвиг в пикселях
    var raf = 0;

    // LTR: ряд уезжает влево (−), RTL: вправо (+)
    function sign() { return document.body.classList.contains('is-rtl') ? 1 : -1; }

    function state() {
      count.textContent = (idx + 1) + ' / ' + (last + 1);
      prev.disabled = idx <= 0;
      next.disabled = idx >= last;
      root.classList.toggle('has-prev', idx > 0);
      root.classList.toggle('has-next', idx < last);
      bar.hidden = last === 0;      // всё помещается — листать нечего
    }

    function place(animate) {
      var target = Math.min(starts[idx] || 0, maxOff);
      cur = target;
      if (animate === false) track.style.transition = 'none';
      track.style.transform = 'translate3d(' + (sign() * target) + 'px,0,0)';
      if (animate === false) {
        void track.offsetWidth;
        track.style.transition = '';
      }
      state();
    }

    function measure() {
      var kids = track.children;
      var rtl = sign() === 1;
      var tw = track.offsetWidth;
      var vw = view.clientWidth;
      starts = [];
      for (var i = 0; i < kids.length; i++) {
        var k = kids[i];
        starts.push(rtl ? tw - k.offsetLeft - k.offsetWidth : k.offsetLeft);
      }
      maxOff = Math.max(0, tw - vw);
      last = Math.max(0, kids.length - 1);
      if (maxOff <= 1) {
        last = 0;
      } else {
        // первая позиция, при которой ряд уже упёрся в край, — и есть последняя
        for (var j = 0; j < starts.length; j++) {
          if (starts[j] >= maxOff - 1) { last = j; break; }
        }
      }
      idx = Math.min(idx, last);
      place(false);
    }

    function go(i) {
      idx = Math.max(0, Math.min(last, i));
      place(true);
    }

    function schedule() {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(measure);
    }

    prev.addEventListener('click', function () { go(idx - 1); });
    next.addEventListener('click', function () { go(idx + 1); });

    // перетаскивание: мышью и пальцем
    var drag = null;
    var swallow = false;

    view.addEventListener('dragstart', function (e) { e.preventDefault(); });

    view.addEventListener('pointerdown', function (e) {
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      drag = { x: e.clientX, base: cur, idx0: idx, moved: false, id: e.pointerId };
    });

    view.addEventListener('pointermove', function (e) {
      if (!drag || e.pointerId !== drag.id) return;
      var dx = e.clientX - drag.x;
      if (!drag.moved && Math.abs(dx) > DRAG_PX) {
        drag.moved = true;
        try { view.setPointerCapture(e.pointerId); } catch (err) { /* не критично */ }
        root.classList.add('is-drag');
      }
      if (drag.moved) {
        var off = Math.max(0, Math.min(maxOff, drag.base + sign() * dx));
        track.style.transform = 'translate3d(' + (sign() * off) + 'px,0,0)';
      }
    });

    function endDrag(e) {
      if (!drag || e.pointerId !== drag.id) return;
      var d = drag;
      drag = null;
      root.classList.remove('is-drag');
      if (!d.moved) return;

      // клик, которым закончилось перетаскивание, кадр не открывает
      swallow = true;
      setTimeout(function () { swallow = false; }, 0);

      var delta = sign() * (e.clientX - d.x);      // > 0 — вперёд
      var off = Math.max(0, Math.min(maxOff, d.base + delta));
      var best = 0;
      var dist = Infinity;
      for (var i = 0; i <= last; i++) {
        var dd = Math.abs(starts[i] - off);
        if (dd < dist) { dist = dd; best = i; }
      }
      // короткий, но явный жест листает на кадр, даже если ближайший прежний
      if (best === d.idx0 && Math.abs(delta) > 40) best = d.idx0 + (delta > 0 ? 1 : -1);
      go(best);
    }
    view.addEventListener('pointerup', endDrag);
    view.addEventListener('pointercancel', endDrag);

    view.addEventListener('click', function (e) {
      if (swallow) { e.preventDefault(); e.stopPropagation(); }
    }, true);

    // колесо вбок (тачпад): один жест — один кадр
    var wheelAt = -1e9;
    view.addEventListener('wheel', function (e) {
      if (Math.abs(e.deltaX) <= Math.abs(e.deltaY) || Math.abs(e.deltaX) < 8) return;
      e.preventDefault();
      if (e.timeStamp - wheelAt < 380) return;
      wheelAt = e.timeStamp;
      var fwd = sign() === -1 ? e.deltaX > 0 : e.deltaX < 0;
      go(idx + (fwd ? 1 : -1));
    }, { passive: false });

    // размеры меняются при смене окна, шрифта и загрузке кадров
    if (window.ResizeObserver) {
      var ro = new ResizeObserver(schedule);
      ro.observe(view);
      ro.observe(track);
    } else {
      window.addEventListener('resize', schedule);
    }

    return {
      el: root,
      update: measure,
      step: function (d) { go(idx + d); },
      get index() { return idx; },
      get last() { return last; },
    };
  }

  /* ── вкладки описания ───────────────────────────────────────────────────── */

  var creditsUI = null;          // что сейчас открыто в описании: работа, вкладка, листалки
  var rebuilding = false;        // перестройка уже идёт — applyLocale не должен запускать вторую

  function buildTabs(into, defs, wantKey) {
    var start = 0;
    defs.forEach(function (d, i) { if (d.key === wantKey) start = i; });

    var bar = null;
    var btns = [];
    if (defs.length > 1) {
      bar = document.createElement('div');
      bar.className = 'panel-tabs';
      bar.setAttribute('role', 'tablist');
    }
    var area = document.createElement('div');
    area.className = 'panel-tabbody';

    function show(i, focus) {
      creditsUI.key = defs[i].key;
      defs.forEach(function (d, n) {
        d.node.hidden = n !== i;
        if (btns[n]) {
          btns[n].classList.toggle('is-on', n === i);
          btns[n].setAttribute('aria-selected', n === i ? 'true' : 'false');
          btns[n].tabIndex = n === i ? 0 : -1;
        }
      });
      if (defs[i].car) defs[i].car.update();
      // видео на скрытой вкладке не играет: незачем жечь процессор
      defs.forEach(function (d, n) {
        if (!d.media) return;
        if (n === i) {
          var pr = d.media.play();
          if (pr && pr.catch) pr.catch(function () { /* автозапуск мог не разрешиться */ });
        } else {
          d.media.pause();
        }
      });
      if (focus && btns[i]) btns[i].focus();
    }

    defs.forEach(function (d, i) {
      d.node.classList.add('panel-pane');
      d.node.setAttribute('role', 'tabpanel');
      area.appendChild(d.node);
      if (!bar) return;

      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'panel-tab';
      b.setAttribute('role', 'tab');
      b.dataset.t = d.label;
      b.addEventListener('click', function () { show(i); });
      b.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
        // клавиши вкладок — их собственные, листалка под ними не должна их забирать
        e.preventDefault();
        e.stopPropagation();
        var fwd = (e.key === 'ArrowRight') !== document.body.classList.contains('is-rtl');
        show((i + (fwd ? 1 : -1) + defs.length) % defs.length, true);
      });
      bar.appendChild(b);
      btns.push(b);
    });

    creditsUI.activeCar = function () {
      for (var i = 0; i < defs.length; i++) if (defs[i].key === creditsUI.key) return defs[i].car || null;
      return null;
    };

    if (bar) into.appendChild(bar);
    into.appendChild(area);
    show(start);
  }

  /* ── описание клипа ─────────────────────────────────────────────────────────
     Только у клипа. Страница не прокручивается: заголовок и вводная строка
     занимают сколько им нужно, всё остальное место — вкладка, а ряд кадров
     растягивается по высоте на оставшееся, так что при любом окне и размере
     шрифта страница видна целиком. Вкладки: «как это снималось» и «из
     инстаграма». У снятых фильмов остался прежний вид (renderFilmPanel). */

  function renderClipPanel(film, wantKey) {
    var body = document.querySelector('#panel-credits .panel-body');
    var head = document.querySelector('#panel-credits .credits-film');
    var h2 = document.querySelector('#panel-credits h2');
    if (!body) return;

    if (h2) h2.dataset.t = film.soon ? 'aboutClip' : 'aboutFilm';
    if (head) head.textContent = tin('films', film.id);
    body.textContent = '';

    var rows = creditsFor(film);
    var syn = tin('synopsis', film.id);

    // вводная строка над вкладками: синопсис, а у клипа — кто снял
    if (syn) {
      var sp = document.createElement('p');
      sp.className = 'credits-synopsis';
      sp.textContent = syn;
      body.appendChild(sp);
    } else if (!rows.length && film.creditsKey) {
      var cl = document.createElement('p');
      cl.className = 'credits-line';
      cl.dataset.t = film.creditsKey;
      body.appendChild(cl);
    }

    creditsUI = { film: film, key: wantKey || null, activeCar: function () { return null; } };
    var defs = [];

    // история клипа — своими словами Дарины, а рядом кусок самого клипа
    if (film.story) {
      var st = film.story;
      var story = document.createElement('div');
      story.className = 'clip-story';

      var txt = document.createElement('div');
      txt.className = 'clip-story-text';
      var paras = tlist(st.text);
      paras.forEach(function (para, i) {
        var pp = document.createElement('p');
        // последняя строка — «премьера скоро»: набирается как плашка «скоро» на анонсе
        if (i === paras.length - 1 && paras.length > 1) pp.className = 'clip-story-end';
        pp.textContent = para;
        txt.appendChild(pp);
      });
      story.appendChild(txt);

      var media = null;
      if (st.src) {
        var fig = document.createElement('figure');
        fig.className = 'clip-story-media';
        media = document.createElement('video');
        media.muted = true;
        media.defaultMuted = true;
        media.loop = true;
        media.playsInline = true;
        media.setAttribute('muted', '');
        media.setAttribute('playsinline', '');
        media.setAttribute('webkit-playsinline', '');
        media.preload = 'auto';
        if (st.poster) media.poster = st.poster;
        (Array.isArray(st.src) ? st.src : [st.src]).forEach(function (url) {
          var so = document.createElement('source');
          so.src = url;
          var type = MIME[(url.split('.').pop() || '').toLowerCase()];
          if (type) so.type = type;
          media.appendChild(so);
        });
        fig.appendChild(media);
        if (st.caption) {
          var fc = document.createElement('figcaption');
          fc.dataset.t = st.caption;
          fig.appendChild(fc);
        }
        story.appendChild(fig);
      }
      defs.push({ key: 'story', label: st.tab, node: story, media: media });
    }

    if (film.bts && film.bts.length) {
      var shots = film.bts.filter(function (x) { return x && x.cover; }).map(function (shot, i) {
        var fig = document.createElement('figure');
        fig.className = 'credits-shot' + (shot.shot !== undefined ? ' credits-shot--cap' : '');
        var im = document.createElement('img');
        im.src = shot.cover;
        im.alt = '';
        im.draggable = false;
        fig.appendChild(im);
        if (shot.shot !== undefined) {
          var cap = document.createElement('figcaption');
          cap.dataset.tShot = String(shot.shot);
          fig.appendChild(cap);
        }
        fig.addEventListener('click', function () { openLightbox(film.bts, i); });
        return fig;
      });
      var carShots = buildCarousel(shots);
      defs.push({ key: 'wall', label: 'wall', node: carShots.el, car: carShots });
    }

    if (film.posts && film.posts.length) {
      var tiles = film.posts.filter(function (x) { return x && x.cover; }).map(function (post) {
        var tile = document.createElement(post.url ? 'a' : 'figure');
        tile.className = 'credits-shot credits-post';
        if (post.url) {
          tile.href = post.url;
          tile.target = '_blank';
          tile.rel = 'noopener';
          tile.draggable = false;
        }
        var pi = document.createElement('img');
        pi.src = post.cover;
        pi.alt = '';
        pi.draggable = false;
        tile.appendChild(pi);
        if (post.kind === 'video') {
          var pl = document.createElement('span');
          pl.className = 'post-play';
          pl.setAttribute('aria-hidden', 'true');
          tile.appendChild(pl);
        }
        return tile;
      });
      var carPosts = buildCarousel(tiles);
      defs.push({ key: 'fromInstagram', label: 'fromInstagram', node: carPosts.el, car: carPosts });
    }

    if (rows.length) {
      var grid = document.createElement('div');
      grid.className = 'credits-grid';
      rows.forEach(function (row) {
        var line = document.createElement('div');
        line.className = 'credits-row';

        var role = document.createElement('span');
        role.className = 'credits-role';
        role.textContent = row[0];
        line.appendChild(role);

        var names = document.createElement('span');
        names.className = 'credits-names';
        (row[1] || []).forEach(function (nm) {
          var one = document.createElement('span');
          one.textContent = nm;
          names.appendChild(one);
        });
        line.appendChild(names);
        grid.appendChild(line);
      });
      defs.push({ key: 'credits', label: 'credits', node: grid });
    }

    buildTabs(body, defs, wantKey);

    // подставить подписи в только что собранное; вторую перестройку из applyLocale не запускаем
    var was = rebuilding;
    rebuilding = true;
    applyLocale();
    rebuilding = was;
  }

  /** Описание снятого фильма: прежний вид — синопсис, лента кадров, титры списком. */
  function renderFilmPanel(film) {
    var body = document.querySelector('#panel-credits .panel-body');
    var head = document.querySelector('#panel-credits .credits-film');
    var h2 = document.querySelector('#panel-credits h2');
    if (!body) return;

    if (h2) h2.dataset.t = film.soon ? 'aboutClip' : 'aboutFilm';
    if (head) head.textContent = tin('films', film.id);
    body.textContent = '';

    var syn = tin('synopsis', film.id);
    if (syn) {
      var sp = document.createElement('p');
      sp.className = 'credits-synopsis';
      sp.textContent = syn;
      body.appendChild(sp);
    }

    // бэкстейдж живёт при своей работе: лента внутри описания фильма.
    // Высота у кадров общая, ширина — по пропорции, поэтому ничего не режется.
    if (film.bts && film.bts.length) {
      var bsub = document.createElement('div');
      bsub.className = 'credits-sub';
      bsub.textContent = t('wall');
      body.appendChild(bsub);

      var strip = document.createElement('div');
      strip.className = 'credits-shots';

      film.bts.forEach(function (shot, idx) {
        if (!shot || !shot.cover) return;
        var fig = document.createElement('figure');
        fig.className = 'credits-shot';

        var im = document.createElement('img');
        im.src = shot.cover;
        im.alt = '';
        im.loading = 'lazy';
        fig.appendChild(im);

        if (shot.shot !== undefined) {
          var cap = document.createElement('figcaption');
          cap.dataset.tShot = String(shot.shot);
          fig.appendChild(cap);
        }

        fig.addEventListener('click', function () { openLightbox(film.bts, idx); });
        strip.appendChild(fig);
      });

      // обёртка нужна для затемнения справа: оно показывает, что ряд длиннее
      var wrap = document.createElement('div');
      wrap.className = 'credits-shots-wrap';
      wrap.appendChild(strip);
      var atEnd = function () {
        var left = Math.abs(strip.scrollLeft);
        wrap.classList.toggle('is-end', left + strip.clientWidth >= strip.scrollWidth - 2);
      };
      strip.addEventListener('scroll', atEnd);
      requestAnimationFrame(atEnd);
      body.appendChild(wrap);
    }

    // посты-анонсы: та же лента, но плитки ведут в инстаграм
    if (film.posts && film.posts.length) {
      var psub = document.createElement('div');
      psub.className = 'credits-sub';
      psub.textContent = t('fromInstagram');
      body.appendChild(psub);

      var pstrip = document.createElement('div');
      pstrip.className = 'credits-shots';

      film.posts.forEach(function (post) {
        if (!post || !post.cover) return;
        var tile = document.createElement(post.url ? 'a' : 'figure');
        tile.className = 'credits-shot credits-post';
        if (post.url) {
          tile.href = post.url;
          tile.target = '_blank';
          tile.rel = 'noopener';
        }
        var pi = document.createElement('img');
        pi.src = post.cover;
        pi.alt = '';
        pi.loading = 'lazy';
        tile.appendChild(pi);
        if (post.kind === 'video') {
          var pl = document.createElement('span');
          pl.className = 'post-play';
          pl.setAttribute('aria-hidden', 'true');
          tile.appendChild(pl);
        }
        pstrip.appendChild(tile);
      });

      var pwrap = document.createElement('div');
      pwrap.className = 'credits-shots-wrap';
      pwrap.appendChild(pstrip);
      var pEnd = function () {
        pwrap.classList.toggle('is-end',
          Math.abs(pstrip.scrollLeft) + pstrip.clientWidth >= pstrip.scrollWidth - 2);
      };
      pstrip.addEventListener('scroll', pEnd);
      requestAnimationFrame(pEnd);
      body.appendChild(pwrap);
    }

    var rows = creditsFor(film);
    if (syn && rows.length) {
      var sub = document.createElement('div');
      sub.className = 'credits-sub';
      sub.textContent = t('credits');
      body.appendChild(sub);
    }

    rows.forEach(function (row) {
      var line = document.createElement('div');
      line.className = 'credits-row';

      var role = document.createElement('span');
      role.className = 'credits-role';
      role.textContent = row[0];
      line.appendChild(role);

      var names = document.createElement('span');
      names.className = 'credits-names';
      (row[1] || []).forEach(function (nm) {
        var one = document.createElement('span');
        one.textContent = nm;
        names.appendChild(one);
      });
      line.appendChild(names);

      body.appendChild(line);
    });

    // одной строкой — там, где титры не разложены по ролям (клип)
    if (!rows.length && film.creditsKey) {
      var one = document.createElement('p');
      one.className = 'credits-line';
      one.textContent = t(film.creditsKey);
      body.appendChild(one);
    }

    applyLocale();
  }

  /** Описание работы. Клип — вкладки и листалка без прокрутки, снятые фильмы — как были. */
  function openCredits(film) {
    var panel = document.getElementById('panel-credits');
    var isClip = !!film.soon;
    if (panel) panel.classList.toggle('panel--clip', isClip);
    if (isClip) {
      renderClipPanel(film, null);
    } else {
      creditsUI = null;
      renderFilmPanel(film);
    }
    openPanel('credits');
  }

  /* ======================================================================
   * 5b. Язык: подстановка строк и переключатель
   * ==================================================================== */

  var langEl = document.getElementById('lang');

  function buildSwitcher() {
    if (!langEl) return;
    langEl.textContent = '';
    ORDER.forEach(function (code) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'lang-btn';
      b.dataset.lang = code;
      b.lang = code;
      b.textContent = dict(code).label || code;
      b.addEventListener('click', function () { setLocale(code); });
      langEl.appendChild(b);
    });
  }

  /** Раскладывает строки текущего языка по разметке. */
  // языки, набранные связным письмом: итальянский (Monotype Corsiva) и арабская
  // вязь. Французский сюда не входит: текст на Didot, на Mistral только заголовки
  var SCRIPT_LOCALES = ['it', 'ar-SA'];

  function applyLocale() {
    var d = dict(locale);
    var rtl = d.dir === 'rtl';

    document.documentElement.lang = locale;
    document.documentElement.dir = d.dir || 'ltr';
    document.title = t('title');

    var meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute('content', t('description'));

    each('[data-t]', function (el) { el.textContent = t(el.dataset.t); });
    each('[data-t-film]', function (el) { el.textContent = tin('films', el.dataset.tFilm); });
    each('[data-t-kind]', function (el) {
      var kind = tin('kinds', el.dataset.tKind);
      var year = el.dataset.year;
      el.textContent = year ? kind + ' · ' + year : kind;
    });
    each('.foot-copy', function (el) { el.textContent = '© ' + el.dataset.year + ' ' + t('name'); });
    var shots = tlist('shots');
    each('[data-t-shot]', function (el) { el.textContent = shots[+el.dataset.tShot] || ''; });

    // текст «о себе» — абзацами
    var aboutBody = document.querySelector('#panel-about .panel-body');
    if (aboutBody) {
      aboutBody.textContent = '';
      tlist('aboutText').forEach(function (para) {
        var pp = document.createElement('p');
        pp.textContent = para;
        aboutBody.appendChild(pp);
      });
    }

    each('.panel-close', function (b) { b.setAttribute('aria-label', t('close')); });
    each('.lightbox-close', function (b) { b.setAttribute('aria-label', t('close')); });
    each('.lb-prev', function (b) { b.setAttribute('aria-label', t('prev')); });
    each('.lb-next', function (b) { b.setAttribute('aria-label', t('next')); });
    each('.lb-restart', function (b) { b.setAttribute('aria-label', t('replay')); });
    each('.car-prev', function (b) { b.setAttribute('aria-label', t('prev')); });
    each('.car-next', function (b) { b.setAttribute('aria-label', t('next')); });
    if (lb.play) lb.play.setAttribute('aria-label', t(lb.playing ? 'pause' : 'play'));
    if (cueEl) cueEl.setAttribute('aria-label', t('next'));

    each('.lang-btn', function (b) {
      var on = b.dataset.lang === locale;
      b.classList.toggle('is-on', on);
      b.setAttribute('aria-current', on ? 'true' : 'false');
    });

    document.body.classList.toggle('is-rtl', rtl);
    // связный рукописный и арабская вязь не терпят разрядки и прописных
    document.body.classList.toggle('is-script', SCRIPT_LOCALES.indexOf(locale) >= 0);

    // открытый правовой документ переписываем на новый язык
    var legal = document.getElementById('panel-legal');
    if (legal && !legal.hidden && legal.dataset.doc) openLegal(legal.dataset.doc);

    // открытое описание работы тоже пересобирается, оставаясь на той же вкладке
    if (!rebuilding && creditsUI && panelOpen && panelOpen.id === 'panel-credits') {
      renderClipPanel(creditsUI.film, creditsUI.key);
    }
  }

  function setLocale(code) {
    if (!I18N[code] || code === locale) return;
    locale = code;
    try { localStorage.setItem(STORE_KEY, code); } catch (e) { /* приватный режим */ }
    applyLocale();
  }

  /* ======================================================================
   * 6. Старт
   * ==================================================================== */

  buildHero();
  buildSwitcher();
  buildContacts();
  buildLightbox();
  applyLocale();

  var startAt = fromHash();
  go(startAt >= 0 ? startAt : 0, true);

  // для отладки и автотестов
  window.__darina = {
    cfg: CFG,
    deck: { go: go, next: next, prev: prev, get current() { return current; } },
    sections: sections,
    engines: engines,
    get heroSlides() { return heroSlides.length; },
    get locale() { return locale; },
    setLocale: setLocale,
    engineBySection: engineBySection,
    playersBySection: playersBySection,
    lightbox: lb,
    openLightbox: openLightbox,
  };
})();

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
    v.loop = false;                            // цикл ведёт CutEngine

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
    var t = document.createElement(film.link ? 'a' : 'span');
    t.className = 't';
    t.textContent = film.title || '';
    if (film.link) { t.href = film.link; t.target = '_blank'; t.rel = 'noopener'; }
    title.appendChild(t);
    if (film.subtitle) {
      var sub = document.createElement('span');
      sub.className = 's';
      sub.textContent = film.subtitle;
      title.appendChild(sub);
    }
    s.appendChild(title);

    return s;
  }

  FILMS.forEach(function (film, i) {
    deckEl.appendChild(buildFilmSection(film, i));
  });

  var sections = Array.prototype.slice.call(deckEl.querySelectorAll('.section'));

  /* ======================================================================
   * 2. CutEngine — нарезка одного фильма на CUTS кусков
   * ==================================================================== */

  function CutEngine(section, film, onCut) {
    this.section = section;
    this.video = section.querySelector('video');
    this.onCut = onCut || function () {};

    this.cuts = film.cuts || CFG.CUTS;
    this.rate = film.rate || CFG.RATE;
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
      m.textContent = 'видео не найдено';
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

    var t = this.video.currentTime;
    var start = this.segStart(this.index);

    // кусок доиграл — режем на следующий;
    // ушли назад (loop/сбой перемотки) — тоже пересобираемся
    if (t >= start + this.hold || t < start - 0.5) this.advance();
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
    this.goTo(this.index, true);

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
   * 3. Индикатор нарезки (29 рисок)
   * ==================================================================== */

  var cutsEl = document.getElementById('cuts');
  var ticks = [];

  function buildTicks(n) {
    if (ticks.length === n) return;
    cutsEl.textContent = '';
    ticks = [];
    for (var i = 0; i < n; i++) {
      var t = document.createElement('i');
      cutsEl.appendChild(t);
      ticks.push(t);
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

  var engines = FILMS.map(function (film, i) {
    return new CutEngine(sections[i + 1], film, function (index, total) {
      if (current === i + 1) paintTicks(index, total);
    });
  });

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

    // видео: играет только активный экран, соседи — прогреваются
    engines.forEach(function (e, n) {
      var si = n + 1;
      if (si === i) { e.start(); return; }
      e.stop();
      if (Math.abs(si - i) === 1) e.warm();
    });

    var onFilm = i >= 1 && i <= engines.length;
    cutsEl.classList.toggle('is-on', onFilm);
    if (onFilm) paintTicks(engines[i - 1].index, engines[i - 1].cuts);

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

  /* — колесо / трекпад — */
  window.addEventListener('wheel', function (e) {
    if (panelOpen) return;
    e.preventDefault();
    if (locked || Math.abs(e.deltaY) < 8) return;
    if (e.deltaY > 0) next(); else prev();
  }, { passive: false });

  /* — тач — */
  var touchY = null;
  window.addEventListener('touchstart', function (e) {
    touchY = e.touches[0].clientY;
  }, { passive: true });

  window.addEventListener('touchmove', function (e) {
    if (!panelOpen) e.preventDefault();
  }, { passive: false });

  window.addEventListener('touchend', function (e) {
    if (panelOpen || touchY === null) return;
    var dy = touchY - e.changedTouches[0].clientY;
    touchY = null;
    if (Math.abs(dy) < 50 || locked) return;
    if (dy > 0) next(); else prev();
  }, { passive: true });

  /* — клавиатура — */
  window.addEventListener('keydown', function (e) {
    if (panelOpen) {
      if (e.key === 'Escape') closePanel();
      return;
    }
    switch (e.key) {
      case 'ArrowDown': case 'PageDown': case ' ':
        e.preventDefault(); next(); break;
      case 'ArrowUp': case 'PageUp':
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

  /* ======================================================================
   * 6. Старт
   * ==================================================================== */

  var startAt = fromHash();
  go(startAt >= 0 ? startAt : 0, true);

  // для отладки и автотестов
  window.__darina = {
    cfg: CFG,
    deck: { go: go, next: next, prev: prev, get current() { return current; } },
    sections: sections,
    engines: engines,
  };
})();

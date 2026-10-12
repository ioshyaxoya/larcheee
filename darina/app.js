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

  /** Экран-анонс: без видео и без нарезки — только типографика поверх свечения. */
  function buildSoonSection(film, i) {
    var s = document.createElement('section');
    s.className = 'section section--soon' + (film.title ? '' : ' soon-untitled');
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

    [['soon-kicker', film.kicker], ['soon-title', film.title]].forEach(function (pair) {
      if (!pair[1]) return;
      var el = document.createElement('div');
      el.className = pair[0];
      el.textContent = pair[1];
      inner.appendChild(el);
    });

    var badge = document.createElement('div');
    badge.className = 'soon-badge';
    badge.textContent = 'soon';
    inner.appendChild(badge);

    if (film.note) {
      var nt = document.createElement('div');
      nt.className = 'soon-note';
      nt.textContent = film.note;
      inner.appendChild(nt);
    }

    if (film.credits) {
      var cr = document.createElement('div');
      cr.className = 'soon-credits';
      cr.textContent = film.credits;
      inner.appendChild(cr);
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

  /** Стена: кадры со съёмок и посты из инстаграма, плитками-постерами. */
  function buildWallSection(film, i) {
    var s = document.createElement('section');
    s.className = 'section section--wall';
    s.dataset.anchor = String(i + 2);

    var scroll = document.createElement('div');
    scroll.className = 'wall-scroll js-scroll';

    var inner = document.createElement('div');
    inner.className = 'wall-inner';

    if (film.kicker) {
      var k = document.createElement('div');
      k.className = 'wall-kicker';
      k.textContent = film.kicker;
      inner.appendChild(k);
    }

    var grid = document.createElement('div');
    grid.className = 'wall-grid';

    (film.posts || []).forEach(function (post, n) {
      if (!post || !post.cover) return;
      var tile = document.createElement(post.url ? 'a' : 'div');
      tile.className = 'wall-tile';
      if (post.url) { tile.href = post.url; tile.target = '_blank'; tile.rel = 'noopener'; }
      // лёгкий детерминированный наклон — читается как приколотые постеры
      tile.style.setProperty('--tilt', ((((n * 37) % 9) - 4) * 0.4).toFixed(2) + 'deg');

      var img = document.createElement('img');
      img.src = post.cover;
      img.alt = post.caption || '';
      img.loading = 'lazy';
      tile.appendChild(img);

      if (post.kind === 'video') {
        var pl = document.createElement('span');
        pl.className = 'wall-play';
        pl.setAttribute('aria-hidden', 'true');
        tile.appendChild(pl);
      }
      if (post.caption) {
        var cap = document.createElement('span');
        cap.className = 'wall-cap';
        cap.textContent = post.caption;
        tile.appendChild(cap);
      }
      grid.appendChild(tile);
    });

    inner.appendChild(grid);
    scroll.appendChild(inner);
    s.appendChild(scroll);
    return s;
  }

  FILMS.forEach(function (film, i) {
    var build = film.wall ? buildWallSection
              : film.soon ? buildSoonSection
              : buildFilmSection;
    deckEl.appendChild(build(film, i));
  });

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

    if (this.prerendered) {
      // склейки уже в файле: ничего не трогаем, только ведём индикатор
      var idx = Math.min(this.cuts - 1, Math.max(0, Math.floor(t / this.segLen)));
      if (idx !== this.index) {
        this.index = idx;
        this.onCut(idx, this.cuts);
      }
      return;
    }

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

  // engineBySection — только фильмы, нужен индикатору нарезки;
  // playersBySection — всё, что надо включать и глушить при листании
  var engineBySection = [];
  var playersBySection = [];
  FILMS.forEach(function (film, i) {
    var si = i + 1;
    if (film.soon || film.wall) {
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
    if (panelOpen) {
      if (e.key === 'Escape') closePanel();
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
    engineBySection: engineBySection,
    playersBySection: playersBySection,
  };
})();

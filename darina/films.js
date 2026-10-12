/* ---------------------------------------------------------------------------
 * films.js — техническая часть контента. Все тексты лежат в i18n.js.
 *
 * Поля экрана с фильмом:
 *   id          — ключ для названия в i18n.js → films[id]
 *   kind        — ключ вида в i18n.js → kinds[kind] ('short' | 'mv')
 *   year        — печатается в подписи после вида
 *   src         — видео: массив путей, браузер берёт первый понятный формат
 *   poster      — кадр, пока видео грузится
 *   link        — ссылка на полную версию, название станет кликабельным
 *   prerendered — файл уже нарезан и ускорен (tools/montage.py), движок его
 *                 не перематывает, а крутит по кругу
 *   credits     — титры: { ru: [[роль, [имена]], …], en: [[…]] }.
 *                 ru показывается на русском, en — на остальных языках
 *   cuts / rate / cutSeconds — переопределить параметры нарезки
 * ------------------------------------------------------------------------ */

window.MONTAGE = {
  CUTS: 29,          // на сколько кусков режем каждый фильм
  RATE: 1.28,        // ускорение воспроизведения
  CUT_SECONDS: 1.6,  // длительность одного куска в секундах исходника
  SCROLL_SPEED: 700, // мс на перелистывание экрана (как на референсе)
};

window.FILMS = [
  {
    id: 'kirill', kind: 'short', year: 2026,
    // Нарезка из мастера 5:53 (1920×1080, scope в кадре 16:9): срезан
    // letterbox (crop 1920:816:0:132), взят диапазон 19.5–331.0 — без
    // карточки курсовой, OrBox, «16+», заставки института и титров.
    // Верхняя граница 331, а не 338: иначе кусок попадал в чёрную паузу.
    prerendered: true,
    src: ['assets/films/kirill.webm', 'assets/films/kirill.mp4'],
    poster: 'assets/films/kirill-poster.jpg',
    link: 'https://www.youtube.com/watch?v=JHgzOetLiqM',
    // титры с постера; ru — как в фильме, en — латиницей для остальных языков
    credits: {
      ru: [
        ['Режиссёр и автор идеи', ['Дарина Данилюк']],
        ['Сценарист',             ['Валерия Саксонова']],
        ['Оператор-постановщик',  ['Артём Золотов']],
        ['Звукорежиссёр',         ['Александр Вязаничев']],
        ['Продюсер',              ['Мария Головина']],
        ['Художник-постановщик',  ['Алиса Кац']],
        ['Второй режиссёр',       ['Яна Ованесянц']],
        ['Ассистент режиссёра',   ['Анастасия Лапидус']],
        ['В ролях',               ['Григорий Баев', 'Арина Лигай',
                                   'Арина Попова', 'Дмитрий Савогин']],
        ['Производство',          ['Институт кино и телевидения']],
      ],
      en: [
        ['Director, original idea', ['Darina Danilyuk']],
        ['Screenwriter',            ['Valeria Saksonova']],
        ['Director of photography',  ['Artem Zolotov']],
        ['Sound designer',          ['Alexander Vyazanichev']],
        ['Producer',                ['Maria Golovina']],
        ['Production designer',     ['Alisa Katz']],
        ['Second unit director',    ['Yana Ovanesyants']],
        ['Assistant director',      ['Anastasia Lapidus']],
        ['Cast',                    ['Grigory Baev', 'Arina Ligay',
                                     'Arina Popova', 'Dmitry Savogin']],
        ['Production',              ['Institute of Cinema and Television']],
      ],
    },
  },
  {
    id: 'drive', kind: 'short', year: 2025,
    // Нарезка из мастера 3:08, диапазон 19.0–182.5.
    prerendered: true,
    src: ['assets/films/drive.webm', 'assets/films/drive.mp4'],
    poster: 'assets/films/drive-poster.jpg',
    link: 'https://www.youtube.com/watch?v=9tVdzKuggLU',   // перезалит
    credits: {
      ru: [
        ['Режиссёр',            ['Дарина Данилюк']],
        ['Оператор',            ['Артём Золотов']],
        ['Звукорежиссёр',       ['Александр Вязаничев']],
        ['Продюсер',            ['Ярослав Гусев']],
        ['Второй режиссёр',     ['Алина Веремей']],
        ['Помощник режиссёра',  ['Анастасия Лапидус']],
        ['Каскадёр',            ['Тимофей Беленький']],
        ['В ролях',             ['Евгений Канунников — Парень',
                                 'Александра Золотова — Женщина',
                                 'Вячеслав Мелешин — Охранник',
                                 'Ева Мелешина — Ребёнок']],
        ['Отдельная благодарность', ['Лариса Данилюк', 'Алексей Золотов',
                                     'Николай Кривов', 'Карина Мелешина']],
        ['Мастерские',          ['Б. П. Моргунов', 'Р. В. Иванов', 'Р. Э. Минлишев',
                                 'Д. Ю. Бобров', 'Е. В. Мустафина', 'П. В. Кириллов']],
      ],
      en: [
        ['Director',              ['Darina Danilyuk']],
        ['Cinematographer',       ['Artem Zolotov']],
        ['Sound designer',        ['Alexander Vyazanichev']],
        ['Producer',              ['Yaroslav Gusev']],
        ['Second unit director',  ['Alina Veremey']],
        ['Assistant director',    ['Anastasia Lapidus']],
        ['Stunt performer',       ['Timofey Belenkiy']],
        ['Cast',                  ['Evgeny Kanunnikov — the young man',
                                   'Alexandra Zolotova — the woman',
                                   'Vyacheslav Meleshin — the guard',
                                   'Eva Meleshina — the child']],
        ['Special thanks',        ['Larisa Danilyuk', 'Alexey Zolotov',
                                   'Nikolay Krivov', 'Karina Meleshina']],
        ['Workshops',             ['B. P. Morgunov', 'R. V. Ivanov', 'R. E. Minlishev',
                                   'D. Yu. Bobrov', 'E. V. Mustafina', 'P. V. Kirillov']],
      ],
    },
  },

  /* ----------------------------------------------------------------------
   * Клип на «MPMGA OUTRO» — закрывающий трек альбома «Make Pop Music Great
   * Again» трио nkeeei / Uniqe / Artem Shilovets.
   *
   * ДО ПУБЛИКАЦИИ (сейчас): название не раскрывается, на экране только
   * «скоро» на языке посетителя. Команда артистов может захотеть выпустить
   * клип сама — объявлять раньше них не нужно.
   *
   * ПОСЛЕ ПУБЛИКАЦИИ заполнить:
   *   id       — и добавить название в i18n.js → films[id] на всех языках
   *   artists  — «[артисты] — MPMGA OUTRO». Порядок имён в трио меняется
   *              от трека к треку, взять его со страницы ИМЕННО этого
   *              трека на стриминге, не по памяти
   *   note     — «13 октября», если Дарина выкладывает сама (старт тура);
   *              пока ждём ответа команды — оставить пустым
   *   links    — куда ведёт экран. VK Видео первым, YouTube вторым:
   *              в России YouTube грузится плохо
   *   credits  — «Режиссёры: Дарина Данилюк, Яна Ованесянц»
   *
   * Когда появится мастер, экран можно превратить в обычный: убрать soon,
   * прогнать клип через tools/montage.py и поставить prerendered.
   * -------------------------------------------------------------------- */
  {
    soon: true,
    kind: 'mv',
    id: '',        // ключ названия в i18n.js, когда можно раскрыть
    artists: '',   // подпись сверху вместо вида, после премьеры
    note: '',
    credits: '',
    links: [],     // [{ label: 'VK Видео', url: '...' }, { label: 'YouTube', url: '...' }]
    // подложка — бэкстейдж со съёмок, сам клип не показывает
    src: ['assets/films/clip-teaser.webm', 'assets/films/clip-teaser.mp4'],
    poster: 'assets/films/clip-poster.jpg',
  },

  /* ----------------------------------------------------------------------
   * Стена: кадры со съёмок и посты-анонсы из инстаграма.
   * Подписи плиток — в i18n.js → shots[], по порядку.
   * url у плитки делает её ссылкой на пост.
   * -------------------------------------------------------------------- */
  {
    wall: true,
    posts: [
      { cover: 'assets/wall/shoot-01.jpg', url: '' },
      { cover: 'assets/wall/shoot-02.jpg', url: '' },
      { cover: 'assets/wall/shoot-03.jpg', url: '' },
      { cover: 'assets/wall/shoot-04.jpg', url: '' },
      { cover: 'assets/wall/shoot-05.jpg', url: '' },
    ],
  },
];

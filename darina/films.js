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

/* Первый экран: фотография из макета и портреты Дарины, медленно
   сменяющие друг друга. Первой всегда идёт фотография со съёмки —
   с неё начинался исходный макет. */
window.HERO = [
  'assets/hero.jpg',
  'assets/portraits/darina-01.jpg',
  'assets/portraits/darina-02.jpg',
  'assets/portraits/darina-03.jpg',
];

/* Контакты. Пустой url — строка не показывается. */
window.CONTACTS = [
  { text: 't.me/darinadanilyuk',   url: 'https://t.me/darinadanilyuk' },
  { text: 'instagram.com/darinadanilyuk', url: 'https://www.instagram.com/darinadanilyuk' },
  { text: 'danilyukk.dar@mail.ru', url: 'mailto:danilyukk.dar@mail.ru' },
];

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
   * Стена: бэкстейдж со всех трёх съёмок, по группе на работу.
   * Подписи плиток необязательны: shot — номер в i18n.js → shots[].
   * url у плитки делает её ссылкой на пост в инстаграме.
   * -------------------------------------------------------------------- */
  {
    wall: true,
    groups: [
      // заголовок берётся из i18n: film → films[id], kind → kinds[kind]
      { film: 'kirill', posts: [
        { cover: 'assets/wall/kirill-01.jpg' },
        { cover: 'assets/wall/kirill-02.jpg' },
        { cover: 'assets/wall/kirill-03.jpg' },
        { cover: 'assets/wall/kirill-04.jpg' },
        { cover: 'assets/wall/kirill-05.jpg' },
        { cover: 'assets/wall/kirill-06.jpg' },
      ] },
      { film: 'drive', posts: [
        { cover: 'assets/wall/drive-01.jpg' },
        { cover: 'assets/wall/drive-02.jpg' },
        { cover: 'assets/wall/drive-03.jpg' },
        { cover: 'assets/wall/drive-04.jpg' },
        { cover: 'assets/wall/drive-05.jpg' },
        { cover: 'assets/wall/drive-06.jpg' },
        { cover: 'assets/wall/drive-07.jpg' },
        { cover: 'assets/wall/drive-08.jpg' },
      ] },
      // посты-анонсы с её аккаунта. Обложки скачаны, а не прилинкованы:
      // Instagram отдаёт их по подписанным ссылкам, которые протухают.
      // kind: 'video' рисует на плитке метку воспроизведения (рилсы).
      { key: 'fromInstagram', posts: [
        { cover: 'assets/wall/ig-01.jpg', url: 'https://www.instagram.com/darinadanilyuk/p/DdbDMEJDbM4/' },
        { cover: 'assets/wall/ig-02.jpg', url: 'https://www.instagram.com/darinadanilyuk/reel/DdUW3YoR6GJ/', kind: 'video' },
        { cover: 'assets/wall/ig-03.jpg', url: 'https://www.instagram.com/darinadanilyuk/p/DdeFqJJjew2/' },
        { cover: 'assets/wall/ig-04.jpg', url: 'https://www.instagram.com/darinadanilyuk/p/DdpSVALjWU2/' },
        { cover: 'assets/wall/ig-05.jpg', url: 'https://www.instagram.com/darinadanilyuk/reel/Ddy96zFNdm2/', kind: 'video' },
        { cover: 'assets/wall/ig-06.jpg', url: 'https://www.instagram.com/darinadanilyuk/reel/DeMTNLxN-ly/', kind: 'video' },
      ] },

      // у съёмки клипа подписи есть: shot — номер в i18n.js → shots[]
      { kind: 'mv', posts: [
        { cover: 'assets/wall/shoot-01.jpg', shot: 0, url: '' },
        { cover: 'assets/wall/shoot-02.jpg', shot: 1, url: '' },
        { cover: 'assets/wall/shoot-03.jpg', shot: 2, url: '' },
        { cover: 'assets/wall/shoot-04.jpg', shot: 3, url: '' },
        { cover: 'assets/wall/shoot-05.jpg', shot: 4, url: '' },
      ] },
    ],
  },
];

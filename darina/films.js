/* ---------------------------------------------------------------------------
 * films.js — техническая часть контента. Все тексты лежат в i18n.js.
 *
 * Поля экрана с фильмом:
 *   id          — служебный ключ (синопсис и т.п. лежат в i18n.js по этому id)
 *   title       — ОРИГИНАЛЬНОЕ название. Одно, на всех языках: не переводится
 *   titleLang   — язык оригинала ('ru'): страницы на этом языке показывают оригинал,
 *                 а под ним английское; все остальные — только английское (русского
 *                 вне русской страницы быть не должно). Нет поля — оригинал везде
 *   titleEn     — ОФИЦИАЛЬНОЕ английское название — второе и последнее. Других нет:
 *                 восемь переводов размывали бы поиск по фестивалям и базам. Берётся
 *                 с ютуб-канала (у «Кирилла» — «Kirill, my love», у «Драйва» — «Drive»).
 *                 Нет поля или то же, что title (MPMGA OUTRO) — второй строки нет
 *   kind        — ключ вида в i18n.js → kinds[kind] ('short' | 'mv')
 *   year        — печатается в подписи после вида
 *   duration    — хронометраж полной версии по ссылке, секунды: идёт на кнопку «смотреть».
 *                 Снимать с самого видео (ютуб показывает его под плеером), не с мастера:
 *                 у «Драйва» мастер 3:08, а на ютубе 2:59
 *   src         — видео: массив путей, браузер берёт первый понятный формат
 *   poster      — кадр, пока видео грузится
 *   link        — ссылка на полную версию: название фильма на экране и строка «смотреть»
 *                 в описании
 *   links       — то же списком [{ url }], если версий несколько (VK Видео первым,
 *                 YouTube вторым: в России YouTube грузится плохо). Если есть, link не нужен.
 *                 Название площадки сайт берёт из адреса сам — «VK Видео» по-русски
 *                 пишется только на русской странице
 *   prerendered — файл уже нарезан и ускорен (tools/montage.py), движок его
 *                 не перематывает, а крутит по кругу
 *   credits     — титры: { ru: [[роль, [имена]], …], en: [[…]] }.
 *                 ru показывается на русском, en — на остальных языках
 *   cutOrder    — порядок кусков в нарезке: cutOrder[j] — какой по счёту кусок
 *                 ФИЛЬМА стоит в нарезке на месте j. Нарезка собрана микс-ом, как
 *                 трейлер: начало, середина, конец, снова начало… (tools/montage.py,
 *                 --order mix). Сайт это поле не читает — оно нужно, чтобы при
 *                 пересборке не потерять соответствие (см. ниже про focus)
 *   cutTimes    — с какого времени файла (с) начинаются куски 1…28; кусок 0 идёт
 *                 с нуля. Берётся из готового файла: python3 tools/cuts.py <файл>.
 *                 Куски в файле не равные доли, и без этого кадрирование
 *                 переключалось бы мимо склейки
 *   focus       — кадрирование для ВЕРТИКАЛЬНОГО экрана: по числу на кусок нарезки
 *                 (29), центр видимой полосы в % ширины кадра, слева направо
 *                 (50 — середина). Индекс — МЕСТО в нарезке (то, что видно на j-м
 *                 куске), а не номер куска в фильме. На телефоне виден узкий срез
 *                 кадра, а герои у режиссёра стоят по третям. Двигать удобно в
 *                 tools/focus.html — он выдаёт готовую строку. Нет поля — всё по
 *                 центру, как раньше. Если нарезку пересобрали в другом порядке, focus
 *                 переносится по куску фильма: focus_новый[j] = focus_старый[p],
 *                 где cutOrder_старый[p] == cutOrder_новый[j] (потом глянуть
 *                 результат в focus.html)
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
window.HERO = {
  // Чёрно-белые портреты. У 01 и 02 Дарина оставила белые поля — они и держат
  // склейки по два-три кадра: поля работают как промежуток между снимками.
  photos: [
    'assets/portraits/darina-01.jpg',
    'assets/portraits/darina-02.jpg',
    'assets/portraits/darina-03.jpg',
    'assets/portraits/darina-04.jpg',
    'assets/portraits/darina-05.jpg',
  ],
  // Склейки, по которым идёт первый экран. Первая — один кадр, крупный план.
  // Дальше чередуются по два, по три и по одному. Числа — номера в photos.
  sets: [
    [2],
    [0, 1],
    [3],
    [4, 2],
    [1, 3, 0],
    [0],
    [2, 4],
    [3, 1],
    [4],
    [0, 2, 3],
    [1],
    [3, 4],
    [2, 0, 1],
    [3, 2],
    [4, 1, 0],
  ],

};

/* Контакты. Пустой url — строка не показывается. */
window.CONTACTS = [
  { text: 't.me/darinadanilyuk',   url: 'https://t.me/darinadanilyuk' },
  { text: 'instagram.com/darinadanilyuk', url: 'https://www.instagram.com/darinadanilyuk' },
  { text: 'danilyukk.dar@mail.ru', url: 'mailto:danilyukk.dar@mail.ru' },
];

window.FILMS = [
  {
    id: 'kirill', kind: 'short', year: 2026,
    title: 'Кирилл, моя любовь',
    titleLang: 'ru',                                 // язык оригинала: читалка экрана не станет читать по-испански
    titleEn: 'Kirill, my love',
    duration: 345,                                   // 5:45 на ютубе
    // бэкстейдж — открывается в описании фильма
    bts: [
      { cover: 'assets/wall/kirill-01.jpg' },
      { cover: 'assets/wall/kirill-02.jpg' },
      { cover: 'assets/wall/kirill-03.jpg' },
      { cover: 'assets/wall/kirill-04.jpg' },
      { cover: 'assets/wall/kirill-05.jpg' },
      { cover: 'assets/wall/kirill-06.jpg' },
    ],
    // Нарезка из мастера 5:53 (1920×1080, scope в кадре 16:9): срезан
    // letterbox (crop 1920:816:0:132), взят диапазон 19.5–331.0 — без
    // карточки курсовой, OrBox, «16+», заставки института и титров.
    // Верхняя граница 331, а не 338: иначе кусок попадал в чёрную паузу.
    prerendered: true,
    src: ['assets/films/kirill.webm', 'assets/films/kirill.mp4'],
    poster: 'assets/films/kirill-poster.jpg',
    cutTimes: [1.32, 2.88, 4.2, 5.32, 6.24, 7.04, 7.76, 8.36, 8.96, 10.68, 11.88, 12.76, 13.44, 14.08, 14.6, 15.08, 15.56, 15.96, 17.72, 19.12, 20.08, 20.84, 21.44, 21.96, 22.44, 22.84, 23.24, 23.72],
    cutOrder: [0, 12, 28, 7, 16, 25, 2, 18, 24, 8, 13, 27, 4, 17, 23, 3, 14, 20, 1, 15, 21, 5, 11, 22, 9, 19, 26, 6, 10],   // какой по счёту кусок фильма стоит на месте j (микс, tools/montage.py)
    focus: [   // центр окна вертикального экрана по кускам 0–28 (по МЕСТУ в нарезке), % ширины кадра
       35,  35,  43,  33,  45,  34,  49,  62,  72,  62,
       66,  53,  46,  58,  69,  33,  52,  70,  45,  63,
       35,  76,  52,  38,  90,  68,  30,  50,  57,
    ],
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
    title: 'Драйв',
    titleLang: 'ru',
    titleEn: 'Drive',
    duration: 179,                                   // 2:59 на ютубе
    // бэкстейдж — открывается в описании фильма
    bts: [
      { cover: 'assets/wall/drive-01.jpg' },
      { cover: 'assets/wall/drive-02.jpg' },
      { cover: 'assets/wall/drive-03.jpg' },
      { cover: 'assets/wall/drive-04.jpg' },
      { cover: 'assets/wall/drive-05.jpg' },
      { cover: 'assets/wall/drive-06.jpg' },
      { cover: 'assets/wall/drive-07.jpg' },
      { cover: 'assets/wall/drive-08.jpg' },
    ],
    // Нарезка из мастера 3:08, диапазон 19.0–182.5.
    prerendered: true,
    src: ['assets/films/drive.webm', 'assets/films/drive.mp4'],
    poster: 'assets/films/drive-poster.jpg',
    cutTimes: [0.8, 2.333, 3.667, 4.8, 5.7, 6.5, 7.2, 7.833, 8.4, 10.167, 11.333, 12.2, 12.9, 13.533, 14.067, 14.567, 15.033, 15.433, 17.233, 18.667, 19.567, 20.333, 20.933, 21.433, 21.9, 22.333, 22.767, 23.3],
    cutOrder: [0, 11, 24, 4, 17, 22, 3, 18, 27, 1, 15, 28, 2, 16, 20, 5, 10, 23, 7, 12, 21, 6, 13, 26, 8, 14, 25, 9, 19],   // какой по счёту кусок фильма стоит на месте j (микс, tools/montage.py)
    focus: [   // центр окна вертикального экрана по кускам 0–28 (по МЕСТУ в нарезке), % ширины кадра
       70,  43,  46,  52,  43,  50,  73,  54,  66,  52,
       19,  30,  80,  39,  58,  65,  58,  64,  37,  49,
       40,  27,  44,  52,  46,  47,  54,  76,  54,
    ],
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
                                   'Nikolai Krivov', 'Karina Meleshina']],
        ['Workshops',             ['B. P. Morgunov', 'R. V. Ivanov', 'R. E. Minlishev',
                                   'D. Yu. Bobrov', 'E. V. Mustafina', 'P. V. Kirillov']],
      ],
    },
  },

  /* ----------------------------------------------------------------------
   * Клип на «MPMGA OUTRO» — закрывающий трек альбома «Make Pop Music Great
   * Again» трио nkeeei / Uniqe / Artem Shilovets.
   *
   * Название раскрыто. Пока клип не вышел, под ним стоит «скоро»:
   * это переключается само, от того, задан id или нет.
   *
   * ОСТАЛОСЬ ЗАПОЛНИТЬ ПОСЛЕ ПРЕМЬЕРЫ:
   *   note   — «13 октября», если Дарина выкладывает сама (старт тура);
   *            пока ждём ответа команды — оставить пустым
   *   links  — куда ведёт экран. VK Видео первым, YouTube вторым:
   *            в России YouTube грузится плохо
   *
   * Когда появится мастер, экран можно превратить в обычный: убрать soon,
   * прогнать клип через tools/montage.py и поставить prerendered.
   * -------------------------------------------------------------------- */
  {
    soon: true,
    kind: 'mv',
    id: 'mpmga',
    title: 'MPMGA OUTRO',         // оригинальное и английское совпадают — вторая строка не нужна
    // Порядок имён сверен со страницей ИМЕННО этого трека в Apple Music:
    // у «MPMGA OUTRO» первым идёт uniqe. На других треках альбома порядок
    // другой — по памяти ставить нельзя.
    artists: 'uniqe, nkeeei & ARTEM SHILOVETS',   // на экране — «by …» под названием
    note: '',            // «13 октября», если Дарина выкладывает сама
    creditsKey: 'clipCredits',   // строка «Режиссёры: …» — на странице клипа, не на экране анонса
    // история клипа: сам текст лежит в i18n.js (clipStory), здесь — вкладка и кусок
    // видео из клипа (вырезан из присланного файла с первого непустого кадра)
    story: {
      text: 'clipStory',
      tab: 'clipStoryTab',
      caption: 'clipFrame',
      src: ['assets/films/clip-excerpt.webm', 'assets/films/clip-excerpt.mp4'],
      poster: 'assets/films/clip-excerpt-poster.jpg',
    },
    // посты-анонсы с её аккаунта: обложки скачаны, а не прилинкованы —
    // инстаграм отдаёт их по подписанным ссылкам, которые протухают
    posts: [
    { cover: 'assets/wall/ig-01.jpg', url: 'https://www.instagram.com/darinadanilyuk/p/DdbDMEJDbM4/' },
    { cover: 'assets/wall/ig-02.jpg', url: 'https://www.instagram.com/darinadanilyuk/reel/DdUW3YoR6GJ/', kind: 'video' },
    { cover: 'assets/wall/ig-03.jpg', url: 'https://www.instagram.com/darinadanilyuk/p/DdeFqJJjew2/' },
    { cover: 'assets/wall/ig-04.jpg', url: 'https://www.instagram.com/darinadanilyuk/p/DdpSVALjWU2/' },
    { cover: 'assets/wall/ig-05.jpg', url: 'https://www.instagram.com/darinadanilyuk/reel/Ddy96zFNdm2/', kind: 'video' },
    { cover: 'assets/wall/ig-06.jpg', url: 'https://www.instagram.com/darinadanilyuk/reel/DeMTNLxN-ly/', kind: 'video' },
    ],
    bts: [
      { cover: 'assets/wall/shoot-01.jpg', shot: 0 },
      { cover: 'assets/wall/shoot-02.jpg', shot: 1 },
      { cover: 'assets/wall/shoot-03.jpg', shot: 2 },
      { cover: 'assets/wall/shoot-04.jpg', shot: 3 },
      { cover: 'assets/wall/shoot-05.jpg', shot: 4 },
    ],
    links: [],     // [{ url: 'https://vk.com/video…' }, { url: 'https://youtu.be/…' }] — VK первым
    // подложка — бэкстейдж со съёмок, сам клип не показывает
    src: ['assets/films/clip-teaser.webm', 'assets/films/clip-teaser.mp4'],
    poster: 'assets/films/clip-poster.jpg',
  },

  /* ----------------------------------------------------------------------
   * Стена: бэкстейдж со всех трёх съёмок, по группе на работу.
   * Подписи плиток необязательны: shot — номер в i18n.js → shots[].
   * url у плитки делает её ссылкой на пост в инстаграме.
   * -------------------------------------------------------------------- */
];

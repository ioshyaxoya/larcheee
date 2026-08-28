/* ---------------------------------------------------------------------------
 * films.js — единственный файл, который нужно править, чтобы поменять контент.
 *
 * Каждый фильм режется движком на CUTS кусков и играет со скоростью RATE.
 * Значения по умолчанию заданы ниже и совпадают с ТЗ: 29 кусков, ×1.28.
 *
 * Поля фильма:
 *   title      — название, печатается слева внизу
 *   subtitle   — вторая строка (роль, год, продакшн)
 *   src        — путь к видео или массив путей (браузер возьмёт первый
 *                 формат, который умеет: webm — лёгкий, mp4 — для Safari)
 *   poster     — кадр-заглушка, показывается пока видео грузится
 *   link       — необязательная ссылка (Vimeo/YouTube) на полную версию
 *   cuts       — переопределить число кусков для этого фильма
 *   rate       — переопределить скорость для этого фильма
 *   cutSeconds — сколько секунд исходника показывать в одном куске
 * ------------------------------------------------------------------------ */

window.MONTAGE = {
  CUTS: 29,          // на сколько кусков режем каждый фильм
  RATE: 1.28,        // ускорение воспроизведения
  CUT_SECONDS: 1.6,  // длительность одного куска в секундах исходника
  SCROLL_SPEED: 700, // мс на перелистывание экрана (как на референсе)
};

window.FILMS = [
  {
    title: 'Красный свет',
    subtitle: 'dir. Darina Danilyuk',
    src: ['assets/films/film-01.webm', 'assets/films/film-01.mp4'],
    poster: 'assets/hero.jpg',
    link: '',
  },
  {
    title: 'Ночная смена',
    subtitle: 'short · dir. Darina Danilyuk',
    src: ['assets/films/film-02.webm', 'assets/films/film-02.mp4'],
    poster: 'assets/hero.jpg',
    link: '',
  },
  {
    title: 'Отражение',
    subtitle: 'music video · dir. Darina Danilyuk',
    src: ['assets/films/film-03.webm', 'assets/films/film-03.mp4'],
    poster: 'assets/hero.jpg',
    link: '',
  },
  {
    title: 'Backstage',
    subtitle: 'doc · dir. Darina Danilyuk',
    src: ['assets/films/film-04.webm', 'assets/films/film-04.mp4'],
    poster: 'assets/hero.jpg',
    link: '',
  },
  {
    title: 'Тихий свет',
    subtitle: 'short · dir. Darina Danilyuk',
    src: ['assets/films/film-05.webm', 'assets/films/film-05.mp4'],
    poster: 'assets/hero.jpg',
    link: '',
  },
];

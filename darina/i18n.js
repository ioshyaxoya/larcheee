/* ---------------------------------------------------------------------------
 * i18n.js — все тексты сайта. Правится переводчиком, без кода.
 *
 * Код языка = тег BCP 47. rtl: true включает зеркальную раскладку.
 * Если строки нет, берётся английская, потом русская.
 *
 * films — названия по id из films.js. Это рабочие переводы: если у фильма
 * есть официальное фестивальное название на языке, его нужно поставить сюда.
 * Английские взяты с ютуб-канала, русские — оригинальные.
 * ------------------------------------------------------------------------ */

window.I18N = {

  ru: {
    label: 'Рус', dir: 'ltr',
    title: 'Дарина Данилюк',
    description: 'Дарина Данилюк — режиссёр. Шоурил.',
    about: 'о себе', contact: 'контакты',
    next: 'дальше', close: 'закрыть',
    credits: 'титры',
    kinds: { short: 'короткий метр', mv: 'музыкальный клип' },
    soon: 'скоро',
    wall: 'как это снималось',
    missing: 'видео не найдено',
    aboutText: ['Дарина Данилюк — режиссёр.'],
    films: { kirill: 'Кирилл, моя любовь', drive: 'Драйв' },
    shots: ['съёмка на зелёнке', 'подготовка', 'стедикам', 'квартира', 'смена'],
  },

  'en-GB': {
    label: 'Eng', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — director. Showreel.',
    about: 'about', contact: 'contact',
    next: 'next', close: 'close',
    credits: 'credits',
    kinds: { short: 'short film', mv: 'music video' },
    soon: 'soon',
    wall: 'behind the scenes',
    missing: 'video not found',
    aboutText: ['Darina Danilyuk — director.'],
    films: { kirill: 'Kirill, my love', drive: 'Drive' },
    shots: ['green screen', 'pre-shoot', 'steadicam', 'the flat', 'shooting day'],
  },

  es: {
    label: 'Esp', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — directora. Reel.',
    about: 'sobre mí', contact: 'contacto',
    next: 'siguiente', close: 'cerrar',
    credits: 'créditos',
    kinds: { short: 'cortometraje', mv: 'videoclip' },
    soon: 'pronto',
    wall: 'cómo se hizo',
    missing: 'vídeo no encontrado',
    aboutText: ['Darina Danilyuk — directora.'],
    films: { kirill: 'Kirill, mi amor', drive: 'Drive' },
    shots: ['croma', 'preparación', 'steadicam', 'el piso', 'jornada de rodaje'],
  },

  eu: {
    label: 'Eus', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — zuzendaria. Lan bilduma.',
    about: 'niri buruz', contact: 'kontaktua',
    next: 'hurrengoa', close: 'itxi',
    credits: 'kredituak',
    kinds: { short: 'film laburra', mv: 'musika bideoa' },
    soon: 'laster',
    wall: 'nola egin zen',
    missing: 'bideoa ez da aurkitu',
    aboutText: ['Darina Danilyuk — zuzendaria.'],
    films: { kirill: 'Kirill, ene maitea', drive: 'Drive' },
    shots: ['pantaila berdea', 'prestaketa', 'steadicam', 'etxea', 'filmaketa eguna'],
  },

  it: {
    label: 'Ita', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — regista. Showreel.',
    about: 'chi sono', contact: 'contatti',
    next: 'avanti', close: 'chiudi',
    credits: 'titoli',
    kinds: { short: 'cortometraggio', mv: 'videoclip' },
    soon: 'presto',
    wall: 'dietro le quinte',
    missing: 'video non trovato',
    aboutText: ['Darina Danilyuk — regista.'],
    films: { kirill: 'Kirill, amore mio', drive: 'Drive' },
    shots: ['green screen', 'preparazione', 'steadicam', "l'appartamento", 'giornata di riprese'],
  },

  fr: {
    label: 'Fra', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — réalisatrice. Bande démo.',
    about: 'à propos', contact: 'contact',
    next: 'suivant', close: 'fermer',
    credits: 'générique',
    kinds: { short: 'court métrage', mv: 'clip' },
    soon: 'bientôt',
    wall: 'les coulisses',
    missing: 'vidéo introuvable',
    aboutText: ['Darina Danilyuk — réalisatrice.'],
    films: { kirill: 'Kirill, mon amour', drive: 'Drive' },
    shots: ['fond vert', 'préparation', 'steadicam', "l'appartement", 'jour de tournage'],
  },

  // Классический хохдойч: без англицизмов — Grüner Hintergrund вместо
  // Greenscreen, demnächst вместо «coming soon», Musikvideo вместо Clip.
  de: {
    label: 'Deu', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — Regisseurin. Werkschau.',
    about: 'über mich', contact: 'Kontakt',
    next: 'weiter', close: 'schließen',
    credits: 'Abspann',
    kinds: { short: 'Kurzfilm', mv: 'Musikvideo' },
    soon: 'demnächst',
    wall: 'hinter den Kulissen',
    missing: 'Film nicht gefunden',
    aboutText: ['Darina Danilyuk — Regisseurin.'],
    films: { kirill: 'Kirill, meine Liebe', drive: 'Drive' },
    shots: ['grüner Hintergrund', 'Vorbereitung', 'Steadicam', 'die Wohnung', 'Drehtag'],
  },

  'ar-SA': {
    label: 'عربي', dir: 'rtl',
    title: 'دارينا دانيليوك',
    description: 'دارينا دانيليوك — مخرجة. عرض الأعمال.',
    about: 'عني', contact: 'تواصل',
    next: 'التالي', close: 'إغلاق',
    credits: 'طاقم العمل',
    kinds: { short: 'فيلم قصير', mv: 'فيديو كليب' },
    soon: 'قريباً',
    wall: 'كواليس التصوير',
    missing: 'الفيديو غير موجود',
    aboutText: ['دارينا دانيليوك — مخرجة.'],
    films: { kirill: 'كيريل، حبيبي', drive: 'درايف' },
    shots: ['الشاشة الخضراء', 'التحضير', 'ستيديكام', 'الشقة', 'يوم التصوير'],
  },
};

// порядок в переключателе
window.I18N_ORDER = ['ru', 'en-GB', 'es', 'eu', 'it', 'fr', 'de', 'ar-SA'];
window.I18N_FALLBACK = ['en-GB', 'ru'];

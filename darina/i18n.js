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
    description: 'Дарина Данилюк — дипломированный режиссёр игрового и документального кино, хореограф.',
    about: 'о себе', contact: 'контакты',
    next: 'дальше', close: 'закрыть',
    credits: 'титры',
    aboutFilm: 'о фильме',
    kinds: { short: 'короткий метр', mv: 'музыкальный клип' },
    soon: 'скоро',
    wall: 'как это снималось',
    fromInstagram: 'из инстаграма',
    missing: 'видео не найдено',
    aboutText: ['Дарина Данилюк — дипломированный режиссёр игрового и документального кино, хореограф.'],
    films: { kirill: 'Кирилл, моя любовь', drive: 'Драйв' },
    synopsis: { kirill: 'После успешного показа своего дебютного фильма Арина встречает бывшего парня, к которому до сих пор испытывает чувства. Теперь ей предстоит понять, как отпустить прошлые отношения и начать новую жизнь.', drive: 'Парень просит милостыню у магазина. Вдруг он замечает выпавшие из сумки прохожей женщины ключи от машины и решается на угон.' },
    shots: ['съёмка на зелёнке', 'подготовка', 'стедикам', 'квартира', 'смена'],
  },

  'en-GB': {
    label: 'Eng', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — a qualified director of fiction and documentary film, and a choreographer.',
    about: 'about', contact: 'contact',
    next: 'next', close: 'close',
    credits: 'credits',
    aboutFilm: 'about the film',
    kinds: { short: 'short film', mv: 'music video' },
    soon: 'soon',
    wall: 'behind the scenes',
    fromInstagram: 'from Instagram',
    missing: 'video not found',
    aboutText: ['Darina Danilyuk — a qualified director of fiction and documentary film, and a choreographer.'],
    films: { kirill: 'Kirill, my love', drive: 'Drive' },
    synopsis: { kirill: 'After the successful premiere of her debut film, Arina runs into her ex-boyfriend, for whom she still has feelings. Now she must work out how to let the past go and begin a new life.', drive: 'A young man is begging outside a shop. He notices car keys that have fallen from a passing woman\u2019s bag, and decides to steal the car.' },
    shots: ['green screen', 'pre-shoot', 'steadicam', 'the flat', 'shooting day'],
  },

  es: {
    label: 'Esp', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — directora titulada de cine de ficción y documental, coreógrafa.',
    about: 'sobre mí', contact: 'contacto',
    next: 'siguiente', close: 'cerrar',
    credits: 'créditos',
    aboutFilm: 'sobre la película',
    kinds: { short: 'cortometraje', mv: 'videoclip' },
    soon: 'pronto',
    wall: 'cómo se hizo',
    fromInstagram: 'desde Instagram',
    missing: 'vídeo no encontrado',
    aboutText: ['Darina Danilyuk — directora titulada de cine de ficción y documental, coreógrafa.'],
    films: { kirill: 'Kirill, mi amor', drive: 'Drive' },
    synopsis: { kirill: 'Tras el exitoso estreno de su ópera prima, Arina se reencuentra con su exnovio, por quien todavía siente algo. Ahora debe descubrir cómo dejar atrás esa relación y empezar una vida nueva.', drive: 'Un chico pide limosna a la puerta de una tienda. De pronto ve las llaves de un coche caídas del bolso de una mujer que pasa y decide robarlo.' },
    shots: ['croma', 'preparación', 'steadicam', 'el piso', 'jornada de rodaje'],
  },

  eu: {
    label: 'Eus', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — fikziozko eta dokumentalezko filmen zuzendari tituluduna, koreografoa.',
    about: 'niri buruz', contact: 'kontaktua',
    next: 'hurrengoa', close: 'itxi',
    credits: 'kredituak',
    aboutFilm: 'filmari buruz',
    kinds: { short: 'film laburra', mv: 'musika bideoa' },
    soon: 'laster',
    wall: 'nola egin zen',
    fromInstagram: 'Instagrametik',
    missing: 'bideoa ez da aurkitu',
    aboutText: ['Darina Danilyuk — fikziozko eta dokumentalezko filmen zuzendari tituluduna, koreografoa.'],
    films: { kirill: 'Kirill, ene maitea', drive: 'Drive' },
    synopsis: { kirill: 'Bere lehen filmaren estreinaldi arrakastatsuaren ondoren, Arinak mutil-lagun ohia topatzen du, eta oraindik zerbait sentitzen du harengatik. Orain iraganeko harremana nola utzi eta bizitza berri bat nola hasi ulertu behar du.', drive: 'Mutil bat denda baten aurrean eskean dago. Bat-batean, ondotik doan emakume baten poltsatik eroritako auto-giltzak ikusten ditu, eta autoa lapurtzea erabakitzen du.' },
    shots: ['pantaila berdea', 'prestaketa', 'steadicam', 'etxea', 'filmaketa eguna'],
  },

  it: {
    label: 'Ita', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — regista diplomata di cinema di finzione e documentario, coreografa.',
    about: 'chi sono', contact: 'contatti',
    next: 'avanti', close: 'chiudi',
    credits: 'titoli',
    aboutFilm: 'sul film',
    kinds: { short: 'cortometraggio', mv: 'videoclip' },
    soon: 'presto',
    wall: 'dietro le quinte',
    fromInstagram: 'da Instagram',
    missing: 'video non trovato',
    aboutText: ['Darina Danilyuk — regista diplomata di cinema di finzione e documentario, coreografa.'],
    films: { kirill: 'Kirill, amore mio', drive: 'Drive' },
    synopsis: { kirill: 'Dopo il successo della prima del suo film d\u2019esordio, Arina incontra il suo ex, per il quale prova ancora qualcosa. Ora deve capire come lasciar andare quella relazione e cominciare una vita nuova.', drive: 'Un ragazzo chiede l\u2019elemosina davanti a un negozio. All\u2019improvviso nota le chiavi dell\u2019auto cadute dalla borsa di una donna di passaggio e decide di rubarla.' },
    shots: ['green screen', 'preparazione', 'steadicam', "l'appartamento", 'giornata di riprese'],
  },

  fr: {
    label: 'Fra', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — réalisatrice diplômée de fiction et de documentaire, chorégraphe.',
    about: 'à propos', contact: 'contact',
    next: 'suivant', close: 'fermer',
    credits: 'générique',
    aboutFilm: 'à propos du film',
    kinds: { short: 'court métrage', mv: 'clip' },
    soon: 'bientôt',
    wall: 'les coulisses',
    fromInstagram: 'sur Instagram',
    missing: 'vidéo introuvable',
    aboutText: ['Darina Danilyuk — réalisatrice diplômée de fiction et de documentaire, chorégraphe.'],
    films: { kirill: 'Kirill, mon amour', drive: 'Drive' },
    synopsis: { kirill: 'Après la projection réussie de son premier film, Arina retrouve son ex, pour qui elle éprouve encore des sentiments. Il lui faut désormais comprendre comment laisser le passé derrière elle et commencer une vie nouvelle.', drive: 'Un garçon mendie devant un magasin. Il remarque soudain les clés de voiture tombées du sac d\u2019une passante et décide de la voler.' },
    shots: ['fond vert', 'préparation', 'steadicam', "l'appartement", 'jour de tournage'],
  },

  // Классический хохдойч: без англицизмов — Grüner Hintergrund вместо
  // Greenscreen, demnächst вместо «coming soon», Musikvideo вместо Clip.
  de: {
    label: 'Deu', dir: 'ltr',
    title: 'Darina Danilyuk',
    description: 'Darina Danilyuk — diplomierte Regisseurin für Spielfilm und Dokumentarfilm, Choreographin.',
    about: 'über mich', contact: 'Kontakt',
    next: 'weiter', close: 'schließen',
    credits: 'Abspann',
    aboutFilm: 'über den Film',
    kinds: { short: 'Kurzfilm', mv: 'Musikvideo' },
    soon: 'demnächst',
    wall: 'hinter den Kulissen',
    fromInstagram: 'auf Instagram',
    missing: 'Film nicht gefunden',
    aboutText: ['Darina Danilyuk — diplomierte Regisseurin für Spielfilm und Dokumentarfilm, Choreographin.'],
    films: { kirill: 'Kirill, meine Liebe', drive: 'Drive' },
    synopsis: { kirill: 'Nach der erfolgreichen Aufführung ihres Erstlingsfilms begegnet Arina ihrem früheren Freund, für den sie noch immer Gefühle hegt. Nun muss sie herausfinden, wie sie die alte Beziehung loslässt und ein neues Leben beginnt.', drive: 'Ein junger Mann bettelt vor einem Geschäft. Plötzlich bemerkt er einen Autoschlüssel, der einer vorübergehenden Frau aus der Tasche gefallen ist, und entschließt sich, den Wagen zu entwenden.' },
    shots: ['grüner Hintergrund', 'Vorbereitung', 'Steadicam', 'die Wohnung', 'Drehtag'],
  },

  'ar-SA': {
    label: 'عربي', dir: 'rtl',
    title: 'دارينا دانيليوك',
    description: 'دارينا دانيليوك — مخرجة أفلام روائية ووثائقية حاصلة على شهادة في الإخراج، ومصممة رقصات.',
    about: 'عني', contact: 'تواصل',
    next: 'التالي', close: 'إغلاق',
    credits: 'طاقم العمل',
    aboutFilm: 'عن الفيلم',
    kinds: { short: 'فيلم قصير', mv: 'فيديو كليب' },
    soon: 'قريباً',
    wall: 'كواليس التصوير',
    fromInstagram: 'من إنستغرام',
    missing: 'الفيديو غير موجود',
    aboutText: ['دارينا دانيليوك — مخرجة أفلام روائية ووثائقية حاصلة على شهادة في الإخراج، ومصممة رقصات.'],
    films: { kirill: 'كيريل، حبيبي', drive: 'درايف' },
    synopsis: { kirill: 'بعد العرض الناجح لفيلمها الأول، تلتقي أرينا بحبيبها السابق الذي ما زالت تكنّ له المشاعر. وعليها الآن أن تدرك كيف تترك علاقة الماضي خلفها وتبدأ حياة جديدة.', drive: 'شاب يتسوّل أمام أحد المتاجر. وفجأة يلمح مفاتيح سيارة سقطت من حقيبة امرأة عابرة، فيقرّر سرقة السيارة.' },
    shots: ['الشاشة الخضراء', 'التحضير', 'ستيديكام', 'الشقة', 'يوم التصوير'],
  },
};

// порядок в переключателе
window.I18N_ORDER = ['ru', 'en-GB', 'es', 'eu', 'it', 'fr', 'de', 'ar-SA'];
window.I18N_FALLBACK = ['en-GB', 'ru'];

const PAGES = {
    en: [
        {
            id: 'page-0',
            title: 'LARCH.AE — the boutique movement for true build',
            kicker: '',
            blocks: [
                {
                    type: 'logo',
                    content: {
                        src: 'assets/logo.png',
                        alt: 'LARCH.AE Logo'
                    }
                },
                {
                    type: 'quotes',
                    content: [
                        '> The future is not fake or weak.',
                        '> The future is true build.',
                        '.المستقبل ليس مزيفاً أو ضعيفاً <',
                        '.المستقبل هو البناء الحقيقي <'
                    ]
                },
                  {
                    type: 'catalog-download',
                    content: {
                      title: 'Siberian Larch — Spec Sheet',
                      subtitle: 'Profiles · grades · finish options · install/warranty basics',
                      file: 'assets/catalog.pdf',
                      button: 'Download PDF'
                    }
                  },                  
                {
                    type: 'contents-label',
                    content: 'CONTENTS'
                },
                {
                    type: 'contents-list',
                    content: [
                        {
                            title: 'True Build Philosophy',
                            href: '#page-1',
                            description: 'Movement & community principles'
                        },
                        {
                            title: 'Proof of Strength (SMASH)',
                            href: '#page-2',
                            description: 'Lab testing & protocols'
                        },
                        {
                            title: 'Community Upgrades (20%)',
                            href: '#page-3',
                            description: 'Local reinvestment fund'
                        },
                        {
                            title: 'Case Studies',
                            href: '#page-4',
                            description: 'Real project results'
                        },
                        {
                            title: 'For Developers & FM',
                            href: '#page-5',
                            description: 'Professional services'
                        },
                        {
                            title: 'Join the Movement',
                            href: '#page-6',
                            description: 'Get involved today'
                        }
                    ]
                },
                {
                    type: 'sub-block',
                    title: 'For contractors',
                    content: `Dubai stock. Delivery in 24–72h across UAE. Decking ・ Cladding ・ Panels. Clear pricing & warranty. 
                      <a class="wa-cta" href="https://wa.me/971501234567?text=Hi%20LARCH.AE%20%E2%80%94%20I%20want%20to%20order" target="_blank" rel="noopener">
                        Call manager
                      </a>`                    
                  },
                {
                    type: 'footer',
                    content: {
                        copyright: 'LARCH.AE · MMXXV',
                        social: ['twitter', 'github', 'instagram'],
                        email: 'hello@larch.ae'
                    }
                }
            ]
        },
        {
            id: 'page-1',
            title: 'True build. Smash the fake.',
            kicker: 'Pillar 1 — Movement',
            blocks: [
                {
                    type: 'lead',
                    content: 'We are a community for honest quality. We replace weak materials with true Siberian larch — and prove it.'
                },
                {
                    type: 'list',
                    content: [
                        'Movement — citizens & partners co-fund visible upgrades',
                        'Lab — open SMASH-tests, public protocols',
                        'Supply — delivery & installation with warranty'
                    ]
                },
                {
                    type: 'sub-block',
                    title: 'Messaging Rules',
                    content: 'Fact → Test → Result → City benefit. Respectful tone. No shaming.'
                },
                {
                    type: 'badges',
                    content: ['Desert-ready', 'Lab-proven', '20% reinvest locally']
                },
                {
                    type: 'cta',
                    content: {
                        text: 'Join True Build',
                        href: '#page-6',
                        primary: true
                    }
                }
            ]
        },
        {
            id: 'page-2',
            title: 'Proof of Strength · Proof-SMASH™',
            kicker: 'Pillar 2 — Quality',
            blocks: [
                {
                    type: 'lead',
                    content: 'Key batches pass public stress-tests in Gulf conditions. Videos and protocols ship with each batch.'
                },
                {
                    type: 'cards',
                    content: [
                        {
                            icon: '🔥',
                            title: 'Heat endurance',
                            description: 'Thermal cycles at 50 °C'
                        },
                        {
                            icon: '🌪',
                            title: 'Sand abrasion',
                            description: 'Erosion rig / dust impact'
                        },
                        {
                            icon: '🔨',
                            title: 'Impact',
                            description: 'Drop/strike on profiles & fixings'
                        }
                    ]
                },
                {
                    type: 'specs',
                    content: [
                        'Density ≈650–700 kg/m³',
                        'Moisture(KD) 13–18%',
                        'Stability low warp/tight grain',
                        'Finish thermo/oil/fire-retard'
                    ]
                },
                {
                    type: 'cta',
                    content: [
                        {
                            text: 'Open test protocol',
                            href: '#',
                            secondary: true
                        },
                        {
                            text: 'Order a batch SMASH',
                            href: '#',
                            primary: true
                        }
                    ]
                }
            ]
        },
        {
            id: 'page-3',
            title: 'Community Upgrades — 20% Fund',
            kicker: 'Local Reinvestment',
            blocks: [
                {
                    type: 'lead',
                    content: '20% of profits reinvested in visible city upgrades: schools, mosque ramps, demo zones.'
                },
                {
                    type: 'kpi-cards',
                    content: [
                        {
                            value: '2,847',
                            label: 'Upgraded m²',
                            suffix: 'sqm'
                        },
                        {
                            value: '12',
                            label: 'Active sites',
                            suffix: 'locations'
                        },
                        {
                            value: 'Q3',
                            label: 'Public report cycle',
                            suffix: '2025'
                        }
                    ]
                },
                {
                    type: 'cta',
                    content: [
                        {
                            text: 'Nominate a site',
                            href: '#',
                            secondary: true
                        },
                        {
                            text: 'Donate/Partner',
                            href: '#',
                            primary: true
                        }
                    ]
                }
            ]
        },
        {
            id: 'page-4',
            title: 'Case Studies',
            kicker: 'Real Results',
            blocks: [
                {
                    type: 'lead',
                    content: 'Proven performance in Gulf conditions across multiple project types.'
                },
                {
                    type: 'case-studies',
                    content: [
                        {
                            title: 'Waterfront Promenade',
                            description: 'Larch deck replaced rotting composite. 10-year LCC saving 18%.',
                            metrics: ['18% cost saving', '10-year warranty', 'Zero maintenance']
                        },
                        {
                            title: 'Private Villa',
                            description: 'Heat-resistant cladding, zero maintenance claims in 24 months.',
                            metrics: ['50°C resistance', '24 months', 'Zero claims']
                        },
                        {
                            title: 'Retail Entrance',
                            description: 'Sand abrasion solved with densified larch steps.',
                            metrics: ['Sand-proof', 'High traffic', '5-year durability']
                        }
                    ]
                },
                {
                    type: 'cta',
                    content: {
                        text: 'See full report',
                        href: '#',
                        secondary: true
                    }
                }
            ]
        },
        {
            id: 'page-5',
            title: 'For Developers & FM',
            kicker: 'Professional Services',
            blocks: [
                {
                    type: 'lead',
                    content: 'Comprehensive solutions for development and facility management professionals.'
                },
                {
                    type: 'list',
                    content: [
                        'Lower maintenance claims & clearer PR',
                        'Decking / cladding / panels / facade systems',
                        'Design-assist, installation & warranty'
                    ]
                },
                {
                    type: 'services',
                    content: [
                        'Design consultation',
                        'Material specification',
                        'Installation support',
                        'Warranty coverage',
                        'Maintenance protocols'
                    ]
                },
                {
                    type: 'cta',
                    content: {
                        text: 'Book a private demo',
                        href: '#',
                        primary: true,
                        modal: 'demo'
                    }
                }
            ]
        },
        {
            id: 'page-6',
            title: 'Join the Movement',
            kicker: 'Get Involved',
            blocks: [
                {
                    type: 'lead',
                    content: 'Be part of the future of honest building in the Gulf. Let\'s build a city that lasts.'
                },
                {
                    type: 'form',
                    content: {
                        fields: [
                            { name: 'name', label: 'Name', type: 'text', required: true },
                            { name: 'email', label: 'Email', type: 'email', required: true },
                            { 
                                name: 'role', 
                                label: 'Role', 
                                type: 'select', 
                                required: true,
                                options: [
                                    'Client/Developer',
                                    'Architect',
                                    'Donor/Partner'
                                ]
                            }
                        ],
                        checkbox: {
                            name: 'policy',
                            label: 'I agree to Respect & Compliance policy',
                            required: true
                        },
                        submit: 'Join True Build'
                    }
                },
                {
                    type: 'policy-note',
                    content: 'Respect & Compliance — private locations/permits, constructive voice, open reports.'
                }
            ]
        }
    ],
    ar: [
        {
            id: 'page-0',
            title: 'LARCH.AE — الحركة البوتيكية للبناء الحقيقي',
            kicker: '',
            blocks: [
                {
                    type: 'logo',
                    content: {
                        src: 'assets/logo.png',
                        alt: 'LARCH.AE Logo'
                    }
                },
                {
                    type: 'quotes',
                    content: [
                        '> المستقبل ليس مزيفاً أو ضعيفاً.',
                        '> المستقبل هو البناء الحقيقي.',
                        '> The future is not fake or weak.',
                        '> The future is true build.'
                    ]
                },
                {
                    type: 'sub-block',
                    title: 'للمقاولين',
                    content: 'مخزون في دبي. توصيل خلال 24–72 ساعة داخل الإمارات. أرضيات · كسوة · ألواح. تسعير شفاف وضمان.'
                  },
                  {
                    type: 'catalog-download',
                    content: {
                      title: 'خشب اللارش السيبيري — ورقة المواصفات',
                      subtitle: 'مقاطع · درجات · خيارات التشطيب · أساسيات التركيب/الضمان',
                      file: 'assets/catalog.pdf',
                      button: 'تنزيل PDF'
                    }
                  },                  
                {
                    type: 'contents-label',
                    content: 'المحتويات'
                },
                {
                    type: 'contents-list',
                    content: [
                        {
                            title: 'فلسفة البناء الحقيقي',
                            href: '#page-1',
                            description: 'مبادئ الحركة والمجتمع'
                        },
                        {
                            title: 'إثبات القوة (SMASH)',
                            href: '#page-2',
                            description: 'اختبارات المختبر والبروتوكولات'
                        },
                        {
                            title: 'ترقيات المجتمع (20%)',
                            href: '#page-3',
                            description: 'صندوق إعادة الاستثمار المحلي'
                        },
                        {
                            title: 'دراسات الحالة',
                            href: '#page-4',
                            description: 'نتائج المشاريع الحقيقية'
                        },
                        {
                            title: 'للمطورين وإدارة المرافق',
                            href: '#page-5',
                            description: 'الخدمات المهنية'
                        },
                        {
                            title: 'انضم إلى الحركة',
                            href: '#page-6',
                            description: 'شارك اليوم'
                        }
                    ]
                },
                {
                    type: 'footer',
                    content: {
                        copyright: 'LARCH.AE · MMXXV',
                        social: ['twitter', 'github', 'instagram'],
                        email: 'hello@larch.ae'
                    }
                }
            ]
        },
        {
            id: 'page-1',
            title: 'بناء حقيقي. اسحق المزيف.',
            kicker: 'الركيزة الأولى — الحركة',
            blocks: [
                {
                    type: 'lead',
                    content: 'نحن مجتمع للجودة الصادقة. نستبدل المواد الضعيفة باللارش السيبيري الحقيقي — ونثبت ذلك.'
                },
                {
                    type: 'list',
                    content: [
                        'الحركة — المواطنون والشركاء يمولون الترقيات المرئية',
                        'المختبر — اختبارات SMASH مفتوحة، بروتوكولات عامة',
                        'الإمداد — التوصيل والتركيب مع الضمان'
                    ]
                },
                {
                    type: 'sub-block',
                    title: 'قواعد الرسائل',
                    content: 'حقيقة → اختبار → نتيجة → فائدة المدينة. نبرة محترمة. لا عار.'
                },
                {
                    type: 'badges',
                    content: ['جاهز للصحراء', 'مثبت في المختبر', '20% إعادة استثمار محلياً']
                },
                {
                    type: 'cta',
                    content: {
                        text: 'انضم إلى البناء الحقيقي',
                        href: '#page-6',
                        primary: true
                    }
                }
            ]
        },
        {
            id: 'page-2',
            title: 'إثبات القوة · Proof-SMASH™',
            kicker: 'الركيزة الثانية — الجودة',
            blocks: [
                {
                    type: 'lead',
                    content: 'الدفعات الرئيسية تمر باختبارات الإجهاد العامة في ظروف الخليج. الفيديوهات والبروتوكولات ترسل مع كل دفعة.'
                },
                {
                    type: 'cards',
                    content: [
                        {
                            icon: '🔥',
                            title: 'مقاومة الحرارة',
                            description: 'دورات حرارية عند 50 درجة مئوية'
                        },
                        {
                            icon: '🌪',
                            title: 'تآكل الرمال',
                            description: 'جهاز التآكل / تأثير الغبار'
                        },
                        {
                            icon: '🔨',
                            title: 'الصدمة',
                            description: 'سقوط/ضربة على الملفات والتثبيتات'
                        }
                    ]
                },
                {
                    type: 'specs',
                    content: [
                        'الكثافة ≈650–700 كجم/م³',
                        'الرطوبة (KD) 10–14%',
                        'الاستقرار انحناء منخفض/حبيبات ضيقة',
                        'الإنهاء حراري/زيت/مقاوم للحريق'
                    ]
                },
                {
                    type: 'cta',
                    content: [
                        {
                            text: 'افتح بروتوكول الاختبار',
                            href: '#',
                            secondary: true
                        },
                        {
                            text: 'اطلب دفعة SMASH',
                            href: '#',
                            primary: true
                        }
                    ]
                }
            ]
        },
        {
            id: 'page-3',
            title: 'ترقيات المجتمع — صندوق 20%',
            kicker: 'إعادة الاستثمار المحلي',
            blocks: [
                {
                    type: 'lead',
                    content: '20% من الأرباح يعاد استثمارها في ترقيات المدينة المرئية: المدارس، منحدرات المساجد، المناطق التجريبية.'
                },
                {
                    type: 'kpi-cards',
                    content: [
                        {
                            value: '2,847',
                            label: 'متر مربع محسن',
                            suffix: 'م²'
                        },
                        {
                            value: '12',
                            label: 'مواقع نشطة',
                            suffix: 'مواقع'
                        },
                        {
                            value: 'Q3',
                            label: 'دورة التقارير العامة',
                            suffix: '2025'
                        }
                    ]
                },
                {
                    type: 'cta',
                    content: [
                        {
                            text: 'رشح موقعاً',
                            href: '#',
                            secondary: true
                        },
                        {
                            text: 'تبرع/شارك',
                            href: '#',
                            primary: true
                        }
                    ]
                }
            ]
        },
        {
            id: 'page-4',
            title: 'دراسات الحالة',
            kicker: 'نتائج حقيقية',
            blocks: [
                {
                    type: 'lead',
                    content: 'أداء مثبت في ظروف الخليج عبر أنواع متعددة من المشاريع.'
                },
                {
                    type: 'case-studies',
                    content: [
                        {
                            title: 'الواجهة البحرية',
                            description: 'سطح اللارش استبدل المركب المتعفن. توفير 18% في التكلفة الإجمالية لمدة 10 سنوات.',
                            metrics: ['توفير 18% في التكلفة', 'ضمان 10 سنوات', 'صفر صيانة']
                        },
                        {
                            title: 'فيلا خاصة',
                            description: 'كسوة مقاومة للحرارة، صفر مطالبات صيانة في 24 شهراً.',
                            metrics: ['مقاومة 50 درجة مئوية', '24 شهراً', 'صفر مطالبات']
                        },
                        {
                            title: 'مدخل تجاري',
                            description: 'تآكل الرمال حُل بالدرجات المقواة من اللارش.',
                            metrics: ['مقاوم للرمال', 'حركة مرور عالية', 'متانة 5 سنوات']
                        }
                    ]
                },
                {
                    type: 'cta',
                    content: {
                        text: 'شاهد التقرير الكامل',
                        href: '#',
                        secondary: true
                    }
                }
            ]
        },
        {
            id: 'page-5',
            title: 'للمطورين وإدارة المرافق',
            kicker: 'الخدمات المهنية',
            blocks: [
                {
                    type: 'lead',
                    content: 'حلول شاملة للمهنيين في التطوير وإدارة المرافق.'
                },
                {
                    type: 'list',
                    content: [
                        'مطالبات صيانة أقل وعلاقات عامة أوضح',
                        'أرضيات / كسوة / ألواح / أنظمة واجهات',
                        'مساعدة التصميم، التركيب والضمان'
                    ]
                },
                {
                    type: 'services',
                    content: [
                        'استشارة التصميم',
                        'مواصفات المواد',
                        'دعم التركيب',
                        'تغطية الضمان',
                        'بروتوكولات الصيانة'
                    ]
                },
                {
                    type: 'cta',
                    content: {
                        text: 'احجز عرض خاص',
                        href: '#',
                        primary: true,
                        modal: 'demo'
                    }
                }
            ]
        },
        {
            id: 'page-6',
            title: 'انضم إلى الحركة',
            kicker: 'شارك',
            blocks: [
                {
                    type: 'lead',
                    content: 'كن جزءاً من مستقبل البناء الصادق في الخليج. دعنا نبني مدينة تدوم.'
                },
                {
                    type: 'form',
                    content: {
                        fields: [
                            { name: 'name', label: 'الاسم', type: 'text', required: true },
                            { name: 'email', label: 'البريد الإلكتروني', type: 'email', required: true },
                            { 
                                name: 'role', 
                                label: 'الدور', 
                                type: 'select', 
                                required: true,
                                options: [
                                    'عميل/مطور',
                                    'مهندس معماري',
                                    'متبرع/شريك'
                                ]
                            }
                        ],
                        checkbox: {
                            name: 'policy',
                            label: 'أوافق على سياسة الاحترام والامتثال',
                            required: true
                        },
                        submit: 'انضم إلى البناء الحقيقي'
                    }
                },
                {
                    type: 'policy-note',
                    content: 'الاحترام والامتثال — مواقع خاصة/تصاريح، صوت بناء، تقارير مفتوحة.'
                }
            ]
        }
    ]
};

const getPageById = (id, lang = 'en') => {
    return PAGES[lang]?.find(page => page.id === id) || PAGES[lang][0];
};

const getPageIndex = (id, lang = 'en') => {
    return PAGES[lang]?.findIndex(page => page.id === id) || 0;
};

const getNextPage = (id, lang = 'en') => {
    const index = getPageIndex(id, lang);
    return index < PAGES[lang].length - 1 ? PAGES[lang][index + 1] : null;
};

const getPrevPage = (id, lang = 'en') => {
    const index = getPageIndex(id, lang);
    return index > 0 ? PAGES[lang][index - 1] : null;
};
class LarchApp {
    constructor() {
        this.currentPage = 'page-0';
        this.currentLang = 'en';
        this.isAnimating = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
    
        const qb = document.getElementById('quickbar');
        if (qb) {
            qb.addEventListener('click', (e) => {
                const tgt = e.target.closest('a');
                if (!tgt) return;
                const type = tgt.classList.contains('qb-call') ? 'call' :
                             tgt.classList.contains('qb-wa') ? 'whatsapp' : 'spec_pdf';
                this.trackEvent('quickbar_click', { page: this.currentPage, language: this.currentLang, type });
            });
        }
    
        // Загружаем page-0 сразу
        const hash = window.location.hash || '#page-0';
        const pageId = hash.slice(1);
        const page = getPageById(pageId, this.currentLang);
        if (page) {
            this.currentPage = pageId;
            this.renderPage(page);
            this.updateNavigation();
        }
    
        this.hidePreloader();
    
        // Ждём появления smash-crew-link и убираем её, если не главная
        setTimeout(() => {
            const smashCrew = document.querySelector('.smash-crew-link');
            if (smashCrew) {
                if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
                    smashCrew.style.display = 'flex';
                } else {
                    smashCrew.remove();
                }
            }
        }, 50);
    }
    

    setupEventListeners() {
        // Language switcher
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchLanguage(e.target.dataset.lang));
        });

        // Navigation arrows
        document.querySelector('.nav-left').addEventListener('click', () => this.navigatePrev());
        document.querySelector('.nav-right').addEventListener('click', () => this.navigateNext());

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeydown(e));

        // Hash change
        window.addEventListener('hashchange', () => this.handleHashChange());

        // Modal close
        document.querySelector('.modal-close').addEventListener('click', () => this.closeModal());
        document.querySelector('.modal-overlay').addEventListener('click', () => this.closeModal());
    }

    handleInitialRoute() {
        const hash = window.location.hash || '#page-0';
        const pageId = hash.slice(1);
        const page = getPageById(pageId, this.currentLang);
        if (page) {
            this.currentPage = pageId; // явно установить
            this.renderPage(page);     // сразу отрисовать
            this.updateNavigation();   // обновить навигацию
        }
    }
    

    handleHashChange() {
        const hash = window.location.hash || '#page-0';
        this.navigateToPage(hash.slice(1));
    }

    async navigateToPage(pageId) {
        if (this.isAnimating || pageId === this.currentPage) return;

        this.isAnimating = true;
        const page = getPageById(pageId, this.currentLang);
        
        if (!page) {
            pageId = 'page-0';
            window.location.hash = '#page-0';
            return;
        }

        // Fade out current content
        await this.fadeOut();

        // Update current page
        this.currentPage = pageId;

        // Render new content
        this.renderPage(page);

        // Fade in new content
        await this.fadeIn();

        // Update navigation
        this.updateNavigation();

        // Update hash without triggering hashchange
        if (window.location.hash !== `#${pageId}`) {
            window.location.hash = `#${pageId}`;
        }

        this.isAnimating = false;
    }

    switchLanguage(lang) {
        if (lang === this.currentLang) return;
        
        this.currentLang = lang;
        
        // Update language switcher UI
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === lang);
        });
        
        // Update HTML lang attribute
        document.documentElement.lang = lang;
        
        // Update body direction for Arabic
        document.body.style.direction = lang === 'ar' ? 'rtl' : 'ltr';
        
        // Re-render current page in new language
        const currentPage = getPageById(this.currentPage, this.currentLang);
        if (currentPage) {
            this.renderPage(currentPage);
        }
    }

    async fadeOut() {
        const content = document.getElementById('page-content');
        content.classList.add('fade-exit');
        content.classList.add('fade-exit-active');
        
        return new Promise(resolve => {
            setTimeout(resolve, 350);
        });
    }

    async fadeIn() {
        const content = document.getElementById('page-content');
        content.classList.remove('fade-exit', 'fade-exit-active');
        content.classList.add('fade-enter');
        
        // Force reflow
        content.offsetHeight;
        
        content.classList.add('fade-enter-active');
        
        return new Promise(resolve => {
            setTimeout(resolve, 500);
        });
    }

    renderPage(page) {
        const container = document.getElementById('page-content');
        container.innerHTML = '';

        // Render page content based on blocks
        page.blocks.forEach(block => {
            const element = this.renderBlock(block);
            if (element) {
                container.appendChild(element);
            }
        });

        // Scroll to top
        window.scrollTo(0, 0);
    }

    renderBlock(block) {
        switch (block.type) {
            case 'logo':
                return this.renderLogo(block.content);
            case 'quotes':
                return this.renderQuotes(block.content);
            case 'contents-label':
                return this.renderContentsLabel(block.content);
            case 'contents-list':
                return this.renderContentsList(block.content);
            case 'lead':
                return this.renderLead(block.content);
            case 'list':
                return this.renderList(block.content);
            case 'cards':
                return this.renderCards(block.content);
            case 'specs':
                return this.renderSpecs(block.content);
            case 'kpi-cards':
                return this.renderKpiCards(block.content);
            case 'case-studies':
                return this.renderCaseStudies(block.content);
            case 'form':
                return this.renderForm(block.content);
            case 'cta':
                return this.renderCta(block.content);
            case 'badges':
                return this.renderBadges(block.content);
            case 'sub-block':
                return this.renderSubBlock(block);
            case 'catalog-download':
                return this.renderCatalogDownload(block.content);
            case 'policy-note':
                return this.renderPolicyNote(block.content);
            case 'footer':
                return this.renderFooter(block.content);
            default:
                return null;
        }
    }

    renderLogo(content) {
        const div = document.createElement('div');
        div.className = 'logo-container';
        div.innerHTML = `
            <img src="${content.src}" alt="${content.alt}" class="logo">
        `;
        return div;
    }

    renderQuotes(quotes) {
        const div = document.createElement('div');
        div.className = 'quotes';
        div.innerHTML = quotes.map(quote => `<p class="quote">${quote}</p>`).join('');
        return div;
    }

    renderContentsLabel(content) {
        const div = document.createElement('div');
        div.className = 'contents-label';
        div.textContent = content;
        return div;
    }

    renderContentsList(items) {
        const ul = document.createElement('ul');
        ul.className = 'contents-list';
        
        items.forEach(item => {
            const li = document.createElement('li');
            li.innerHTML = `
                <a href="${item.href}" class="content-link">
                    <strong>${item.title}</strong>
                    <span class="content-description">${item.description}</span>
                </a>
            `;
            
            li.addEventListener('click', (e) => {
                e.preventDefault();
                const pageId = item.href.slice(1);
                this.navigateToPage(pageId);
            });
            
            ul.appendChild(li);
        });
        
        return ul;
    }

    renderLead(content) {
        const p = document.createElement('p');
        p.className = 'lead';
        p.textContent = content;
        return p;
    }

    renderList(items) {
        const ul = document.createElement('ul');
        ul.className = 'content-list';
        
        items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            ul.appendChild(li);
        });
        
        return ul;
    }

    renderCards(cards) {
        const div = document.createElement('div');
        div.className = 'card-grid';
        
        cards.forEach(card => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'card';
            cardDiv.innerHTML = `
                <div class="card-icon">${card.icon}</div>
                <h3>${card.title}</h3>
                <p>${card.description}</p>
            `;
            div.appendChild(cardDiv);
        });
        
        return div;
    }

    renderSpecs(specs) {
        const div = document.createElement('div');
        div.className = 'specs-grid';
        
        specs.forEach(spec => {
            const specDiv = document.createElement('div');
            specDiv.className = 'spec-item';
            specDiv.textContent = spec;
            div.appendChild(specDiv);
        });
        
        return div;
    }

    renderKpiCards(kpis) {
        const div = document.createElement('div');
        div.className = 'kpi-grid';
        
        kpis.forEach(kpi => {
            const kpiDiv = document.createElement('div');
            kpiDiv.className = 'kpi-card';
            kpiDiv.innerHTML = `
                <div class="kpi-value">${kpi.value}</div>
                <div class="kpi-label">${kpi.label}</div>
                <div class="kpi-suffix">${kpi.suffix}</div>
            `;
            div.appendChild(kpiDiv);
        });
        
        return div;
    }

    renderCaseStudies(cases) {
        const div = document.createElement('div');
        div.className = 'case-studies';
        
        cases.forEach(caseStudy => {
            const caseDiv = document.createElement('div');
            caseDiv.className = 'case-study-card';
            caseDiv.innerHTML = `
                <h3>${caseStudy.title}</h3>
                <p>${caseStudy.description}</p>
                <div class="case-metrics">
                    ${caseStudy.metrics.map(metric => `<span class="metric">${metric}</span>`).join('')}
                </div>
            `;
            div.appendChild(caseDiv);
        });
        
        return div;
    }

    renderForm(formData) {
        const form = document.createElement('form');
        form.className = 'contact-form';
        
        formData.fields.forEach(field => {
            const group = document.createElement('div');
            group.className = 'form-group';
            
            const label = document.createElement('label');
            label.textContent = field.label;
            label.setAttribute('for', field.name);
            
            let input;
            if (field.type === 'select') {
                input = document.createElement('select');
                field.options.forEach(option => {
                    const optionEl = document.createElement('option');
                    optionEl.value = option;
                    optionEl.textContent = option;
                    input.appendChild(optionEl);
                });
            } else {
                input = document.createElement('input');
                input.type = field.type;
            }
            
            input.id = field.name;
            input.name = field.name;
            input.required = field.required;
            
            group.appendChild(label);
            group.appendChild(input);
            form.appendChild(group);
        });
        
        if (formData.checkbox) {
            const checkboxGroup = document.createElement('div');
            checkboxGroup.className = 'checkbox-group';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = formData.checkbox.name;
            checkbox.required = formData.checkbox.required;
            
            const checkboxLabel = document.createElement('label');
            checkboxLabel.textContent = formData.checkbox.label;
            checkboxLabel.setAttribute('for', formData.checkbox.name);
            
            checkboxGroup.appendChild(checkbox);
            checkboxGroup.appendChild(checkboxLabel);
            form.appendChild(checkboxGroup);
        }
        
        const submitBtn = document.createElement('button');
        submitBtn.type = 'submit';
        submitBtn.className = 'btn btn-primary';
        submitBtn.textContent = formData.submit;
        
        form.appendChild(submitBtn);
        
        form.addEventListener('submit', (e) => this.handleFormSubmit(e, formData));
        
        return form;
    }

    renderCta(ctaData) {
        const div = document.createElement('div');
        div.className = 'cta-container';
        
        if (Array.isArray(ctaData)) {
            ctaData.forEach(cta => {
                const btn = this.createCtaButton(cta);
                div.appendChild(btn);
            });
        } else {
            const btn = this.createCtaButton(ctaData);
            div.appendChild(btn);
        }
        
        return div;
    }

    createCtaButton(cta) {
        if (cta.modal) {
            const btn = document.createElement('button');
            btn.className = `btn ${cta.primary ? 'btn-primary' : 'btn-secondary'}`;
            btn.textContent = cta.text;
            btn.addEventListener('click', () => this.openModal(cta.modal));
            return btn;
        } else if (cta.href) {
            const btn = document.createElement('a');
            btn.className = `btn ${cta.primary ? 'btn-primary' : 'btn-secondary'}`;
            btn.href = cta.href;
            btn.textContent = cta.text;
            return btn;
        } else {
            const btn = document.createElement('button');
            btn.className = `btn ${cta.primary ? 'btn-primary' : 'btn-secondary'}`;
            btn.textContent = cta.text;
            return btn;
        }
    }

    renderBadges(badges) {
        const div = document.createElement('div');
        div.className = 'badges';
        
        badges.forEach(badge => {
            const span = document.createElement('span');
            span.className = 'badge';
            span.textContent = badge;
            div.appendChild(span);
        });
        
        return div;
    }

    renderSubBlock(block) {
        const div = document.createElement('div');
        div.className = 'sub-block';
        div.innerHTML = `
            <h3>${block.title}</h3>
            <p>${block.content}</p>
        `;
        return div;
    }

    renderCatalogDownload(content) {
        const div = document.createElement('div');
        div.className = 'catalog-download';
        
        const title = document.createElement('h3');
        title.textContent = content.title;
        
        const subtitle = document.createElement('p');
        subtitle.textContent = content.subtitle;
        subtitle.className = 'catalog-subtitle';
        
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'btn btn-primary catalog-btn';
        downloadBtn.textContent = content.button;
        downloadBtn.addEventListener('click', () => {
            this.downloadCatalog(content.file);
        });
        
        div.appendChild(title);
        div.appendChild(subtitle);
        div.appendChild(downloadBtn);
        
        return div;
    }

    downloadCatalog(filePath) {
        // Track download for analytics
        this.trackEvent('catalog_download', {
            page: this.currentPage,
            language: this.currentLang
        });
        
        // Create download link
        const link = document.createElement('a');
        link.href = filePath;
        link.download = 'LARCH-AE-Catalog.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Show success message
        this.showNotification('Catalog downloaded successfully!', 'success');
    }

    renderPolicyNote(content) {
        const div = document.createElement('div');
        div.className = 'policy-note';
        div.innerHTML = `<p>${content}</p>`;
        return div;
    }

    renderFooter(content) {
        const footer = document.createElement('footer');
        footer.className = 'footer';
        
        const footerContent = document.createElement('div');
        footerContent.className = 'footer-content';
        
        const copyright = document.createElement('span');
        copyright.textContent = content.copyright;
        
        const email = document.createElement('a');
        email.href = `mailto:${content.email}`;
        email.textContent = content.email;
        email.className = 'footer-email';
        
        const social = document.createElement('div');
        social.className = 'social-icons';
        
        content.social.forEach(platform => {
            const icon = document.createElement('div');
            icon.className = `social-icon social-${platform}`;
            icon.innerHTML = this.getSocialIcon(platform);
            social.appendChild(icon);
        });
        
        footerContent.appendChild(copyright);
        footerContent.appendChild(email);
        footerContent.appendChild(social);
        footer.appendChild(footerContent);
        
        return footer;
    }

    getSocialIcon(platform) {
        const icons = {
            twitter: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
            github: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>',
            instagram: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>'
        };
        return icons[platform] || '';
    }

    handleFormSubmit(e, formData) {
        e.preventDefault();
        
        // Basic validation
        const form = e.target;
        const formDataObj = new FormData(form);
        
        let isValid = true;
        formData.fields.forEach(field => {
            if (field.required) {
                const value = formDataObj.get(field.name);
                if (!value) {
                    isValid = false;
                }
            }
        });
        
        if (formData.checkbox && formData.checkbox.required) {
            const checkbox = form.querySelector(`#${formData.checkbox.name}`);
            if (!checkbox.checked) {
                isValid = false;
            }
        }
        
        if (isValid) {
            // Show success message
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Submitted!';
            submitBtn.disabled = true;
            
            setTimeout(() => {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                form.reset();
            }, 2000);
        }
    }

    navigatePrev() {
        const prevPage = getPrevPage(this.currentPage, this.currentLang);
        if (prevPage) {
            this.navigateToPage(prevPage.id);
        }
    }

    navigateNext() {
        const nextPage = getNextPage(this.currentPage, this.currentLang);
        if (nextPage) {
            this.navigateToPage(nextPage.id);
        }
    }

    handleKeydown(e) {
        switch (e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                this.navigatePrev();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.navigateNext();
                break;
            case 'Escape':
                e.preventDefault();
                this.navigateToPage('page-0');
                break;
        }
    }

    updateNavigation() {
        const prevPage = getPrevPage(this.currentPage, this.currentLang);
        const nextPage = getNextPage(this.currentPage, this.currentLang);
        
        const leftArrow = document.querySelector('.nav-left');
        const rightArrow = document.querySelector('.nav-right');
        
        leftArrow.classList.toggle('hidden', !prevPage);
        rightArrow.classList.toggle('hidden', !nextPage);
    }

    openModal(type) {
        const modal = document.getElementById('modal');
        const modalBody = modal.querySelector('.modal-body');
        
        if (type === 'demo') {
            modalBody.innerHTML = `
                <h2>Book a Private Demo</h2>
                <p>Schedule a personalized demonstration of our materials and testing protocols.</p>
                <form class="demo-form">
                    <div class="form-group">
                        <label for="demo-name">Name</label>
                        <input type="text" id="demo-name" name="name" required>
                    </div>
                    <div class="form-group">
                        <label for="demo-company">Company</label>
                        <input type="text" id="demo-company" name="company" required>
                    </div>
                    <div class="form-group">
                        <label for="demo-email">Email</label>
                        <input type="email" id="demo-email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="demo-date">Preferred Date</label>
                        <input type="date" id="demo-date" name="date" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Schedule Demo</button>
                </form>
            `;
            
            const form = modalBody.querySelector('form');
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                alert('Demo request submitted! We\'ll contact you soon.');
                this.closeModal();
            });
        }
        
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
    }

    closeModal() {
        const modal = document.getElementById('modal');
        modal.classList.remove('active');
        modal.setAttribute('aria-hidden', 'true');
    }

    trackEvent(eventName, data) {
        // Google Analytics 4
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, data);
        }
        
        // Facebook Pixel
        if (typeof fbq !== 'undefined') {
            fbq('track', eventName, data);
        }
        
        // Custom tracking
        console.log('Event tracked:', eventName, data);
        
        // Send to CRM/Email
        this.sendToCRM(eventName, data);
    }

    sendToCRM(eventName, data) {
        const crmData = {
            event: eventName,
            timestamp: new Date().toISOString(),
            page: data.page,
            language: data.language,
            userAgent: navigator.userAgent,
            referrer: document.referrer
        };

        // Send to your CRM endpoint
        fetch('https://your-crm-endpoint.com/api/events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(crmData)
        }).catch(error => {
            console.log('CRM tracking error:', error);
        });
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    hidePreloader() {
        // Wait for fonts to load
        document.fonts.ready.then(() => {
            setTimeout(() => {
                const preloader = document.getElementById('preloader');
                preloader.classList.add('hidden');
            }, 1000);
        });
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new LarchApp();
});
/* ===== MOBILE FAB (⋯) TOGGLE ===== */
(function attachFabToggle() {
  function ready(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn, { once: true });
    } else {
      fn();
    }
  }

  ready(function () {
    const fab = document.getElementById('fab');
    const menu = document.getElementById('fabMenu');
    if (!fab || !menu) return;

    const isOpen = () => fab.getAttribute('aria-expanded') === 'true';
    const toggle = (open) => {
      fab.setAttribute('aria-expanded', String(open));
      menu.classList.toggle('open', open);
      menu.setAttribute('aria-hidden', String(!open));
    };

    // Клик по FAB
    fab.addEventListener('click', () => toggle(!isOpen()));

    // Клик вне меню — закрыть
    document.addEventListener('click', (e) => {
      if (!isOpen()) return;
      const clickedFab = e.target === fab;
      const clickedInsideMenu = menu.contains(e.target);
      if (!clickedFab && !clickedInsideMenu) toggle(false);
    });

    // ESC — закрыть
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') toggle(false);
    });

    // Если у тебя есть свой роутер и он эмитит событие — закрываем меню на переход
    window.addEventListener('hashchange', () => toggle(false));
  });
})();

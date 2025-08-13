# LARCH.AE - True Build Movement Website

## 🚀 **Features**

- **Bilingual Support**: English & Arabic with RTL support
- **Single Page Application**: Smooth navigation between 7 pages
- **PDF Catalog Download**: Product catalog with tracking
- **CRM Integration**: Lead capture and analytics
- **Responsive Design**: Mobile-first approach
- **Modern UI**: ODEI-style minimalist design

## 📁 **Project Structure**

```
LARCH Odei/
├── assets/
│   ├── logo.png          # Company logo
│   ├── favicon.ico       # Browser favicon
│   ├── grain.png         # Texture overlay
│   ├── catalog.pdf       # Product catalog (create this)
│   └── divider.svg       # Decorative elements
├── index.html            # Main HTML file
├── styles.css            # All CSS styles
├── script.js             # Main JavaScript app
├── content.js            # Content data (bilingual)
└── README.md             # This file
```

## 🔧 **Setup Instructions**

### **1. Create Missing Assets**
- **`assets/catalog.pdf`**: Create product catalog with specifications
- **`assets/logo.png`**: Add your company logo
- **`assets/favicon.ico`**: Add browser favicon

### **2. CRM Integration Options**

#### **Option A: Email Integration (Simple)**
```javascript
// In script.js, replace the CRM endpoint with email service
sendToCRM(eventName, data) {
    const emailData = {
        to: 'sales@larch.ae',
        subject: `New Lead: ${eventName}`,
        body: JSON.stringify(data, null, 2)
    };
    
    // Use email service like EmailJS, Formspree, or your own endpoint
    fetch('https://your-email-service.com/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(emailData)
    });
}
```

#### **Option B: Popular CRM Platforms**

##### **HubSpot**
```javascript
// Add HubSpot tracking code to index.html
<script type="text/javascript" id="hs-script-loader" async defer src="//js.hs-scripts.com/YOUR_PORTAL_ID.js"></script>

// In script.js
trackEvent(eventName, data) {
    if (window.hbspt) {
        window.hbspt.forms.create({
            portalId: 'YOUR_PORTAL_ID',
            formId: 'YOUR_FORM_ID',
            target: '#hubspot-form'
        });
    }
}
```

##### **Salesforce**
```javascript
// Add Salesforce tracking
trackEvent(eventName, data) {
    if (window.sforce) {
        window.sforce.one.createRecord('Lead', {
            Company: 'LARCH.AE',
            Event__c: eventName,
            Description: JSON.stringify(data)
        });
    }
}
```

##### **Zoho CRM**
```javascript
// Zoho CRM integration
trackEvent(eventName, data) {
    fetch('https://www.zohoapis.com/crm/v2/Leads', {
        method: 'POST',
        headers: {
            'Authorization': 'Zoho-oauthtoken YOUR_TOKEN',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            data: [{
                Company: 'LARCH.AE',
                Event_Type: eventName,
                Description: JSON.stringify(data)
            }]
        })
    });
}
```

#### **Option C: Custom CRM Endpoint**
```javascript
// Replace with your CRM API endpoint
sendToCRM(eventName, data) {
    fetch('https://your-crm.com/api/leads', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer YOUR_API_KEY',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            event: eventName,
            timestamp: new Date().toISOString(),
            page: data.page,
            language: data.language,
            userAgent: navigator.userAgent,
            referrer: document.referrer
        })
    });
}
```

### **3. Analytics Integration**

#### **Google Analytics 4**
```html
<!-- Add to index.html head section -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

#### **Facebook Pixel**
```html
<!-- Add to index.html head section -->
<script>
  !function(f,b,e,v,n,t,s)
  {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', 'YOUR_PIXEL_ID');
  fbq('track', 'PageView');
</script>
```

### **4. Form Submission Handling**

#### **EmailJS (Recommended for simple setup)**
```html
<!-- Add to index.html head section -->
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/@emailjs/browser@3/dist/email.min.js"></script>
<script type="text/javascript">
  (function() {
    emailjs.init("YOUR_USER_ID");
  })();
</script>
```

```javascript
// In script.js, update form submission
handleFormSubmit(e, formData) {
    e.preventDefault();
    
    const form = e.target;
    const formDataObj = new FormData(form);
    
    // Send to EmailJS
    emailjs.send('YOUR_SERVICE_ID', 'YOUR_TEMPLATE_ID', {
        name: formDataObj.get('name'),
        email: formDataObj.get('email'),
        role: formDataObj.get('role'),
        page: this.currentPage,
        language: this.currentLang
    }).then(
        (response) => {
            this.showNotification('Form submitted successfully!', 'success');
            form.reset();
        },
        (error) => {
            this.showNotification('Error submitting form. Please try again.', 'error');
        }
    );
}
```

## 📊 **Tracking Events**

The website automatically tracks these events:

- **Page Views**: Each page navigation
- **Language Switches**: EN ↔ العربية
- **Catalog Downloads**: PDF catalog downloads
- **Form Submissions**: Contact form submissions
- **Button Clicks**: CTA button interactions

## 🎯 **Lead Capture Points**

1. **Catalog Download**: Tracks interest in products
2. **Contact Form**: Captures lead information
3. **Page Navigation**: Tracks user journey
4. **Language Preference**: Identifies market preference

## 🚀 **Deployment**

### **Local Development**
```bash
# Use Live Server extension in VS Code
# Or Python HTTP server
python -m http.server 8000
```

### **Production Deployment**
1. **Upload files** to your web hosting
2. **Update CRM endpoints** in `script.js`
3. **Add analytics codes** to `index.html`
4. **Test all functionality** on live site

## 📱 **Mobile Optimization**

- **Responsive design** for all screen sizes
- **Touch-friendly** navigation
- **Optimized performance** for mobile devices
- **RTL support** for Arabic mobile users

## 🔒 **Security Considerations**

- **HTTPS required** for production
- **API key protection** for CRM integration
- **Form validation** on both client and server
- **Rate limiting** for form submissions

## 📞 **Support**

For technical support or customization:
- **Email**: hello@larch.ae
- **Documentation**: This README file
- **Code Comments**: Inline documentation in all files

## 🎉 **Success Metrics**

Track these KPIs after deployment:
- **Catalog Downloads**: Product interest
- **Form Submissions**: Lead generation
- **Page Engagement**: User interaction
- **Language Usage**: Market preference
- **Mobile vs Desktop**: Device preference

---

**Built with ❤️ for LARCH.AE - The True Build Movement**

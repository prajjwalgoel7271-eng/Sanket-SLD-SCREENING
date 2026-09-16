// ── Sanket Multilingual Engine & Google Translate API Helper ────────────────
const langTagMap = {
    en:'en', hi:'hi', bn:'bn', mr:'mr', ta:'ta', te:'te',
    gu:'gu', kn:'kn', ml:'ml', pa:'pa', or:'or', ur:'ur', bho:'bho'
};

const langOptions = [
    { val: 'en', label: '🇬🇧 English',          flag: '🇬🇧' },
    { val: 'hi', label: '🇮🇳 हिन्दी (Hindi)',    flag: '🇮🇳' },
    { val: 'bn', label: '🇧🇩 বাংলা (Bengali)',  flag: '🇧🇩' },
    { val: 'mr', label: '🇮🇳 मराठी (Marathi)',  flag: '🇮🇳' },
    { val: 'ta', label: '🇮🇳 தமிழ் (Tamil)',    flag: '🇮🇳' },
    { val: 'te', label: '🇮🇳 తెలుగు (Telugu)',  flag: '🇮🇳' },
    { val: 'gu', label: '🇮🇳 ગુજરાતી (Gujarati)', flag: '🇮🇳' },
    { val: 'kn', label: '🇮🇳 ಕನ್ನಡ (Kannada)',  flag: '🇮🇳' },
    { val: 'ml', label: '🇮🇳 മലയാളം (Malayalam)', flag: '🇮🇳' },
    { val: 'pa', label: '🇮🇳 ਪੰਜਾਬੀ (Punjabi)', flag: '🇮🇳' },
    { val: 'or', label: '🇮🇳 ଓଡ଼ିଆ (Odia)',     flag: '🇮🇳' },
    { val: 'ur', label: '🇵🇰 اردو (Urdu)',       flag: '🇵🇰' },
    { val: 'bho', label: '🇮🇳 भोजपुरी (Bhojpuri)', flag: '🇮🇳' }
];

const translationCache = {};

window.translateTextWithGoogle = async function(text, targetLang) {
    if (!text || targetLang === 'en') return text;

    const cacheKey = `${targetLang}::${text.trim()}`;
    if (translationCache[cacheKey]) return translationCache[cacheKey];

    const gtLang = langTagMap[targetLang] || targetLang;

    // 1. Client-Side Google Translate Public Endpoint
    try {
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=${gtLang}&dt=t&q=${encodeURIComponent(text.trim())}`;
        const res = await fetch(url);
        if (res.ok) {
            const data = await res.json();
            if (data && data[0]) {
                const translated = data[0].map(part => part[0]).join('');
                if (translated) {
                    translationCache[cacheKey] = translated;
                    return translated;
                }
            }
        }
    } catch (e) {
        console.warn('Google client endpoint failed, trying backend server proxy...', e);
    }

    // 2. Server-side /api/translate proxy fallback
    try {
        const res = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text.trim(), target_lang: gtLang })
        });
        if (res.ok) {
            const data = await res.json();
            if (data.translated_text) {
                translationCache[cacheKey] = data.translated_text;
                return data.translated_text;
            }
        }
    } catch (e) {
        console.error('Server-side translate proxy failed:', e);
    }

    return text;
};

window.autoTranslatePageContent = async function(targetLang) {
    if (targetLang === 'en') return;
    const elements = document.querySelectorAll('[data-translatable]');
    for (const el of elements) {
        const originalText = el.getAttribute('data-original-text') || el.innerText.trim();
        if (!el.getAttribute('data-original-text')) {
            el.setAttribute('data-original-text', originalText);
        }
        if (originalText) {
            const translated = await window.translateTextWithGoogle(originalText, targetLang);
            if (translated && translated !== originalText) {
                el.innerText = translated;
            }
        }
    }
};

// Auto-initialize global language selector & dynamic page translation
document.addEventListener('DOMContentLoaded', () => {
    const globalLangSel = document.getElementById('global-lang-select');
    const intake = JSON.parse(localStorage.getItem('sld_intake') || '{}');
    const currentLang = intake.lang || 'en';

    if (globalLangSel) {
        globalLangSel.value = currentLang;

        globalLangSel.addEventListener('change', async (e) => {
            const newLang = e.target.value;
            intake.lang = newLang;
            localStorage.setItem('sld_intake', JSON.stringify(intake));
            
            // Translate dynamic page elements immediately
            await window.autoTranslatePageContent(newLang);
            
            // Refresh to load localized content banks if on tier pages
            if (window.location.pathname.includes('/test/sld')) {
                location.reload();
            }
        });
    }

    if (currentLang !== 'en') {
        window.autoTranslatePageContent(currentLang);
    }
});

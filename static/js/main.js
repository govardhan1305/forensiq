/* ============================================================
   ForensIQ — Main JavaScript
   ============================================================ */

'use strict';

// ── Language Toggle ─────────────────────────────────────────
const TRANSLATIONS = {
  hi: {
    'Start Analyzing':       'विश्लेषण शुरू करें',
    'View Dashboard':        'डैशबोर्ड देखें',
    'Evidence Locker':       'साक्ष्य लॉकर',
    'AI Assistant':          'AI सहायक',
    'Awareness':             'जागरूकता',
    'Analyze Message':       'संदेश विश्लेषण',
    'Check Link':            'लिंक जांचें',
    'Screenshot':            'स्क्रीनशॉट',
    'Job Detector':          'जॉब डिटेक्टर',
    'AI Chat':               'AI चैट',
    'Safety Tips':           'सुरक्षा टिप्स',
    'Analyse Message':       'संदेश विश्लेषण करें',
    'Check URL':             'URL जांचें',
    'Analyse Screenshot':    'स्क्रीनशॉट विश्लेषण करें',
    'Analyse Job Offer':     'नौकरी की पेशकश विश्लेषण करें',
    'Dashboard':             'डैशबोर्ड',
    'Analyze':               'विश्लेषण',
    'Total Cases':           'कुल मामले',
    'Scams Detected':        'धोखाधड़ी का पता चला',
    'Safe':                  'सुरक्षित',
    'Suspicious':            'संदिग्ध',
    'Recent Cases':          'हाल के मामले',
    'New Analysis':          'नया विश्लेषण',
    'Generate Complaint':    'शिकायत उत्पन्न करें',
    'View Evidence':         'साक्ष्य देखें',
  }
};

let currentLang = 'en';

function setLang(lang) {
  currentLang = lang;

  // Update button states
  document.getElementById('btn-en')?.classList.toggle('active', lang === 'en');
  document.getElementById('btn-hi')?.classList.toggle('active', lang === 'hi');

  if (lang === 'en') {
    // Restore originals
    document.querySelectorAll('[data-orig]').forEach(el => {
      el.textContent = el.dataset.orig;
      delete el.dataset.orig;
    });
    return;
  }

  const map = TRANSLATIONS[lang] || {};

  // Walk text nodes in buttons, nav-links, labels, headings
  document.querySelectorAll(
    '.btn-fiq-primary, .btn-hero-primary, .btn-hero-outline, .btn-sm-outline, ' +
    '.nav-link, .dropdown-item, .stat-label, .feature-title, .step-title, ' +
    '.page-title, .page-sub, .fiq-card-header, label, th, h1, h2, h4, h5, h6'
  ).forEach(el => {
    // Only translate leaf text
    const txt = el.childNodes;
    txt.forEach(node => {
      if (node.nodeType === Node.TEXT_NODE) {
        const trimmed = node.textContent.trim();
        if (map[trimmed]) {
          if (!el.dataset.orig) el.dataset.orig = node.textContent;
          node.textContent = node.textContent.replace(trimmed, map[trimmed]);
        }
      }
    });
  });
}


// ── Risk Bar Animation ──────────────────────────────────────
function animateRiskBars() {
  document.querySelectorAll('.risk-bar[data-risk]').forEach(el => {
    const risk = parseInt(el.dataset.risk, 10);
    el.style.background =
      risk >= 70 ? '#ff4d6d' :
      risk >= 40 ? '#ffca3a' :
                   '#00ff9f';
  });
}


// ── Copy to Clipboard Utility ───────────────────────────────
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Copied!';
    setTimeout(() => { btn.innerHTML = orig; }, 2000);
  }).catch(() => {
    // Fallback for older browsers
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity  = '0';
    document.body.appendChild(ta);
    ta.focus(); ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  });
}


// ── Toast Notification ──────────────────────────────────────
function showToast(message, type = 'info') {
  const colours = {
    info:    '#00e5ff',
    success: '#00ff9f',
    warning: '#ffd60a',
    danger:  '#ff4d6d',
  };
  const toast = document.createElement('div');
  toast.style.cssText = `
    position: fixed; bottom: 1.5rem; right: 1.5rem; z-index: 9999;
    background: #0d1120; border: 1px solid ${colours[type] || colours.info};
    border-left: 4px solid ${colours[type] || colours.info};
    color: #e2e8f0; border-radius: 8px; padding: .75rem 1.25rem;
    font-size: .85rem; max-width: 320px; box-shadow: 0 8px 32px rgba(0,0,0,.6);
    animation: slideInToast .3s ease;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity .3s';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Inject keyframe for toast
const toastStyle = document.createElement('style');
toastStyle.textContent = `
  @keyframes slideInToast {
    from { transform: translateX(100%); opacity: 0; }
    to   { transform: none; opacity: 1; }
  }
`;
document.head.appendChild(toastStyle);


// ── Auto-dismiss Alerts ──────────────────────────────────────
function initAlertAutoDismiss() {
  document.querySelectorAll('.fiq-alert').forEach(alert => {
    setTimeout(() => {
      alert.classList.remove('show');
      setTimeout(() => alert.remove(), 350);
    }, 5000);
  });
}


// ── Active Nav Link Highlighting ────────────────────────────
function highlightActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
}


// ── Character Counter for Textareas ─────────────────────────
function initCharCounters() {
  document.querySelectorAll('textarea[maxlength]').forEach(ta => {
    const counter = document.createElement('div');
    counter.style.cssText = 'text-align:right;font-size:.72rem;color:#64748b;margin-top:.2rem;';
    ta.after(counter);
    const update = () => {
      counter.textContent = `${ta.value.length} / ${ta.maxLength}`;
    };
    ta.addEventListener('input', update);
    update();
  });
}


// ── Smooth scroll for anchor links ──────────────────────────
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', e => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}


// ── Typing effect for hero title (landing page) ─────────────
function initTypingEffect() {
  const el = document.querySelector('.hero-badge');
  if (!el) return;
  const texts = [
    '🛡 AI-Powered Cyber Protection',
    '🔍 Detect Scams Instantly',
    '⚡ Real-Time Threat Analysis',
    '🔒 Protect Your Digital Life',
  ];
  let idx = 0;
  setInterval(() => {
    idx = (idx + 1) % texts.length;
    el.style.opacity = '0';
    setTimeout(() => {
      el.textContent = texts[idx];
      el.style.opacity = '1';
      el.style.transition = 'opacity .4s';
    }, 300);
  }, 3500);
}


// ── Ripple Effect on Buttons ─────────────────────────────────
function initRipple() {
  document.querySelectorAll('.btn-fiq-primary, .btn-hero-primary').forEach(btn => {
    btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.addEventListener('click', e => {
      const rect   = btn.getBoundingClientRect();
      const ripple = document.createElement('span');
      const size   = Math.max(rect.width, rect.height);
      ripple.style.cssText = `
        position:absolute; border-radius:50%;
        width:${size}px; height:${size}px;
        left:${e.clientX - rect.left - size/2}px;
        top:${e.clientY - rect.top - size/2}px;
        background:rgba(255,255,255,.25);
        transform:scale(0); animation:ripple .5s linear;
        pointer-events:none;
      `;
      btn.appendChild(ripple);
      setTimeout(() => ripple.remove(), 500);
    });
  });
  const s = document.createElement('style');
  s.textContent = '@keyframes ripple{to{transform:scale(2);opacity:0;}}';
  document.head.appendChild(s);
}


// ── Evidence search/filter (client-side) ────────────────────
function initEvidenceFilter() {
  const searchInput = document.getElementById('evidenceSearch');
  if (!searchInput) return;
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase();
    document.querySelectorAll('.evidence-card').forEach(card => {
      const text = card.textContent.toLowerCase();
      card.closest('.col-sm-6').style.display = text.includes(q) ? '' : 'none';
    });
  });
}


// ── Verdict colour map for dynamic elements ──────────────────
function colorVerdictElements() {
  const map = {
    SAFE:       '#00ff9f',
    SCAM:       '#ff4d6d',
    PHISHING:   '#ffd60a',
    FRAUD:      '#ff9f1c',
    SUSPICIOUS: '#c77dff',
  };
  document.querySelectorAll('[data-verdict]').forEach(el => {
    const v = el.dataset.verdict?.toUpperCase();
    if (map[v]) el.style.color = map[v];
  });
}


// ── Number count-up animation ────────────────────────────────
function countUp(el, target, duration = 1200) {
  const start     = 0;
  const startTime = performance.now();
  const update = (now) => {
    const elapsed  = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const value    = Math.floor(progress * target);
    el.textContent = value;
    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = target;
  };
  requestAnimationFrame(update);
}

function initCountUp() {
  document.querySelectorAll('.stat-val').forEach(el => {
    const val = parseInt(el.textContent, 10);
    if (!isNaN(val) && val > 0) {
      el.textContent = '0';
      const obs = new IntersectionObserver(entries => {
        if (entries[0].isIntersecting) {
          countUp(el, val);
          obs.disconnect();
        }
      });
      obs.observe(el);
    }
  });
  // Hero stats
  document.querySelectorAll('.hstat-num').forEach(el => {
    const val = parseInt(el.textContent, 10);
    if (!isNaN(val) && val > 0) {
      el.textContent = '0';
      const obs = new IntersectionObserver(entries => {
        if (entries[0].isIntersecting) {
          countUp(el, val);
          obs.disconnect();
        }
      });
      obs.observe(el);
    }
  });
}


// ── Feature card stagger animation ──────────────────────────
function initCardStagger() {
  const cards = document.querySelectorAll('.feature-card, .stat-card, .evidence-card');
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        const delay = (Array.from(cards).indexOf(entry.target)) * 60;
        entry.target.style.transition = `opacity .4s ${delay}ms, transform .4s ${delay}ms`;
        entry.target.style.opacity    = '1';
        entry.target.style.transform  = 'translateY(0)';
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  cards.forEach(card => {
    card.style.opacity   = '0';
    card.style.transform = 'translateY(20px)';
    obs.observe(card);
  });
}


// ── Confirm delete ───────────────────────────────────────────
function confirmDelete(evId) {
  return confirm(`Delete evidence ${evId}? This action cannot be undone.`);
}


// ── Voice Input Language Support ─────────────────────────────
const VOICE_LANGUAGES = [
  { code: 'en-US', label: 'English' },
  { code: 'hi-IN', label: 'हिंदी (Hindi)' },
  { code: 'ta-IN', label: 'தமிழ் (Tamil)' },
  { code: 'te-IN', label: 'తెలుగు (Telugu)' },
  { code: 'kn-IN', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'ml-IN', label: 'മലയാളം (Malayalam)' },
  { code: 'bn-IN', label: 'বাংলা (Bengali)' },
  { code: 'mr-IN', label: 'मराठी (Marathi)' },
  { code: 'gu-IN', label: 'ગુજરાતી (Gujarati)' },
  { code: 'pa-IN', label: 'ਪੰਜਾਬੀ (Punjabi)' },
  { code: 'ur-PK', label: 'اردو (Urdu)' },
  { code: 'ar-SA', label: 'العربية (Arabic)' },
  { code: 'fr-FR', label: 'Français (French)' },
  { code: 'de-DE', label: 'Deutsch (German)' },
  { code: 'es-ES', label: 'Español (Spanish)' },
  { code: 'pt-BR', label: 'Português (Portuguese)' },
  { code: 'zh-CN', label: '中文 (Chinese)' },
  { code: 'ja-JP', label: '日本語 (Japanese)' },
  { code: 'ko-KR', label: '한국어 (Korean)' },
  { code: 'ru-RU', label: 'Русский (Russian)' },
];

function getSelectedVoiceLang() {
  const sel = document.getElementById('voiceLangSelect');
  return sel ? sel.value : 'en-US';
}

function initVoiceLangDropdown() {
  const container = document.getElementById('voiceLangContainer');
  if (!container) return;

  const select = document.createElement('select');
  select.id = 'voiceLangSelect';
  select.style.cssText = `
    background: var(--bg-card2);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    border-radius: var(--radius-sm);
    font-size: .8rem;
    padding: .3rem .6rem;
    cursor: pointer;
    margin-top: .5rem;
    width: 100%;
  `;

  VOICE_LANGUAGES.forEach(lang => {
    const opt = document.createElement('option');
    opt.value = lang.code;
    opt.textContent = lang.label;
    select.appendChild(opt);
  });

  container.appendChild(select);
}

function startVoiceInput(textareaId) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showToast('Voice input not supported in this browser.', 'danger');
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = getSelectedVoiceLang();
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.start();

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    const ta = document.getElementById(textareaId);
    if (ta) {
      ta.value += (ta.value ? ' ' : '') + transcript;
      ta.dispatchEvent(new Event('input'));
    }
    showToast('Voice input captured!', 'success');
  };

  recognition.onerror = (event) => {
    showToast('Voice error: ' + event.error, 'danger');
  };
}


// ── Initialise on DOM ready ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  animateRiskBars();
  initAlertAutoDismiss();
  highlightActiveNav();
  initCharCounters();
  initSmoothScroll();
  initTypingEffect();
  initRipple();
  initEvidenceFilter();
  colorVerdictElements();
  initCountUp();
  initCardStagger();
  initVoiceLangDropdown();
});

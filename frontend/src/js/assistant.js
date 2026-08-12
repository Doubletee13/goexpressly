/**
 * GoExpressly AI Virtual Assistant Widget
 * Enterprise-grade floating assistant with real-time tracking lookup,
 * logistics knowledge base, and human support escalation to support@goexpressly.com
 */

(function () {
  'use strict';

  // Prevent multiple initializations
  if (window.GoExpresslyAssistant) return;

  const STORAGE_KEY = 'goexpressly_chat_history';
  const API_BASE = '/api/v1';
  const SUPPORT_EMAIL = 'support@goexpressly.com';

  // Knowledge base intent matchers
  const KNOWLEDGE_BASE = [
    {
      keywords: ['hello', 'hi', 'hey', 'start', 'greeting', 'good morning', 'good afternoon'],
      answer: "Hello! I am the **GoExpressly Virtual Assistant**. How can I help you today? You can enter a tracking ID (e.g. `GX-VSVMCTRXU8`), ask about our shipping services, or request human support."
    },
    {
      keywords: ['track', 'where is my package', 'status', 'locate', 'parcel', 'shipment'],
      answer: "To track your package, simply type your tracking ID here (format: `GX-XXXXXXXXXX`) or click the **🔍 Track Package** button below!"
    },
    {
      keywords: ['customs', 'held', 'clearance', 'border', 'duty', 'tax', 'inspection', 'delay'],
      answer: "When a shipment shows **'Customs Clearance'**, it means your package has arrived at an international border facility (e.g., USPS International Mail Facility) for routine inspection. You can view the exact facility name and address directly on our map."
    },
    {
      keywords: ['service', 'services', 'air', 'ocean', 'land', 'freight', 'warehouse', 'express', 'shipping options'],
      answer: "GoExpressly offers 5 core logistics verticals:\n• **✈️ Air Freight** (24-48 hr express delivery)\n• **🚢 Ocean Freight** (Full/Partial container)\n• **🚚 Land Cargo** (Interstate haulage)\n• **🏭 Warehousing** (Bonded storage)\n• **⚡ Express Courier** (Door-to-door)\n\nVisit our [Services Page](services.html) for detailed specifications!"
    },
    {
      keywords: ['location', 'address', 'office', 'headquarters', 'where are you', 'irving', 'texas', 'phone', 'contact'],
      answer: "Our global headquarters and logistics hub is located at:\n📍 **GoExpressly Logistics Center**\n600 E Las Colinas Blvd, Suite 1200\nIrving, Texas 75039, USA\n\n📧 Email: **support@goexpressly.com**\n📞 Phone: **+1 (800) 555-0199** (24/7 Desk)"
    },
    {
      keywords: ['format', 'tracking number', 'tracking id', 'gx-'],
      answer: "GoExpressly tracking numbers always start with **`GX-`** followed by 10 alphanumeric characters (e.g. `GX-VSVMCTRXU8`). You can find this code in your booking confirmation email."
    },
    {
      keywords: ['faq', 'questions', 'help', 'pricing', 'rate', 'quote'],
      answer: "For common questions, visit our [FAQ Page](faq.html). For volume quotes, feel free to submit a message on our [Contact Page](contact.html) or email us directly!"
    }
  ];

  class Assistant {
    constructor() {
      this.isOpen = false;
      this.history = this.loadHistory();
      this.initUI();
      this.bindEvents();
      if (this.history.length === 0) {
        this.addBotMessage("👋 **Welcome to GoExpressly!** How can I assist with your shipment today?", [
          { label: '🔍 Track Package', action: 'track_prompt' },
          { label: '🛃 Customs Hold Help', action: 'customs_help' },
          { label: '✈️ Services & Rates', action: 'services_info' },
          { label: '👤 Speak with Support', action: 'human_support' }
        ]);
      } else {
        this.renderHistory();
      }
    }

    loadHistory() {
      try {
        const saved = sessionStorage.getItem(STORAGE_KEY);
        return saved ? JSON.parse(saved) : [];
      } catch (e) {
        return [];
      }
    }

    saveHistory() {
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(this.history.slice(-20)));
      } catch (e) { }
    }

    initUI() {
      const container = document.createElement('div');
      container.id = 'goexpressly-assistant-root';
      container.innerHTML = `
        <!-- Floating Launcher Button -->
        <div id="assistant-launcher-wrapper" class="fixed bottom-6 right-6 z-50 flex items-center gap-3">
          <!-- Unread Hint Tooltip -->
          <div id="assistant-tooltip" class="hidden sm:flex items-center gap-2 bg-slate-900/90 text-white text-xs font-semibold px-3.5 py-2 rounded-xl backdrop-blur-md border border-white/10 shadow-xl animate-bounce-slow">
            <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
            Virtual Assistant Online
          </div>
          
          <button id="assistant-toggle-btn" aria-label="Open GoExpressly AI Assistant" class="relative w-14 h-14 rounded-full bg-brand-500 hover:bg-brand-600 text-white shadow-2xl flex items-center justify-center transition-transform hover:scale-105 active:scale-95 focus:outline-none">
            <span class="absolute -top-1 -right-1 w-4 h-4 bg-emerald-400 border-2 border-white rounded-full"></span>
            <!-- Bot Icon -->
            <svg id="assistant-icon-bot" class="w-7 h-7" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
            </svg>
            <!-- Close Icon -->
            <svg id="assistant-icon-close" class="w-7 h-7 hidden" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <!-- Glassmorphic Chat Window -->
        <div id="assistant-modal" class="fixed bottom-24 right-4 sm:right-6 z-50 w-[calc(100vw-2rem)] sm:w-[420px] h-[560px] max-h-[calc(100vh-8rem)] rounded-2xl bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-white/20 dark:border-white/10 shadow-2xl flex flex-col overflow-hidden transition-all duration-300 transform opacity-0 scale-95 pointer-events-none">
          
          <!-- Header -->
          <div class="px-5 py-4 bg-gradient-to-r from-brand-600 to-brand-500 text-white flex items-center justify-between shrink-0 shadow-md">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center font-bold text-lg">🤖</div>
              <div>
                <h3 class="font-bold text-sm leading-snug">GoExpressly Virtual Assistant</h3>
                <p class="text-[11px] text-white/80 flex items-center gap-1.5">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-300"></span>
                  Real-time Tracking & Support
                </p>
              </div>
            </div>
            <div class="flex items-center gap-1">
              <button id="assistant-reset-btn" title="Clear Chat" class="p-1.5 rounded-lg hover:bg-white/15 text-white/80 hover:text-white transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
              </button>
              <button id="assistant-close-btn" aria-label="Close assistant" class="p-1.5 rounded-lg hover:bg-white/15 text-white/80 hover:text-white transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>
          </div>

          <!-- Chat Stream -->
          <div id="assistant-stream" class="flex-1 p-4 overflow-y-auto space-y-4 text-sm scroll-smooth">
            <!-- Messages render here -->
          </div>

          <!-- Typing Indicator -->
          <div id="assistant-typing" class="hidden px-5 py-2 text-xs text-slate-400 dark:text-slate-500 flex items-center gap-2 border-t border-slate-100 dark:border-slate-800">
            <span class="flex gap-1">
              <span class="w-1.5 h-1.5 bg-brand-500 rounded-full animate-pulse"></span>
              <span class="w-1.5 h-1.5 bg-brand-500 rounded-full animate-pulse delay-100"></span>
              <span class="w-1.5 h-1.5 bg-brand-500 rounded-full animate-pulse delay-200"></span>
            </span>
            <span>GoExpressly Assistant is thinking...</span>
          </div>

          <!-- Footer Input -->
          <form id="assistant-form" class="p-3 bg-slate-50/80 dark:bg-slate-900/80 border-t border-slate-200/60 dark:border-slate-800 flex items-center gap-2 shrink-0">
            <input id="assistant-input" type="text" placeholder="Type a message or tracking ID..." autocomplete="off" class="flex-1 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 text-sm px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 focus:outline-none focus:border-brand-500 dark:focus:border-brand-400 transition-colors" />
            <button type="submit" class="w-10 h-10 rounded-xl bg-brand-500 hover:bg-brand-600 text-white flex items-center justify-center shrink-0 transition-all hover:scale-105 active:scale-95">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
            </button>
          </form>

        </div>
      `;
      document.body.appendChild(container);

      // Cache DOM references
      this.modal = document.getElementById('assistant-modal');
      this.toggleBtn = document.getElementById('assistant-toggle-btn');
      this.iconBot = document.getElementById('assistant-icon-bot');
      this.iconClose = document.getElementById('assistant-icon-close');
      this.stream = document.getElementById('assistant-stream');
      this.form = document.getElementById('assistant-form');
      this.input = document.getElementById('assistant-input');
      this.typing = document.getElementById('assistant-typing');
      this.tooltip = document.getElementById('assistant-tooltip');
    }

    bindEvents() {
      this.toggleBtn.addEventListener('click', () => this.toggleModal());
      document.getElementById('assistant-close-btn').addEventListener('click', () => this.toggleModal(false));
      document.getElementById('assistant-reset-btn').addEventListener('click', () => {
        this.history = [];
        this.saveHistory();
        this.stream.innerHTML = '';
        this.addBotMessage("Chat cleared! How can I help you today?", [
          { label: '🔍 Track Package', action: 'track_prompt' },
          { label: '🛃 Customs Hold Help', action: 'customs_help' },
          { label: '✈️ Services & Rates', action: 'services_info' },
          { label: '👤 Speak with Support', action: 'human_support' }
        ]);
      });

      this.form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = this.input.value.trim();
        if (!text) return;
        this.input.value = '';
        this.handleUserMessage(text);
      });
    }

    toggleModal(force) {
      this.isOpen = force !== undefined ? force : !this.isOpen;
      if (this.isOpen) {
        this.modal.classList.remove('opacity-0', 'scale-95', 'pointer-events-none');
        this.modal.classList.add('opacity-100', 'scale-100', 'pointer-events-auto');
        this.iconBot.classList.add('hidden');
        this.iconClose.classList.remove('hidden');
        if (this.tooltip) this.tooltip.classList.add('hidden');
        this.input.focus();
        this.scrollToBottom();
      } else {
        this.modal.classList.remove('opacity-100', 'scale-100', 'pointer-events-auto');
        this.modal.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
        this.iconBot.classList.remove('hidden');
        this.iconClose.classList.add('hidden');
      }
    }

    scrollToBottom() {
      setTimeout(() => {
        this.stream.scrollTop = this.stream.scrollHeight;
      }, 50);
    }

    renderHistory() {
      this.stream.innerHTML = '';
      this.history.forEach(item => {
        if (item.sender === 'user') {
          this.renderUserBubble(item.text);
        } else {
          this.renderBotBubble(item.text, item.pills, item.card);
        }
      });
      this.scrollToBottom();
    }

    addUserMessage(text) {
      this.history.push({ sender: 'user', text });
      this.saveHistory();
      this.renderUserBubble(text);
      this.scrollToBottom();
    }

    addBotMessage(text, pills = null, card = null) {
      this.history.push({ sender: 'bot', text, pills, card });
      this.saveHistory();
      this.renderBotBubble(text, pills, card);
      this.scrollToBottom();
    }

    renderUserBubble(text) {
      const bubble = document.createElement('div');
      bubble.className = 'flex justify-end';
      bubble.innerHTML = `
        <div class="max-w-[82%] bg-brand-500 text-white px-4 py-2.5 rounded-2xl rounded-tr-none shadow-sm text-sm leading-relaxed">
          ${this.escapeHTML(text)}
        </div>
      `;
      this.stream.appendChild(bubble);
    }

    renderBotBubble(text, pills = null, card = null) {
      const container = document.createElement('div');
      container.className = 'flex flex-col gap-2 items-start';

      let cardHTML = '';
      if (card && card.type === 'tracking') {
        const t = card.data;
        const statusColors = {
          'Delivered': 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
          'In Transit': 'bg-brand-500/15 text-brand-600 dark:text-brand-400 border-brand-500/30',
          'Customs Clearance': 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30',
          'Picked Up': 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30'
        };
        const statusVal = t.status || t.current_status || 'Active';
        const badgeClass = statusColors[statusVal] || 'bg-brand-500/15 text-brand-600 dark:text-brand-400 border-brand-500/30';
        const displayLocation = t.current_location || t.display_name || t.formatted_address || t.origin || 'Package Location Active';

        cardHTML = `
          <div class="mt-2.5 p-3.5 rounded-2xl bg-slate-100/90 dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700/80 w-full text-xs space-y-3 shadow-md">
            <!-- Visual Snippet Image Card Header -->
            <div class="relative w-full rounded-xl overflow-hidden bg-gradient-to-r from-brand-600 via-sky-600 to-indigo-600 p-3.5 text-white shadow-inner">
              <div class="flex items-center justify-between mb-2">
                <span class="text-[10px] font-bold tracking-wider uppercase bg-white/20 backdrop-blur-md px-2 py-0.5 rounded-full">Package Snippet</span>
                <span class="text-xs font-mono font-extrabold bg-black/30 px-2.5 py-0.5 rounded-md border border-white/20">${t.tracking_id}</span>
              </div>
              <div class="flex items-end justify-between gap-2">
                <div>
                  <div class="text-[10px] text-sky-100 uppercase tracking-wide font-medium">Route Path</div>
                  <div class="text-xs font-bold truncate max-w-[150px]">${this.escapeHTML(t.origin || 'Origin')} ➔ ${this.escapeHTML(t.destination || 'Destination')}</div>
                </div>
                <div class="text-right">
                  <div class="text-[10px] text-sky-100 uppercase tracking-wide font-medium">Current Location</div>
                  <div class="text-xs font-bold truncate max-w-[130px]">📍 ${this.escapeHTML(displayLocation)}</div>
                </div>
              </div>
              <div class="absolute -right-4 -bottom-4 w-16 h-16 bg-white/10 rounded-full blur-xs pointer-events-none"></div>
            </div>

            <!-- Detailed Grid Info -->
            <div class="space-y-1.5 pt-0.5">
              <div class="flex items-center justify-between">
                <span class="text-slate-500 dark:text-slate-400 font-medium">Current Status:</span>
                <span class="px-2 py-0.5 rounded-full border text-[11px] font-bold ${badgeClass}">${this.escapeHTML(statusVal)}</span>
              </div>
              ${t.recipient_name ? `<div class="flex items-center justify-between text-slate-700 dark:text-slate-200">
                <span class="text-slate-500 dark:text-slate-400 font-medium">Recipient:</span>
                <span class="font-semibold">${this.escapeHTML(t.recipient_name)}</span>
              </div>` : ''}
              ${t.carrier ? `<div class="flex items-center justify-between text-slate-700 dark:text-slate-200">
                <span class="text-slate-500 dark:text-slate-400 font-medium">Carrier:</span>
                <span class="font-semibold">${this.escapeHTML(t.carrier)}</span>
              </div>` : ''}
              ${t.estimated_delivery_date ? `<div class="flex items-center justify-between text-slate-700 dark:text-slate-200">
                <span class="text-slate-500 dark:text-slate-400 font-medium">Est. Delivery:</span>
                <span class="font-semibold text-brand-500 dark:text-brand-400">${new Date(t.estimated_delivery_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
              </div>` : ''}
            </div>

            <div class="pt-2 border-t border-slate-200 dark:border-slate-700/60 flex justify-between items-center">
              <a href="/track?id=${encodeURIComponent(t.tracking_id)}" class="text-brand-500 dark:text-brand-400 font-bold hover:underline flex items-center gap-1.5">
                Full Details & Map Pin →
              </a>
            </div>
          </div>
        `;
      } else if (card && card.type === 'human_escalation') {
        const trackingId = card.tracking_id || '';
        const mailSubject = encodeURIComponent(`[GoExpressly Support] Inquiry regarding ${trackingId || 'Package Status'}`);
        const mailBody = encodeURIComponent(
          `Hello GoExpressly Support Team,\n\nI need assistance with my shipment.\n` +
          (trackingId ? `Tracking ID: ${trackingId}\n` : '') +
          `Office: Irving, Texas Hub\n\nPlease follow up with me regarding my inquiry.\n\nThank you!`
        );
        const mailtoUrl = `mailto:${SUPPORT_EMAIL}?subject=${mailSubject}&body=${mailBody}`;
        const contactUrl = trackingId ? `/contact?tracking_id=${encodeURIComponent(trackingId)}` : `/contact`;

        cardHTML = `
          <div class="mt-2 p-4 rounded-xl bg-amber-500/10 dark:bg-amber-500/15 border border-amber-500/30 w-full text-xs space-y-3">
            <div class="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-bold">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/></svg>
              Escalate to Human Agent
            </div>
            <p class="text-slate-600 dark:text-slate-300 leading-relaxed">
              Our 24/7 support team in <strong>Irving, Texas</strong> is ready to assist you directly.
            </p>
            <div class="flex flex-col gap-2 pt-1">
              <a href="${mailtoUrl}" target="_blank" class="w-full py-2 px-3 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold text-center transition-colors flex items-center justify-center gap-2">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 8l7.89 5.26a2 2 0 0 0 2.22 0L21 8M5 19h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2z"/></svg>
                Email support@goexpressly.com
              </a>
              <a href="${contactUrl}" class="w-full py-2 px-3 rounded-lg bg-white/50 dark:bg-slate-800/80 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-center border border-slate-300 dark:border-slate-600 transition-colors">
                Open Contact Desk Form
              </a>
            </div>
          </div>
        `;
      }

      let pillsHTML = '';
      if (pills && pills.length > 0) {
        pillsHTML = `
          <div class="flex flex-wrap gap-1.5 mt-2">
            ${pills.map(p => `
              <button class="assistant-pill bg-slate-100 dark:bg-slate-800 hover:bg-brand-500 hover:text-white dark:hover:bg-brand-500 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 px-3 py-1 rounded-full text-xs font-semibold transition-all" data-action="${p.action}">
                ${this.escapeHTML(p.label)}
              </button>
            `).join('')}
          </div>
        `;
      }

      const bubble = document.createElement('div');
      bubble.className = 'flex gap-2 max-w-[90%] items-start';
      bubble.innerHTML = `
        <div class="w-7 h-7 rounded-xl bg-brand-500/20 text-brand-500 dark:text-brand-400 font-bold flex items-center justify-center shrink-0 text-xs mt-0.5">🤖</div>
        <div class="flex-1">
          <div class="bg-slate-100 dark:bg-slate-800/90 text-slate-800 dark:text-slate-100 px-4 py-2.5 rounded-2xl rounded-tl-none border border-slate-200/50 dark:border-slate-700/50 text-sm leading-relaxed">
            ${this.parseMarkdown(text)}
            ${cardHTML}
          </div>
          ${pillsHTML}
        </div>
      `;

      // Attach pill click events
      bubble.querySelectorAll('.assistant-pill').forEach(btn => {
        btn.addEventListener('click', () => {
          const action = btn.dataset.action;
          const label = btn.textContent.trim();
          this.handlePillAction(action, label);
        });
      });

      this.stream.appendChild(bubble);
    }

    showTyping(show = true) {
      if (show) {
        this.typing.classList.remove('hidden');
        this.typing.classList.add('flex');
      } else {
        this.typing.classList.add('hidden');
        this.typing.classList.remove('flex');
      }
      this.scrollToBottom();
    }

    async handleUserMessage(text) {
      this.addUserMessage(text);
      this.showTyping(true);

      // Check if text contains a tracking ID pattern (GX-XXXXXXXXXX or similar code)
      const trackingMatch = text.match(/\b(GX-[A-Za-z0-9]{8,12})\b/i) || text.match(/\b([A-Za-z0-9]{10,12})\b/i);

      setTimeout(async () => {
        if (trackingMatch) {
          const id = trackingMatch[0].toUpperCase();
          await this.lookupTracking(id);
        } else {
          this.processKnowledgeBase(text);
        }
        this.showTyping(false);
      }, 600);
    }

    async lookupTracking(trackingId) {
      try {
        let data = null;
        if (typeof Api !== 'undefined' && Api.trackPackage) {
          try {
            data = await Api.trackPackage(trackingId);
          } catch (e) {
            data = null;
          }
        }

        if (!data) {
          const host = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
            ? 'http://localhost:8000'
            : 'https://goexpressly.onrender.com';
          const res = await fetch(`${host}/api/track/${encodeURIComponent(trackingId)}`);
          if (res.ok) data = await res.json();
        }

        if (data && data.tracking_id) {
          const status = data.current_status || (data.is_delivered ? 'Delivered' : 'In Transit');
          this.addBotMessage(
            `I retrieved live tracking data for **${trackingId}**:`,
            [
              { label: '📍 View Map & Full Timeline', action: `track_view:${trackingId}` },
              { label: '👤 Speak with Support', action: 'human_support' }
            ],
            { type: 'tracking', data: { ...data, status } }
          );
        } else {
          this.addBotMessage(
            `We searched our system but could not locate tracking ID **${trackingId}**.\n\n` +
            `💡 **Helpful Hint:** GoExpressly tracking numbers are formatted starting with \`GX-\` (for example: \`GX-VSVMCTRXU8\`). Please verify your tracking number for any typos.`,
            [
              { label: '🔍 Try Another ID', action: 'track_prompt' },
              { label: '👤 Contact Support Desk', action: 'human_support' }
            ]
          );
        }
      } catch (err) {
        this.addBotMessage(
          `Unable to connect to live tracking service at this moment. Our team in Irving, Texas is standing by to help!`,
          [{ label: '👤 Contact Human Support', action: 'human_support' }]
        );
      }
    }

    processKnowledgeBase(query) {
      const lower = query.toLowerCase();

      // Human support request
      if (lower.includes('human') || lower.includes('support') || lower.includes('speak') || lower.includes('agent') || lower.includes('person') || lower.includes('call')) {
        this.addBotMessage(
          "I can connect you directly with our 24/7 human support team in Irving, Texas. Click below to open an email draft or submit a contact ticket:",
          null,
          { type: 'human_escalation', tracking_id: null }
        );
        return;
      }

      // Match knowledge base
      for (const item of KNOWLEDGE_BASE) {
        if (item.keywords.some(k => lower.includes(k))) {
          this.addBotMessage(item.answer, [
            { label: '🔍 Track Package', action: 'track_prompt' },
            { label: '👤 Talk to Support', action: 'human_support' }
          ]);
          return;
        }
      }

      // Default fallback
      this.addBotMessage(
        "I'm here to help with package tracking, customs inquiries, shipping services, or general support. What would you like to do?",
        [
          { label: '🔍 Track Package', action: 'track_prompt' },
          { label: '✈️ View Services', action: 'services_info' },
          { label: '❓ Read FAQs', action: 'faq_info' },
          { label: '👤 Speak to Support', action: 'human_support' }
        ]
      );
    }

    handlePillAction(action, label) {
      this.addUserMessage(label);
      this.showTyping(true);

      setTimeout(() => {
        this.showTyping(false);
        if (action.startsWith('track_view:')) {
          const id = action.split(':')[1];
          window.location.href = `/track?id=${encodeURIComponent(id)}`;
          return;
        }
        switch (action) {
          case 'track_prompt':
            this.addBotMessage("Please enter your tracking ID below (e.g. `GX-VSVMCTRXU8`):");
            break;
          case 'customs_help':
            this.addBotMessage(
              "When a package status reads **'Customs Clearance'**, it means your shipment is being processed by international border customs. Our map displays the exact facility building name and address.\n\nNeed help clearing a held parcel?",
              [{ label: '👤 Contact Customs Support', action: 'human_support' }]
            );
            break;
          case 'services_info':
            this.addBotMessage(
              "GoExpressly provides **Air Freight**, **Ocean Freight**, **Land Cargo**, **Warehousing**, and **Express Courier**. Learn more on our [Services Page](services.html)!"
            );
            break;
          case 'faq_info':
            this.addBotMessage("You can view complete questions and answers on our [FAQ Page](faq.html).");
            break;
          case 'human_support':
            this.addBotMessage(
              "Connecting you to human support at **support@goexpressly.com**:",
              null,
              { type: 'human_escalation', tracking_id: null }
            );
            break;
          default:
            this.processKnowledgeBase(label);
        }
      }, 400);
    }

    parseMarkdown(text) {
      let html = this.escapeHTML(text);
      // Bold
      html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      // Code
      html = html.replace(/`(.*?)`/g, '<code class="bg-black/10 dark:bg-white/10 px-1 py-0.5 rounded text-xs font-mono">$1</code>');
      // Links
      html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" class="text-brand-500 font-semibold underline hover:text-brand-600">$1</a>');
      // Newlines
      html = html.replace(/\n/g, '<br />');
      return html;
    }

    escapeHTML(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }
  }

  // Initialize when DOM ready
  document.addEventListener('DOMContentLoaded', () => {
    window.GoExpresslyAssistant = new Assistant();
  });

})();

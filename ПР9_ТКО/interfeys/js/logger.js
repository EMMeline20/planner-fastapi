/* Клиентский модуль фиксации событий.
   Каждое событие отправляется на /api/log и дописывается сервером в JSONL-файл. */
(function () {
  'use strict';

  const STORAGE_KEY = 'tko_session';
  const FALLBACK_KEY = 'tko_log_fallback';

  function slug(value) {
    return String(value || '')
      .trim()
      .replace(/\s+/g, '_')
      .replace(/[^0-9A-Za-zА-Яа-я_\-]/g, '')
      .slice(0, 40) || 'anon';
  }

  function randomId() {
    const t = Date.now().toString(36);
    const r = Math.random().toString(36).slice(2, 8);
    return 'sess_' + t + '_' + r;
  }

  function readConfig() {
    const q = new URLSearchParams(location.search);
    const fromQuery = q.has('subject') || q.has('session') || q.get('demo') === '1';
    let cfg = null;

    if (!fromQuery) {
      try {
        cfg = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || 'null');
      } catch (e) {
        cfg = null;
      }
    }

    if (!cfg) {
      cfg = {
        sessionId: q.get('session') || randomId(),
        subject: q.get('subject') || 'demo',
        condition: q.get('condition') || 'success',
        scenario: q.get('scenario') || 'UC-1',
        role: q.get('role') || 'dispatcher',
        mode: q.get('demo') === '1' ? 'demo' : (q.get('mode') || 'test'),
        startedAt: new Date().toISOString()
      };
      try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(cfg)); } catch (e) { /* ignore */ }
    }
    return cfg;
  }

  const cfg = readConfig();
  const state = {
    sessionId: cfg.sessionId,
    subject: cfg.subject,
    actorId: 'u_' + slug(cfg.subject),
    condition: cfg.condition,
    scenario: cfg.scenario || 'UC-1',
    role: cfg.role || 'dispatcher',
    mode: cfg.mode || 'test',
    startedAt: cfg.startedAt,
    seq: 0,
    sent: 0,
    failed: 0
  };

  function currentScreen() {
    return window.__screen || 'E1';
  }

  function buildEvent(action, opts) {
    const o = opts || {};
    const event = {
      timestamp: new Date().toISOString(),
      client_ms: Math.round(performance.now() * 1000) / 1000,
      seq: ++state.seq,
      actor: { id: state.actorId, role: state.role },
      action: action,
      object: {
        type: o.objectType || 'screen',
        id: o.objectId || currentScreen()
      },
      outcome: o.outcome || 'success',
      step: o.step || '-',
      scenario: state.scenario,
      screen: o.screen || currentScreen(),
      context: {
        session_id: state.sessionId,
        subject: state.subject,
        role: state.role,
        condition: state.condition,
        mode: state.mode,
        correlation_id: state.sessionId,
        user_agent: navigator.userAgent,
        viewport: window.innerWidth + 'x' + window.innerHeight,
        language: navigator.language
      }
    };
    if (o.changes) event.changes = o.changes;
    return event;
  }

  function storeFallback(event) {
    try {
      const list = JSON.parse(localStorage.getItem(FALLBACK_KEY) || '[]');
      list.push(event);
      localStorage.setItem(FALLBACK_KEY, JSON.stringify(list.slice(-500)));
    } catch (e) { /* ignore */ }
  }

  function send(event) {
    return fetch('/api/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event),
      keepalive: true
    }).then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      state.sent++;
      return true;
    }).catch(function () {
      state.failed++;
      storeFallback(event);
      return false;
    });
  }

  function log(action, opts) {
    const event = buildEvent(action, opts);
    send(event);
    if (window.console && console.debug) {
      console.debug('[log]', event.seq, action, event.outcome, event.step);
    }
    return event;
  }

  function flushFallback() {
    let list = [];
    try {
      list = JSON.parse(localStorage.getItem(FALLBACK_KEY) || '[]');
    } catch (e) { list = []; }
    if (!list.length) return Promise.resolve(0);
    localStorage.removeItem(FALLBACK_KEY);
    return Promise.all(list.map(send)).then(function (res) {
      return res.filter(Boolean).length;
    });
  }

  // Досылаем накопленное при восстановлении связи.
  window.addEventListener('online', flushFallback);

  // Последнее событие при закрытии/уходе со страницы.
  window.addEventListener('pagehide', function () {
    if (window.__sessionEnded) return;
    const event = buildEvent('session_end', {
      objectType: 'session',
      objectId: state.sessionId,
      outcome: 'success',
      step: '-'
    });
    try {
      const blob = new Blob([JSON.stringify(event)], { type: 'application/json' });
      navigator.sendBeacon('/api/log', blob);
    } catch (e) { /* ignore */ }
  });

  window.LogClient = {
    state: state,
    log: log,
    flushFallback: flushFallback,
    config: cfg
  };
})();

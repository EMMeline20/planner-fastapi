/* ЛР2, UC-3 «Подтверждение вывоза контейнера», роль «Водитель».
   Планшет: активное задание → текущая точка → «Вывезено» (0 %) → следующая.
   Предусмотрены альтернатива («Пропустить» + причина) и офлайн-очередь. */
(function () {
  'use strict';

  const $ = id => document.getElementById(id);
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const cfg = window.LogClient.config;
  const PENDING_KEY = 'tko_pending_pickup';

  const POINTS = [
    { id: 'c14', address: 'ул. Менделеева, 15', district: 'Ленинский', type: 'ТКО', volume: '0,75 м³', fill: 82, x: 200, y: 430, arrival: '12:20' },
    { id: 'c11', address: 'ул. Аксакова, 7', district: 'Кировский', type: 'Смешанные', volume: '1,1 м³', fill: 89, x: 120, y: 260, arrival: '12:35' },
    { id: 'c01', address: 'ул. Шукина, 12', district: 'Кировский', type: 'Смешанные', volume: '1,1 м³', fill: 96, x: 180, y: 150, arrival: '12:52' },
    { id: 'c02', address: 'пр. Ленина, 45', district: 'Кировский', type: 'Смешанные', volume: '1,1 м³', fill: 87, x: 300, y: 220, arrival: '12:58' },
    { id: 'c03', address: 'ул. Гагарина, 3', district: 'Кировский', type: 'ТКО', volume: '0,75 м³', fill: 85, x: 420, y: 160, arrival: '13:05' },
    { id: 'c12', address: 'ул. Заки Валиди, 32', district: 'Кировский', type: 'Смешанные', volume: '1,1 м³', fill: 86, x: 680, y: 250, arrival: '13:15' },
    { id: 'c05', address: 'ул. Мира, 8', district: 'Советский', type: 'Пластик', volume: '0,75 м³', fill: 88, x: 610, y: 180, arrival: '13:22' },
    { id: 'c09', address: 'ул. Цюрупы, 17', district: 'Ленинский', type: 'Смешанные', volume: '1,1 м³', fill: 83, x: 560, y: 390, arrival: '13:30' },
    { id: 'c13', address: 'ул. Чернышевского, 88', district: 'Ленинский', type: 'Смешанные', volume: '1,1 м³', fill: 90, x: 430, y: 450, arrival: '13:38' },
    { id: 'c07', address: 'ул. Горького, 30', district: 'Ленинский', type: 'Смешанные', volume: '1,1 м³', fill: 91, x: 360, y: 380, arrival: '13:45' }
  ];

  const state = {
    current: 0,
    done: new Set(),
    skipped: new Set(),
    doneTimes: {},
    skipReasons: {},
    pending: null,
    online: true,
    busy: false,
    lastConfirmed: null,
    lastSkipped: null,
    lastSync: '12:50',
    demo: cfg.mode === 'demo'
  };

  window.__screen = 'D1';

  function log(action, opts) {
    window.LogClient.log(action, opts || {});
  }

  function nowTime() {
    const d = new Date();
    return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
  }

  function timeFromIso(value) {
    if (!value) return nowTime();
    const d = new Date(value);
    if (isNaN(d.getTime())) return nowTime();
    return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
  }

  function text(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function formatNumber(value) {
    return String(value).replace('.', ',');
  }

  function buildPayload(point, index) {
    return {
      task_id: 'T-245',
      stop_seq: index + 1,
      stops_total: POINTS.length,
      container_id: point.id,
      address: point.address,
      district: point.district,
      waste_type: point.type,
      volume_m3: parseFloat(String(point.volume).replace(',', '.')) || 0,
      fill_before: point.fill,
      fill_after: 0,
      driver: 'Петров А.С.',
      vehicle: 'Мусоровоз №1',
      idempotency_key: 'T-245:' + point.id
    };
  }

  function showResult(record) {
    const body = $('resultBody');
    if (!body) return;

    const rows = [
      ['ID записи', record.pickup_id],
      ['Задание', record.task_id],
      ['Точка', record.stop_seq + ' из ' + record.stops_total],
      ['Контейнер', record.container_id],
      ['Адрес', record.address],
      ['Район', record.district],
      ['Тип и объём', record.waste_type + ', ' + formatNumber(record.volume_m3) + ' м³'],
      ['Заполненность', record.fill_before + ' % → ' + record.fill_after + ' %'],
      ['Водитель', record.driver],
      ['Мусоровоз', record.vehicle],
      ['Время (UTC, ISO)', record.confirmed_at],
      ['Статус', record.status === 'confirmed' ? 'Вывезено (confirmed)' : record.status],
      ['Ключ идемпотентности', record.idempotency_key]
    ];

    body.innerHTML = rows.map(function (row) {
      return '<div class="result-row"><span>' + text(row[0]) + '</span><b>' + text(row[1]) + '</b></div>';
    }).join('');

    const link = $('resultApiLink');
    if (link) link.href = '/api/pickups/' + encodeURIComponent(record.pickup_id);

    $('resultPanel').classList.remove('hidden');
  }

  function setStatus(kind, text) {
    const msg = document.querySelector('.status-msg');
    const dot = msg ? msg.querySelector('.dot') : null;
    const colors = { ok: '#2e9e57', warn: '#ef9a1e', error: '#d32f2f', busy: '#1565c0' };
    if (dot) dot.style.background = colors[kind] || '#2e9e57';
    $('statusText').textContent = text;
    $('statusText').style.color =
      kind === 'error' ? '#b3261e' : kind === 'warn' ? '#9a5a00' : kind === 'busy' ? '#1565c0' : '#42544a';
  }

  function toast(title, text, kind, timeout) {
    const wrap = $('toastWrap');
    const node = document.createElement('div');
    node.className = 'toast' + (kind ? ' ' + kind : '');
    const b = document.createElement('b');
    b.textContent = title;
    node.appendChild(b);
    node.appendChild(document.createTextNode(text));
    wrap.appendChild(node);
    setTimeout(function () {
      node.classList.add('fade');
      setTimeout(function () { node.remove(); }, 400);
    }, timeout || 4200);
  }

  function clearToasts() {
    const wrap = $('toastWrap');
    if (wrap) wrap.innerHTML = '';
  }

  function colorOf(fill) {
    if (fill >= 85) return '#d32f2f';
    if (fill >= 60) return '#ef6c00';
    return '#2e7d32';
  }

  function setPulse(point) {
    const pulse = $('pulseCircle');
    if (!pulse) return;
    pulse.setAttribute('cx', point.x);
    pulse.setAttribute('cy', point.y);
  }

  function savePending() {
    try {
      if (state.pending) {
        localStorage.setItem(PENDING_KEY, JSON.stringify(state.pending));
      }
    } catch (e) { /* ignore */ }
  }

  function clearPending() {
    try { localStorage.removeItem(PENDING_KEY); } catch (e) { /* ignore */ }
  }

  function loadPending() {
    try {
      const p = JSON.parse(localStorage.getItem(PENDING_KEY) || 'null');
      if (p && Number.isInteger(p.index) && p.index >= 0 && p.index < POINTS.length && !state.done.has(p.index)) {
        state.pending = p;
        state.current = p.index;
        state.online = false;
      }
    } catch (e) { /* ignore */ }
  }

  function renderNetwork() {
    const btn = $('netToggle');
    if (!btn) return;
    btn.textContent = state.online ? 'Онлайн' : 'Офлайн';
    btn.classList.toggle('offline', !state.online);
    $('syncState').textContent = state.pending ? 'Ожидает' : (state.online ? state.lastSync : '—');
  }

  function renderProgress() {
    const completed = state.done.size;
    const skipped = state.skipped.size;
    $('progressLabel').textContent = 'Выполнено ' + completed + ' из ' + POINTS.length +
      (skipped ? ' · пропущено ' + skipped : '');
    $('progressFill').style.width = (completed / POINTS.length * 100) + '%';
    $('remaining').textContent = 'Осталось ' + (POINTS.length - completed - skipped);
  }

  function renderList() {
    const box = $('stopList');
    box.innerHTML = '';

    POINTS.forEach(function (point, index) {
      let cls = '';
      let meta = 'Ожидает';
      let mark = '○';

      if (state.done.has(index)) {
        cls = 'done';
        meta = 'Вывезено · ' + (state.doneTimes[index] || point.arrival);
        mark = '✓';
      } else if (state.skipped.has(index)) {
        cls = 'skipped';
        meta = 'Пропущено · ' + (state.skipReasons[index] || 'причина');
        mark = '!';
      } else if (state.pending && state.pending.index === index) {
        cls = 'queued';
        meta = 'Ожидает отправки · ' + point.fill + ' %';
        mark = '…';
      } else if (index === state.current) {
        cls = 'current';
        meta = 'Текущая · ' + point.fill + ' %';
        mark = '●';
      }

      const row = document.createElement('div');
      row.className = 'stop ' + cls;
      row.innerHTML =
        '<span class="num">' + (index + 1) + '</span>' +
        '<span><span class="addr">' + point.address + '</span>' +
        '<span class="meta">' + meta + '</span></span>' +
        '<span class="status">' + mark + '</span>';
      box.appendChild(row);
    });
  }

  function renderCurrent() {
    const btnP = $('btnPickup');
    const btnS = $('btnSkip');
    $('pointsBadge').textContent = POINTS.length;

    if (state.lastConfirmed) {
      const item = state.lastConfirmed;
      const point = item.point;
      $('currentBadge').textContent = (item.index + 1) + ' из ' + POINTS.length;
      $('currentAddr').textContent = point.address;
      $('currentSub').textContent = point.district + ' район · ' + point.type + ', ' + point.volume;
      $('currentFill').textContent = '0 %';
      $('currentFill').style.color = '#2e7d32';
      $('currentBar').style.width = '0%';
      $('currentBar').style.background = '#2e7d32';
      $('arrival').textContent = item.time;
      $('pointType').textContent = 'Вывезено';
      btnP.disabled = true;
      btnP.textContent = '✓ ВЫВЕЗЕНО';
      btnS.disabled = true;
      $('mapBadge').textContent = 'точка ' + (item.index + 1) + ' · 0 %';
      setPulse(point);
      return;
    }

    if (state.lastSkipped) {
      const item = state.lastSkipped;
      const point = item.point;
      $('currentBadge').textContent = (item.index + 1) + ' из ' + POINTS.length;
      $('currentAddr').textContent = point.address;
      $('currentSub').textContent = 'Причина: ' + item.reason;
      $('currentFill').textContent = '—';
      $('currentFill').style.color = '#a35a00';
      $('currentBar').style.width = '0%';
      $('currentBar').style.background = '#ef6c00';
      $('arrival').textContent = point.arrival;
      $('pointType').textContent = 'Пропуск';
      btnP.disabled = true;
      btnP.textContent = 'ПРОПУЩЕНО';
      btnS.disabled = true;
      $('mapBadge').textContent = 'точка ' + (item.index + 1) + ' · пропуск';
      setPulse(point);
      return;
    }

    if (state.pending) {
      const point = state.pending.point;
      $('currentBadge').textContent = (state.pending.index + 1) + ' из ' + POINTS.length;
      $('currentAddr').textContent = point.address;
      $('currentSub').textContent = point.district + ' район · ' + point.type + ', ' + point.volume;
      $('currentFill').textContent = point.fill + ' %';
      $('currentFill').style.color = colorOf(point.fill);
      $('currentBar').style.width = point.fill + '%';
      $('currentBar').style.background = colorOf(point.fill);
      $('arrival').textContent = point.arrival;
      $('pointType').textContent = 'Офлайн';
      btnP.disabled = true;
      btnP.textContent = 'ОЖИДАЕТ ОТПРАВКИ';
      btnS.disabled = true;
      $('mapBadge').textContent = 'точка ' + (state.pending.index + 1) + ' · офлайн';
      setPulse(point);
      return;
    }

    if (state.current >= POINTS.length) {
      $('currentBadge').textContent = POINTS.length + ' из ' + POINTS.length;
      $('currentAddr').textContent = 'Маршрут обработан';
      $('currentSub').textContent = 'Выполнено: ' + state.done.size + ' · пропущено: ' + state.skipped.size;
      $('currentFill').textContent = '—';
      $('currentFill').style.color = '#6b7a71';
      $('currentBar').style.width = '0%';
      $('currentBar').style.background = '#b8c7bd';
      $('arrival').textContent = '—';
      $('pointType').textContent = 'Готово';
      btnP.disabled = true;
      btnP.textContent = 'ЗАДАНИЕ ЗАВЕРШЕНО';
      btnS.disabled = true;
      $('mapBadge').textContent = 'маршрут обработан';
      return;
    }

    const point = POINTS[state.current];
    $('currentBadge').textContent = (state.current + 1) + ' из ' + POINTS.length;
    $('currentAddr').textContent = point.address;
    $('currentSub').textContent = point.district + ' район · ' + point.type + ', ' + point.volume;
    $('currentFill').textContent = point.fill + ' %';
    $('currentFill').style.color = colorOf(point.fill);
    $('currentBar').style.width = point.fill + '%';
    $('currentBar').style.background = colorOf(point.fill);
    $('arrival').textContent = point.arrival;
    $('pointType').textContent = point.type;
    btnP.disabled = state.busy;
    btnP.textContent = '✓ ВЫВЕЗЕНО';
    btnS.disabled = state.busy;
    $('mapBadge').textContent = 'точка ' + (state.current + 1) + ' из ' + POINTS.length;
    setPulse(point);
  }

  function render() {
    renderList();
    renderProgress();
    renderCurrent();
    renderNetwork();
  }

  function addJournal(kind, point, extra, time) {
    const label = kind === 'pickup'
      ? 'Вывезен контейнер'
      : kind === 'skip'
        ? 'Точка пропущена'
        : 'Данные синхронизированы';
    const row = document.createElement('div');
    row.className = 'jrow';
    row.innerHTML =
      '<time>' + (time || nowTime()) + '</time>' +
      '<div><b>' + label + '</b><span>' + point.address + (extra ? ' · ' + extra : '') + '</span></div>';
    $('journalList').prepend(row);

    const rows = $('journalList').querySelectorAll('.jrow');
    if (rows.length > 6) rows[rows.length - 1].remove();
  }

  function nextAfter(index) {
    return index + 1 < POINTS.length ? POINTS[index + 1] : null;
  }

  async function confirmPickup() {
    if (state.busy || state.pending || state.lastConfirmed || state.lastSkipped || state.current >= POINTS.length) return;

    const point = POINTS[state.current];

    clearToasts();
    log('pickup_confirm_click', {
      objectType: 'stop', objectId: point.id, outcome: 'success',
      step: 'S3', screen: 'D1',
      changes: { point_number: state.current + 1, address: point.address, fill: point.fill }
    });

    if (!state.online) {
      state.pending = { index: state.current, point: point, timestamp: new Date().toISOString() };
      savePending();
      log('pickup_queued', {
        objectType: 'stop', objectId: point.id, outcome: 'neutral',
        step: 'S3', screen: 'D1',
        changes: { reason: 'offline', point_number: state.current + 1, address: point.address }
      });
      setStatus('warn', 'Нет связи. Данные сохранены локально и ожидают отправки.');
      toast('Ожидает отправки', 'Нет связи. Точка сохранена локально.', 'warn', 5200);
      render();
      return;
    }

    state.busy = true;
    $('btnPickup').disabled = true;
    $('btnSkip').disabled = true;
    $('btnPickup').textContent = 'Сохранение…';
    setStatus('busy', 'Фиксация вывоза: ' + point.address);

    let record;
    try {
      record = await window.Api.createPickup(buildPayload(point, state.current));
    } catch (error) {
      state.busy = false;
      $('btnPickup').disabled = false;
      $('btnSkip').disabled = false;
      $('btnPickup').textContent = '✓ ВЫВЕЗЕНО';
      setStatus('error', 'Не удалось сохранить акт: ' + error.message);
      toast('Ошибка сохранения', error.message, 'error', 7000);
      render();
      return;
    }

    const confirmedTime = timeFromIso(record.confirmed_at);
    state.done.add(state.current);
    state.doneTimes[state.current] = confirmedTime;
    state.lastConfirmed = {
      index: state.current,
      point: point,
      fillBefore: point.fill,
      fillAfter: 0,
      time: confirmedTime,
      record: record
    };
    state.busy = false;
    showResult(record);

    const next = nextAfter(state.current);
    log('pickup_confirmed', {
      objectType: 'stop', objectId: point.id, outcome: 'success',
      step: 'S4', screen: 'D1',
      changes: {
        pickup_id: record.pickup_id,
        address: point.address,
        fill_before: point.fill,
        fill_after: 0,
        done_count: state.done.size,
        next_stop: next ? next.id : null,
        next_address: next ? next.address : null
      }
    });
    addJournal('pickup', point, 'заполненность 0 % · ' + record.pickup_id, confirmedTime);
    render();
    setStatus('ok', 'Запись ' + record.pickup_id + ' сохранена в MongoDB. Заполненность 0 %.');
    toast('Запись создана', record.pickup_id + ' · данные в MongoDB', '', 5500);

    await sleep(1400);

    state.lastConfirmed = null;
    state.current += 1;
    render();

    if (next) {
      log('next_point_view', {
        objectType: 'stop', objectId: next.id, outcome: 'success',
        step: 'S5', screen: 'D1',
        changes: { point_number: state.current + 1, address: next.address }
      });
      setStatus('ok', 'Следующая точка: ' + next.address);
    } else {
      log('task_completed', {
        objectType: 'task', objectId: 'T-245', outcome: 'success',
        step: 'S6', screen: 'D1',
        changes: { done: state.done.size, skipped: state.skipped.size }
      });
      setStatus('ok', 'Задание №245 завершено. Выполнено: ' + state.done.size + ', пропущено: ' + state.skipped.size + '.');
    }

    $('statusMeta').textContent = 'Обновлено ' + nowTime();
  }

  function openSkip() {
    if (state.busy || state.pending || state.lastConfirmed || state.lastSkipped || state.current >= POINTS.length) return;
    $('skipModal').classList.remove('hidden');
    log('skip_dialog_open', {
      objectType: 'stop', objectId: POINTS[state.current].id, outcome: 'neutral',
      step: 'S3', screen: 'D1',
      changes: { point_number: state.current + 1 }
    });
  }

  function closeSkip() {
    $('skipModal').classList.add('hidden');
  }

  async function confirmSkip() {
    if (state.busy || state.pending || state.lastConfirmed || state.lastSkipped || state.current >= POINTS.length) {
      closeSkip();
      return;
    }

    const reason = $('skipReason').value;
    closeSkip();
    clearToasts();

    const point = POINTS[state.current];
    state.busy = true;

    log('skip_click', {
      objectType: 'stop', objectId: point.id, outcome: 'neutral',
      step: 'S3', screen: 'D1',
      changes: { point_number: state.current + 1, address: point.address, reason: reason }
    });

    state.skipped.add(state.current);
    state.skipReasons[state.current] = reason;
    state.lastSkipped = { index: state.current, point: point, reason: reason };
    state.busy = false;

    addJournal('skip', point, reason);
    render();
    setStatus('warn', 'Точка пропущена: ' + reason + '. Диспетчер увидит статус.');
    toast('Точка пропущена', reason + ' · статус передан диспетчеру.', 'warn', 5200);

    log('stop_skipped', {
      objectType: 'stop', objectId: point.id, outcome: 'neutral',
      step: 'S4', screen: 'D1',
      changes: { reason: reason, skipped_count: state.skipped.size }
    });

    await sleep(1200);

    const next = nextAfter(state.current);
    state.lastSkipped = null;
    state.current += 1;
    render();

    if (next) {
      log('next_point_view', {
        objectType: 'stop', objectId: next.id, outcome: 'success',
        step: 'S5', screen: 'D1',
        changes: { point_number: state.current + 1, address: next.address }
      });
      setStatus('warn', 'Следующая точка: ' + next.address + '. Есть пропущенная точка.');
    } else {
      log('task_completed', {
        objectType: 'task', objectId: 'T-245', outcome: 'success',
        step: 'S6', screen: 'D1',
        changes: { done: state.done.size, skipped: state.skipped.size }
      });
      setStatus('warn', 'Маршрут обработан. Выполнено: ' + state.done.size + ', пропущено: ' + state.skipped.size + '.');
    }

    $('statusMeta').textContent = 'Обновлено ' + nowTime();
  }

  async function syncPending() {
    if (!state.pending || !state.online || state.busy) return;

    const item = state.pending;
    const point = item.point;

    state.busy = true;
    $('btnPickup').disabled = true;
    $('btnSkip').disabled = true;
    $('btnPickup').textContent = 'Отправка…';
    clearToasts();
    setStatus('busy', 'Отправка сохранённых данных…');

    try { await window.LogClient.flushFallback(); } catch (e) { /* continue */ }
    await sleep(600);

    state.done.add(item.index);
    state.doneTimes[item.index] = nowTime();
    state.lastConfirmed = {
      index: item.index,
      point: point,
      fillBefore: point.fill,
      fillAfter: 0,
      time: nowTime()
    };
    state.pending = null;
    state.lastSync = nowTime();
    clearPending();
    state.busy = false;

    log('pickup_synced', {
      objectType: 'stop', objectId: point.id, outcome: 'success',
      step: 'S4', screen: 'D1',
      changes: {
        synced_after_offline: true,
        fill_before: point.fill,
        fill_after: 0,
        done_count: state.done.size
      }
    });
    addJournal('sync', point, 'заполненность 0 %');
    render();
    setStatus('ok', 'Связь восстановлена. Данные отправлены, заполненность 0 %.');
    toast('Синхронизировано', 'Сохранённые данные отправлены на сервер.', '', 4200);

    await sleep(1400);

    state.lastConfirmed = null;
    state.current = item.index + 1;
    render();

    const next = nextAfter(item.index);
    if (next) {
      log('next_point_view', {
        objectType: 'stop', objectId: next.id, outcome: 'success',
        step: 'S5', screen: 'D1',
        changes: { point_number: state.current + 1, address: next.address }
      });
      setStatus('ok', 'Следующая точка: ' + next.address);
    } else {
      log('task_completed', {
        objectType: 'task', objectId: 'T-245', outcome: 'success',
        step: 'S6', screen: 'D1',
        changes: { done: state.done.size, skipped: state.skipped.size }
      });
      setStatus('ok', 'Задание №245 завершено. Выполнено: ' + state.done.size + ', пропущено: ' + state.skipped.size + '.');
    }

    $('statusMeta').textContent = 'Обновлено ' + nowTime();
  }

  async function toggleNetwork() {
    if (state.busy) return;

    clearToasts();
    state.online = !state.online;
    renderNetwork();

    log(state.online ? 'network_online' : 'network_offline', {
      objectType: 'network', objectId: 'link', outcome: 'neutral',
      step: '-', screen: 'D1'
    });

    if (!state.online) {
      setStatus('warn', 'Нет связи. Новые отметки сохраняются локально.');
      toast('Офлайн', 'Нет связи. Отметки сохранятся локально и уйдут после восстановления.', 'warn', 4600);
      return;
    }

    if (state.pending) {
      await syncPending();
    } else {
      setStatus('ok', 'Соединение восстановлено.');
      toast('Онлайн', 'Связь восстановлена.', '', 3000);
    }
  }

  function bind() {
    $('btnPickup').addEventListener('click', confirmPickup);
    const resultClose = $('resultClose');
    if (resultClose) {
      resultClose.addEventListener('click', function () {
        $('resultPanel').classList.add('hidden');
      });
    }
    $('btnSkip').addEventListener('click', openSkip);
    $('netToggle').addEventListener('click', toggleNetwork);

    $('skipClose').addEventListener('click', closeSkip);
    $('skipCancel').addEventListener('click', closeSkip);
    $('skipConfirm').addEventListener('click', confirmSkip);
    $('skipModal').addEventListener('click', function (event) {
      if (event.target === $('skipModal')) closeSkip();
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && !$('skipModal').classList.contains('hidden')) closeSkip();
    });

    $('btnExit').addEventListener('click', function () {
      window.__sessionEnded = true;
      log('session_end', {
        objectType: 'session', objectId: cfg.sessionId, outcome: 'success',
        step: '-', screen: 'D1'
      });
      setTimeout(function () { location.href = '/'; }, 150);
    });
  }

  function init() {
    const pv = Number(new URLSearchParams(location.search).get('point'));
    if (Number.isInteger(pv) && pv >= 3 && pv <= POINTS.length) {
      state.current = pv - 1;
    }

    clearPending();
    state.pending = null;
    state.online = true;
    state.lastSync = nowTime();

    if ($('btnSkip')) $('btnSkip').style.display = 'none';
    if ($('netToggle')) {
      $('netToggle').disabled = true;
      $('netToggle').title = 'В первом сценарии связь всегда онлайн';
    }

    $('statusMeta').textContent = 'Обновлено ' + nowTime();
    bind();
    render();

    if (state.pending) {
      setStatus('warn', 'Есть неотправленная отметка. Включите связь для синхронизации.');
    } else {
      setStatus('', 'Задание №245 · точка ' + (state.current + 1) + ' из ' + POINTS.length + ' · ожидает подтверждения');
    }

    log('session_start', {
      objectType: 'session', objectId: cfg.sessionId, outcome: 'success',
      step: 'S0', screen: 'D1',
      changes: { scenario: 'UC-3', mode: state.demo ? 'demo' : 'test' }
    });
    log('screen_view', {
      objectType: 'screen', objectId: 'D1', outcome: 'success',
      step: 'S0', screen: 'D1'
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();

/* Тонкий клиент API: все запросы к FastAPI идут отсюда. */
(function () {
  'use strict';

  async function request(url, options) {
    const response = await fetch(url, options);
    let data = null;
    try {
      data = await response.json();
    } catch (e) {
      data = null;
    }

    if (!response.ok) {
      let detail = 'HTTP ' + response.status;
      if (data && data.detail) {
        detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
      throw new Error(detail);
    }

    return data;
  }

  window.Api = {
    createPickup: function (payload) {
      return request('/api/pickups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    },

    getPickup: function (pickupId) {
      return request('/api/pickups/' + encodeURIComponent(pickupId));
    },

    deletePickup: function (pickupId) {
      return request('/api/pickups/' + encodeURIComponent(pickupId), { method: 'DELETE' });
    }
  };
})();

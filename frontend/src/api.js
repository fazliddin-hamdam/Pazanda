export const tg = window.Telegram?.WebApp

const BASE = import.meta.env.VITE_API_URL || ''

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(method, path, body) {
  const headers = { 'Content-Type': 'application/json' }
  if (tg?.initData) headers.Authorization = `tma ${tg.initData}`
  let res
  try {
    res = await fetch(BASE + path, { method, headers, body: body ? JSON.stringify(body) : undefined })
  } catch {
    throw new ApiError('', 0) // matnni ilova tanlangan tilda ko'rsatadi
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new ApiError(typeof data.detail === 'string' ? data.detail : '', res.status)
  return data
}

export const api = {
  me: () => request('GET', '/api/me'),
  setLanguage: (language) => request('PUT', '/api/me/language', { language }),
  stock: () => request('GET', '/api/stock'),
  parseStock: (text) => request('POST', '/api/stock/parse', { text }),
  updateStock: (id, grams) => request('PATCH', `/api/stock/${id}`, { grams }),
  deleteStock: (id) => request('DELETE', `/api/stock/${id}`),
  recipes: () => request('GET', '/api/recipes'),
  suggest: (servings) => request('POST', '/api/suggest', { servings }),
  resolve: (query) => request('POST', '/api/recipes/resolve', { query }),
  plan: (slug, servings) => request('POST', '/api/plan', { slug, servings }),
  cookStart: (slug, servings) => request('POST', '/api/cook/start', { slug, servings }),
  cookFinish: (slug, servings) => request('POST', '/api/cook/finish', { slug, servings }),
  shopping: () => request('GET', '/api/shopping'),
  addShopping: (items) => request('POST', '/api/shopping', { items }),
  bought: (id) => request('POST', `/api/shopping/${id}/bought`),
  deleteShopping: (id) => request('DELETE', `/api/shopping/${id}`),
  chat: (messages, slug, servings) => request('POST', '/api/chat', { messages, slug, servings }),
}

export function haptic(type = 'light') {
  try {
    if (type === 'success' || type === 'error') tg?.HapticFeedback?.notificationOccurred(type)
    else tg?.HapticFeedback?.impactOccurred(type)
  } catch {
    /* Telegramdan tashqarida */
  }
}

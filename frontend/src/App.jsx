import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, haptic, tg } from './api.js'
import { ChatMessage, EditSheet, LanguageList, ServingsPicker, ShoppingSheet, Sheet, StockBoard, Typing } from './components.jsx'
import { LANGS, guessLang, makeT } from './i18n.js'

let nextId = 1
const bot = (text, extra = {}) => ({ id: nextId++, from: 'bot', text, ...extra })
const me = (text) => ({ id: nextId++, from: 'user', text })

const CATEGORY_ICONS = { gosht: '🥩', sabzavot: '🥕', don: '🌾', sut: '🥚', yog: '🫒', ziravor: '🧂', boshqa: '🧺' }

export default function App() {
  const [user, setUser] = useState(null)
  const [lang, setLang] = useState(null) // null — til hali tanlanmagan
  const [stock, setStock] = useState({ categories: [], count: 0 })
  const [recipes, setRecipes] = useState([])
  const [shopping, setShopping] = useState([])
  const [servings, setServings] = useState(() => {
    try {
      return Number(localStorage.getItem('servings')) || 3
    } catch {
      return 3
    }
  })

  const [view, setView] = useState('home') // home | chat
  const [messages, setMessages] = useState([])
  const [busy, setBusy] = useState('')
  const [session, setSession] = useState(null) // {slug, name, servings, steps, step, phase, missing}

  const [sheet, setSheet] = useState(null) // {type: 'suggest'|'choose'|'shopping'|'edit'|'language', item?}
  const [input, setInput] = useState('')
  const [toast, setToast] = useState('')
  const [fatal, setFatal] = useState('') // ilova umuman ochilmadi (masalan, Telegramdan tashqarida)
  const chatEnd = useRef(null)

  const t = useMemo(() => makeT(lang || guessLang(tg?.initDataUnsafe?.user?.language_code)), [lang])
  const push = useCallback((...msgs) => setMessages((m) => [...m, ...msgs]), [])

  const errorText = useCallback(
    (e) => (e.status === 0 ? t('errNetwork') : e.status === 401 ? t('errTelegram') : e.message || t('errGeneric')),
    [t],
  )

  const showError = useCallback(
    (e) => {
      haptic('error')
      setToast(errorText(e))
      setTimeout(() => setToast(''), 3500)
    },
    [errorText],
  )

  // ---------------------------------------------------------------- yuklash
  const loadData = useCallback(async () => {
    const [s, r, sh] = await Promise.all([api.stock(), api.recipes(), api.shopping()])
    setStock(s)
    setRecipes(r)
    setShopping(sh)
  }, [])

  useEffect(() => {
    api
      .me()
      .then(async (u) => {
        // Ma'lumotlar kelguncha boshqa tilda bo'sh ekran ko'rinmasin
        if (u.language) await loadData()
        setLang(u.language)
        setUser(u)
      })
      .catch((e) => setFatal(errorText(e)))
    // faqat bir marta, ilova ochilganda
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (lang) document.documentElement.lang = lang
  }, [lang])

  useEffect(() => {
    try {
      localStorage.setItem('servings', String(servings))
    } catch {
      /* brauzer xotirasi yopiq */
    }
  }, [servings])

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy])

  const goHome = useCallback(() => {
    setView('home')
    setSession(null)
    setMessages([])
  }, [])

  // Telegram "Orqaga" tugmasi
  useEffect(() => {
    const back = tg?.BackButton
    if (!back) return
    if (view === 'chat') {
      back.show()
      back.onClick(goHome)
      return () => back.offClick(goHome)
    }
    back.hide()
  }, [view, goHome])

  // ---------------------------------------------------------------- til
  async function chooseLanguage(code) {
    haptic()
    try {
      const u = await api.setLanguage(code)
      setUser(u)
      setLang(code)
      setSheet(null)
      goHome() // eski tildagi suhbat qolmasin
      await loadData() // masalliq va taom nomlari yangi tilda
    } catch (err) {
      showError(err)
    }
  }

  // ---------------------------------------------------------------- ombor
  async function addStock(e) {
    e?.preventDefault()
    const text = input.trim()
    if (!text || busy) return
    setBusy(t('busyStock'))
    try {
      const res = await api.parseStock(text)
      setStock(res.stock)
      setInput('')
      haptic(res.added.length ? 'success' : 'error')
      setToast(res.message)
      setTimeout(() => setToast(''), 4500)
    } catch (err) {
      showError(err)
    } finally {
      setBusy('')
    }
  }

  async function saveStockItem(item, grams) {
    try {
      setStock(grams > 0 ? await api.updateStock(item.id, grams) : await api.deleteStock(item.id))
      setSheet(null)
    } catch (err) {
      showError(err)
    }
  }

  // ---------------------------------------------------------------- A ssenariy
  async function runSuggest(n) {
    setSheet(null)
    setView('chat')
    setMessages([me(t('msgSuggest', { n }))])
    setBusy(t('busySuggest'))
    try {
      const res = await api.suggest(n)
      push(bot(res.message, { kind: 'suggestions', data: res.suggestions }))
    } catch (err) {
      showError(err)
    } finally {
      setBusy('')
    }
  }

  // ---------------------------------------------------------------- B ssenariy
  async function runChoose({ slug, query }, n) {
    setSheet(null)
    const label = slug ? recipes.find((r) => r.slug === slug)?.name : query
    const first = me(t('msgChoose', { dish: label, n }))
    setMessages((m) => (view === 'chat' ? [...m, first] : [first]))
    setView('chat')
    try {
      let target = slug
      if (!target) {
        setBusy(t('busyResolve'))
        const recipe = await api.resolve(query)
        target = recipe.slug
        if (!recipes.some((r) => r.slug === recipe.slug)) {
          setRecipes((rs) => [...rs, { slug: recipe.slug, name: recipe.name, time_minutes: recipe.time_minutes }])
        }
      }
      await runPlan(target, n)
    } catch (err) {
      push(bot(errorText(err)))
      haptic('error')
    } finally {
      setBusy('')
    }
  }

  async function runPlan(slug, n) {
    setBusy(t('busyPlan'))
    try {
      const res = await api.plan(slug, n)
      const { check, recipe } = res
      setSession({ slug, name: recipe.name, servings: n, steps: recipe.steps, step: -1, phase: 'plan', missing: check.missing })
      const actions = check.ready
        ? [{ label: t('actStartReady'), action: 'start' }]
        : [
            { label: t('actAddMissing'), action: 'addMissing' },
            { label: t('actStartAnyway'), action: 'start', secondary: true },
          ]
      push(bot(res.message, { kind: 'plan', data: { check, recipe }, actions }))
    } finally {
      setBusy('')
    }
  }

  // ---------------------------------------------------------------- pishirish
  async function handleAction(action, payload) {
    haptic()
    if (busy) return
    try {
      if (action === 'choose') {
        push(me(t('msgPick', { dish: payload.name })))
        await runPlan(payload.slug, servings)
      } else if (action === 'addMissing') {
        const items = session.missing.map((m) => ({ name: m.name, grams: Math.ceil(m.missing_g) }))
        const res = await api.addShopping(items)
        setShopping(res.items)
        push(me(t('msgAddYes')), bot(res.message, { actions: [{ label: t('actStart'), action: 'start' }] }))
      } else if (action === 'start') {
        setBusy(t('busyStart'))
        const res = await api.cookStart(session.slug, session.servings)
        setSession((s) => ({ ...s, phase: 'cooking', step: 0 }))
        push(bot(res.message), stepMessage(session.steps, 0))
      } else if (action === 'next') {
        const step = session.step + 1
        setSession((s) => ({ ...s, step }))
        push(stepMessage(session.steps, step))
      } else if (action === 'finish') {
        setBusy(t('busyStock'))
        const res = await api.cookFinish(session.slug, session.servings)
        setStock(res.stock)
        setSession((s) => ({ ...s, phase: 'done' }))
        haptic('success')
        push(me(t('msgDone')), bot(res.message, { kind: 'finish', data: res.used, actions: [{ label: t('actHome'), action: 'home' }] }))
      } else if (action === 'home') {
        goHome()
      }
    } catch (err) {
      showError(err)
    } finally {
      setBusy('')
    }
  }

  function stepMessage(steps, i) {
    const last = i >= steps.length - 1
    return bot(steps[i], {
      kind: 'step',
      data: { index: i, total: steps.length },
      actions: last ? [{ label: t('actFinish'), action: 'finish' }] : [{ label: t('actNext'), action: 'next' }],
    })
  }

  // ---------------------------------------------------------------- savol-javob
  async function askChef(e) {
    e?.preventDefault()
    const text = input.trim()
    if (!text || busy) return
    setInput('')
    const history = [...messages, me(text)]
    setMessages(history)
    setBusy(t('busyThink'))
    try {
      const payload = history.filter((m) => m.text).map((m) => ({ role: m.from === 'bot' ? 'assistant' : 'user', content: m.text }))
      const res = await api.chat(payload, session?.slug, session?.servings)
      // savol javobidan keyin ham oxirgi tugmalar ishlashi uchun ularni javobga ko'chiramiz
      const lastActions = [...messages].reverse().find((m) => m.actions)?.actions
      push(bot(res.reply, { actions: session?.phase !== 'done' ? lastActions : undefined }))
    } catch (err) {
      push(bot(errorText(err)))
    } finally {
      setBusy('')
    }
  }

  // ---------------------------------------------------------------- render
  if (!user) {
    return (
      <div className="app language-screen">
        <div className="language-card">
          <div className="logo big">🍲</div>
          {fatal && <p className="muted">{fatal}</p>}
        </div>
      </div>
    )
  }

  if (!lang) {
    return (
      <div className="app language-screen">
        <div className="language-card">
          <div className="logo big">🍲</div>
          <h1>Pazanda</h1>
          <p className="muted">O'zbek oshxonasi · Uzbek cuisine · Özbek mutfağı</p>
          <LanguageList current={guessLang(tg?.initDataUnsafe?.user?.language_code)} onPick={chooseLanguage} highlight />
          <p className="muted small">{t('langSub')}</p>
        </div>
        {toast && <div className="toast">{toast}</div>}
      </div>
    )
  }

  const lastActionable = [...messages].reverse().find((m) => m.actions || m.kind === 'suggestions')?.id
  const shoppingCount = shopping.length
  const currentLang = LANGS.find((l) => l.code === lang)

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">🍲</span>
          <div>
            <div className="title">Pazanda</div>
            <div className="subtitle">{view === 'chat' && session ? session.name : t('subtitle')}</div>
          </div>
        </div>
        <div className="top-actions">
          <button className="icon-btn" onClick={() => setSheet({ type: 'language' })} aria-label={t('language')}>
            {currentLang?.flag || '🌐'}
          </button>
          <button className="icon-btn" onClick={() => setSheet({ type: 'shopping' })} aria-label={t('cart')}>
            🛒{shoppingCount > 0 && <span className="badge">{shoppingCount}</span>}
          </button>
        </div>
      </header>

      {view === 'home' && (
        <main className="home">
          {user && <div className="bubble bot greeting">{user.greeting}</div>}

          <section className="actions">
            <button className="action primary" onClick={() => setSheet({ type: 'suggest' })}>
              <span className="action-icon">🤔</span>
              <span>
                <b>{t('suggestTitle')}</b>
                <small>{t('suggestSub')}</small>
              </span>
            </button>
            <button className="action" onClick={() => setSheet({ type: 'choose' })}>
              <span className="action-icon">📖</span>
              <span>
                <b>{t('chooseTitle')}</b>
                <small>{t('chooseSub')}</small>
              </span>
            </button>
          </section>

          <StockBoard stock={stock} icons={CATEGORY_ICONS} t={t} onEdit={(item) => setSheet({ type: 'edit', item })} />
        </main>
      )}

      {view === 'chat' && (
        <main className="chat">
          {messages.map((m) => (
            <ChatMessage key={m.id} msg={m} t={t} active={m.id === lastActionable && !busy} onAction={handleAction} />
          ))}
          {busy && <Typing text={busy} />}
          <div ref={chatEnd} />
        </main>
      )}

      <form className="bottombar" onSubmit={view === 'home' ? addStock : askChef}>
        {view === 'chat' && !user?.llm ? (
          <button type="button" className="ghost wide" onClick={goHome}>
            {t('home')}
          </button>
        ) : (
          <>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={view === 'home' ? t('stockPlaceholder') : t('chatPlaceholder')}
              disabled={!!busy && view === 'home'}
              enterKeyHint="send"
            />
            <button type="submit" className="send" disabled={!input.trim() || !!busy} aria-label={t('send')}>
              {view === 'home' ? '＋' : '➤'}
            </button>
          </>
        )}
      </form>

      {toast && <div className="toast">{toast}</div>}

      {sheet?.type === 'language' && (
        <Sheet title={t('langTitle')} t={t} onClose={() => setSheet(null)}>
          <LanguageList current={lang} onPick={chooseLanguage} />
        </Sheet>
      )}

      {sheet?.type === 'suggest' && (
        <Sheet title={t('servingsQ')} t={t} onClose={() => setSheet(null)}>
          <ServingsPicker value={servings} onChange={setServings} t={t} />
          <button className="btn wide" onClick={() => runSuggest(servings)}>
            {t('suggestBtn')}
          </button>
        </Sheet>
      )}

      {sheet?.type === 'choose' && (
        <ChooseSheet recipes={recipes} servings={servings} setServings={setServings} t={t} onClose={() => setSheet(null)} onSubmit={runChoose} />
      )}

      {sheet?.type === 'shopping' && (
        <ShoppingSheet
          items={shopping}
          t={t}
          onClose={() => setSheet(null)}
          onBought={async (item) => {
            try {
              const res = await api.bought(item.id)
              setShopping(res.items)
              setStock(res.stock)
              haptic('success')
            } catch (err) {
              showError(err)
            }
          }}
          onDelete={async (item) => {
            try {
              setShopping(await api.deleteShopping(item.id))
            } catch (err) {
              showError(err)
            }
          }}
        />
      )}

      {sheet?.type === 'edit' && <EditSheet item={sheet.item} t={t} onClose={() => setSheet(null)} onSave={saveStockItem} />}
    </div>
  )
}

function ChooseSheet({ recipes, servings, setServings, t, onClose, onSubmit }) {
  const [slug, setSlug] = useState('')
  const [query, setQuery] = useState('')
  const ready = slug || query.trim()
  return (
    <Sheet title={t('chooseTitle')} t={t} onClose={onClose}>
      <label className="field">
        <span>{t('dish')}</span>
        <select
          value={slug}
          onChange={(e) => {
            setSlug(e.target.value)
            setQuery('')
          }}
        >
          <option value="">{t('pickFromList')}</option>
          {recipes.map((r) => (
            <option key={r.slug} value={r.slug}>
              {r.name} · {r.time_minutes} {t('minShort')}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>{t('orType')}</span>
        <input
          value={query}
          placeholder={t('dishPlaceholder')}
          onChange={(e) => {
            setQuery(e.target.value)
            setSlug('')
          }}
        />
      </label>
      <div className="field">
        <span>{t('servingsQ')}</span>
        <ServingsPicker value={servings} onChange={setServings} t={t} />
      </div>
      <button className="btn wide" disabled={!ready} onClick={() => onSubmit(slug ? { slug } : { query: query.trim() }, servings)}>
        {t('calcBtn')}
      </button>
    </Sheet>
  )
}

import { useCallback, useEffect, useRef, useState } from 'react'
import { api, haptic, tg } from './api.js'
import { ChatMessage, EditSheet, ServingsPicker, ShoppingSheet, Sheet, StockBoard, Typing } from './components.jsx'

let nextId = 1
const bot = (text, extra = {}) => ({ id: nextId++, from: 'bot', text, ...extra })
const me = (text) => ({ id: nextId++, from: 'user', text })

const CATEGORY_ICONS = { gosht: '🥩', sabzavot: '🥕', don: '🌾', sut: '🥚', yog: '🫒', ziravor: '🧂', boshqa: '🧺' }

export default function App() {
  const [user, setUser] = useState(null)
  const [stock, setStock] = useState({ categories: [], count: 0 })
  const [recipes, setRecipes] = useState([])
  const [shopping, setShopping] = useState([])
  const [servings, setServings] = useState(() => Number(localStorage.getItem('servings')) || 3)

  const [view, setView] = useState('home') // home | chat
  const [messages, setMessages] = useState([])
  const [busy, setBusy] = useState('')
  const [session, setSession] = useState(null) // {slug, name, servings, steps, step, phase}

  const [sheet, setSheet] = useState(null) // {type: 'suggest'|'choose'|'shopping'|'edit', item?}
  const [input, setInput] = useState('')
  const [toast, setToast] = useState('')
  const chatEnd = useRef(null)

  const push = useCallback((...msgs) => setMessages((m) => [...m, ...msgs]), [])

  const showError = useCallback((e) => {
    haptic('error')
    setToast(e.message || 'Xatolik yuz berdi')
    setTimeout(() => setToast(''), 3500)
  }, [])

  // ---------------------------------------------------------------- yuklash
  useEffect(() => {
    Promise.all([api.me(), api.stock(), api.recipes(), api.shopping()])
      .then(([u, s, r, sh]) => {
        setUser(u)
        setStock(s)
        setRecipes(r)
        setShopping(sh)
      })
      .catch(showError)
  }, [showError])

  useEffect(() => {
    localStorage.setItem('servings', String(servings))
  }, [servings])

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy])

  // Telegram "Orqaga" tugmasi
  const goHome = useCallback(() => {
    setView('home')
    setSession(null)
    setMessages([])
  }, [])

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

  // ---------------------------------------------------------------- ombor
  async function addStock(e) {
    e?.preventDefault()
    const text = input.trim()
    if (!text || busy) return
    setBusy('Omborni yangilayapman...')
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
    setMessages([me(`Bugun nima ovqat qilsam ekan? Uyda ${n} kishi bormiz.`)])
    setBusy('Omborga qarab chiqyapman...')
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
    setView('chat')
    const label = slug ? recipes.find((r) => r.slug === slug)?.name : query
    setMessages((m) => (view === 'chat' ? [...m, me(`${label} qilmoqchiman, ${n} kishiga.`)] : [me(`${label} qilmoqchiman, ${n} kishiga.`)]))
    try {
      let target = slug
      if (!target) {
        setBusy("Retseptlar daftarimni varaqlayapman... Topolmasam, internetdan izlab ko'raman")
        const recipe = await api.resolve(query)
        target = recipe.slug
        if (!recipes.some((r) => r.slug === recipe.slug)) {
          setRecipes((rs) => [...rs, { slug: recipe.slug, name: recipe.name, time_minutes: recipe.time_minutes }])
        }
      }
      await runPlan(target, n)
    } catch (err) {
      push(bot(err.message))
      haptic('error')
    } finally {
      setBusy('')
    }
  }

  async function runPlan(slug, n) {
    setBusy('Masalliqlarni hisoblayapman...')
    try {
      const res = await api.plan(slug, n)
      const { check, recipe } = res
      setSession({ slug, name: recipe.name, servings: n, steps: recipe.steps, step: -1, phase: 'plan', missing: check.missing })
      const actions = check.ready
        ? [{ label: 'Boshladik! 🔥', action: 'start' }]
        : [
            { label: "Ha, ro'yxatga qo'sh 🛒", action: 'addMissing' },
            { label: 'Shundoq boshlayveramiz', action: 'start', secondary: true },
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
        push(me(`${payload.name} bo'la qolsin!`))
        await runPlan(payload.slug, servings)
      } else if (action === 'addMissing') {
        const items = session.missing.map((m) => ({ name: m.name, grams: Math.ceil(m.missing_g) }))
        const res = await api.addShopping(items)
        setShopping(res.items)
        push(me("Ha, qo'shib qo'y"), bot(res.message, { actions: [{ label: 'Boshlaymiz 🔥', action: 'start' }] }))
      } else if (action === 'start') {
        setBusy('Qozonni tayyorlayapman...')
        const res = await api.cookStart(session.slug, session.servings)
        setSession((s) => ({ ...s, phase: 'cooking', step: 0 }))
        push(bot(res.message), stepMessage(session.steps, 0))
      } else if (action === 'next') {
        const step = session.step + 1
        setSession((s) => ({ ...s, step }))
        push(stepMessage(session.steps, step))
      } else if (action === 'finish') {
        setBusy('Omborni yangilayapman...')
        const res = await api.cookFinish(session.slug, session.servings)
        setStock(res.stock)
        setSession((s) => ({ ...s, phase: 'done' }))
        haptic('success')
        push(me('Taom tayyor! ✅'), bot(res.message, { kind: 'finish', data: res.used, actions: [{ label: 'Bosh sahifaga', action: 'home' }] }))
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
      actions: last ? [{ label: 'Taom tayyor ✅', action: 'finish' }] : [{ label: 'Keyingi qadam →', action: 'next' }],
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
    setBusy("O'ylab ko'ryapman...")
    try {
      const payload = history.filter((m) => m.text).map((m) => ({ role: m.from === 'bot' ? 'assistant' : 'user', content: m.text }))
      const res = await api.chat(payload, session?.slug, session?.servings)
      // savol javobidan keyin ham oxirgi tugmalar ishlashi uchun ularni javobga ko'chiramiz
      const lastActions = [...messages].reverse().find((m) => m.actions)?.actions
      push(bot(res.reply, { actions: session?.phase !== 'done' ? lastActions : undefined }))
    } catch (err) {
      push(bot(err.message))
    } finally {
      setBusy('')
    }
  }

  // ---------------------------------------------------------------- render
  const lastActionable = [...messages].reverse().find((m) => m.actions || m.kind === 'suggestions')?.id
  const shoppingCount = shopping.length

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">🍲</span>
          <div>
            <div className="title">Pazanda</div>
            <div className="subtitle">{view === 'chat' && session ? session.name : "O'zbek oshxonasi yordamchisi"}</div>
          </div>
        </div>
        <button className="icon-btn" onClick={() => setSheet({ type: 'shopping' })} aria-label="Xarid ro'yxati">
          🛒{shoppingCount > 0 && <span className="badge">{shoppingCount}</span>}
        </button>
      </header>

      {view === 'home' && (
        <main className="home">
          {user && <div className="bubble bot greeting">{user.greeting}</div>}

          <section className="actions">
            <button className="action primary" onClick={() => setSheet({ type: 'suggest' })}>
              <span className="action-icon">🤔</span>
              <span>
                <b>Bugun nima ovqat qilsam ekan?</b>
                <small>Ombordagi masalliqlarga qarab tavsiya</small>
              </span>
            </button>
            <button className="action" onClick={() => setSheet({ type: 'choose' })}>
              <span className="action-icon">📖</span>
              <span>
                <b>O'zim ovqat tanlayman</b>
                <small>Taomni tanlang yoki yozing</small>
              </span>
            </button>
          </section>

          <StockBoard stock={stock} icons={CATEGORY_ICONS} onEdit={(item) => setSheet({ type: 'edit', item })} />
        </main>
      )}

      {view === 'chat' && (
        <main className="chat">
          {messages.map((m) => (
            <ChatMessage key={m.id} msg={m} active={m.id === lastActionable && !busy} onAction={handleAction} />
          ))}
          {busy && <Typing text={busy} />}
          <div ref={chatEnd} />
        </main>
      )}

      <form className="bottombar" onSubmit={view === 'home' ? addStock : askChef}>
        {view === 'chat' && !user?.llm ? (
          <button type="button" className="ghost wide" onClick={goHome}>
            ← Bosh sahifaga
          </button>
        ) : (
          <>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={view === 'home' ? "Masalan: 2 kg guruch, 10 ta piyoz, 1 kg go'sht" : 'Oshpazga savol bering...'}
              disabled={!!busy && view === 'home'}
              enterKeyHint="send"
            />
            <button type="submit" className="send" disabled={!input.trim() || !!busy} aria-label="Yuborish">
              {view === 'home' ? '＋' : '➤'}
            </button>
          </>
        )}
      </form>

      {toast && <div className="toast">{toast}</div>}

      {sheet?.type === 'suggest' && (
        <Sheet title="Uyda nechta odam bor bugun?" onClose={() => setSheet(null)}>
          <ServingsPicker value={servings} onChange={setServings} />
          <button className="btn wide" onClick={() => runSuggest(servings)}>
            Tavsiya bering
          </button>
        </Sheet>
      )}

      {sheet?.type === 'choose' && (
        <ChooseSheet recipes={recipes} servings={servings} setServings={setServings} onClose={() => setSheet(null)} onSubmit={runChoose} />
      )}

      {sheet?.type === 'shopping' && (
        <ShoppingSheet
          items={shopping}
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

      {sheet?.type === 'edit' && <EditSheet item={sheet.item} onClose={() => setSheet(null)} onSave={saveStockItem} />}
    </div>
  )
}

function ChooseSheet({ recipes, servings, setServings, onClose, onSubmit }) {
  const [slug, setSlug] = useState('')
  const [query, setQuery] = useState('')
  const ready = slug || query.trim()
  return (
    <Sheet title="O'zim ovqat tanlayman" onClose={onClose}>
      <label className="field">
        <span>Taom</span>
        <select
          value={slug}
          onChange={(e) => {
            setSlug(e.target.value)
            setQuery('')
          }}
        >
          <option value="">— Ro'yxatdan tanlang —</option>
          {recipes.map((r) => (
            <option key={r.slug} value={r.slug}>
              {r.name} · {r.time_minutes} daq
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>yoki yozing</span>
        <input
          value={query}
          placeholder="Masalan: norin, qovurma lag'mon"
          onChange={(e) => {
            setQuery(e.target.value)
            setSlug('')
          }}
        />
      </label>
      <div className="field">
        <span>Uyda nechta odam bor bugun?</span>
        <ServingsPicker value={servings} onChange={setServings} />
      </div>
      <button className="btn wide" disabled={!ready} onClick={() => onSubmit(slug ? { slug } : { query: query.trim() }, servings)}>
        Hisoblab ber
      </button>
    </Sheet>
  )
}

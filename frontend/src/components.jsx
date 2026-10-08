import { useState } from 'react'

export function StockBoard({ stock, icons, onEdit }) {
  if (!stock.count) {
    return (
      <section className="empty">
        <div className="empty-icon">🧺</div>
        <b>Ombor hozircha bo'sh</b>
        <p>Bozordan nima olib kelganingizni pastdagi qatorga yozing — o'zim tartiblab qo'yaman.</p>
      </section>
    )
  }
  return (
    <section className="stock">
      <h2>Oshxona omborim</h2>
      <div className="cards">
        {stock.categories.map((cat) => (
          <div className="card" key={cat.key}>
            <div className="card-title">
              <span>{icons[cat.key] || '🧺'}</span> {cat.title}
            </div>
            <ul>
              {cat.items.map((item) => (
                <li key={item.id} onClick={() => onEdit(item)}>
                  <span className="item-name">{item.name}</span>
                  <span className="item-qty">{item.label}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  )
}

export function ChatMessage({ msg, active, onAction }) {
  return (
    <div className={`msg ${msg.from}`}>
      {msg.kind === 'step' && (
        <div className="step-label">
          {msg.data.index + 1}-qadam / {msg.data.total}
        </div>
      )}
      <div className={`bubble ${msg.from} ${msg.kind || ''}`}>
        {msg.text && <p className="text">{msg.text}</p>}
        {msg.kind === 'suggestions' && <Suggestions items={msg.data} active={active} onAction={onAction} />}
        {msg.kind === 'plan' && <PlanDetails check={msg.data.check} recipe={msg.data.recipe} />}
        {msg.kind === 'finish' && msg.data.length > 0 && (
          <ul className="used">
            {msg.data.map((u) => (
              <li key={u.name}>
                − {u.label} {u.name}
              </li>
            ))}
          </ul>
        )}
      </div>
      {msg.actions && active && (
        <div className="msg-actions">
          {msg.actions.map((a) => (
            <button key={a.action} className={a.secondary ? 'btn ghost' : 'btn'} onClick={() => onAction(a.action, a.payload)}>
              {a.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function Suggestions({ items, active, onAction }) {
  if (!items.length) return null
  return (
    <div className="suggestions">
      {items.map((s) => (
        <div className={`suggestion ${s.ready ? 'ready' : ''}`} key={s.slug}>
          <div className="suggestion-head">
            <b>{s.name}</b>
            <span className="coverage">{Math.round(s.coverage * 100)}%</span>
          </div>
          <div className="meter">
            <span style={{ width: `${Math.round(s.coverage * 100)}%` }} />
          </div>
          {s.missing.length > 0 && <small>Yetishmaydi: {s.missing.map((m) => `${m.missing_label} ${m.name}`).join(', ')}</small>}
          {active && (
            <button className="btn small" onClick={() => onAction('choose', { slug: s.slug, name: s.name })}>
              Shuni tanlayman
            </button>
          )}
        </div>
      ))}
    </div>
  )
}

function PlanDetails({ check, recipe }) {
  const [open, setOpen] = useState(false)
  const items = check.ingredients.filter((i) => !i.staple)
  return (
    <div className="plan">
      <button className="link" onClick={() => setOpen(!open)}>
        {open ? 'Masalliqlarni yashirish ▴' : `Masalliqlar (${check.servings} kishiga) · ${recipe.time_minutes} daqiqa ▾`}
      </button>
      {open && (
        <ul className="ingredients">
          {items.map((i) => (
            <li key={i.name} className={i.missing_g > 5 && !i.optional ? 'missing' : ''}>
              <span>
                {i.name}
                {i.optional && <em> (ixtiyoriy)</em>}
              </span>
              <span>{i.need_label}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function Typing({ text }) {
  return (
    <div className="msg bot">
      <div className="bubble bot typing">
        <span className="dots">
          <i />
          <i />
          <i />
        </span>
        {text}
      </div>
    </div>
  )
}

export function Sheet({ title, onClose, children }) {
  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <div className="sheet-head">
          <b>{title}</b>
          <button className="icon-btn" onClick={onClose} aria-label="Yopish">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function ServingsPicker({ value, onChange }) {
  return (
    <div className="servings">
      <button type="button" onClick={() => onChange(Math.max(1, value - 1))} aria-label="Kamaytirish">
        −
      </button>
      <div className="servings-value">
        <b>{value}</b>
        <small>kishi</small>
      </div>
      <button type="button" onClick={() => onChange(Math.min(50, value + 1))} aria-label="Ko'paytirish">
        +
      </button>
    </div>
  )
}

export function ShoppingSheet({ items, onClose, onBought, onDelete }) {
  return (
    <Sheet title="Xarid ro'yxati" onClose={onClose}>
      {!items.length ? (
        <p className="muted">Ro'yxat bo'sh. Taom uchun nima yetishmasa, shu yerga qo'shib qo'yaman.</p>
      ) : (
        <ul className="shopping">
          {items.map((item) => (
            <li key={item.id}>
              <span>
                <b>{item.name}</b>
                <small>{item.label}</small>
              </span>
              <span className="row-actions">
                <button className="btn small" onClick={() => onBought(item)}>
                  Oldim ✓
                </button>
                <button className="icon-btn" onClick={() => onDelete(item)} aria-label="O'chirish">
                  🗑
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </Sheet>
  )
}

export function EditSheet({ item, onClose, onSave }) {
  const [grams, setGrams] = useState(String(item.grams))
  return (
    <Sheet title={item.name} onClose={onClose}>
      <label className="field">
        <span>Miqdori (gramm)</span>
        <input type="number" inputMode="numeric" min="0" value={grams} onChange={(e) => setGrams(e.target.value)} />
      </label>
      <div className="row">
        <button className="btn ghost" onClick={() => onSave(item, 0)}>
          O'chirish
        </button>
        <button className="btn" onClick={() => onSave(item, Number(grams) || 0)}>
          Saqlash
        </button>
      </div>
    </Sheet>
  )
}

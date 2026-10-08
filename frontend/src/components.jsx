import { useState } from 'react'
import { LANGS } from './i18n.js'

export function StockBoard({ stock, icons, t, onEdit }) {
  if (!stock.count) {
    return (
      <section className="empty">
        <div className="empty-icon">🧺</div>
        <b>{t('emptyTitle')}</b>
        <p>{t('emptyText')}</p>
      </section>
    )
  }
  return (
    <section className="stock">
      <h2>{t('stockTitle')}</h2>
      <div className="cards">
        {stock.categories.map((cat) => (
          <div className="card" key={cat.key}>
            <div className="card-title">
              <span>{icons[cat.key] || '🧺'}</span> {cat.title}
            </div>
            <ul>
              {cat.items.map((item) => (
                <li key={item.id} onClick={() => onEdit(item)}>
                  <span className="item-name">{item.display || item.name}</span>
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

export function ChatMessage({ msg, t, active, onAction }) {
  return (
    <div className={`msg ${msg.from}`}>
      {msg.kind === 'step' && <div className="step-label">{t('step', { i: msg.data.index + 1, n: msg.data.total })}</div>}
      <div className={`bubble ${msg.from} ${msg.kind || ''}`}>
        {msg.text && <p className="text">{msg.text}</p>}
        {msg.kind === 'suggestions' && <Suggestions items={msg.data} t={t} active={active} onAction={onAction} />}
        {msg.kind === 'plan' && <PlanDetails check={msg.data.check} recipe={msg.data.recipe} t={t} />}
        {msg.kind === 'finish' && msg.data.length > 0 && (
          <ul className="used">
            {msg.data.map((u) => (
              <li key={u.name}>
                − {u.label} {u.display || u.name}
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

function Suggestions({ items, t, active, onAction }) {
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
          {s.missing.length > 0 && (
            <small>
              {t('missingPrefix')} {s.missing.map((m) => `${m.missing_label} ${m.display || m.name}`).join(', ')}
            </small>
          )}
          {active && (
            <button className="btn small" onClick={() => onAction('choose', { slug: s.slug, name: s.name })}>
              {t('pickThis')}
            </button>
          )}
        </div>
      ))}
    </div>
  )
}

function PlanDetails({ check, recipe, t }) {
  const [open, setOpen] = useState(false)
  const items = check.ingredients.filter((i) => !i.staple)
  return (
    <div className="plan">
      <button className="link" onClick={() => setOpen(!open)}>
        {open ? t('hideIngr') : t('showIngr', { n: check.servings, m: recipe.time_minutes })}
      </button>
      {open && (
        <ul className="ingredients">
          {items.map((i) => (
            <li key={i.name} className={i.missing_g > 5 && !i.optional ? 'missing' : ''}>
              <span>
                {i.display || i.name}
                {i.optional && <em> ({t('optional')})</em>}
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

export function Sheet({ title, t, onClose, children }) {
  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <div className="sheet-head">
          <b>{title}</b>
          <button className="icon-btn" onClick={onClose} aria-label={t('close')}>
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function LanguageList({ current, onPick, highlight = false }) {
  return (
    <div className="languages">
      {LANGS.map((l) => (
        <button
          key={l.code}
          className={`language ${l.code === current ? (highlight ? 'suggested' : 'selected') : ''}`}
          onClick={() => onPick(l.code)}
        >
          <span className="flag">{l.flag}</span>
          <span>{l.label}</span>
          {l.code === current && !highlight && <span className="check">✓</span>}
        </button>
      ))}
    </div>
  )
}

export function ServingsPicker({ value, onChange, t }) {
  return (
    <div className="servings">
      <button type="button" onClick={() => onChange(Math.max(1, value - 1))} aria-label={t('decrease')}>
        −
      </button>
      <div className="servings-value">
        <b>{value}</b>
        <small>{t('people')}</small>
      </div>
      <button type="button" onClick={() => onChange(Math.min(50, value + 1))} aria-label={t('increase')}>
        +
      </button>
    </div>
  )
}

export function ShoppingSheet({ items, t, onClose, onBought, onDelete }) {
  return (
    <Sheet title={t('cart')} t={t} onClose={onClose}>
      {!items.length ? (
        <p className="muted">{t('shoppingEmpty')}</p>
      ) : (
        <ul className="shopping">
          {items.map((item) => (
            <li key={item.id}>
              <span>
                <b>{item.display || item.name}</b>
                <small>{item.label}</small>
              </span>
              <span className="row-actions">
                <button className="btn small" onClick={() => onBought(item)}>
                  {t('bought')}
                </button>
                <button className="icon-btn" onClick={() => onDelete(item)} aria-label={t('remove')}>
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

export function EditSheet({ item, t, onClose, onSave }) {
  const [grams, setGrams] = useState(String(item.grams))
  return (
    <Sheet title={item.display || item.name} t={t} onClose={onClose}>
      <label className="field">
        <span>{t('amountLabel')}</span>
        <input type="number" inputMode="numeric" min="0" value={grams} onChange={(e) => setGrams(e.target.value)} />
      </label>
      <div className="row">
        <button className="btn ghost" onClick={() => onSave(item, 0)}>
          {t('remove')}
        </button>
        <button className="btn" onClick={() => onSave(item, Number(grams) || 0)}>
          {t('save')}
        </button>
      </div>
    </Sheet>
  )
}

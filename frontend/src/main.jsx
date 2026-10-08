import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import { tg } from './api.js'
import './styles.css'

if (tg) {
  tg.ready()
  tg.expand()
  // Telegramdan tashqarida colorScheme doim "light" — u holda tizim mavzusiga ishonamiz
  if (tg.initData) {
    document.documentElement.dataset.scheme = tg.colorScheme
    tg.onEvent?.('themeChanged', () => {
      document.documentElement.dataset.scheme = tg.colorScheme
    })
  }
}

createRoot(document.getElementById('root')).render(<App />)

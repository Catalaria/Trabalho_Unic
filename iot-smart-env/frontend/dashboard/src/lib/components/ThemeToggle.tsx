import React from 'react'

export default function ThemeToggle() {
  const [dark, setDark] = React.useState<boolean>(() =>
    document.documentElement.classList.contains('dark'),
  )

  const toggle = () => {
    const next = !dark
    setDark(next)
    document.documentElement.classList.toggle('dark', next)
    localStorage.setItem('theme', next ? 'dark' : 'light')
  }

  return (
    <button onClick={toggle} className="btn-ghost px-3" title="Alternar tema">
      {dark ? '🌙' : '☀️'}
      <span className="sr-only">Alternar tema</span>
    </button>
  )
}

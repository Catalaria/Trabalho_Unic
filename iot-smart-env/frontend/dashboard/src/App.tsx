import React from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './lib/pages/Dashboard'
import Rules from './lib/pages/Rules'
import ThemeToggle from './lib/components/ThemeToggle'

function Header() {
  return (
    <div className="sticky top-0 border-b backdrop-blur bg-white/70 dark:bg-slate-900/70">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="font-extrabold">IoT Dashboard</div>
          <nav className="flex gap-2">
            <NavLink to="/" className="btn-ghost">
              Dashboard
            </NavLink>
            <NavLink to="/rules" className="btn-ghost">
              Regras
            </NavLink>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">Sem login</span>
          <ThemeToggle />
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <div className="max-w-6xl mx-auto px-4 py-6 space-y-4">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/rules" element={<Rules />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

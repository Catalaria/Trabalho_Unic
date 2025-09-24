import React from 'react'
import { createRoot } from 'react-dom/client'

const App = () => (
  <div style={{ fontFamily: 'system-ui', padding: 16 }}>
    <h1>Proto3 Charts (mínimo)</h1>
    <p>React + Vite + TypeScript funcionando.</p>
  </div>
)

const root = document.getElementById('root')!
createRoot(root).render(<App />)

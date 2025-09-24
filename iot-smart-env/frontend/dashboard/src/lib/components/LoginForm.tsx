import React from 'react'
import { setToken } from '../api'

type Props = {
  onDone?: (token: string) => void
}

export default function LoginForm({ onDone }: Props) {
  const [token, setTokenInput] = React.useState('admin-demo-token')
  const [show, setShow] = React.useState(false)

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setToken(token)
    onDone?.(token)
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <h2 className="text-lg font-semibold">Login administrativo (simulado)</h2>
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Token padrão do backend:{' '}
        <code className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800">
          admin-demo-token
        </code>
      </p>

      <label className="block space-y-1">
        <span className="label">Token</span>
        <div className="relative">
          <input
            className="input pr-10"
            type={show ? 'text' : 'password'}
            value={token}
            onChange={(e) => setTokenInput(e.target.value)}
            placeholder="admin-demo-token"
            required
          />
          <button
            type="button"
            className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500 hover:text-gray-800 dark:hover:text-gray-200"
            onClick={() => setShow((s) => !s)}
          >
            {show ? 'Ocultar' : 'Mostrar'}
          </button>
        </div>
      </label>

      <div className="flex items-center gap-2">
        <button className="btn-primary" type="submit">
          Entrar
        </button>
        <button
          className="btn-ghost"
          type="button"
          onClick={() => setTokenInput('admin-demo-token')}
        >
          Usar padrão
        </button>
      </div>
    </form>
  )
}

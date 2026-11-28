import { useState } from 'react'
import type { FormEvent } from 'react'
import { errorMessage, login } from '../api'

type LoginFormProps = {
  onLoggedIn: (username: string) => void
  onCancel: () => void
}

// Admin login. Accounts are made on the server with
// `python -m app.manage_admins add <username>`, never from here.
function LoginForm({ onLoggedIn, onCancel }: LoginFormProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const admin = await login(username, password)
      if (admin.username !== null) {
        onLoggedIn(admin.username)
      }
    } catch (err) {
      setError(errorMessage(err))
      setPassword('') // don't leave a wrong password sitting in the box
      setSubmitting(false)
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <p className="form-hint">
        Only admins log in. Everyone else can view the schedule and upload their own class
        calendar without an account.
      </p>
      <label>
        Username
        <input
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
          required
        />
      </label>
      <label>
        Password
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
        />
      </label>

      {error && <p className="form-error">{error}</p>}

      <div className="form-actions">
        <button type="button" className="button" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="button primary" disabled={submitting}>
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
      </div>
    </form>
  )
}

export default LoginForm

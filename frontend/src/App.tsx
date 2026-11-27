import { useEffect, useState } from 'react'
import { getSwimmers } from './api'
import type { Swimmer } from './types'

function App() {
  const [swimmers, setSwimmers] = useState<Swimmer[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadSwimmers() {
      try {
        setSwimmers(await getSwimmers())
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err))
      }
    }

    loadSwimmers()
  }, [])

  if (error) {
    return <p>Couldn't load swimmers: {error}</p>
  }

  return (
    <div>
      <h1>Swimmers</h1>
      {swimmers.length === 0 && <p>No swimmers yet.</p>}
      <ul>
        {swimmers.map((swimmer) => (
          <li key={swimmer.swimmer_id}>
            {swimmer.first_name} {swimmer.last_name}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default App
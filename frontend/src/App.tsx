import { useEffect, useState } from 'react'

type WeightsGroup = 'THREE_DAY_A' | 'THREE_DAY_B' | 'FOUR_DAY'

type Swimmer = {
  swimmer_id: number
  first_name: string
  last_name: string
  weights_group: WeightsGroup
  tags: string[]
  has_schedule: boolean
}

function App() {
  const [swimmers, setSwimmers] = useState<Swimmer[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadSwimmers() {
      try {
        const response = await fetch('/api/swimmers')
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`)
        }
        const data: Swimmer[] = await response.json()
        setSwimmers(data)
      } catch (err) {
        setError(String(err))
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
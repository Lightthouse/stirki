import { useState } from 'react'

const BUSY_TIMERS = ['~5 мин', '~10 мин', '~15 мин', '~20 мин', '~30 мин']
const STORAGE_KEY = 'machines_state'
const TTL_MS = 60 * 60 * 1000

interface MachineState {
  id: number
  name: string
  status: 'free' | 'busy'
  timer: string
}

interface StoredState {
  timestamp: number
  machines: MachineState[]
}

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function generateMachines(): MachineState[] {
  const freeCount = randomInt(1, 4)
  const ids = shuffle([1, 2, 3, 4])
  return ids
    .map((id, idx) => ({
      id,
      name: `№${id}`,
      status: (idx < freeCount ? 'free' : 'busy') as 'free' | 'busy',
      timer: idx < freeCount ? 'готова' : BUSY_TIMERS[randomInt(0, BUSY_TIMERS.length - 1)],
    }))
    .sort((a, b) => a.id - b.id)
}

function loadOrGenerateMachines(): MachineState[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const stored: StoredState = JSON.parse(raw)
      if (Date.now() - stored.timestamp < TTL_MS) {
        return stored.machines
      }
    }
  } catch {
    // ignore corrupt storage
  }
  const machines = generateMachines()
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ timestamp: Date.now(), machines }))
  } catch {
    // ignore
  }
  return machines
}

interface Props {
  onHintActivate: () => void
  hintActive: boolean
  onMachineSelect?: () => void
  freeTariffAvailable: boolean
}

export function MachinesCard({ onHintActivate, hintActive, onMachineSelect, freeTariffAvailable }: Props) {
  const [machines] = useState<MachineState[]>(loadOrGenerateMachines)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  function occupy(id: number) {
    setSelectedId(id)
    onHintActivate()
    onMachineSelect?.()
  }

  function getBtnClass(m: MachineState) {
    if (!freeTariffAvailable) return 'machine-occupy-btn'
    if (selectedId === m.id) return 'machine-occupy-btn occupied'
    if (m.status === 'free') return 'machine-occupy-btn available'
    return 'machine-occupy-btn'
  }

  function isUnavailable(m: MachineState) {
    return !freeTariffAvailable || m.status === 'busy'
  }

  return (
    <div className="swipe-card">
      <div className="card-content">
        <h3 style={{ color: '#4F9DA7', textAlign: 'center', marginBottom: 16, fontSize: 16 }}>
          <i className="fas fa-tachometer-alt" /> Выберите стиральную машину для бесплатной стирки
        </h3>

        {!freeTariffAvailable && (
          <p style={{ textAlign: 'center', color: '#e05a5a', marginBottom: 12, fontSize: 14 }}>
            <i className="fas fa-clock" /> Все машины заняты, попробуйте позже
          </p>
        )}

        <div className="machines-grid">
          {machines.map((m) => (
            <div key={m.id} className={`machine-mini${selectedId === m.id ? ' selected' : ''}`}>
              <div className="machine-icon">
                <i className="fas fa-tshirt" />
              </div>
              <div className="machine-name">{m.name}</div>
              <div className="machine-status">
                {freeTariffAvailable && m.status === 'free' ? 'свободна' : 'занята'}
              </div>
              <div className="machine-timer">{freeTariffAvailable ? m.timer : '—'}</div>
              <button
                className={getBtnClass(m)}
                disabled={isUnavailable(m) && selectedId !== m.id}
                onClick={() => !isUnavailable(m) && selectedId !== m.id && occupy(m.id)}
              >
                {selectedId === m.id ? (
                  <><i className="fas fa-check" /> выбрана</>
                ) : isUnavailable(m) ? (
                  'недоступна'
                ) : (
                  'выбрать'
                )}
              </button>
            </div>
          ))}
        </div>

        <div className={`swipe-hint${hintActive ? ' active' : ''}`}>
          <i className="fas fa-chevron-up" /> потяните вверх <i className="fas fa-chevron-up" />
        </div>
      </div>
    </div>
  )
}

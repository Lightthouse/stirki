import { useState } from 'react'

const MACHINES = [
  { id: 1, name: '№1', status: 'busy', timer: '~15 мин' },
  { id: 2, name: '№2', status: 'free', timer: 'готова' },
  { id: 3, name: '№3', status: 'busy', timer: '~7 мин' },
  { id: 4, name: '№4', status: 'free', timer: 'готова' },
]

interface Props {
  onHintActivate: () => void
  hintActive: boolean
  onMachineSelect?: () => void
}

export function MachinesCard({ onHintActivate, hintActive, onMachineSelect }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null)

  function occupy(id: number) {
    setSelectedId(id)
    onHintActivate()
    onMachineSelect?.()
  }

  function getBtnClass(m: typeof MACHINES[0]) {
    if (selectedId === m.id) return 'machine-occupy-btn occupied'
    if (m.status === 'free') return 'machine-occupy-btn available'
    return 'machine-occupy-btn'
  }

  return (
    <div className="swipe-card">
      <div className="card-content">
        <h3 style={{ color: '#4F9DA7', textAlign: 'center', marginBottom: 16, fontSize: 16 }}>
          <i className="fas fa-tachometer-alt" /> Выберите стиральную машину для бесплатной стирки
        </h3>

        <div className="machines-grid">
          {MACHINES.map((m) => (
            <div key={m.id} className={`machine-mini${selectedId === m.id ? ' selected' : ''}`}>
              <div className="machine-icon">
                <i className="fas fa-tshirt" />
              </div>
              <div className="machine-name">{m.name}</div>
              <div className="machine-status">
                {m.status === 'free' ? 'свободна' : 'занята'}
              </div>
              <div className="machine-timer">{m.timer}</div>
              <button
                className={getBtnClass(m)}
                disabled={m.status === 'busy' && selectedId !== m.id}
                onClick={() => m.status === 'free' && selectedId !== m.id && occupy(m.id)}
              >
                {selectedId === m.id ? (
                  <><i className="fas fa-check" /> выбрана</>
                ) : m.status === 'busy' ? (
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

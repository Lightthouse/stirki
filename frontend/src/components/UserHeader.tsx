import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { clearToken, clearPhone, getPhone, isAuthenticated } from '../api/client'

export function UserHeader() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  if (!isAuthenticated()) return null

  const phone = getPhone() ?? ''

  function handleLogout() {
    clearToken()
    clearPhone()
    navigate('/')
  }

  return (
    <div style={{ position: 'absolute', top: '1rem', right: '1rem', zIndex: 100 }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          background: 'none',
          border: '1px solid #ccc',
          borderRadius: '2rem',
          padding: '0.3rem 0.8rem',
          cursor: 'pointer',
          fontSize: '0.9rem',
        }}
      >
        <span>👤</span>
        <span>{phone}</span>
      </button>
      {open && (
        <div
          style={{
            position: 'absolute',
            right: 0,
            marginTop: '0.4rem',
            background: '#fff',
            border: '1px solid #ddd',
            borderRadius: '0.5rem',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            minWidth: '140px',
          }}
        >
          <button
            onClick={handleLogout}
            style={{
              display: 'block',
              width: '100%',
              padding: '0.7rem 1rem',
              background: 'none',
              border: 'none',
              textAlign: 'left',
              cursor: 'pointer',
              fontSize: '0.9rem',
            }}
          >
            Выйти
          </button>
        </div>
      )}
    </div>
  )
}

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/LoginPage'
import { OrderPage } from './pages/OrderPage'

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', width: '100%', background: '#0f1720' }}>
        <div className="app">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/order" element={<OrderPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}

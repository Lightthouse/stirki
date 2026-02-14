import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { OrderPage } from './pages/OrderPage'
import { OrdersPage } from './pages/OrdersPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<OrderPage />} />
        <Route path="/orders" element={<OrdersPage />} />
      </Routes>
    </BrowserRouter>
  )
}

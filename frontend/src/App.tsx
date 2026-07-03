import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import HomePage from './pages/HomePage'
import SwingPage from './pages/SwingPage'
import StockPage from './pages/StockPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<HomePage />} />
        <Route path="/swing" element={<SwingPage />} />
        <Route path="/stock/:ticker" element={<StockPage />} />
      </Routes>
    </BrowserRouter>
  )
}

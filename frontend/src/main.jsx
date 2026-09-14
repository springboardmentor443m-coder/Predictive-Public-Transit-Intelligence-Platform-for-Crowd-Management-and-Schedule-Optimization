import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import Overview from './pages/Overview'
import Crowd from './pages/Crowd'
import Scheduling from './pages/Scheduling'
import Predictions from './pages/Predictions'
import Alerts from './pages/Alerts'
import Analytics from './pages/Analytics'
import { Login, Guard } from './pages/Login'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Guard><Overview /></Guard>} />
        <Route path="/crowd" element={<Guard><Crowd /></Guard>} />
        <Route path="/scheduling" element={<Guard><Scheduling /></Guard>} />
        <Route path="/predictions" element={<Guard><Predictions /></Guard>} />
        <Route path="/alerts" element={<Guard><Alerts /></Guard>} />
        <Route path="/analytics" element={<Guard><Analytics /></Guard>} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)

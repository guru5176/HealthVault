import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Vault from './pages/Vault'
import Chat from './pages/Chat'
import CareRouter from './pages/CareRouter'

function App() {
  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/vault" element={<Vault />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/care-router" element={<CareRouter />} />
        </Routes>
      </main>
    </div>
  )
}

export default App

import { useState } from 'react'
import TicketList from './components/TicketList'
import CreateTicketForm from './components/CreateTicketForm'
import AnalyticsDashboard from './components/AnalyticsDashboard'
import ThresholdSettings from './components/ThresholdSettings'
import './App.css'

const TABS = [
  { id: 'tickets', label: 'Tickets' },
  { id: 'create', label: 'Create Ticket' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'settings', label: 'Settings' },
]

function App() {
  const [activeTab, setActiveTab] = useState('tickets')
  const [refreshKey, setRefreshKey] = useState(0)

  function handleTicketCreated() {
    setRefreshKey((k) => k + 1)
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>IT Helpdesk Dashboard</h1>
        <nav className="tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="app-main">
        {activeTab === 'tickets' && <TicketList refreshKey={refreshKey} />}
        {activeTab === 'create' && <CreateTicketForm onCreated={handleTicketCreated} />}
        {activeTab === 'analytics' && <AnalyticsDashboard refreshKey={refreshKey} />}
        {activeTab === 'settings' && <ThresholdSettings />}
      </main>
    </div>
  )
}

export default App

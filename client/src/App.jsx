import { useState } from 'react'
import { patients } from './data/patients'
import PatientList from './components/PatientList'
import ClaimCard from './components/ClaimCard'
import VickiResponse from './components/VickiResponse'
import BreakdownChart from './components/BreakdownChart'

export default function App() {
  const [selectedPatient, setSelectedPatient] = useState(patients[0])
  const [demoMode, setDemoMode] = useState(false)
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSelectPatient = (patient) => {
    setSelectedPatient(patient)
    setResponse(null)
    setError(null)
  }

  const handleGenerate = async () => {
    if (demoMode) {
      setResponse(selectedPatient.demoResponse)
      return
    }

    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient: selectedPatient,
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.error || `Server error ${res.status}`)
      }

      const data = await res.json()
      setResponse(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">V</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">Vicki</h1>
            <p className="text-xs text-gray-500">Billing Support Assistant</p>
          </div>
          {demoMode && (
            <span className="ml-2 px-2 py-0.5 bg-orange-100 text-orange-700 text-xs font-semibold rounded-full border border-orange-200 uppercase tracking-wide">
              Demo
            </span>
          )}
        </div>
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <span className="text-sm text-gray-600 font-medium">Demo Mode</span>
          <div
            onClick={() => {
              setDemoMode((d) => !d)
              setResponse(null)
              setError(null)
            }}
            className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
              demoMode ? 'bg-orange-400' : 'bg-gray-300'
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${
                demoMode ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </div>
        </label>
      </header>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel */}
        <aside className="w-80 border-r border-gray-200 bg-white overflow-y-auto">
          <div className="px-4 py-3 border-b border-gray-100">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Patient Inquiries
            </p>
          </div>
          <PatientList
            patients={patients}
            selected={selectedPatient}
            onSelect={handleSelectPatient}
          />
        </aside>

        {/* Right panel */}
        <main className="flex-1 overflow-y-auto p-6 space-y-5">
          {selectedPatient && (
            <>
              <ClaimCard patient={selectedPatient} />
              <BreakdownChart claim={selectedPatient.claim} />
              <VickiResponse
                demoMode={demoMode}
                response={response}
                loading={loading}
                error={error}
                onGenerate={handleGenerate}
              />
            </>
          )}
        </main>
      </div>
    </div>
  )
}

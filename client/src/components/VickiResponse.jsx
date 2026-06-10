import { useState, useEffect } from 'react'

const sections = [
  { key: 'greeting', label: null, bg: 'bg-white' },
  { key: 'why_you_owe', label: 'Why You Owe This', bg: 'bg-blue-50' },
  { key: 'what_this_means', label: 'What This Means', bg: 'bg-purple-50' },
  { key: 'next_steps', label: 'What to Do Next', bg: 'bg-green-50' },
  { key: 'signoff', label: null, bg: 'bg-white' },
]

function formatAsPlainText(response) {
  if (!response) return ''
  return [
    response.greeting,
    '',
    'WHY YOU OWE THIS',
    response.why_you_owe,
    '',
    'WHAT THIS MEANS',
    response.what_this_means,
    '',
    'WHAT TO DO NEXT',
    response.next_steps,
    '',
    response.signoff,
    '',
    'Vicki',
    'Billing Support',
  ].join('\n')
}

export default function VickiResponse({ demoMode, response, loading, error, onGenerate }) {
  const [editMode, setEditMode] = useState(false)
  const [editedText, setEditedText] = useState('')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (response) {
      setEditedText(formatAsPlainText(response))
      setEditMode(false)
    }
  }, [response])

  const handleCopy = async () => {
    const text = editMode ? editedText : formatAsPlainText(response)
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">Vicki's Response</h3>
          <p className="text-xs text-gray-400 mt-0.5">AI-generated billing explanation</p>
        </div>
        {response && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setEditMode((e) => !e)}
              className="text-xs px-3 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
            >
              {editMode ? 'View formatted' : 'Edit'}
            </button>
            <button
              onClick={handleCopy}
              className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                copied
                  ? 'bg-green-100 text-green-700 border border-green-200'
                  : 'bg-indigo-600 text-white hover:bg-indigo-700'
              }`}
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        )}
      </div>

      <div className="p-5">
        {!response && !loading && !error && (
          <div className="text-center py-10">
            <div className="w-12 h-12 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-3 3-3-3z" />
              </svg>
            </div>
            <p className="text-sm text-gray-500 mb-4">
              {demoMode
                ? 'Click below to view the pre-written demo response for this patient.'
                : 'Click below to generate a plain-English email response from Vicki.'}
            </p>
            <button
              onClick={onGenerate}
              className="px-5 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
            >
              {demoMode ? 'Show demo response' : 'Generate response'}
            </button>
          </div>
        )}

        {loading && (
          <div className="text-center py-10">
            <div className="w-8 h-8 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-3" />
            <p className="text-sm text-gray-500">Vicki is drafting a response...</p>
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
            <p className="text-sm text-red-700 font-medium mb-1">Something went wrong</p>
            <p className="text-xs text-red-600">{error}</p>
            <button
              onClick={onGenerate}
              className="mt-3 text-xs px-3 py-1.5 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              Try again
            </button>
          </div>
        )}

        {response && (
          <>
            {editMode ? (
              <textarea
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                className="w-full h-72 text-sm text-gray-700 border border-gray-200 rounded-lg p-3 resize-y focus:outline-none focus:ring-2 focus:ring-indigo-300 font-mono"
              />
            ) : (
              <div className="space-y-3">
                {sections.map(({ key, label, bg }) => (
                  <div key={key} className={`rounded-lg p-4 ${bg}`}>
                    {label && (
                      <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5">
                        {label}
                      </p>
                    )}
                    <p className="text-sm text-gray-800 leading-relaxed">{response[key]}</p>
                  </div>
                ))}
                <div className="pt-1 flex items-center gap-1.5 text-xs text-gray-400">
                  <span className="w-4 h-4 bg-indigo-600 rounded flex items-center justify-center">
                    <span className="text-white font-bold" style={{ fontSize: '9px' }}>V</span>
                  </span>
                  Vicki, Billing Support
                </div>
              </div>
            )}

            <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
              <button
                onClick={onGenerate}
                className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
              >
                {demoMode ? 'Reload demo response' : 'Regenerate'}
              </button>
              <button
                onClick={handleCopy}
                className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                  copied
                    ? 'bg-green-100 text-green-700 border border-green-200'
                    : 'bg-indigo-600 text-white hover:bg-indigo-700'
                }`}
              >
                {copied ? 'Copied!' : 'Copy for email'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

import { scenarioColors } from '../data/patients'

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'UTC',
  })
}

function ClaimRow({ label, value, highlight }) {
  return (
    <div className={`flex justify-between items-center py-2 px-3 rounded-md ${highlight ? 'bg-indigo-50' : ''}`}>
      <span className="text-sm text-gray-500">{label}</span>
      <span className={`text-sm font-medium ${highlight ? 'text-indigo-700 font-semibold' : 'text-gray-900'}`}>
        {value}
      </span>
    </div>
  )
}

export default function ClaimCard({ patient }) {
  const { claim } = patient
  const colors = scenarioColors[patient.scenario]

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-gray-900">{patient.name}</h2>
          <p className="text-xs text-gray-500 mt-0.5">{claim.carrier} &middot; {claim.plan}</p>
        </div>
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${colors.bg} ${colors.text}`}>
          {colors.label}
        </span>
      </div>
      <div className="p-4 space-y-0.5">
        <ClaimRow label="Service" value={claim.service} />
        <ClaimRow label="Date of Service" value={formatDate(claim.date)} />
        <ClaimRow label="Amount Billed" value={`$${claim.amountBilled.toLocaleString()}`} />
        <ClaimRow label="Allowed Amount" value={`$${claim.allowedAmount.toLocaleString()}`} />
        <ClaimRow label="Insurance Paid" value={`$${claim.insurancePaid.toLocaleString()}`} />
        <ClaimRow label="Patient Owes" value={`$${claim.patientOwes.toLocaleString()}`} highlight />
      </div>
      <div className="px-5 py-3 bg-gray-50 border-t border-gray-100">
        <p className="text-xs text-gray-500 italic line-clamp-2">{patient.questionPreview}</p>
      </div>
    </div>
  )
}

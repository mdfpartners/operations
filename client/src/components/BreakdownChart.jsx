const bars = [
  { key: 'amountBilled', label: 'Billed', color: 'bg-gray-400' },
  { key: 'allowedAmount', label: 'Allowed', color: 'bg-blue-400' },
  { key: 'insurancePaid', label: 'Ins. Paid', color: 'bg-green-400' },
  { key: 'patientOwes', label: 'Pt. Owes', color: 'bg-red-400' },
]

export default function BreakdownChart({ claim }) {
  const max = claim.amountBilled || 1

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">Claim Breakdown</h3>
      <div className="space-y-3">
        {bars.map(({ key, label, color }) => {
          const value = claim[key]
          const pct = Math.round((value / max) * 100)
          return (
            <div key={key} className="flex items-center gap-3">
              <span className="w-20 shrink-0 text-xs text-gray-500 text-right">{label}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                <div
                  className={`h-full rounded-full ${color} transition-all duration-500`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="w-14 shrink-0 text-xs font-medium text-gray-700">
                ${value.toLocaleString()}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

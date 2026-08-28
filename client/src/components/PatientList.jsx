import { scenarioColors } from '../data/patients'

export default function PatientList({ patients, selected, onSelect }) {
  return (
    <ul className="divide-y divide-gray-100">
      {patients.map((patient) => {
        const colors = scenarioColors[patient.scenario]
        const isSelected = selected?.id === patient.id
        return (
          <li key={patient.id}>
            <button
              onClick={() => onSelect(patient)}
              className={`w-full text-left px-4 py-4 hover:bg-gray-50 transition-colors ${
                isSelected ? 'bg-indigo-50 border-l-2 border-indigo-500' : 'border-l-2 border-transparent'
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <span className="font-medium text-gray-900 text-sm">{patient.name}</span>
                <span
                  className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full ${colors.bg} ${colors.text}`}
                >
                  {colors.label}
                </span>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">
                {patient.questionPreview}
              </p>
              <p className="text-xs text-gray-400 mt-1.5">
                Patient owes: <span className="font-semibold text-gray-600">${patient.claim.patientOwes}</span>
              </p>
            </button>
          </li>
        )
      })}
    </ul>
  )
}

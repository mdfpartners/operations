export default function OrderDetailLoading() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="h-5 bg-gray-200 rounded w-16" />
        <div className="h-7 bg-gray-200 rounded w-32" />
        <div className="h-6 bg-gray-200 rounded-full w-20" />
      </div>
      <div className="grid sm:grid-cols-3 gap-4">
        {[1,2,3].map(i => (
          <div key={i} className="bg-white rounded-lg shadow-sm p-4 space-y-2">
            <div className="h-3 bg-gray-200 rounded w-16" />
            <div className="h-5 bg-gray-200 rounded w-24" />
          </div>
        ))}
      </div>
      <div className="bg-white rounded-lg shadow-sm p-4 space-y-3">
        <div className="h-5 bg-gray-200 rounded w-24 mb-4" />
        {[1,2,3].map(i => (
          <div key={i} className="border border-gray-100 rounded p-3 space-y-2">
            <div className="h-4 bg-gray-200 rounded w-40" />
            <div className="h-4 bg-gray-200 rounded w-24" />
          </div>
        ))}
      </div>
    </div>
  )
}

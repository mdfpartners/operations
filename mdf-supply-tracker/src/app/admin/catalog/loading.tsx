export default function CatalogLoading() {
  return (
    <div className="animate-pulse">
      <div className="flex items-center justify-between mb-6">
        <div className="h-7 bg-gray-200 rounded w-32" />
        <div className="h-8 bg-gray-200 rounded w-28" />
      </div>
      <div className="flex gap-3 mb-4">
        <div className="h-8 bg-gray-200 rounded w-36" />
        <div className="h-8 bg-gray-200 rounded w-20" />
      </div>
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="bg-gray-50 border-b border-gray-200 px-4 py-3 flex gap-8">
          {['Item','Category','Unit','Vendor'].map(h => (
            <div key={h} className="h-4 bg-gray-200 rounded w-16" />
          ))}
        </div>
        {[...Array(10)].map((_, i) => (
          <div key={i} className="px-4 py-3 border-b border-gray-100 flex gap-8 items-center">
            <div className="h-4 bg-gray-200 rounded w-48" />
            <div className="h-4 bg-gray-200 rounded w-24" />
            <div className="h-4 bg-gray-200 rounded w-16" />
            <div className="h-4 bg-gray-200 rounded w-20" />
          </div>
        ))}
      </div>
    </div>
  )
}

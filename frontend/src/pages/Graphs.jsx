import { useEffect, useState } from 'react'
import { useStore } from '../stores/useStore.js'
import { listEntities } from '../services/api.js'
import {
  Network,
  Search,
  Loader2,
  Target,
  Link2,
  ChevronRight,
  Hash,
} from 'lucide-react'

export default function Graphs() {
  const { entities, setEntities } = useStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedEntity, setSelectedEntity] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchEntities = async () => {
      try {
        const data = await listEntities()
        setEntities(data.entities || data || [])
      } catch (err) {
        console.error('Failed to fetch entities:', err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchEntities()
  }, [setEntities])

  const filteredEntities = (entities || []).filter((entity) => {
    const term = searchTerm.toLowerCase()
    return (
      (entity.name || '').toLowerCase().includes(term) ||
      (entity.type || '').toLowerCase().includes(term) ||
      (entity.description || '').toLowerCase().includes(term)
    )
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600 dark:text-primary-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Graphs</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          Explore knowledge graph entities and their relationships
        </p>
      </div>

      {/* Search */}
      <div className="card">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            className="input pl-11"
            placeholder="Search entities by name, type, or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Entity list */}
        <div className="lg:col-span-2 space-y-3">
          {filteredEntities.length === 0 ? (
            <div className="card text-center py-12">
              <Network className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" />
              <p className="text-gray-500 dark:text-gray-400">
                {searchTerm ? 'No entities match your search' : 'No entities found in the graph'}
              </p>
            </div>
          ) : (
            filteredEntities.map((entity, index) => (
              <div
                key={entity.id || index}
                className={`card p-4 cursor-pointer transition-all hover:shadow-md ${
                  selectedEntity?.id === entity.id
                    ? 'ring-2 ring-primary-500 dark:ring-primary-400'
                    : ''
                }`}
                onClick={() => setSelectedEntity(entity)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 min-w-0">
                    <div className="p-2 rounded-lg bg-primary-50 dark:bg-primary-900/20 flex-shrink-0">
                      <Target className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                    </div>
                    <div className="min-w-0">
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        {entity.name || 'Unnamed Entity'}
                      </h3>
                      {entity.type && (
                        <span className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-xs text-gray-600 dark:text-gray-400">
                          <Hash className="w-3 h-3" />
                          {entity.type}
                        </span>
                      )}
                      {entity.description && (
                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                          {entity.description}
                        </p>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0 mt-1" />
                </div>
              </div>
            ))
          )}
        </div>

        {/* Detail panel */}
        <div className="lg:col-span-1">
          <div className="card sticky top-4">
            {selectedEntity ? (
              <div className="space-y-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {selectedEntity.name}
                  </h2>
                  {selectedEntity.type && (
                    <span className="inline-flex items-center gap-1 mt-1 px-2.5 py-1 rounded-full bg-primary-50 dark:bg-primary-900/20 text-xs font-medium text-primary-700 dark:text-primary-300">
                      <Hash className="w-3 h-3" />
                      {selectedEntity.type}
                    </span>
                  )}
                </div>

                {selectedEntity.description && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Description
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {selectedEntity.description}
                    </p>
                  </div>
                )}

                {selectedEntity.properties && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Properties
                    </h4>
                    <div className="space-y-1.5">
                      {Object.entries(selectedEntity.properties).map(([key, value]) => (
                        <div
                          key={key}
                          className="flex items-center justify-between text-sm px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-700/50"
                        >
                          <span className="text-gray-600 dark:text-gray-400 capitalize">
                            {key}
                          </span>
                          <span className="font-medium text-gray-900 dark:text-white">
                            {String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedEntity.relationships && selectedEntity.relationships.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                      <Link2 className="w-4 h-4" />
                      Relationships
                    </h4>
                    <div className="space-y-2">
                      {selectedEntity.relationships.map((rel, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-700/50"
                        >
                          <span className="text-gray-900 dark:text-white font-medium">
                            {rel.type || 'relates to'}
                          </span>
                          <ChevronRight className="w-3 h-3 text-gray-400" />
                          <span className="text-gray-600 dark:text-gray-400">
                            {rel.target || rel.name || 'Unknown'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <Network className="w-10 h-10 mx-auto mb-3 opacity-50" />
                <p className="text-sm">Select an entity to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

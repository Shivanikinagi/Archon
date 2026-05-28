import { useEffect, useState, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
  Handle,
  Position,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useStore } from '../stores/useStore.js'
import { getGraphTopology } from '../services/api.js'
import {
  Network,
  Search,
  Loader2,
  Target,
  Link2,
  ChevronRight,
  Hash,
  Maximize2,
  GitBranch,
  AlertTriangle,
  BarChart3,
} from 'lucide-react'

// --- Custom Node Component ---
function EntityNode({ data, selected }) {
  const colors = {
    Technology: { bg: '#6366f1', border: '#4f46e5', light: '#e0e7ff' },
    'Financial Instrument': { bg: '#10b981', border: '#059669', light: '#d1fae5' },
    Software: { bg: '#f59e0b', border: '#d97706', light: '#fef3c7' },
    Algorithm: { bg: '#ec4899', border: '#db2777', light: '#fce7f3' },
    Ecosystem: { bg: '#8b5cf6', border: '#7c3aed', light: '#ede9fe' },
    Organization: { bg: '#06b6d4', border: '#0891b2', light: '#cffafe' },
    Person: { bg: '#f97316', border: '#ea580c', light: '#ffedd5' },
    Model: { bg: '#14b8a6', border: '#0d9488', light: '#ccfbf1' },
    Company: { bg: '#6366f1', border: '#4f46e5', light: '#e0e7ff' },
    Product: { bg: '#f59e0b', border: '#d97706', light: '#fef3c7' },
    default: { bg: '#6b7280', border: '#4b5563', light: '#f3f4f6' },
  }
  const c = colors[data.type] || colors.default

  return (
    <div
      className={`relative px-3 py-2 rounded-lg border-2 shadow-sm transition-all duration-200 ${
        selected ? 'ring-2 ring-offset-2 ring-primary-500 scale-105' : ''
      }`}
      style={{
        backgroundColor: c.light,
        borderColor: c.border,
        minWidth: 140,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: c.bg, width: 8, height: 8 }} />
      <div className="flex items-center gap-2">
        <span
          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
          style={{ backgroundColor: c.bg }}
        />
        <span className="text-xs font-bold text-gray-900 dark:text-gray-900 truncate">
          {data.label}
        </span>
      </div>
      <div className="text-[10px] text-gray-500 mt-0.5 truncate">{data.type}</div>
      <Handle type="source" position={Position.Bottom} style={{ background: c.bg, width: 8, height: 8 }} />
    </div>
  )
}

const nodeTypes = { entity: EntityNode }

// --- Build React Flow graph from topology ---
function buildFlowGraph(topology) {
  if (!topology || !topology.nodes || topology.nodes.length === 0) {
    return { nodes: [], edges: [] }
  }

  const nodes = []
  const edges = []

  // Use a force-directed-like layout based on connectivity
  const connectedness = new Map()
  topology.edges.forEach((e) => {
    connectedness.set(e.source, (connectedness.get(e.source) || 0) + 1)
    connectedness.set(e.target, (connectedness.get(e.target) || 0) + 1)
  })

  // Sort by connectedness (hubs first)
  const sortedNodes = [...topology.nodes].sort(
    (a, b) => (connectedness.get(b.id) || 0) - (connectedness.get(a.id) || 0)
  )

  // Place hubs in center, others in rings
  const placed = new Map()
  const centerX = 0
  const centerY = 0

  sortedNodes.forEach((node, index) => {
    const conn = connectedness.get(node.id) || 0
    let x, y

    if (index === 0) {
      x = centerX
      y = centerY
    } else {
      const ring = Math.ceil(index / 5)
      const angle = (index * 137.5 * Math.PI) / 180 // Golden angle
      const radius = 200 + ring * 180 + Math.random() * 60
      x = centerX + Math.cos(angle) * radius
      y = centerY + Math.sin(angle) * radius
    }

    placed.set(node.id, { x, y })

    nodes.push({
      id: node.id,
      type: 'entity',
      position: { x, y },
      data: {
        label: node.label || node.id,
        type: node.type || 'Entity',
        properties: node.properties || {},
      },
    })
  })

  topology.edges.forEach((edge, idx) => {
    edges.push({
      id: edge.id || `e-${idx}`,
      source: edge.source,
      target: edge.target,
      label: edge.label || edge.relationship_type || 'relates to',
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#94a3b8', strokeWidth: 1.5 + (edge.weight || 1) * 0.5 },
      labelStyle: { fontSize: 10, fill: '#64748b' },
      labelBgStyle: { fill: '#f8fafc', fillOpacity: 0.9 },
      labelBgPadding: [4, 4],
      labelBgBorderRadius: 4,
    })
  })

  return { nodes, edges }
}

export default function Graphs() {
  const { entities, setEntities } = useStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedEntity, setSelectedEntity] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [reactFlowInstance, setReactFlowInstance] = useState(null)
  const [topology, setTopology] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchTopology = async () => {
      try {
        const data = await getGraphTopology()
        if (data && data.nodes && data.nodes.length > 0) {
          setTopology(data)
          // Convert to entity format for list view
          const entityList = data.nodes.map((n) => ({
            id: n.id,
            name: n.label,
            type: n.type,
            properties: n.properties,
            relationships: data.edges
              .filter((e) => e.source === n.id || e.target === n.id)
              .map((e) => ({
                type: e.label,
                target: e.source === n.id ? e.target : e.source,
              })),
          }))
          setEntities(entityList)
        } else {
          const demo = getDemoEntities()
          setEntities(demo)
          setTopology(demoToTopology(demo))
        }
      } catch (err) {
        console.error('Failed to fetch topology:', err)
        setError('Backend not connected — showing demo data')
        const demo = getDemoEntities()
        setEntities(demo)
        setTopology(demoToTopology(demo))
      } finally {
        setIsLoading(false)
      }
    }
    fetchTopology()
  }, [setEntities])

  useEffect(() => {
    if (!topology) return

    const filteredNodes = topology.nodes.filter((node) => {
      if (!searchTerm) return true
      const term = searchTerm.toLowerCase()
      return (
        (node.label || '').toLowerCase().includes(term) ||
        (node.type || '').toLowerCase().includes(term)
      )
    })

    const filteredNodeIds = new Set(filteredNodes.map((n) => n.id))
    const filteredEdges = topology.edges.filter(
      (e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
    )

    const { nodes: flowNodes, edges: flowEdges } = buildFlowGraph({
      nodes: filteredNodes,
      edges: filteredEdges,
    })
    setNodes(flowNodes)
    setEdges(flowEdges)
  }, [topology, searchTerm, setNodes, setEdges])

  const onNodeClick = useCallback((_, node) => {
    const entity = (entities || []).find((e) => e.id === node.id)
    if (entity) {
      setSelectedEntity(entity)
    } else {
      setSelectedEntity({
        id: node.id,
        name: node.data.label,
        type: node.data.type,
        properties: node.data.properties,
        relationships: [],
      })
    }
  }, [entities])

  const onFitView = useCallback(() => {
    reactFlowInstance?.fitView({ padding: 0.2, duration: 800 })
  }, [reactFlowInstance])

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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Knowledge Graph</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          Explore entities, relationships, and reasoning paths extracted from research
        </p>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="card p-3 flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary-50 dark:bg-primary-900/20">
            <Network className="w-4 h-4 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <p className="text-lg font-bold text-gray-900 dark:text-white">{topology?.nodes?.length || 0}</p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400">Entities</p>
          </div>
        </div>
        <div className="card p-3 flex items-center gap-3">
          <div className="p-2 rounded-lg bg-green-50 dark:bg-green-900/20">
            <Link2 className="w-4 h-4 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <p className="text-lg font-bold text-gray-900 dark:text-white">{topology?.edges?.length || 0}</p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400">Relationships</p>
          </div>
        </div>
        <div className="card p-3 flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-50 dark:bg-purple-900/20">
            <GitBranch className="w-4 h-4 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <p className="text-lg font-bold text-gray-900 dark:text-white">
              {new Set(topology?.nodes?.map((n) => n.type)).size || 0}
            </p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400">Entity Types</p>
          </div>
        </div>
        <div className="card p-3 flex items-center gap-3">
          <div className="p-2 rounded-lg bg-amber-50 dark:bg-amber-900/20">
            <BarChart3 className="w-4 h-4 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <p className="text-lg font-bold text-gray-900 dark:text-white">
              {topology?.edges?.length
                ? (topology.edges.length / Math.max(1, topology.nodes.length)).toFixed(2)
                : '0.00'}
            </p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400">Avg Connections</p>
          </div>
        </div>
      </div>

      {/* React Flow Graph */}
      <div className="card p-0 overflow-hidden" style={{ height: 520 }}>
        <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-center gap-2">
            <Network className="w-4 h-4 text-primary-600 dark:text-primary-400" />
            <h3 className="font-semibold text-gray-900 dark:text-white text-sm">Graph Visualization</h3>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {nodes.length} nodes · {edges.length} edges
            </span>
          </div>
          <div className="flex items-center gap-1">
            {error && (
              <span className="text-[10px] text-amber-600 dark:text-amber-400 flex items-center gap-1 mr-2">
                <AlertTriangle className="w-3 h-3" />
                {error}
              </span>
            )}
            <button
              onClick={onFitView}
              className="p-1.5 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="Fit to view"
            >
              <Maximize2 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>
        </div>
        <div style={{ height: 'calc(100% - 41px)' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            onInit={setReactFlowInstance}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-right"
            minZoom={0.1}
            maxZoom={2}
          >
            <Background color="#cbd5e1" gap={20} size={1} />
            <Controls />
            <MiniMap
              nodeStrokeWidth={3}
              zoomable
              pannable
              className="!bg-white dark:!bg-gray-900 !border-gray-200 dark:!border-gray-700"
            />
            <Panel position="top-left" className="m-2">
              <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg p-2 shadow-sm border border-gray-200 dark:border-gray-700">
                <p className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 mb-1 uppercase">
                  Node Types
                </p>
                <div className="grid grid-cols-2 gap-x-3 gap-y-1">
                  {[
                    ['Technology', '#6366f1'],
                    ['Financial Instrument', '#10b981'],
                    ['Software', '#f59e0b'],
                    ['Algorithm', '#ec4899'],
                    ['Ecosystem', '#8b5cf6'],
                    ['Organization', '#06b6d4'],
                    ['Model', '#14b8a6'],
                    ['Company', '#6366f1'],
                  ].map(([type, color]) => (
                    <div key={type} className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                      <span className="text-[10px] text-gray-600 dark:text-gray-400">{type}</span>
                    </div>
                  ))}
                </div>
              </div>
            </Panel>
          </ReactFlow>
        </div>
      </div>

      {/* Search */}
      <div className="card">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            className="input pl-11"
            placeholder="Filter entities by name or type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Entity list */}
        <div className="lg:col-span-2 space-y-3">
          {(entities || []).length === 0 ? (
            <div className="card text-center py-12">
              <Network className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" />
              <p className="text-gray-500 dark:text-gray-400">No entities found in the graph</p>
            </div>
          ) : (
            (entities || [])
              .filter((entity) => {
                const term = searchTerm.toLowerCase()
                return (
                  (entity.name || '').toLowerCase().includes(term) ||
                  (entity.type || '').toLowerCase().includes(term) ||
                  (entity.description || '').toLowerCase().includes(term)
                )
              })
              .map((entity, index) => (
                <div
                  key={entity.id || index}
                  className={`card p-4 cursor-pointer transition-all hover:shadow-md ${
                    selectedEntity?.id === entity.id || selectedEntity?.name === entity.name
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
                        {entity.properties && Object.keys(entity.properties).length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {Object.entries(entity.properties).slice(0, 3).map(([k, v]) => (
                              <span
                                key={k}
                                className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
                              >
                                {k}: {String(v).slice(0, 20)}
                              </span>
                            ))}
                          </div>
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
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{selectedEntity.description}</p>
                  </div>
                )}

                {selectedEntity.properties && Object.keys(selectedEntity.properties).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Properties</h4>
                    <div className="space-y-1.5">
                      {Object.entries(selectedEntity.properties).map(([key, value]) => (
                        <div
                          key={key}
                          className="flex items-center justify-between text-sm px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-700/50"
                        >
                          <span className="text-gray-600 dark:text-gray-400 capitalize">{key}</span>
                          <span className="font-medium text-gray-900 dark:text-white">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedEntity.relationships && selectedEntity.relationships.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                      <Link2 className="w-4 h-4" />
                      Relationships ({selectedEntity.relationships.length})
                    </h4>
                    <div className="space-y-2">
                      {selectedEntity.relationships.map((rel, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-700/50"
                        >
                          <span className="text-gray-900 dark:text-white font-medium">{rel.type || 'relates to'}</span>
                          <ChevronRight className="w-3 h-3 text-gray-400" />
                          <span className="text-gray-600 dark:text-gray-400">{rel.target || rel.name || 'Unknown'}</span>
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
                <p className="text-xs mt-1 opacity-70">Or click a node in the graph above</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function demoToTopology(demoEntities) {
  const nodes = demoEntities.map((e) => ({
    id: e.id,
    label: e.name,
    type: e.type,
    properties: e.properties,
  }))

  const edges = []
  demoEntities.forEach((entity) => {
    entity.relationships?.forEach((rel, idx) => {
      const target = demoEntities.find((e) => e.name === rel.target)
      if (target) {
        edges.push({
          id: `e-${entity.id}-${target.id}-${idx}`,
          source: entity.id,
          target: target.id,
          label: rel.type,
          weight: 1,
        })
      }
    })
  })

  return { nodes, edges }
}

function getDemoEntities() {
  return [
    {
      id: 'openai',
      name: 'OpenAI',
      type: 'Company',
      description: 'AI research and deployment company behind GPT models and ChatGPT.',
      properties: { founded: '2015', valuation: '$80B+', hq: 'San Francisco', key_products: 'GPT-4, ChatGPT, DALL-E' },
      relationships: [
        { type: 'funded_by', target: 'Microsoft' },
        { type: 'competes_with', target: 'Anthropic' },
        { type: 'partnered_with', target: 'NVIDIA' },
        { type: 'creates', target: 'GPT-4o' },
      ],
    },
    {
      id: 'microsoft',
      name: 'Microsoft',
      type: 'Company',
      description: 'Technology corporation and major investor in OpenAI, integrating AI across Azure and Office.',
      properties: { founded: '1975', market_cap: '$3T+', ceo: 'Satya Nadella', cloud: 'Azure' },
      relationships: [
        { type: 'invests_in', target: 'OpenAI' },
        { type: 'competes_with', target: 'Google' },
        { type: 'uses_chips_from', target: 'NVIDIA' },
        { type: 'integrates', target: 'Copilot' },
      ],
    },
    {
      id: 'nvidia',
      name: 'NVIDIA',
      type: 'Company',
      description: 'Dominant AI chip manufacturer providing GPUs that power most large model training.',
      properties: { founded: '1993', market_cap: '$3T+', key_product: 'H100, B200 GPUs', data_center_revenue: '$47B' },
      relationships: [
        { type: 'supplies_chips_to', target: 'OpenAI' },
        { type: 'supplies_chips_to', target: 'Microsoft' },
        { type: 'supplies_chips_to', target: 'Google' },
        { type: 'partnered_with', target: 'Anthropic' },
        { type: 'competes_with', target: 'AMD' },
      ],
    },
    {
      id: 'anthropic',
      name: 'Anthropic',
      type: 'Company',
      description: 'AI safety company founded by former OpenAI researchers, creator of Claude models.',
      properties: { founded: '2021', valuation: '$18B+', focus: 'AI Safety', key_products: 'Claude 3.5 Sonnet, Opus' },
      relationships: [
        { type: 'founded_by_ex', target: 'OpenAI' },
        { type: 'funded_by', target: 'Google' },
        { type: 'competes_with', target: 'OpenAI' },
        { type: 'partnered_with', target: 'Amazon' },
      ],
    },
    {
      id: 'google',
      name: 'Google',
      type: 'Company',
      description: 'Alphabet subsidiary developing Gemini models, DeepMind research, and Bard/AI Search.',
      properties: { founded: '1998', parent: 'Alphabet', key_products: 'Gemini 1.5, DeepMind, Bard', cloud: 'GCP' },
      relationships: [
        { type: 'invests_in', target: 'Anthropic' },
        { type: 'competes_with', target: 'OpenAI' },
        { type: 'competes_with', target: 'Microsoft' },
        { type: 'creates', target: 'Gemini 1.5' },
        { type: 'owns', target: 'DeepMind' },
      ],
    },
    {
      id: 'gpt-4o',
      name: 'GPT-4o',
      type: 'Model',
      description: 'OpenAI flagship multimodal model ("omni") with native audio, vision, and text reasoning.',
      properties: { release: 'May 2024', modality: 'Text, Image, Audio', context: '128K', benchmark_mmlu: '88.7%' },
      relationships: [
        { type: 'created_by', target: 'OpenAI' },
        { type: 'competes_with', target: 'Gemini 1.5' },
        { type: 'competes_with', target: 'Claude 3.5' },
      ],
    },
    {
      id: 'gemini-1.5',
      name: 'Gemini 1.5',
      type: 'Model',
      description: 'Google multimodal model with up to 2M token context window and Mixture-of-Experts architecture.',
      properties: { release: 'Feb 2024', modality: 'Text, Image, Audio, Video', context: '2M tokens', architecture: 'MoE' },
      relationships: [
        { type: 'created_by', target: 'Google' },
        { type: 'competes_with', target: 'GPT-4o' },
        { type: 'competes_with', target: 'Claude 3.5' },
      ],
    },
    {
      id: 'claude-3.5',
      name: 'Claude 3.5 Sonnet',
      type: 'Model',
      description: 'Anthropic model with advanced reasoning, coding, and agentic capabilities via Artifacts.',
      properties: { release: 'June 2024', modality: 'Text, Image', context: '200K', strength: 'Reasoning, Coding' },
      relationships: [
        { type: 'created_by', target: 'Anthropic' },
        { type: 'competes_with', target: 'GPT-4o' },
        { type: 'competes_with', target: 'Gemini 1.5' },
      ],
    },
    {
      id: 'copilot',
      name: 'Microsoft Copilot',
      type: 'Product',
      description: 'AI assistant integrated across Microsoft 365, Windows, and GitHub, powered by OpenAI models.',
      properties: { launch: '2023', users: '400M+', platforms: 'Windows, Office, GitHub', model: 'GPT-4' },
      relationships: [
        { type: 'powered_by', target: 'OpenAI' },
        { type: 'integrates_with', target: 'Microsoft' },
      ],
    },
    {
      id: 'deepmind',
      name: 'DeepMind',
      type: 'Organization',
      description: 'Google AI research lab, merged with Google Brain in 2023, behind AlphaGo, AlphaFold, and Gemini.',
      properties: { founded: '2010', acquired: '2014', merged: '2023', key_work: 'AlphaFold, Gemini' },
      relationships: [
        { type: 'owned_by', target: 'Google' },
        { type: 'collaborates_with', target: 'Gemini 1.5' },
      ],
    },
    {
      id: 'amazon',
      name: 'Amazon',
      type: 'Company',
      description: 'Cloud provider (AWS) and partner to Anthropic, offering Bedrock model hosting platform.',
      properties: { founded: '1994', cloud: 'AWS', ai_platform: 'Bedrock', investment: '$4B in Anthropic' },
      relationships: [
        { type: 'partners_with', target: 'Anthropic' },
        { type: 'competes_with', target: 'Microsoft' },
        { type: 'competes_with', target: 'Google' },
      ],
    },
  ]
}

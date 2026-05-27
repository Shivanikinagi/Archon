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
import { listEntities } from '../services/api.js'
import {
  Network,
  Search,
  Loader2,
  Target,
  Link2,
  ChevronRight,
  Hash,
  Info,
  ZoomIn,
  ZoomOut,
  Maximize2,
  GitBranch,
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

// --- Build React Flow graph from entities ---
function buildFlowGraph(entities) {
  if (!entities || entities.length === 0) return { nodes: [], edges: [] }

  const nodes = []
  const edges = []
  const nodeMap = new Map()
  const positions = [
    { x: 0, y: 0 },
    { x: 250, y: -80 },
    { x: 250, y: 80 },
    { x: 500, y: -120 },
    { x: 500, y: 0 },
    { x: 500, y: 120 },
    { x: -250, y: -60 },
    { x: -250, y: 60 },
    { x: 0, y: -180 },
    { x: 0, y: 180 },
    { x: 750, y: -60 },
    { x: 750, y: 60 },
  ]

  entities.forEach((entity, index) => {
    const id = entity.id || `node-${index}`
    const pos = positions[index % positions.length]
    // Add some randomness to prevent perfect overlap
    const jitterX = (Math.random() - 0.5) * 60
    const jitterY = (Math.random() - 0.5) * 60

    nodes.push({
      id,
      type: 'entity',
      position: { x: pos.x + jitterX, y: pos.y + jitterY },
      data: {
        label: entity.name || entity.label || 'Unknown',
        type: entity.type || 'Entity',
        description: entity.description || '',
        properties: entity.properties || {},
        relationships: entity.relationships || [],
      },
    })
    nodeMap.set(entity.name || entity.label, id)
    nodeMap.set(id, id)
  })

  // Create edges from relationships
  entities.forEach((entity) => {
    const sourceId = nodeMap.get(entity.id) || nodeMap.get(entity.name)
    if (!sourceId) return

    ;(entity.relationships || []).forEach((rel, idx) => {
      const targetName = rel.target || rel.name
      let targetId = nodeMap.get(targetName)

      if (!targetId) {
        const newId = `implicit-${targetName.replace(/\s+/g, '-').toLowerCase()}`
        if (!nodeMap.has(newId)) {
          const angle = Math.random() * 2 * Math.PI
          const radius = 350 + Math.random() * 150
          nodes.push({
            id: newId,
            type: 'entity',
            position: { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius },
            data: {
              label: targetName,
              type: 'Related',
              description: '',
              properties: {},
              relationships: [],
            },
          })
          nodeMap.set(targetName, newId)
          nodeMap.set(newId, newId)
        }
        targetId = newId
      }

      if (targetId && targetId !== sourceId) {
        edges.push({
          id: `e-${sourceId}-${targetId}-${idx}`,
          source: sourceId,
          target: targetId,
          label: rel.type || 'relates to',
          type: 'smoothstep',
          animated: true,
          style: { stroke: '#94a3b8', strokeWidth: 1.5 },
          labelStyle: { fontSize: 10, fill: '#64748b' },
          labelBgStyle: { fill: '#f8fafc', fillOpacity: 0.9 },
          labelBgPadding: [4, 4],
          labelBgBorderRadius: 4,
        })
      }
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

  useEffect(() => {
    const fetchEntities = async () => {
      try {
        const data = await listEntities()
        const fetched = data.entities || data || []
        if (fetched.length === 0) {
          setEntities(getDemoEntities())
        } else {
          setEntities(fetched)
        }
      } catch (err) {
        console.error('Failed to fetch entities:', err)
        setEntities(getDemoEntities())
      } finally {
        setIsLoading(false)
      }
    }
    fetchEntities()
  }, [setEntities])

  useEffect(() => {
    const filtered = (entities || []).filter((entity) => {
      const term = searchTerm.toLowerCase()
      return (
        (entity.name || '').toLowerCase().includes(term) ||
        (entity.type || '').toLowerCase().includes(term) ||
        (entity.description || '').toLowerCase().includes(term)
      )
    })
    const { nodes: flowNodes, edges: flowEdges } = buildFlowGraph(filtered)
    setNodes(flowNodes)
    setEdges(flowEdges)
  }, [entities, searchTerm, setNodes, setEdges])

  const onNodeClick = useCallback((_, node) => {
    const entity = (entities || []).find(
      (e) => (e.id || e.name) === (node.id || node.data.label)
    )
    if (entity) {
      setSelectedEntity(entity)
    } else {
      // Implicit node
      setSelectedEntity({
        id: node.id,
        name: node.data.label,
        type: node.data.type,
        description: node.data.description,
        properties: node.data.properties,
        relationships: node.data.relationships,
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

      {/* React Flow Graph */}
      <div className="card p-0 overflow-hidden" style={{ height: 520 }}>
        <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-center gap-2">
            <Network className="w-4 h-4 text-primary-600 dark:text-primary-400" />
            <h3 className="font-semibold text-gray-900 dark:text-white text-sm">
              Graph Visualization
            </h3>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {nodes.length} nodes · {edges.length} edges
            </span>
          </div>
          <div className="flex items-center gap-1">
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
            placeholder="Search entities by name, type, or description..."
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
              <p className="text-gray-500 dark:text-gray-400">
                No entities found in the graph
              </p>
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

                {selectedEntity.properties && Object.keys(selectedEntity.properties).length > 0 && (
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
                <p className="text-xs mt-1 opacity-70">Or click a node in the graph above</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function getDemoEntities() {
  return [
    {
      id: 'demo-1',
      name: 'Blockchain',
      type: 'Technology',
      description: 'A decentralized, distributed ledger technology that records transactions across multiple computers.',
      properties: { origin: '2008', creator: 'Satoshi Nakamoto', category: 'Distributed Systems' },
      relationships: [
        { type: 'enables', target: 'Cryptocurrency' },
        { type: 'uses', target: 'Consensus Mechanisms' },
        { type: 'powers', target: 'Smart Contracts' },
      ],
    },
    {
      id: 'demo-2',
      name: 'Cryptocurrency',
      type: 'Financial Instrument',
      description: 'Digital or virtual currency that uses cryptography for security and operates on blockchain networks.',
      properties: { market_cap: '$2.5T', top_coins: 'Bitcoin, Ethereum', volatility: 'High' },
      relationships: [
        { type: 'built_on', target: 'Blockchain' },
        { type: 'regulated_by', target: 'SEC' },
        { type: 'traded_on', target: 'Coinbase' },
      ],
    },
    {
      id: 'demo-3',
      name: 'Smart Contracts',
      type: 'Software',
      description: 'Self-executing contracts with the terms of the agreement directly written into code.',
      properties: { platforms: 'Ethereum, Solana', language: 'Solidity', use_cases: 'DeFi, NFTs' },
      relationships: [
        { type: 'runs_on', target: 'Blockchain' },
        { type: 'powers', target: 'DeFi' },
        { type: 'enables', target: 'NFTs' },
      ],
    },
    {
      id: 'demo-4',
      name: 'Consensus Mechanisms',
      type: 'Algorithm',
      description: 'Protocols that ensure all nodes in a blockchain network agree on the current state of the ledger.',
      properties: { types: 'PoW, PoS, DPoS', energy_usage: 'Variable', security: 'High' },
      relationships: [
        { type: 'secures', target: 'Blockchain' },
        { type: 'validates', target: 'Cryptocurrency' },
      ],
    },
    {
      id: 'demo-5',
      name: 'DeFi',
      type: 'Ecosystem',
      description: 'Decentralized Finance — financial services built on blockchain without traditional intermediaries.',
      properties: { tvl: '$100B+', protocols: 'Uniswap, Aave', risk: 'Smart contract risk' },
      relationships: [
        { type: 'uses', target: 'Smart Contracts' },
        { type: 'disrupts', target: 'Traditional Finance' },
        { type: 'built_on', target: 'Ethereum' },
      ],
    },
    {
      id: 'demo-6',
      name: 'NFTs',
      type: 'Technology',
      description: 'Non-Fungible Tokens — unique digital assets verified using blockchain technology.',
      properties: { market: '$15B', standard: 'ERC-721', use_cases: 'Art, Gaming, Music' },
      relationships: [
        { type: 'built_on', target: 'Blockchain' },
        { type: 'powered_by', target: 'Smart Contracts' },
      ],
    },
    {
      id: 'demo-7',
      name: 'Ethereum',
      type: 'Technology',
      description: 'A decentralized, open-source blockchain with smart contract functionality.',
      properties: { launched: '2015', founder: 'Vitalik Buterin', consensus: 'PoS' },
      relationships: [
        { type: 'is_a', target: 'Blockchain' },
        { type: 'supports', target: 'Smart Contracts' },
        { type: 'hosts', target: 'DeFi' },
      ],
    },
    {
      id: 'demo-8',
      name: 'SEC',
      type: 'Organization',
      description: 'U.S. Securities and Exchange Commission — regulates securities markets.',
      properties: { country: 'USA', formed: '1934', focus: 'Securities regulation' },
      relationships: [
        { type: 'regulates', target: 'Cryptocurrency' },
      ],
    },
    {
      id: 'demo-9',
      name: 'Coinbase',
      type: 'Organization',
      description: 'A secure online platform for buying, selling, transferring, and storing cryptocurrency.',
      properties: { founded: '2012', users: '100M+', hq: 'USA' },
      relationships: [
        { type: 'lists', target: 'Cryptocurrency' },
      ],
    },
  ]
}

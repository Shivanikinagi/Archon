import { useEffect, useRef, useState, useCallback } from 'react'
import { ZoomIn, ZoomOut, Move, RotateCcw } from 'lucide-react'

/**
 * Interactive SVG Graph Visualization
 * Renders nodes and edges with pan, zoom, and click interactions.
 */
export default function GraphVisualization({ entities, onSelectNode }) {
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 })
  const [dragging, setDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [hoveredNode, setHoveredNode] = useState(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 })

  // Build graph data from entities
  const graphData = buildGraph(entities)

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setDimensions({ width: rect.width, height: Math.max(400, rect.height) })
      }
    }
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // Center the graph initially
  useEffect(() => {
    if (graphData.nodes.length > 0) {
      const bounds = getBounds(graphData.nodes)
      const k = Math.min(
        (dimensions.width - 80) / (bounds.maxX - bounds.minX || 1),
        (dimensions.height - 80) / (bounds.maxY - bounds.minY || 1),
        1.2
      )
      const cx = (bounds.minX + bounds.maxX) / 2
      const cy = (bounds.minY + bounds.maxY) / 2
      setTransform({
        x: dimensions.width / 2 - cx * k,
        y: dimensions.height / 2 - cy * k,
        k: Math.max(0.3, k),
      })
    }
  }, [graphData.nodes.length, dimensions.width, dimensions.height])

  const handleWheel = useCallback((e) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    setTransform((prev) => {
      const newK = Math.max(0.2, Math.min(3, prev.k * delta))
      return { ...prev, k: newK }
    })
  }, [])

  const handleMouseDown = useCallback((e) => {
    if (e.target.tagName === 'circle' || e.target.tagName === 'text') return
    setDragging(true)
    setDragStart({ x: e.clientX - transform.x, y: e.clientY - transform.y })
  }, [transform])

  const handleMouseMove = useCallback((e) => {
    if (!dragging) return
    setTransform((prev) => ({
      ...prev,
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    }))
  }, [dragging, dragStart])

  const handleMouseUp = useCallback(() => {
    setDragging(false)
  }, [])

  const zoomIn = () => setTransform((prev) => ({ ...prev, k: Math.min(3, prev.k * 1.3) }))
  const zoomOut = () => setTransform((prev) => ({ ...prev, k: Math.max(0.2, prev.k / 1.3) }))
  const resetView = () => {
    const bounds = getBounds(graphData.nodes)
    const k = Math.min(
      (dimensions.width - 80) / (bounds.maxX - bounds.minX || 1),
      (dimensions.height - 80) / (bounds.maxY - bounds.minY || 1),
      1.2
    )
    const cx = (bounds.minX + bounds.maxX) / 2
    const cy = (bounds.minY + bounds.maxY) / 2
    setTransform({
      x: dimensions.width / 2 - cx * k,
      y: dimensions.height / 2 - cy * k,
      k: Math.max(0.3, k),
    })
  }

  const nodeColors = {
    Technology: '#6366f1',
    'Financial Instrument': '#10b981',
    Software: '#f59e0b',
    Algorithm: '#ec4899',
    Ecosystem: '#8b5cf6',
    Organization: '#06b6d4',
    Person: '#f97316',
    default: '#6b7280',
  }

  return (
    <div
      ref={containerRef}
      className="relative w-full h-[500px] bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{ cursor: dragging ? 'grabbing' : 'grab' }}
    >
      {/* Controls */}
      <div className="absolute top-3 right-3 z-10 flex flex-col gap-1">
        <button
          onClick={zoomIn}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          title="Zoom in"
        >
          <ZoomIn className="w-4 h-4 text-gray-700 dark:text-gray-300" />
        </button>
        <button
          onClick={zoomOut}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          title="Zoom out"
        >
          <ZoomOut className="w-4 h-4 text-gray-700 dark:text-gray-300" />
        </button>
        <button
          onClick={resetView}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          title="Reset view"
        >
          <RotateCcw className="w-4 h-4 text-gray-700 dark:text-gray-300" />
        </button>
      </div>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 z-10 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg p-2 shadow-sm border border-gray-200 dark:border-gray-700">
        <p className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 mb-1 uppercase">Node Types</p>
        <div className="flex flex-wrap gap-x-3 gap-y-1">
          {Object.entries(nodeColors).filter(([k]) => k !== 'default').map(([type, color]) => (
            <div key={type} className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-[10px] text-gray-600 dark:text-gray-400">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Hint */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-1 text-[10px] text-gray-400 dark:text-gray-500 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm px-2 py-1 rounded-lg">
        <Move className="w-3 h-3" />
        Scroll to zoom, drag to pan
      </div>

      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="w-full h-full"
      >
        <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}>
          {/* Edges */}
          {graphData.edges.map((edge, i) => {
            const source = graphData.nodes.find((n) => n.id === edge.source)
            const target = graphData.nodes.find((n) => n.id === edge.target)
            if (!source || !target) return null
            const isHighlighted = hoveredNode && (hoveredNode === edge.source || hoveredNode === edge.target)
            return (
              <g key={`edge-${i}`}>
                <line
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={isHighlighted ? '#6366f1' : '#cbd5e1'}
                  strokeWidth={isHighlighted ? 2.5 : 1.5}
                  className="transition-all duration-200"
                  strokeDasharray={edge.type === 'indirect' ? '4,4' : 'none'}
                />
                {/* Edge label */}
                {edge.label && (
                  <g>
                    <rect
                      x={(source.x + target.x) / 2 - 30}
                      y={(source.y + target.y) / 2 - 8}
                      width={60}
                      height={16}
                      rx={4}
                      fill={isHighlighted ? '#e0e7ff' : '#f1f5f9'}
                      className="dark:fill-gray-800"
                      stroke={isHighlighted ? '#6366f1' : '#e2e8f0'}
                      strokeWidth={0.5}
                    />
                    <text
                      x={(source.x + target.x) / 2}
                      y={(source.y + target.y) / 2 + 3}
                      textAnchor="middle"
                      className="text-[8px] fill-gray-600 dark:fill-gray-400"
                      style={{ fontSize: '7px' }}
                    >
                      {edge.label}
                    </text>
                  </g>
                )}
              </g>
            )
          })}

          {/* Nodes */}
          {graphData.nodes.map((node) => {
            const isHovered = hoveredNode === node.id
            const color = nodeColors[node.type] || nodeColors.default
            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => onSelectNode && onSelectNode(node)}
              >
                {/* Glow effect on hover */}
                {isHovered && (
                  <circle r={node.r + 8} fill={color} opacity={0.15} className="animate-pulse" />
                )}
                {/* Main node circle */}
                <circle
                  r={node.r}
                  fill={color}
                  stroke={isHovered ? '#ffffff' : 'transparent'}
                  strokeWidth={isHovered ? 3 : 0}
                  className="transition-all duration-200"
                  opacity={isHovered ? 1 : 0.9}
                />
                {/* Node label */}
                <text
                  y={node.r + 14}
                  textAnchor="middle"
                  className="text-xs font-semibold fill-gray-800 dark:fill-gray-200"
                  style={{ fontSize: '10px', pointerEvents: 'none' }}
                >
                  {node.label.length > 14 ? node.label.slice(0, 12) + '...' : node.label}
                </text>
                {/* Type label */}
                <text
                  y={node.r + 26}
                  textAnchor="middle"
                  className="fill-gray-500 dark:fill-gray-500"
                  style={{ fontSize: '8px', pointerEvents: 'none' }}
                >
                  {node.type}
                </text>
              </g>
            )
          })}
        </g>
      </svg>
    </div>
  )
}

// --- Helpers ---

function buildGraph(entities) {
  if (!entities || entities.length === 0) return { nodes: [], edges: [] }

  const nodes = []
  const edges = []
  const nodeMap = new Map()

  // Create nodes from entities
  entities.forEach((entity, index) => {
    const id = entity.id || `node-${index}`
    const angle = (index / entities.length) * 2 * Math.PI
    const radius = 120 + Math.random() * 60
    const x = Math.cos(angle) * radius
    const y = Math.sin(angle) * radius

    nodes.push({
      id,
      label: entity.name || entity.label || 'Unknown',
      type: entity.type || 'Entity',
      description: entity.description || '',
      x,
      y,
      r: 24,
      properties: entity.properties || {},
      relationships: entity.relationships || [],
    })
    nodeMap.set(entity.name || entity.label, id)
    nodeMap.set(id, id)
  })

  // Create edges from relationships
  entities.forEach((entity) => {
    const sourceId = nodeMap.get(entity.id) || nodeMap.get(entity.name)
    if (!sourceId) return

    ;(entity.relationships || []).forEach((rel) => {
      const targetName = rel.target || rel.name
      // Find target node by name or ID
      let targetId = nodeMap.get(targetName)
      if (!targetId) {
        // Create implicit node if target doesn't exist
        const newId = `implicit-${targetName}`
        if (!nodeMap.has(newId)) {
          const angle = Math.random() * 2 * Math.PI
          const radius = 180 + Math.random() * 80
          nodes.push({
            id: newId,
            label: targetName,
            type: 'Related',
            x: Math.cos(angle) * radius,
            y: Math.sin(angle) * radius,
            r: 18,
            properties: {},
            relationships: [],
          })
          nodeMap.set(targetName, newId)
          nodeMap.set(newId, newId)
        }
        targetId = newId
      }

      if (targetId && targetId !== sourceId) {
        edges.push({
          source: sourceId,
          target: targetId,
          label: rel.type || 'relates to',
          type: 'direct',
        })
      }
    })
  })

  // Simple force-like adjustment to reduce overlap
  for (let iter = 0; iter < 30; iter++) {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x
        const dy = nodes[j].y - nodes[i].y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const minDist = nodes[i].r + nodes[j].r + 40
        if (dist < minDist) {
          const force = (minDist - dist) / dist * 0.5
          const fx = dx * force
          const fy = dy * force
          nodes[i].x -= fx
          nodes[i].y -= fy
          nodes[j].x += fx
          nodes[j].y += fy
        }
      }
    }
  }

  return { nodes, edges }
}

function getBounds(nodes) {
  if (nodes.length === 0) return { minX: -100, maxX: 100, minY: -100, maxY: 100 }
  return {
    minX: Math.min(...nodes.map((n) => n.x - n.r)),
    maxX: Math.max(...nodes.map((n) => n.x + n.r)),
    minY: Math.min(...nodes.map((n) => n.y - n.r)),
    maxY: Math.max(...nodes.map((n) => n.y + n.r)),
  }
}

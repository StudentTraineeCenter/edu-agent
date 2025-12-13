import { useMemo } from 'react'
import { Canvas } from '@/components/ai-elements/canvas'
import type { Node, Edge } from '@xyflow/react'

type MindMapData = {
  nodes: Array<{
    id: string
    type?: string
    position: { x: number; y: number }
    data: { label: string; [key: string]: unknown }
  }>
  edges: Array<{
    id: string
    source: string
    target: string
    label?: string | null
    type?: string
  }>
}

type MindMapViewProps = {
  mapData: MindMapData
}

export const MindMapView = ({ mapData }: MindMapViewProps) => {
  const nodes: Node[] = useMemo(
    () =>
      mapData.nodes.map((node) => ({
        id: node.id,
        type: node.type || 'default',
        position: node.position,
        data: node.data,
      })),
    [mapData.nodes],
  )

  const edges: Edge[] = useMemo(
    () =>
      mapData.edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label || undefined,
        type: edge.type || 'smoothstep',
        animated: false,
      })),
    [mapData.edges],
  )

  return (
    <div className="h-full w-full">
      <Canvas nodes={nodes} edges={edges} fitView />
    </div>
  )
}

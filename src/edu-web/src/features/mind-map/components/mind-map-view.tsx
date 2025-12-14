import { useState, useMemo } from 'react'
import { ChevronRight, ChevronDown, Circle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

// --- Types ---

export interface MindMapNodeData {
  id: string
  label: string
  content?: string
  children?: MindMapNodeData[]
}

// Helper function to convert nodes/edges format to hierarchical tree
function convertToTree(
  nodes: Array<{
    id: string
    data: { label: string; [key: string]: unknown }
    position?: { x: number; y: number }
  }>,
  edges: Array<{
    id: string
    source: string
    target: string
    label?: string | null
  }>,
): MindMapNodeData | null {
  if (nodes.length === 0) {
    return null
  }

  // Build a map of node ID to node data
  const nodeMap = new Map<string, MindMapNodeData>()
  const childrenMap = new Map<string, string[]>()

  // Initialize all nodes
  nodes.forEach((node) => {
    nodeMap.set(node.id, {
      id: node.id,
      label: node.data.label,
      content: node.data.content as string | undefined,
      children: [],
    })
    childrenMap.set(node.id, [])
  })

  // Build parent-child relationships from edges
  edges.forEach((edge) => {
    const children = childrenMap.get(edge.source) || []
    children.push(edge.target)
    childrenMap.set(edge.source, children)
  })

  // Build the tree structure
  const buildNode = (nodeId: string): MindMapNodeData | null => {
    const node = nodeMap.get(nodeId)
    if (!node) return null

    const childIds = childrenMap.get(nodeId) || []
    node.children = childIds
      .map((childId) => buildNode(childId))
      .filter((child): child is MindMapNodeData => child !== null)

    return node
  }

  // Find root nodes (nodes that are not targets of any edge)
  const targetIds = new Set(edges.map((e) => e.target))
  const rootNodes = nodes.filter((node) => !targetIds.has(node.id))

  if (rootNodes.length === 0) {
    // If no clear root, use the first node
    return buildNode(nodes[0].id)
  }

  // If multiple roots, create a synthetic root
  if (rootNodes.length > 1) {
    const syntheticRoot: MindMapNodeData = {
      id: 'root',
      label: 'Root',
      children: rootNodes
        .map((node) => buildNode(node.id))
        .filter((node): node is MindMapNodeData => node !== null),
    }
    return syntheticRoot
  }

  return buildNode(rootNodes[0].id)
}

// --- Recursive Node Component ---

const MindMapNode = ({
  data,
  depth = 0,
  isLast = false,
}: {
  data: MindMapNodeData
  depth?: number
  isLast?: boolean
}) => {
  const [isExpanded, setIsExpanded] = useState(true)
  const hasChildren = data.children && data.children.length > 0
  const isRoot = depth === 0

  return (
    <div className="flex flex-row items-center">
      {/* The Node Card */}
      <div className="relative flex items-center z-10">
        <div
          className={cn(
            'group flex items-center gap-2 border rounded-xl transition-all duration-200 shadow-sm',
            isRoot
              ? 'bg-card text-card-foreground px-6 py-4 border-primary/30'
              : 'bg-card text-card-foreground px-4 py-2 hover:border-primary/50 hover:shadow-md',
          )}
        >
          {/* Collapse Toggle Button */}
          {hasChildren && (
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                'h-5 w-5 shrink-0',
                isRoot &&
                  'absolute -right-3 top-1/2 -translate-y-1/2 bg-background border shadow-sm',
              )}
              onClick={(e) => {
                e.stopPropagation()
                setIsExpanded(!isExpanded)
              }}
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? (
                isRoot ? (
                  <ChevronRight className="h-3.5 w-3.5" />
                ) : (
                  <ChevronDown className="h-3.5 w-3.5 rotate-[-90deg]" />
                )
              ) : (
                <ChevronRight className="h-3.5 w-3.5" />
              )}
            </Button>
          )}

          {!hasChildren && !isRoot && (
            <Circle size={8} className="text-primary fill-current shrink-0" />
          )}

          <div className="flex flex-col min-w-0">
            <span
              className={cn(
                'font-medium break-words',
                isRoot ? 'text-lg text-foreground' : 'text-sm text-foreground',
              )}
            >
              {data.label}
            </span>
            {data.content && isRoot && (
              <span className="text-xs text-muted-foreground mt-1 max-w-[200px] truncate">
                {data.content}
              </span>
            )}
          </div>
        </div>

        {/* Connector Line to Children Group */}
        {hasChildren && isExpanded && <div className="w-8 h-px bg-border" />}
      </div>

      {/* Recursive Children Rendering */}
      {hasChildren && isExpanded && (
        <div className="flex flex-col gap-4 ml-0 border-l border-border pl-8 py-2 relative">
          {data.children?.map((child, index) => (
            <div key={child.id} className="relative">
              {/* Horizontal connector line */}
              <div className="absolute -left-8 top-1/2 w-8 h-px bg-border" />

              {/* Vertical Line Cover (to stop line going past last child or before first) */}
              {index === 0 && (
                <div className="absolute -left-[33px] -top-4 h-1/2 w-1 bg-background" />
              )}
              {index === data.children!.length - 1 && (
                <div className="absolute -left-[33px] top-1/2 h-full w-1 bg-background" />
              )}

              <MindMapNode
                data={child}
                depth={depth + 1}
                isLast={index === data.children!.length - 1}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// --- Main Container Component ---

type MindMapViewProps = {
  mapData: {
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
}

export const MindMapView = ({ mapData }: MindMapViewProps) => {
  // Convert nodes/edges to hierarchical tree
  const rootNode = useMemo(() => {
    return convertToTree(mapData.nodes, mapData.edges)
  }, [mapData.nodes, mapData.edges])

  if (!rootNode) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <p>No mind map data available</p>
      </div>
    )
  }

  return (
    <div className="h-full w-full overflow-auto bg-background">
      <div className="min-w-full flex flex-col p-8">
        <div className="flex items-center justify-start">
          <MindMapNode data={rootNode} />
        </div>
      </div>
    </div>
  )
}

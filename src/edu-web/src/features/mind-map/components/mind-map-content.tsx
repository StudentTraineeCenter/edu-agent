import { useAtomValue } from '@effect-atom/atom-react'
import { Result } from '@effect-atom/atom-react'
import { mindMapAtom } from '@/data-acess/mind-map'
import { MindMapView } from './mind-map-view'
import { Loader2Icon } from 'lucide-react'

type MindMapContentProps = {
  mindMapId: string
  projectId: string
  className?: string
}

export const MindMapContent = ({
  mindMapId,
  projectId,
  className,
}: MindMapContentProps) => {
  const mindMapResult = useAtomValue(mindMapAtom(`${projectId}:${mindMapId}`))

  return Result.builder(mindMapResult)
    .onSuccess((mindMap) => {
      if (!mindMap) {
        return (
          <div className="flex flex-1 items-center justify-center text-muted-foreground">
            <p>Mind map not found</p>
          </div>
        )
      }

      return (
        <div className={`flex flex-col h-full ${className || ''}`}>
          {mindMap.description && (
            <div className="text-muted-foreground text-sm mb-4">
              {mindMap.description}
            </div>
          )}
          <div className="flex-1 min-h-0 border rounded-lg overflow-hidden">
            <MindMapView
              mapData={
                mindMap.map_data as {
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
            />
          </div>
        </div>
      )
    })
    .onInitialOrWaiting(() => (
      <div className="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin" />
        <span>Loading mind map...</span>
      </div>
    ))
    .onFailure(() => (
      <div className="flex flex-1 items-center justify-center gap-2 text-destructive">
        <span>Failed to load mind map</span>
      </div>
    ))
    .render()
}

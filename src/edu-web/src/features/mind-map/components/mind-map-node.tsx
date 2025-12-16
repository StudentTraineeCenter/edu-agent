import { ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

type MindMapNodeProps = {
  id: string
  label: string
  level: number
  hasChildren: boolean
  isExpanded: boolean
  onToggleExpand: () => void
}

export const MindMapNode = ({
  label,
  level,
  hasChildren,
  isExpanded,
  onToggleExpand,
}: MindMapNodeProps) => {
  return (
    <div
      className={cn(
        'mind-map-node flex items-start gap-2 group',
        'transition-all duration-200',
      )}
    >
      {hasChildren ? (
        <Button
          variant="ghost"
          size="icon"
          className={cn(
            'h-6 w-6 shrink-0 mt-0.5 transition-all duration-200',
            'hover:bg-accent hover:scale-110',
            'opacity-70 group-hover:opacity-100',
          )}
          onClick={(e) => {
            e.stopPropagation()
            onToggleExpand()
          }}
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </Button>
      ) : (
        <div className="w-6 shrink-0" />
      )}

      <div
        className={cn(
          'flex-1 rounded-lg border bg-card px-4 py-2.5',
          'shadow-sm transition-all duration-200',
          'hover:shadow-md hover:border-primary/50',
          'cursor-pointer select-none',
          level === 0 && 'border-primary/30 bg-primary/5',
        )}
        onClick={hasChildren ? onToggleExpand : undefined}
      >
        <div className="text-sm font-medium leading-relaxed break-words text-foreground">
          {label}
        </div>
      </div>
    </div>
  )
}

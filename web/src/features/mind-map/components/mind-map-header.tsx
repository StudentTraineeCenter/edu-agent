import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { useAtomValue, useAtomSet } from '@effect-atom/atom-react'
import {
  mindMapsAtom,
  generateMindMapAtom,
  mindMapAtom,
} from '@/data-acess/mind-map'
import { Result } from '@effect-atom/atom-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { ArrowLeft, RefreshCwIcon, Loader2Icon, PlusIcon } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { format } from 'date-fns'
import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

const MindMapHeaderContent = ({
  projectId,
  mindMapId,
}: {
  projectId: string
  mindMapId: string
}) => {
  const mindMapsResult = useAtomValue(mindMapAtom(mindMapId))

  return Result.builder(mindMapsResult)
    .onSuccess((mindMap) => {
      if (!mindMap) {
        return (
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage className="line-clamp-1 font-medium">
                  Mind Maps
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        )
      }

      return (
        <div className="flex items-center gap-4">
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage className="line-clamp-1 font-medium">
                  {mindMap.title}
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <span className="text-xs text-muted-foreground">
            Generated:{' '}
            {format(new Date(mindMap.generated_at), 'MMM dd, yyyy HH:mm')}
          </span>
        </div>
      )
    })
    .onInitialOrWaiting(() => <Skeleton className="w-72 h-7" />)
    .onFailure(() => (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage className="line-clamp-1 font-medium">
              Mind Maps
            </BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    ))
    .render()
}

type MindMapHeaderProps = {
  projectId: string
  mindMapId: string
}

export const MindMapHeader = ({ projectId, mindMapId }: MindMapHeaderProps) => {
  const generateMap = useAtomSet(generateMindMapAtom, { mode: 'promise' })
  const [isGenerating, setIsGenerating] = useState(false)
  const [userPrompt, setUserPrompt] = useState('')
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const handleGenerate = async () => {
    setIsGenerating(true)
    try {
      await generateMap({
        projectId,
        userPrompt: userPrompt || undefined,
      })
      setUserPrompt('')
      setIsDialogOpen(false)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <header className="bg-background sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b px-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        <SidebarTrigger />
        <Button variant="ghost" size="icon" className="size-7" asChild>
          <Link to="/dashboard/p/$projectId" params={{ projectId }}>
            <ArrowLeft className="size-4" />
            <span className="sr-only">Back to project</span>
          </Link>
        </Button>
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <MindMapHeaderContent projectId={projectId} mindMapId={mindMapId} />
      </div>
      <div className="flex items-center gap-2 px-3">
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="default" size="sm">
              <PlusIcon className="size-4 mr-2" />
              <span>Generate Mind Map</span>
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Generate Mind Map</DialogTitle>
              <DialogDescription>
                Create a new mind map from your project documents. Optionally
                specify a topic or focus area.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="prompt">Topic or Focus Area (Optional)</Label>
                <Textarea
                  id="prompt"
                  placeholder="e.g., Machine Learning, Data Structures, History of Art..."
                  value={userPrompt}
                  onChange={(e) => setUserPrompt(e.target.value)}
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsDialogOpen(false)}
                disabled={isGenerating}
              >
                Cancel
              </Button>
              <Button onClick={handleGenerate} disabled={isGenerating}>
                {isGenerating ? (
                  <>
                    <Loader2Icon className="size-4 mr-2 animate-spin" />
                    <span>Generating...</span>
                  </>
                ) : (
                  <span>Generate</span>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </header>
  )
}

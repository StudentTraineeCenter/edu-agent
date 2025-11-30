import { useForm } from 'react-hook-form'
import { effectTsResolver } from '@hookform/resolvers/effect-ts'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { create } from 'zustand'
import { useAtom } from '@effect-atom/atom-react'
import { upsertProjectAtom } from '@/data-acess/project'
import * as S from 'effect/Schema'
import { ProjectDto } from '@/integrations/api/client'
import { useEffect } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

type CreateProjectDialogStore = {
  isOpen: boolean
  project?: ProjectDto
  open: (project?: ProjectDto) => void
  close: () => void
  toggle: () => void
}

export const useCreateProjectDialog = create<CreateProjectDialogStore>(
  (set) => ({
    isOpen: false,
    open: (project?: ProjectDto) =>
      set({ isOpen: true, project: project ?? undefined }),
    close: () => set({ isOpen: false }),
    toggle: () => set((state) => ({ isOpen: !state.isOpen })),
  }),
)

const schema = S.Struct({
  name: S.String,
  description: S.optional(S.String),
  language_code: S.String,
})

type UpsertProjectSchema = typeof schema.Type

const languages = [
  { code: 'cs', name: 'Czech' },
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' },
  { code: 'zh', name: 'Chinese' },
]

export function UpsertProjectDialog() {
  const { isOpen, close, project } = useCreateProjectDialog()

  const [upsertProjectResult, upsertProject] = useAtom(upsertProjectAtom, {
    mode: 'promise',
  })
  const isLoading = upsertProjectResult.waiting

  const form = useForm<UpsertProjectSchema>({
    resolver: effectTsResolver(schema),
    defaultValues: {
      name: '',
      description: '',
      language_code: 'cs',
    },
  })

  useEffect(() => {
    if (isOpen) {
      form.reset({
        name: project?.name ?? '',
        description: project?.description ?? '',
        language_code: project?.language_code ?? 'cs',
      })
    }
  }, [isOpen, project, form])

  const handleClose = () => {
    close()
    form.reset()
  }

  const onSubmit = async (data: UpsertProjectSchema) => {
    await upsertProject(data)
    handleClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create Project</DialogTitle>
          <DialogDescription>
            Create a new project to organize your learning materials and
            conversations.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., My Project" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description (Optional)</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., Project description" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="language_code"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Language Code</FormLabel>
                  <FormControl>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select a language" />
                      </SelectTrigger>
                      <SelectContent>
                        {languages.map((language) => (
                          <SelectItem key={language.code} value={language.code}>
                            {language.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Creating...' : 'Create Project'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

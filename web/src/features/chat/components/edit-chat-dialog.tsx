import React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
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
import { updateChatAtom } from '@/data-acess/chat'
import { create } from 'zustand'
import { useAtom } from '@effect-atom/atom-react'

type EditChatDialogStore = {
  isOpen: boolean
  chatId: string | null
  projectId: string | null
  currentTitle: string | null
  open: (projectId: string, chatId: string, currentTitle: string | null) => void
  close: () => void
}

export const useEditChatDialog = create<EditChatDialogStore>((set) => ({
  isOpen: false,
  chatId: null,
  projectId: null,
  currentTitle: null,
  open: (projectId: string, chatId: string, currentTitle: string | null) =>
    set({ isOpen: true, projectId, chatId, currentTitle }),
  close: () =>
    set({ isOpen: false, projectId: null, chatId: null, currentTitle: null }),
}))

const editChatSchema = z.object({
  title: z.string().min(1, 'Title is required').max(100, 'Title too long'),
})

type EditChatForm = z.infer<typeof editChatSchema>

export function EditChatDialog() {
  const { isOpen, projectId, chatId, currentTitle, close } = useEditChatDialog()

  const [updateChatResult, updateChatMutation] = useAtom(updateChatAtom, {
    mode: 'promise',
  })

  const form = useForm<EditChatForm>({
    resolver: zodResolver(editChatSchema),
    defaultValues: {
      title: currentTitle || '',
    },
  })

  // Update form when dialog opens with new data
  React.useEffect(() => {
    if (isOpen && currentTitle !== null) {
      form.reset({ title: currentTitle || '' })
    }
  }, [isOpen, currentTitle, form])

  const handleClose = () => {
    close()
    form.reset()
  }

  const onSubmit = async (data: EditChatForm) => {
    if (!projectId || !chatId) return

    await updateChatMutation({
      chatId,
      projectId,
      title: data.title,
    })

    handleClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Chat</DialogTitle>
          <DialogDescription>
            Update the name of your chat conversation.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Chat Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., My Chat" {...field} />
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
                disabled={updateChatResult.waiting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={updateChatResult.waiting}>
                {updateChatResult.waiting ? 'Updating...' : 'Update Chat'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

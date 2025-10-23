import React, { useState } from 'react'
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
import { useQueryClient } from '@tanstack/react-query'
import { useUpdateChatMutation } from '@/data-acess/chat'
import { create } from 'zustand'

type EditChatDialogStore = {
    isOpen: boolean
    chatId: string | null
    currentTitle: string | null
    open: (chatId: string, currentTitle: string | null) => void
    close: () => void
}

export const useEditChatDialog = create<EditChatDialogStore>((set) => ({
    isOpen: false,
    chatId: null,
    currentTitle: null,
    open: (chatId: string, currentTitle: string | null) =>
        set({ isOpen: true, chatId, currentTitle }),
    close: () => set({ isOpen: false, chatId: null, currentTitle: null }),
}))

const editChatSchema = z.object({
    title: z.string().min(1, 'Title is required').max(100, 'Title too long'),
})

type EditChatForm = z.infer<typeof editChatSchema>

export function EditChatDialog() {
    const { isOpen, chatId, currentTitle, close } = useEditChatDialog()
    const [isLoading, setIsLoading] = useState(false)

    const queryClient = useQueryClient()

    const updateChatMutation = useUpdateChatMutation({
        onSuccess: () => {
            handleClose()
            // Invalidate both chat list and individual chat queries
            queryClient.invalidateQueries({
                queryKey: ['chats'],
            })
            if (chatId) {
                queryClient.invalidateQueries({
                    queryKey: ['chat', chatId],
                })
            }
        },
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
        if (!chatId) return

        try {
            setIsLoading(true)

            updateChatMutation.mutate({
                chatId,
                title: data.title,
            })

            handleClose()
        } catch (error) {
            console.error('Failed to update chat:', error)
        } finally {
            setIsLoading(false)
        }
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
                                disabled={isLoading}
                            >
                                Cancel
                            </Button>
                            <Button type="submit" disabled={isLoading}>
                                {isLoading ? 'Updating...' : 'Update Chat'}
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    )
}

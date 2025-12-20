import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { AlertTriangleIcon } from 'lucide-react'
import { create } from 'zustand'

type ConfirmationDialogState = {
  isOpen: boolean
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'default' | 'destructive'
  resolve?: (value: boolean) => void
}

type ConfirmationDialogStore = ConfirmationDialogState & {
  open: (options: {
    title: string
    description: string
    confirmLabel?: string
    cancelLabel?: string
    variant?: 'default' | 'destructive'
  }) => Promise<boolean>
  close: (confirmed: boolean) => void
}

export const useConfirmationDialog = create<ConfirmationDialogStore>((set) => ({
  isOpen: false,
  title: '',
  description: '',
  confirmLabel: 'Confirm',
  cancelLabel: 'Cancel',
  variant: 'default',
  open: (options) => {
    return new Promise<boolean>((resolve) => {
      set({
        isOpen: true,
        title: options.title,
        description: options.description,
        confirmLabel: options.confirmLabel || 'Confirm',
        cancelLabel: options.cancelLabel || 'Cancel',
        variant: options.variant || 'default',
        resolve,
      })
    })
  },
  close: (confirmed: boolean) => {
    set((state) => {
      state.resolve?.(confirmed)
      return {
        isOpen: false,
        title: '',
        description: '',
        confirmLabel: 'Confirm',
        cancelLabel: 'Cancel',
        variant: 'default',
        resolve: undefined,
      }
    })
  },
}))

export function ConfirmationDialog() {
  const {
    isOpen,
    title,
    description,
    confirmLabel,
    cancelLabel,
    variant,
    close,
  } = useConfirmationDialog()

  const handleConfirm = () => {
    close(true)
  }

  const handleCancel = () => {
    close(false)
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleCancel()}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            {variant === 'destructive' && (
              <AlertTriangleIcon className="size-5 text-destructive" />
            )}
            <DialogTitle>{title}</DialogTitle>
          </div>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            {cancelLabel}
          </Button>
          <Button
            variant={variant === 'destructive' ? 'destructive' : 'default'}
            onClick={handleConfirm}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

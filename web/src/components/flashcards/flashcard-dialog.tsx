import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { FlashcardDetail } from './flashcard-detail'
import { create } from 'zustand'

type FlashcardDialogStore = {
  isOpen: boolean
  flashcardGroupId: string | null
  open: (flashcardGroupId: string) => void
  close: () => void
}

export const useFlashcardDialog = create<FlashcardDialogStore>((set) => ({
  isOpen: false,
  flashcardGroupId: null,
  open: (flashcardGroupId: string) => set({ isOpen: true, flashcardGroupId }),
  close: () => set({ isOpen: false, flashcardGroupId: null }),
}))

export function FlashcardDialog() {
  const { isOpen, flashcardGroupId, close } = useFlashcardDialog()

  if (!flashcardGroupId) return null

  return (
    <Dialog open={isOpen} onOpenChange={close}>
      <DialogContent className="max-w-7xl max-h-[95vh] overflow-hidden w-full h-[95vh]">
        <DialogHeader>
          <DialogTitle>Study Flashcards</DialogTitle>
          <DialogDescription>
            Review and practice with your flashcard set.
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 overflow-auto">
          <FlashcardDetail flashcardGroupId={flashcardGroupId} />
        </div>
      </DialogContent>
    </Dialog>
  )
}

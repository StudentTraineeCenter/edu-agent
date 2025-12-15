import { useConfirmationDialog } from '@/components/confirmation-dialog'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { usageAtom } from '@/data-acess/usage'
import { useAuth } from '@/hooks/use-auth'
import { useTheme } from '@/providers/theme-provider'
import { Result, useAtomValue } from '@effect-atom/atom-react'
import { Loader2Icon, Trash2Icon } from 'lucide-react'
import { useState } from 'react'

export function SettingsPage() {
  const { user } = useAuth()
  const { theme, setTheme } = useTheme()
  const confirmationDialog = useConfirmationDialog()
  const usageResult = useAtomValue(usageAtom)
  const [isDeletingAllChats, setIsDeletingAllChats] = useState(false)

  const handleDeleteAllChats = async () => {
    const confirmed = await confirmationDialog.open({
      title: 'Delete All Chats',
      description:
        'This is a mock action. Your chats will not actually be deleted. Are you sure you want to proceed?',
      confirmLabel: 'Delete All',
      cancelLabel: 'Cancel',
      variant: 'destructive',
    })

    if (!confirmed) return

    setIsDeletingAllChats(true)

    // Mock action - simulate delay
    await new Promise((resolve) => setTimeout(resolve, 1500))

    alert('Delete all chats is not implemented. This is a mock action.')
    setIsDeletingAllChats(false)
  }

  const handleDeleteAccount = async () => {
    const confirmed = await confirmationDialog.open({
      title: 'Delete Account',
      description:
        'This is a mock action. Your account will not actually be deleted. Are you sure you want to proceed?',
      confirmLabel: 'Delete',
      cancelLabel: 'Cancel',
      variant: 'destructive',
    })

    if (confirmed) {
      // Mock action - just show an alert
      alert('Account deletion is not implemented. This is a mock action.')
    }
  }

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <div className="flex h-full flex-col">
      <header className="bg-background sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b px-2">
        <div className="flex flex-1 items-center gap-2 px-3">
          <SidebarTrigger />
          <Separator
            orientation="vertical"
            className="mr-2 data-[orientation=vertical]:h-4"
          />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage className="font-medium">
                  Settings
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>
      </header>

      <div className="flex flex-1 flex-col min-h-0 overflow-y-auto">
        <div className="max-w-4xl mx-auto w-full p-4 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Account</CardTitle>
              <CardDescription>Your account information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <Avatar className="size-16">
                  <AvatarFallback>
                    {user?.user_metadata?.name
                      ? getInitials(user.user_metadata.name)
                      : 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <p className="font-semibold">
                    {user?.user_metadata?.name || 'Unknown'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {user?.email || 'Unknown'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>Choose your preferred theme</CardDescription>
            </CardHeader>
            <CardContent>
              <Select
                value={theme}
                onValueChange={(value) => setTheme(value as typeof theme)}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select theme" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">Light</SelectItem>
                  <SelectItem value="dark">Dark</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Usage</CardTitle>
              <CardDescription>
                Your daily usage statistics and limits
              </CardDescription>
            </CardHeader>
            <CardContent>
              {Result.builder(usageResult)
                .onInitialOrWaiting(() => (
                  <div className="text-muted-foreground text-sm">
                    Loading usage statistics...
                  </div>
                ))
                .onFailure(() => (
                  <div className="text-destructive text-sm">
                    Failed to load usage statistics
                  </div>
                ))
                .onSuccess((usage) => (
                  <div className="space-y-6">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">Chat Messages</span>
                        <span className="text-muted-foreground">
                          {usage.chat_messages.used} /{' '}
                          {usage.chat_messages.limit}
                        </span>
                      </div>
                      <Progress
                        value={
                          (usage.chat_messages.used /
                            usage.chat_messages.limit) *
                          100
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">
                          Flashcard Generations
                        </span>
                        <span className="text-muted-foreground">
                          {usage.flashcard_generations.used} /{' '}
                          {usage.flashcard_generations.limit}
                        </span>
                      </div>
                      <Progress
                        value={
                          (usage.flashcard_generations.used /
                            usage.flashcard_generations.limit) *
                          100
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">Quiz Generations</span>
                        <span className="text-muted-foreground">
                          {usage.quiz_generations.used} /{' '}
                          {usage.quiz_generations.limit}
                        </span>
                      </div>
                      <Progress
                        value={
                          (usage.quiz_generations.used /
                            usage.quiz_generations.limit) *
                          100
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">
                          Mind Map Generations
                        </span>
                        <span className="text-muted-foreground">
                          {usage.mindmap_generations.used} /{' '}
                          {usage.mindmap_generations.limit}
                        </span>
                      </div>
                      <Progress
                        value={
                          (usage.mindmap_generations.used /
                            usage.mindmap_generations.limit) *
                          100
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">Document Uploads</span>
                        <span className="text-muted-foreground">
                          {usage.document_uploads.used} /{' '}
                          {usage.document_uploads.limit}
                        </span>
                      </div>
                      <Progress
                        value={
                          (usage.document_uploads.used /
                            usage.document_uploads.limit) *
                          100
                        }
                      />
                    </div>
                  </div>
                ))
                .render()}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Danger Zone</CardTitle>
              <CardDescription>
                Irreversible and destructive actions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Delete All Chats</p>
                    <p className="text-sm text-muted-foreground">
                      Permanently delete all your chat conversations (mock)
                    </p>
                  </div>
                  <Button
                    variant="destructive"
                    onClick={handleDeleteAllChats}
                    disabled={isDeletingAllChats}
                  >
                    {isDeletingAllChats ? (
                      <>
                        <Loader2Icon className="size-4 mr-2 animate-spin" />
                        Deleting...
                      </>
                    ) : (
                      <>
                        <Trash2Icon className="size-4 mr-2" />
                        Delete All
                      </>
                    )}
                  </Button>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Delete Account</p>
                    <p className="text-sm text-muted-foreground">
                      Permanently delete your account and all associated data
                      (mock)
                    </p>
                  </div>
                  <Button variant="destructive" onClick={handleDeleteAccount}>
                    <Trash2Icon className="size-4 mr-2" />
                    Delete Account
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

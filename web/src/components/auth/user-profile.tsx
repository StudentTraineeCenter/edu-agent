import { useAuth } from '@/hooks/use-auth'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { LogoutButton } from '@/components/auth/logout-button'
import { Link } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import { buttonVariants } from '@/components/ui/button'
import { useEffect } from 'react'
import { profilePhotoAtom } from '@/data-acess/auth'
import { useAtomValue } from '@effect-atom/atom-react'

export const UserProfile = () => {
  const { user, account } = useAuth()

  const profilePhotoResult = useAtomValue(profilePhotoAtom)
  const photoUrl =
    profilePhotoResult._tag === 'Success' ? profilePhotoResult.value : undefined

  useEffect(() => {
    return () => {
      if (photoUrl) {
        URL.revokeObjectURL(photoUrl)
      }
    }
  }, [photoUrl])

  if (!user || !account) return null

  const initials = user.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()

  return (
    <div className="flex items-center gap-3 p-3 border rounded-lg">
      <Avatar>
        <AvatarImage
          src={
            profilePhotoResult._tag === 'Success'
              ? profilePhotoResult.value
              : undefined
          }
        />
        <AvatarFallback>{initials}</AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{user.name}</p>
        <p className="text-xs text-gray-500 truncate">{user.email}</p>
      </div>
      <div className="flex items-center gap-2">
        <Link to="/" className={cn(buttonVariants({ variant: 'default' }))}>
          Dashboard
        </Link>
      </div>
      <LogoutButton />
    </div>
  )
}

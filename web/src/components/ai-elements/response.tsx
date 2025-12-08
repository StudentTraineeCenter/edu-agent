'use client'

import { cn } from '@/lib/utils'
import { type ComponentProps, memo } from 'react'
import { Streamdown } from 'streamdown'

type ResponseProps = ComponentProps<typeof Streamdown>

export const Response = memo(
  ({ className, ...props }: ResponseProps) => (
    <Streamdown
      className={cn(
        'size-full prose prose-sm dark:prose-invert max-w-none',
        '[&>*:first-child]:mt-0 [&>*:last-child]:mb-0',
        '[&_p]:my-2 [&_p]:leading-relaxed',
        '[&_h1]:text-2xl [&_h1]:font-bold [&_h1]:mt-4 [&_h1]:mb-2',
        '[&_h2]:text-xl [&_h2]:font-semibold [&_h2]:mt-3 [&_h2]:mb-2',
        '[&_h3]:text-lg [&_h3]:font-semibold [&_h3]:mt-2 [&_h3]:mb-1',
        '[&_ul]:list-disc [&_ul]:ml-4 [&_ul]:my-2',
        '[&_ol]:list-decimal [&_ol]:ml-4 [&_ol]:my-2',
        '[&_li]:my-1',
        '[&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm [&_code]:font-mono',
        '[&_pre]:bg-muted [&_pre]:p-4 [&_pre]:rounded-lg [&_pre]:overflow-x-auto [&_pre]:my-2',
        '[&_pre_code]:bg-transparent [&_pre_code]:p-0',
        '[&_blockquote]:border-l-4 [&_blockquote]:border-muted-foreground [&_blockquote]:pl-4 [&_blockquote]:italic [&_blockquote]:my-2',
        '[&_a]:text-primary [&_a]:underline',
        '[&_strong]:font-bold',
        '[&_em]:italic',
        '[&_table]:w-full [&_table]:border-collapse [&_table]:my-2',
        '[&_th]:border [&_th]:border-border [&_th]:px-4 [&_th]:py-2 [&_th]:bg-muted [&_th]:font-semibold',
        '[&_td]:border [&_td]:border-border [&_td]:px-4 [&_td]:py-2',
        className,
      )}
      {...props}
    />
  ),
  (prevProps, nextProps) => prevProps.children === nextProps.children,
)

Response.displayName = 'Response'

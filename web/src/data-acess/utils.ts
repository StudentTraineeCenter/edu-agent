import type { UseMutationOptions } from '@tanstack/react-query'

export type MutationOptions<TData, TVariables> = UseMutationOptions<
  TData,
  Error,
  TVariables,
  unknown
>

import * as S from 'effect/Schema'

export const ProjectIdSchema = S.UUID.pipe(S.brand('ProjectId'))
export type ProjectId = typeof ProjectIdSchema.Type

export const UserIdSchema = S.UUID.pipe(S.brand('UserId'))
export type UserId = typeof UserIdSchema.Type

export const DocumentIdSchema = S.UUID.pipe(S.brand('DocumentId'))
export type DocumentId = typeof DocumentIdSchema.Type

export const QuizIdSchema = S.UUID.pipe(S.brand('QuizId'))
export type QuizId = typeof QuizIdSchema.Type

export const QuizQuestionIdSchema = S.UUID.pipe(S.brand('QuizQuestionId'))
export type QuizQuestionId = typeof QuizQuestionIdSchema.Type

export const NoteIdSchema = S.UUID.pipe(S.brand('NoteId'))
export type NoteId = typeof NoteIdSchema.Type

export const ChatIdSchema = S.UUID.pipe(S.brand('ChatId'))
export type ChatId = typeof ChatIdSchema.Type

export const MessageIdSchema = S.UUID.pipe(S.brand('MessageId'))
export type MessageId = typeof MessageIdSchema.Type

export const PartIdSchema = S.UUID.pipe(S.brand('PartId'))
export type PartId = typeof PartIdSchema.Type

export const FlashcardIdSchema = S.UUID.pipe(S.brand('FlashcardId'))
export type FlashcardId = typeof FlashcardIdSchema.Type

export const FlashcardGroupIdSchema = S.UUID.pipe(S.brand('FlashcardGroupId'))
export type FlashcardGroupId = typeof FlashcardGroupIdSchema.Type

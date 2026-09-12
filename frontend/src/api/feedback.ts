import { post } from './client'
import type { FeedbackCreate, FeedbackOut } from '../types'

export function submit(data: FeedbackCreate): Promise<FeedbackOut> {
  return post<FeedbackOut>('/feedback/', data)
}

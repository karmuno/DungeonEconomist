import { post } from './client'
import type { AccountOut } from '../types'

export function advanceTutorial(step: number): Promise<AccountOut> {
  return post<AccountOut>('/tutorial/advance', { step })
}

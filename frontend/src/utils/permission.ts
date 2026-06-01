import { USER_ROLE_ADMIN, USER_ROLE_VIP } from '@/constants/user'
import type { LoginUserVO } from '@/types/user'

export function isAdmin(user?: LoginUserVO | null): boolean {
  return user?.userRole === USER_ROLE_ADMIN
}

export function isVip(user?: LoginUserVO | null): boolean {
  return user?.userRole === USER_ROLE_VIP || isAdmin(user)
}

export function hasQuota(user?: LoginUserVO | null): boolean {
  if (isAdmin(user) || isVip(user)) return true
  return (user?.quota ?? 0) > 0
}

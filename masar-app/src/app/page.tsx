'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()
  useEffect(() => {
    const profile = localStorage.getItem('masar_profile')
    router.replace(profile ? '/dashboard' : '/onboarding')
  }, [router])
  return null
}

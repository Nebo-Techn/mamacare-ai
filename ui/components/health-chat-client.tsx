"use client"

import dynamic from "next/dynamic"

  const HealthChat = dynamic(() => import("./health-chat").then((mod) => mod?.default ?? mod.HealthChat), {
  ssr: false,
  loading: () => <div className="flex min-h-screen items-center justify-center">Inakuja...</div>,
})

export default function HealthChatClient() {
  return <HealthChat />
}

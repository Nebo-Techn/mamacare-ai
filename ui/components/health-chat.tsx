"use client"

import type React from "react"

import { useChat } from "@ai-sdk/react"
import { DefaultChatTransport } from "ai"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Activity, Send, Sparkles, Heart, Brain, Pill, Paperclip, X } from "lucide-react"

type ChatHistory = {
  id: string
  title: string
  timestamp: Date
  messages: any[]
}

function HealthChat() {
  const [inputValue, setInputValue] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({ api: "/api/chat" }),
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Removed chat history sidebar; history logic has been cleaned up

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleRemoveFile = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (inputValue.trim() && String(status) !== "in_progress") {
        const currentInput = inputValue
        let messageText = currentInput
        if (selectedFile) {
          messageText = `[Attached file: ${selectedFile.name}]\n\n${currentInput}`
        }

        // Clear UI immediately for snappier UX
        setInputValue("")
        handleRemoveFile()

        // Debug log: show the outgoing user message
        console.log("Sending message to transport:", messageText)

        // sendMessage may be async depending on transport implementation
        try {
          await sendMessage({ text: messageText })
          console.log("sendMessage completed")
        } catch (sendErr) {
          console.error("sendMessage error:", sendErr)
        }
      } else {
        // Log why message wasn't sent
        console.log("handleSubmit: not sending — empty input or transport busy", { inputValue, status })
      }
    } catch (err) {
      console.error("handleSubmit error:", err)
    }
  }

  const quickPrompts = [
    { icon: Heart, text: "Dondoo za afya ya moyo", prompt: "Ni dalili zipi za maradhi ya moyo kwa mtoto mchanga?" },
    { icon: Brain, text: "Afya ya akili", prompt: "Je ninaweza vipi kulinda afya ya akili ya mtoto?" },
    { icon: Pill, text: "Matumizi sahihi ya dawa", prompt: "Je nitumie vipi dawa kwa mtoto ninapohisi ni mgonjwa?" },
  ]

  return (
  <div className="flex h-screen bg-background overflow-hidden">

      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <header className="border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80 px-4 md:px-5 py-3">
          <div className="flex items-center gap-2.5 max-w-4xl mx-auto">
            <div className="flex items-center justify-center w-9 h-9 md:w-10 md:h-10 rounded-full bg-primary shadow-sm">
              <Activity className="w-3.5 h-3.5 md:w-4 md:h-4 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-[15px] md:text-base font-semibold text-card-foreground">Mama care AI</h1>
              <p className="text-[13px] md:text-sm text-muted-foreground">Rafiki na msaidizi wako katika malezi bora ya mtoto</p>
            </div>
          </div>
        </header>

        {/* Messages Area */}
  <div className="flex-1 overflow-y-auto px-5 py-5 pb-28">
          <div className="max-w-4xl mx-auto space-y-5">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-5">
                <div className="flex items-center justify-center w-12 h-12 md:w-16 md:h-16 rounded-full bg-primary/10">
                  <Sparkles className="w-6 h-6 md:w-8 md:h-8 text-primary" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-xl md:text-2xl font-semibold text-balance">
                    Ni jambo gani kuhusu afya ya mtoto linakutatiza?
                  </h2>
                  <p className="text-muted-foreground text-balance max-w-md text-sm md:text-[13px]">
                  Niulize kuhusu dalili, dondoo za afya bora, taarifa kuhusu na matumizi ya dawa, na ukuaji wa mtoto kwa ujumla.
                  </p>
                </div>

                {/* Quick Prompts: horizontal scroll on mobile, row on md+ */}
                <div className="flex gap-2.5 w-full max-w-2xl pt-3.5 overflow-x-auto [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                  {quickPrompts.map((prompt, index) => (
                    <Card
                      key={index}
                      onClick={() => setInputValue(prompt.prompt)}
                      className="p-2 md:p-3 cursor-pointer hover:shadow-md hover:-translate-y-0.5 transition-transform duration-200 border-border flex-1 min-w-[160px] md:min-w-0 basis-0"
                    >
                      <div className="flex flex-col items-center gap-1.5 text-center">
                        <div className="flex items-center justify-center w-8 h-8 md:w-9 md:h-9 rounded-full bg-primary/10">
                          <prompt.icon className="w-3 md:w-4 h-3 md:h-4 text-primary" />
                        </div>
                        <p className="text-xs md:text-sm font-medium text-card-foreground whitespace-normal break-words text-center">{prompt.text}</p>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-2.5 ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {message.role === "assistant" && (
                      <div className="flex items-center justify-center w-7 h-7 rounded-full bg-primary flex-shrink-0 mt-1">
                        <Activity className="w-3.5 h-3.5 text-primary-foreground" />
                      </div>
                    )}
                    <div
                      className={`rounded-2xl px-3 py-2 md:px-3.5 md:py-2.5 max-w-[80%] sm:max-w-[70%] md:max-w-[72%] shadow-sm ${
                        message.role === "user"
                          ? "bg-gradient-to-br from-teal-500 to-teal-600 text-white shadow-md"
                          : "bg-card text-card-foreground border border-border"
                      }`}
                    >
                      {message.parts.map((part, index) => {
                        if (part.type === "text") {
                          return (
                            <p key={index} className="text-xs md:text-sm leading-relaxed whitespace-pre-wrap">
                              {part.text}
                            </p>
                          )
                        }
                        return null
                      })}
                    </div>
                    {message.role === "user" && (
                      <div className="flex items-center justify-center w-7 h-7 rounded-full bg-accent flex-shrink-0 mt-1">
                        <div className="w-4.5 h-4.5 rounded-full bg-accent-foreground/20" />
                      </div>
                    )}
                  </div>
                ))}
                {String(status) === "in_progress" && (
                  <div className="flex gap-3 justify-start">
                    <div className="flex items-center justify-center w-7 h-7 rounded-full bg-primary flex-shrink-0">
                      <Activity className="w-3.5 h-3.5 text-primary-foreground" />
                    </div>
                    <div className="rounded-2xl px-3.5 py-2.5 bg-card border border-border">
                      <div className="flex gap-1">
                        <div
                          className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce"
                          style={{ animationDelay: "0ms" }}
                        />
                        <div
                          className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce"
                          style={{ animationDelay: "150ms" }}
                        />
                        <div
                          className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce"
                          style={{ animationDelay: "300ms" }}
                        />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-border bg-card px-4 py-3 md:px-5">
          {/* Fixed input bar at bottom */}
          <div className="fixed left-0 right-0 bottom-0 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80 border-t border-border py-3">
            <form onSubmit={handleSubmit} className="max-w-4xl mx-auto px-4">
            {selectedFile && (
              <div className="mb-2 flex items-center gap-2 p-2 bg-accent rounded-md">
                <Paperclip className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-[13px] text-foreground flex-1 truncate">{selectedFile.name}</span>
                <Button type="button" variant="ghost" size="icon" className="h-6 w-6" onClick={handleRemoveFile}>
                  <X className="w-3.5 h-3.5" />
                </Button>
              </div>
            )}
            <div className="flex gap-2 items-end">
              <div className="flex-1 relative">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault()
                      handleSubmit(e)
                    }
                  }}
                  placeholder="Uliza kuhusu afya ya mama na mtoto..."
                  className="w-full px-3.5 py-2.5 pr-11 rounded-xl border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-teal-400 resize-none min-h-[44px] max-h-32 text-[13px]"
                  rows={1}
                  disabled={String(status) === "in_progress"}
                />
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  onChange={handleFileSelect}
                  accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
                />
                <Button type="button" variant="ghost" size="icon" className="absolute right-2 bottom-2 h-7 w-7" onClick={() => fileInputRef.current?.click()} disabled={String(status) === "in_progress"}>
                  <Paperclip className="w-3.5 h-3.5" />
                  <span className="sr-only">pakia nyaraka</span>
                </Button>
              </div>
              <Button
                type="submit"
                size="icon"
                className="h-[44px] w-[44px] rounded-xl flex-shrink-0 bg-teal-500 text-white hover:bg-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-400 shadow-sm hover:shadow"
                aria-label="Tuma ujumbe"
                disabled={!inputValue.trim() || String(status) === "in_progress"}
              >
                <Send className="w-4 h-4" />
                <span className="sr-only">Tuma ujumbe</span>
              </Button>
            </div>
            {/* Footer text removed as requested */}
          </form>
          </div>
        </div>
      </div>
    </div>
  )
}

// Named export for compatibility
export { HealthChat }

// Default export to make dynamic imports simpler
export default HealthChat

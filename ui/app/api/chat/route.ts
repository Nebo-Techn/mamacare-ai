import { consumeStream, convertToModelMessages, type UIMessage } from "ai"

export const maxDuration = 30

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();
  const prompt = convertToModelMessages(messages);

  // Extract last user message text
  const userMsgs = messages.filter((m) => m.role === "user");
  const lastUser = userMsgs[userMsgs.length - 1];
  const userQuery = lastUser
    ? lastUser.parts
        .filter((p: any) => p.type === "text")
        .map((p: any) => p.text)
        .join("\n")
    : "";

  // 🧠 High-quality prompt template for maternal model
  const fullPrompt = `
You are a maternal health assistant that provides accurate and empathetic responses in fluent Kiswahili.

Below is a question from a pregnant woman or mother. 
Write a clear, natural, and well-organized response in Kiswahili.

Guidelines:
- Use short, easy-to-understand sentences.
- Organize information in short paragraphs or bullet points.
- Include specific examples when possible (e.g., mention food types, symptoms, or habits).
- Maintain a kind and reassuring tone throughout.
- Do not repeat words or phrases unnecessarily.
- Avoid moralizing or scolding language.
- Always end with this sentence exactly:
  "muone daktari au mtaalamu wa afya kwa taarifa zaidi"

### Intruction:
${userQuery}

### Response:
`;

  try {
    const externalRes = await fetch("http://34.41.66.56:3050/v1/completions", {
      method: "POST",
      headers: {
        accept: "application/json",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: "NeboTech/maternal-swahili-model",
        prompt: fullPrompt,
        max_tokens: 400,
        temperature: 0.4,
        top_p: 0.9,
        frequency_penalty: 0.7,
        presence_penalty: 0.6,
        repetition_penalty: 1.3,
        use_beam_search: false,
        top_k: 50,
        n: 1,
        stop: ["###", "muone daktari", "End"]
      }),
      signal: req.signal,
    });

    if (!externalRes.ok) {
      const text = await externalRes.text().catch(() => "");
      return new Response(
        JSON.stringify({
          error: "External model request failed",
          status: externalRes.status,
          body: text,
        }),
        { status: 502, headers: { "content-type": "application/json" } }
      );
    }

    const data = await externalRes.json().catch(() => null);
    let assistantText = "";

    // 🧩 Extract model output from different possible formats
    if (data) {
      if (Array.isArray(data.choices) && data.choices.length > 0) {
        const choice = data.choices[0];
        assistantText =
          choice.text ??
          (choice.message?.content
            ? Array.isArray(choice.message.content)
              ? choice.message.content.map((c: any) => c.text ?? "").join("")
              : String(choice.message.content)
            : "");
      } else if (typeof data.output === "string") {
        assistantText = data.output;
      } else if (Array.isArray(data.output)) {
        assistantText = data.output
          .map((o: any) =>
            o.text ??
            (o.content
              ? Array.isArray(o.content)
                ? o.content.map((c: any) => c.text ?? "").join("")
                : String(o.content)
              : "")
          )
          .join("\n");
      } else if (typeof data.text === "string") {
        assistantText = data.text;
      }
    }

    // 🔍 Fallback if empty
    if (!assistantText) assistantText = JSON.stringify(data ?? {});

    // 🧹 Clean output (remove "### End" artifacts and normalize whitespace)
    try {
      assistantText = assistantText
        .replace(/###\s*End[\s\S]*$/gi, "")
        .replace(/(###\s*End\s*\w+\.?\s*)+/gi, "")
        .replace(/(\r?\n\s*){3,}/g, "\n\n")
        .trim();
    } catch (e) {}

    // ✅ Ensure closing line is included
    const closing = "muone daktari au mtaalamu wa afya kwa taarifa zaidi";
    if (!assistantText.toLowerCase().includes(closing.toLowerCase())) {
      assistantText = `${assistantText.trim()}`;
    }

    // 🎧 Stream back response as SSE
    const encoder = new TextEncoder();
    const chunkSize = 1024;
    const parts: string[] = [];
    for (let i = 0; i < assistantText.length; i += chunkSize) {
      parts.push(assistantText.slice(i, i + chunkSize));
    }

    const stream = new ReadableStream({
      start(controller) {
        const enqueue = (obj: any) =>
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(obj)}\n\n`));
        try {
          enqueue({ type: "start" });
          enqueue({ type: "start-step" });
          enqueue({ type: "text-start", id: "text-1" });

          for (const p of parts) enqueue({ type: "text-delta", id: "text-1", delta: p });

          enqueue({ type: "text-end", id: "text-1" });
          enqueue({ type: "finish-step" });
          enqueue({ type: "finish" });
          controller.close();
        } catch (err) {
          controller.error(err);
        }
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
        "x-vercel-ai-ui-message-stream": "v1",
        "x-accel-buffering": "no",
      },
    });
  } catch (err: any) {
    console.error("Chat handler error", err);
    return new Response(JSON.stringify({ error: String(err) }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }
}


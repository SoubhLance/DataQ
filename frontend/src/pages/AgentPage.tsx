import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import { Send, Sparkles, User, MessageSquare, Plus, Star, CheckCircle2, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { useSession } from "@/context/SessionContext";
import { useQuality } from "@/hooks/useQuality";
import { useDataset } from "@/hooks/useDataset";
import { useQuery } from "@tanstack/react-query";
import { duplicateService } from "@/services/duplicateService";
import { aiAgentService } from "@/services/aiAgentService";
import { toast } from "sonner";



interface ChatMessage {
  sender: "user" | "agent";
  text: string;
}

export default function AgentPage() {
  useEffect(() => {
    document.title = "AI Agent — DataQ";
  }, []);
  const { sessionId, filename, rows, columns } = useSession();
  const navigate = useNavigate();
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sessionId) {
      navigate("/dashboard/upload");
    }
  }, [sessionId, navigate]);

  const { qualityQuery } = useQuality(sessionId);
  const { inspectQuery } = useDataset(sessionId);

  const duplicatesQuery = useQuery({
    queryKey: ["dataset", "duplicates", sessionId],
    queryFn: () => duplicateService.getDuplicates(),
    enabled: !!sessionId,
  });

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: "agent",
      text: "Hello! I am your DataQ Preprocessing Assistant. I have analyzed your dataset and I am ready to help you with data cleaning recommendations, feature scaling, encoding advice, or suggesting machine learning models. What would you like to know?",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || sending) return;

    const userText = input;
    setInput("");
    setMessages((prev) => [...prev, { sender: "user", text: userText }]);
    setSending(true);

    try {
      const chatRes = await aiAgentService.chatWithAgent(userText, false);
      if ("response" in chatRes) {
        setMessages((prev) => [...prev, { sender: "agent", text: chatRes.response }]);
      }
    } catch (err) {
      toast.error("AI response failed");
      setMessages((prev) => [
        ...prev,
        { sender: "agent", text: "Sorry, I encountered an error. Please try again." },
      ]);
    } finally {
      setSending(false);
    }
  };

  const startNewChat = () => {
    setMessages([
      {
        sender: "agent",
        text: "Sure! Let's start a fresh discussion about your dataset. How can I help you preprocess or model your features?",
      },
    ]);
  };

  const totalMissing = inspectQuery.data
    ? inspectQuery.data.columns.reduce((acc, col) => acc + col.missing, 0)
    : 0;
  const totalCells = inspectQuery.data
    ? inspectQuery.data.shape[0] * inspectQuery.data.shape[1]
    : 1;
  const missingPercent = totalCells > 0 ? (totalMissing / totalCells) * 100 : 0;

  return (
    <div>
      <PageHeader
        eyebrow="Intelligence"
        title="AI Agent"
        description="Talk to your dataset. Ask for analyses, fixes, pipelines or model recommendations."
      />

      <div className="grid lg:grid-cols-[300px_1fr] gap-6">
        {/* Sidebar */}
        <aside className="space-y-4">
          <button
            onClick={startNewChat}
            className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-brand px-4 py-2.5 text-sm font-semibold text-white shadow-[var(--glow-orange)] hover:scale-[1.01] transition"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>

          {/* Dataset Health summary */}
          <div className="glass-card rounded-2xl p-5 border-primary/30 shadow-[var(--glow-orange)]">
            <div className="text-[10px] uppercase tracking-widest text-primary mb-2 font-bold">
              Dataset Health
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-black text-gradient-brand">
                {qualityQuery.data?.score || 0}
              </span>
              <span className="text-muted-foreground">/100</span>
            </div>
            <div className="mt-4 space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-border/20">
                <span className="text-muted-foreground">Rows</span>
                <span className="font-mono">{(rows || 0).toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/20">
                <span className="text-muted-foreground">Columns</span>
                <span className="font-mono">{columns || 0}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/20">
                <span className="text-muted-foreground">Missing</span>
                <span className="font-mono">{missingPercent.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/20">
                <span className="text-muted-foreground">Duplicates</span>
                <span className="font-mono">{duplicatesQuery.data?.duplicate_rows ?? 0}</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Chat window */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card rounded-3xl flex flex-col h-[650px] overflow-hidden"
        >
          {/* Messages container */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((m, idx) => {
              const isAgent = m.sender === "agent";
              return (
                <div
                  key={idx}
                  className={`flex items-start gap-3 ${
                    isAgent ? "justify-start" : "justify-end"
                  }`}
                >
                  {isAgent && (
                    <div className="grid place-items-center w-8 h-8 rounded-full bg-gradient-brand text-white shadow-[var(--glow-orange)] shrink-0">
                      <Sparkles className="w-4.5 h-4.5" />
                    </div>
                  )}
                  <div
                    className={`rounded-2xl px-4 py-3 max-w-lg text-sm leading-relaxed whitespace-pre-wrap ${
                      isAgent
                        ? "border border-border/60 bg-card/60 backdrop-blur"
                        : "bg-gradient-brand text-white shadow-[var(--glow-orange)]"
                    }`}
                  >
                    {m.text}
                  </div>
                  {!isAgent && (
                    <div className="grid place-items-center w-8 h-8 rounded-full bg-secondary text-foreground shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}
            {sending && (
              <div className="flex items-start gap-3 justify-start">
                <div className="grid place-items-center w-8 h-8 rounded-full bg-gradient-brand text-white shadow-[var(--glow-orange)]">
                  <Sparkles className="w-4.5 h-4.5 animate-pulse" />
                </div>
                <div className="rounded-2xl px-4 py-3 bg-card/60 border border-border/60 text-sm flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="w-4 h-4 animate-spin text-primary" /> Preprocessing expert is typing...
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Form input */}
          <form onSubmit={handleSend} className="border-t border-border/60 p-4 bg-secondary/20">
            <div className="relative">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask DataQ to suggest models, explain anomalies or write cleaning code..."
                disabled={sending}
                className="w-full pl-4 pr-14 py-3 rounded-xl bg-secondary/80 border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none text-sm transition disabled:opacity-80"
              />
              <button
                type="submit"
                disabled={sending || !input.trim()}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 grid place-items-center w-8 h-8 rounded-lg bg-gradient-brand text-white shadow-[var(--glow-orange)] hover:scale-[1.02] active:scale-95 transition disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
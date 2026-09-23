import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type ReactNode,
} from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  ArrowUp,
  Clock3,
  MessageCircle,
  RotateCcw,
  Sparkles,
  WifiOff,
} from 'lucide-react';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import NotFound from '@/pages/not-found';
import {
  Route,
  Switch,
  useLocation,
  Router as WouterRouter,
} from 'wouter';

const queryClient = new QueryClient();

type Role = 'user' | 'assistant';

type ChatMessage = {
  id: string;
  role: Role;
  content: string;
  createdAt: number;
};

const starters = [
  'Tell me something gentle',
  'I had a long day',
  'What can you help with?',
];

function formatTime(timestamp: number) {
  return new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  }).format(timestamp);
}

function MiraAvatar({ small = false }: { small?: boolean }) {
  return (
    <div className={small ? 'mira-mini-mark' : 'mira-mark'} aria-hidden="true">
      <Sparkles size={small ? 15 : 18} strokeWidth={1.8} />
    </div>
  );
}

function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lastMessageRef = useRef('');

  useEffect(() => {
    const container = scrollRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, isSending, error]);

  const sendMessage = async (value: string) => {
    const message = value.trim();
    if (!message || isSending) return;

    setError(null);
    setDraft('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    lastMessageRef.current = message;

    const userMessage: ChatMessage = {
      id: `${Date.now()}-user`,
      role: 'user',
      content: message,
      createdAt: Date.now(),
    };
    const history = [...messages, userMessage].map(({ role, content }) => ({
      role,
      content,
    }));
    setMessages((current) => [...current, userMessage]);
    setIsSending(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history }),
      });

      if (!response.ok) {
        throw new Error('Aura could not respond right now.');
      }

      const data = (await response.json()) as { reply?: string };
      const reply = data.reply;
      if (!reply) throw new Error('Aura sent an empty reply.');

      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-assistant`,
          role: 'assistant',
          content: reply,
          createdAt: Date.now(),
        },
      ]);
    } catch {
      setError('Aura is taking a quiet moment. Try sending that again.');
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void sendMessage(draft);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void sendMessage(draft);
    }
  };

  const handleDraftChange = (value: string) => {
    setDraft(value);
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 128)}px`;
    }
  };

  const clearConversation = () => {
    if (isSending) return;
    setMessages([]);
    setError(null);
    setDraft('');
  };

  const retry = () => {
    if (lastMessageRef.current) void sendMessage(lastMessageRef.current);
  };

  return (
    <main className="mira-app">
      <div className="mira-shell">
        <aside className="mira-sidebar" aria-label="Aura introduction">
          <div className="mira-brand">
            <MiraAvatar />
            <div>
              <div className="mira-brand-name">aura</div>
              <p className="mira-brand-note">a little room to be human</p>
            </div>
          </div>

          <div className="mira-side-copy">
            <div className="mira-kicker">A soft place to land</div>
            <h1>Say what is on your mind.</h1>
            <p>
              Aura is here for the small thoughts, the curious questions, and
              the days that need a little untangling.
            </p>
            <div className="mira-side-footer">
              <span className="mira-online-dot" />
              <span>Here whenever you are</span>
            </div>
          </div>
        </aside>

        <section className="mira-chat-card" aria-label="Conversation with Aura">
          <header className="mira-chat-header">
            <div className="mira-chat-heading">
              <MiraAvatar small />
              <div>
                <h2>Aura</h2>
                <p><span className="mira-online-dot" />&nbsp; online and listening</p>
              </div>
            </div>
            <button
              type="button"
              className="mira-clear"
              onClick={clearConversation}
              disabled={isSending || messages.length === 0}
              data-testid="button-clear-conversation"
              aria-label="Start a fresh conversation"
            >
              <RotateCcw size={14} />
              <span>New chat</span>
            </button>
          </header>

          <div className="mira-messages" ref={scrollRef} data-testid="list-messages">
            {messages.length === 0 ? (
              <div className="mira-empty">
                <div className="mira-empty-orbit" aria-hidden="true">
                  <MessageCircle size={25} strokeWidth={1.5} />
                </div>
                <div className="mira-eyebrow">No pressure, no agenda</div>
                <h3>Hi, I am Aura.</h3>
                <p>
                  Start anywhere. A hello is plenty, or choose a thought to
                  ease into the room.
                </p>
                <div className="mira-starters" aria-label="Conversation starters">
                  {starters.map((starter) => (
                    <button
                      type="button"
                      className="mira-starter"
                      key={starter}
                      onClick={() => void sendMessage(starter)}
                      disabled={isSending}
                      data-testid={`button-starter-${starter.toLowerCase().replaceAll(' ', '-')}`}
                    >
                      {starter}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <article
                  className={`mira-message ${message.role === 'user' ? 'is-user' : ''}`}
                  key={message.id}
                  data-testid={`message-${message.role}-${message.id}`}
                >
                  <div className="mira-avatar" aria-hidden="true">
                    {message.role === 'assistant' ? <Sparkles size={14} /> : 'you'}
                  </div>
                  <div className="mira-message-body">
                    <div className="mira-bubble" data-testid={`text-message-${message.id}`}>
                      {message.content}
                    </div>
                    <time className="mira-time" dateTime={new Date(message.createdAt).toISOString()}>
                      {formatTime(message.createdAt)}
                    </time>
                  </div>
                </article>
              ))
            )}

            {isSending && (
              <div className="mira-message" data-testid="status-aura-thinking">
                <div className="mira-avatar" aria-hidden="true"><Sparkles size={14} /></div>
                <div className="mira-message-body">
                  <div className="mira-loading-bubble" aria-label="Aura is thinking">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="mira-error" role="alert" data-testid="status-chat-error">
              <WifiOff size={15} />
              <span>{error}</span>
              <button type="button" onClick={retry} data-testid="button-retry-message">
                Try again
              </button>
            </div>
          )}

          <div className="mira-composer-wrap">
            <form className="mira-composer" onSubmit={handleSubmit}>
              <textarea
                ref={textareaRef}
                value={draft}
                onChange={(event) => handleDraftChange(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Write something to Aura..."
                rows={1}
                aria-label="Message Aura"
                data-testid="input-message"
              />
              <button
                type="submit"
                className="mira-send"
                disabled={!draft.trim() || isSending}
                aria-label="Send message"
                data-testid="button-send-message"
              >
                <ArrowUp size={18} strokeWidth={2.2} />
              </button>
            </form>
            <div className="mira-hint">
              <Clock3 size={10} />&nbsp; enter to send&nbsp;&nbsp; · &nbsp;shift + enter for a new line
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function Router() {
  return (
    // Keep a shared shell (sidebar, navbar) outside the boundary so it
    // survives a page crash.
    <RoutedErrorBoundary>
      <Switch>
        <Route path="/" component={Home} />
        <Route component={NotFound} />
      </Switch>
    </RoutedErrorBoundary>
  );
}

function RoutedErrorBoundary({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  return <ErrorBoundary resetKey={location}>{children}</ErrorBoundary>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}>
          <Router />
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;

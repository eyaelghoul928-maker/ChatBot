import { useState, useRef, useEffect } from "react";

const BACKEND = "http://localhost:8000";

// ─── DESIGN SYSTEM ────────────────────────────────────────────────────────
const C = {
  bg:      "#07090f",
  panel:   "#0c1018",
  card:    "#111620",
  border:  "#1c2535",
  blue:    "#4f8ef7",
  cyan:    "#00d4ff",
  green:   "#00e896",
  yellow:  "#ffd166",
  orange:  "#ff8c42",
  red:     "#ff4d6d",
  purple:  "#c77dff",
  text:    "#e8edf5",
  dim:     "#6b7fa3",
  muted:   "#2d3a50",
};

const FONTS = `@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');`;

// ─── ATOMS ────────────────────────────────────────────────────────────────
function Dot({ color, size = 8, pulse }) {
  return (
    <span style={{
      display: "inline-block", width: size, height: size,
      borderRadius: "50%", background: color, flexShrink: 0,
      boxShadow: pulse ? `0 0 0 3px ${color}30` : "none",
      animation: pulse ? "dotpulse 2s infinite" : "none",
    }} />
  );
}

function Tag({ children, color = C.blue }) {
  return (
    <span style={{
      background: `${color}18`, border: `1px solid ${color}40`,
      color, fontSize: 10, fontWeight: 700, padding: "2px 8px",
      borderRadius: 99, letterSpacing: "0.5px", fontFamily: "JetBrains Mono, monospace",
      textTransform: "uppercase",
    }}>{children}</span>
  );
}

// ─── SQL BLOCK ────────────────────────────────────────────────────────────
function SqlBlock({ sql }) {
  const [show, setShow] = useState(false);
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div style={{ marginTop: 10 }}>
      <button onClick={() => setShow(!show)} style={{
        background: "none", border: "none", color: C.dim,
        fontSize: 11, cursor: "pointer", fontFamily: "inherit",
        display: "flex", alignItems: "center", gap: 5, padding: 0,
      }}>
        <span style={{ transform: show ? "rotate(90deg)" : "none", transition: "transform .2s" }}>▶</span>
        {show ? "Masquer" : "Voir"} le SQL généré
      </button>
      {show && (
        <div style={{
          background: "#060a12", border: `1px solid ${C.border}`,
          borderRadius: 8, padding: "10px 12px", marginTop: 6, position: "relative"
        }}>
          <button onClick={copy} style={{
            position: "absolute", top: 6, right: 6,
            background: copied ? `${C.green}20` : C.muted + "60",
            border: `1px solid ${copied ? C.green : C.muted}`,
            color: copied ? C.green : C.dim, borderRadius: 5,
            padding: "2px 8px", fontSize: 10, cursor: "pointer", fontFamily: "inherit",
          }}>{copied ? "✓" : "Copy"}</button>
          <pre style={{
            margin: 0, fontFamily: "JetBrains Mono, monospace",
            fontSize: 11, color: C.yellow, lineHeight: 1.7,
            whiteSpace: "pre-wrap", wordBreak: "break-all", paddingRight: 44,
          }}>{sql}</pre>
        </div>
      )}
    </div>
  );
}

// ─── DATA TABLE ───────────────────────────────────────────────────────────
function DataTable({ data }) {
  if (!data || data.length === 0) return null;
  const keys = Object.keys(data[0]);
  return (
    <div style={{ marginTop: 10, overflowX: "auto", borderRadius: 8, border: `1px solid ${C.border}` }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}>
        <thead>
          <tr style={{ background: C.muted + "60" }}>
            {keys.map(k => (
              <th key={k} style={{ padding: "6px 10px", color: C.cyan, fontWeight: 700, textAlign: "left", whiteSpace: "nowrap", borderBottom: `1px solid ${C.border}` }}>{k}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 5).map((row, i) => (
            <tr key={i} style={{ background: i % 2 === 0 ? "transparent" : C.muted + "20" }}>
              {keys.map(k => (
                <td key={k} style={{ padding: "5px 10px", color: C.text, borderBottom: `1px solid ${C.border}30`, whiteSpace: "nowrap" }}>
                  {row[k] === null ? <span style={{ color: C.muted }}>NULL</span> : String(row[k])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > 5 && (
        <div style={{ padding: "6px 10px", color: C.muted, fontSize: 11, background: C.muted + "20" }}>
          + {data.length - 5} autres lignes
        </div>
      )}
    </div>
  );
}

// ─── MESSAGE ──────────────────────────────────────────────────────────────
function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-end" : "flex-start", marginBottom: 16 }}>
      {!isUser && (
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
          <div style={{
            width: 26, height: 26, borderRadius: 8,
            background: `linear-gradient(135deg,${C.blue},${C.purple})`,
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13,
          }}>🤖</div>
          <span style={{ fontSize: 11, color: C.dim, fontFamily: "JetBrains Mono, monospace" }}>
            {msg.langue && <span style={{ color: C.cyan, marginRight: 6 }}>[{msg.langue?.toUpperCase()}]</span>}
            {msg.time}
            {msg.temps_ms && <span style={{ color: C.muted, marginLeft: 6 }}>{msg.temps_ms}ms</span>}
            {msg.cached && <span style={{ color: C.green, marginLeft: 6 }}>⚡ cache</span>}
          </span>
        </div>
      )}
      <div style={{
        maxWidth: "86%",
        background: isUser
          ? `linear-gradient(135deg,${C.blue}dd,${C.purple}cc)`
          : msg.error ? `${C.red}12` : C.card,
        border: isUser ? "none" : `1px solid ${msg.error ? C.red + "50" : C.border}`,
        borderRadius: isUser ? "16px 16px 4px 16px" : "4px 16px 16px 16px",
        padding: "12px 16px",
        color: C.text,
        fontSize: 14,
        lineHeight: 1.7,
        boxShadow: isUser ? `0 4px 20px ${C.blue}30` : "none",
      }}>
        <div style={{ whiteSpace: "pre-wrap" }}>{msg.text}</div>
        {msg.sql && <SqlBlock sql={msg.sql} />}
        {msg.rawData && msg.rawData.length > 0 && <DataTable data={msg.rawData} />}
        {msg.nb != null && (
          <div style={{ marginTop: 8, display: "flex", gap: 6, flexWrap: "wrap" }}>
            <Tag color={C.green}>📊 {msg.nb} résultat{msg.nb !== 1 ? "s" : ""}</Tag>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── TYPING INDICATOR ─────────────────────────────────────────────────────
function Typing() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 0" }}>
      <div style={{
        width: 26, height: 26, borderRadius: 8,
        background: `linear-gradient(135deg,${C.blue},${C.purple})`,
        display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13,
      }}>🤖</div>
      <div style={{
        background: C.card, border: `1px solid ${C.border}`,
        borderRadius: "4px 16px 16px 16px", padding: "12px 16px",
        display: "flex", gap: 5, alignItems: "center",
      }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{
            width: 7, height: 7, borderRadius: "50%", background: C.blue,
            animation: `bounce 1.2s ${i * 0.2}s infinite ease-in-out`,
          }} />
        ))}
        <span style={{ color: C.dim, fontSize: 12, marginLeft: 6 }}>Analyse en cours...</span>
      </div>
    </div>
  );
}

// ─── SIDEBAR ──────────────────────────────────────────────────────────────
function Sidebar({ connected, tables, onLogin, loginData, setLoginData, loginStatus }) {
  const [showLogin, setShowLogin] = useState(!connected);

  const SUGGESTIONS = [
    { icon: "📦", text: "Combien de colis livrés aujourd'hui ?", color: C.green },
    { icon: "🏆", text: "Top 5 livreurs ce mois", color: C.yellow },
    { icon: "📍", text: "Répartition des livraisons par ville", color: C.cyan },
    { icon: "⚠️", text: "Colis en retard depuis plus de 48h", color: C.orange },
    { icon: "💰", text: "Chiffre d'affaires total cette semaine", color: C.purple },
    { icon: "🔄", text: "Taux de retour par société", color: C.red },
    { icon: "📊", text: "Évolution des livraisons par mois", color: C.blue },
    { icon: "❌", text: "Principaux motifs d'échec de livraison", color: C.orange },
  ];

  return (
    <div style={{
      width: 280, flexShrink: 0, background: C.panel,
      borderRight: `1px solid ${C.border}`, display: "flex",
      flexDirection: "column", overflow: "hidden",
    }}>
      {/* Logo */}
      <div style={{ padding: "20px 20px 16px", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: `linear-gradient(135deg,${C.blue},${C.purple})`,
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
          }}>🤖</div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 15, fontFamily: "Syne, sans-serif", color: C.text }}>DataChat AI</div>
            <div style={{ fontSize: 10, color: C.dim, fontFamily: "JetBrains Mono, monospace" }}>Universal DB Chatbot</div>
          </div>
        </div>
      </div>

      {/* Status */}
      <div style={{ padding: "12px 16px", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <Dot color={connected ? C.green : C.red} pulse={connected} />
          <span style={{ fontSize: 12, color: connected ? C.green : C.red, fontWeight: 700 }}>
            {connected ? "Connecté" : "Non connecté"}
          </span>
        </div>
        {connected && tables.length > 0 && (
          <div style={{ fontSize: 11, color: C.dim }}>
            {tables.length} table{tables.length > 1 ? "s" : ""} détectée{tables.length > 1 ? "s" : ""}:
            <div style={{ marginTop: 4, display: "flex", flexWrap: "wrap", gap: 4 }}>
              {tables.map(t => <Tag key={t} color={C.cyan}>{t}</Tag>)}
            </div>
          </div>
        )}
      </div>

      {/* Login */}
      <div style={{ padding: "12px 16px", borderBottom: `1px solid ${C.border}` }}>
        <button onClick={() => setShowLogin(!showLogin)} style={{
          background: "none", border: "none", color: C.dim,
          fontSize: 11, cursor: "pointer", fontFamily: "inherit",
          display: "flex", alignItems: "center", gap: 5, padding: 0, marginBottom: showLogin ? 10 : 0,
        }}>
          🔑 {showLogin ? "▲" : "▼"} Connexion
        </button>
        {showLogin && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <input value={loginData.url} onChange={e => setLoginData(d => ({ ...d, url: e.target.value }))}
              style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", color: C.text, fontSize: 11, fontFamily: "JetBrains Mono, monospace" }} />
            <input value={loginData.email} onChange={e => setLoginData(d => ({ ...d, email: e.target.value }))}
              placeholder="Email" style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", color: C.text, fontSize: 11 }} />
            <input value={loginData.password} onChange={e => setLoginData(d => ({ ...d, password: e.target.value }))}
              type="password" placeholder="Mot de passe" style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", color: C.text, fontSize: 11 }} />
            <button onClick={onLogin} style={{
              background: `linear-gradient(135deg,${C.blue},${C.purple})`,
              border: "none", borderRadius: 8, padding: "8px", color: "#fff",
              fontWeight: 700, fontSize: 12, cursor: "pointer", fontFamily: "Syne, sans-serif",
            }}>Se connecter</button>
            {loginStatus && (
              <div style={{ fontSize: 11, color: loginStatus.startsWith("✅") ? C.green : C.red, textAlign: "center" }}>
                {loginStatus}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Suggestions */}
      <div style={{ flex: 1, overflow: "auto", padding: "12px 16px" }}>
        <div style={{ fontSize: 10, color: C.muted, fontWeight: 700, marginBottom: 8, letterSpacing: "1px", textTransform: "uppercase" }}>Questions suggérées</div>
        {SUGGESTIONS.map((s, i) => (
          <button key={i} onClick={() => window._setQuestion && window._setQuestion(s.text)} style={{
            width: "100%", background: "transparent", border: `1px solid ${C.border}`,
            borderRadius: 8, padding: "8px 10px", color: C.dim, textAlign: "left",
            fontSize: 12, cursor: "pointer", fontFamily: "inherit", marginBottom: 4,
            display: "flex", gap: 8, alignItems: "flex-start", transition: "all .15s",
          }}
            onMouseOver={e => { e.currentTarget.style.borderColor = s.color; e.currentTarget.style.color = s.color; e.currentTarget.style.background = s.color + "10"; }}
            onMouseOut={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.dim; e.currentTarget.style.background = "transparent"; }}>
            <span>{s.icon}</span>
            <span style={{ lineHeight: 1.5 }}>{s.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────
export default function App() {
  const [token, setToken] = useState("");
  const [connected, setConnected] = useState(false);
  const [tables, setTables] = useState([]);
  const [loginStatus, setLoginStatus] = useState("");
  const [loginData, setLoginData] = useState({
    url: BACKEND,
    email: "demo@chatbot.tn",
    password: "password123",
  });
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Bonjour ! 👋\n\nJe suis DataChat AI — un chatbot IA connecté à ta base MariaDB.\n\nConnecte-toi à gauche, puis pose-moi n'importe quelle question sur tes données en français, arabe ou anglais.\n\nJ'analyserai ta question, générerai le SQL adapté et te répondrai en langage naturel.",
      time: new Date().toLocaleTimeString(),
    }
  ]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  // Expose setQuestion globalement pour les suggestions
  window._setQuestion = setQuestion;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const serverUrl = loginData.url;

  const login = async () => {
    setLoginStatus("Connexion...");
    try {
      const r = await fetch(`${serverUrl}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: loginData.email, password: loginData.password }),
      });
      const d = await r.json();
      if (d.access_token) {
        setToken(d.access_token);
        setConnected(true);
        setLoginStatus("✅ Connecté !");

        // Récupérer les tables détectées
        try {
          const sh = await fetch(`${serverUrl}/schema`, {
            headers: { "Authorization": `Bearer ${d.access_token}` }
          });
          const sd = await sh.json();
          const matches = (sd.schema || "").match(/^TABLE (\w+)/gm) || [];
          setTables(matches.map(m => m.replace("TABLE ", "")));
        } catch (_) {}

        setMessages(m => [...m, {
          role: "bot",
          text: `✅ Connecté avec succès !\n\nJe suis maintenant connecté à la base "${serverUrl.replace("http://", "")}" et j'ai analysé son schéma automatiquement.\n\nPose-moi ta première question !`,
          time: new Date().toLocaleTimeString(),
        }]);
      } else {
        setLoginStatus("❌ " + (d.detail || "Erreur"));
      }
    } catch {
      setLoginStatus("❌ Serveur inaccessible");
    }
  };

  const ask = async () => {
    if (!question.trim() || loading || !token) return;
    const q = question.trim();
    setQuestion("");
    setMessages(m => [...m, { role: "user", text: q, time: new Date().toLocaleTimeString() }]);
    setLoading(true);

    try {
      const r = await fetch(`${serverUrl}/api/chat/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ question: q }),
      });
      const d = await r.json();

      if (r.ok) {
        setMessages(m => [...m, {
          role: "bot",
          text: d.reponse,
          sql: d.sql,
          nb: d.nb_resultats,
          cached: d.cached,
          temps_ms: d.temps_ms,
          langue: d.langue,
          time: new Date().toLocaleTimeString(),
        }]);
      } else {
        setMessages(m => [...m, {
          role: "bot",
          text: `❌ Erreur: ${d.detail || r.status}`,
          error: true,
          time: new Date().toLocaleTimeString(),
        }]);
      }
    } catch {
      setMessages(m => [...m, {
        role: "bot",
        text: "❌ Impossible de contacter le backend. Vérifie que les 2 serveurs tournent.",
        error: true,
        time: new Date().toLocaleTimeString(),
      }]);
    }
    setLoading(false);
  };

  return (
    <>
      <style>{`
        ${FONTS}
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${C.bg}; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${C.muted}; border-radius: 99px; }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
        @keyframes dotpulse {
          0%, 100% { box-shadow: 0 0 0 3px transparent; }
          50% { box-shadow: 0 0 0 5px ${C.green}30; }
        }
        @keyframes fadein {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        input:focus { outline: none; border-color: ${C.blue} !important; }
        textarea:focus { outline: none; }
      `}</style>

      <div style={{ display: "flex", height: "100vh", fontFamily: "Syne, sans-serif", color: C.text, background: C.bg }}>

        {/* Sidebar */}
        <Sidebar
          connected={connected} tables={tables}
          onLogin={login} loginData={loginData}
          setLoginData={setLoginData} loginStatus={loginStatus}
        />

        {/* Main */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

          {/* Header */}
          <div style={{
            background: C.panel, borderBottom: `1px solid ${C.border}`,
            padding: "14px 24px", display: "flex", alignItems: "center",
            justifyContent: "space-between",
          }}>
            <div>
              <div style={{ fontWeight: 800, fontSize: 16, fontFamily: "Syne, sans-serif" }}>
                DataChat AI
                <span style={{ marginLeft: 10, fontSize: 11, color: C.dim, fontWeight: 400, fontFamily: "JetBrains Mono, monospace" }}>
                  {connected ? `· ${serverUrl}` : "· Non connecté"}
                </span>
              </div>
              <div style={{ fontSize: 11, color: C.dim, marginTop: 2 }}>
                Pipeline: NLP → SQL → MariaDB → NLG · 3 appels GPT-4o
              </div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <Tag color={connected ? C.green : C.muted}>{connected ? "● LIVE" : "○ OFFLINE"}</Tag>
              {connected && <Tag color={C.purple}>GPT-4o</Tag>}
            </div>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: "auto", padding: "24px 28px" }}>
            <div style={{ maxWidth: 780, margin: "0 auto" }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ animation: "fadein .3s ease" }}>
                  <Message msg={msg} />
                </div>
              ))}
              {loading && <Typing />}
              <div ref={bottomRef} />
            </div>
          </div>

          {/* Input */}
          <div style={{ background: C.panel, borderTop: `1px solid ${C.border}`, padding: "16px 28px" }}>
            <div style={{ maxWidth: 780, margin: "0 auto" }}>
              {!connected && (
                <div style={{
                  background: `${C.orange}12`, border: `1px solid ${C.orange}30`,
                  borderRadius: 10, padding: "10px 14px", marginBottom: 12,
                  fontSize: 13, color: C.orange, display: "flex", alignItems: "center", gap: 8,
                }}>
                  ⚠️ Connecte-toi dans le panneau de gauche pour commencer
                </div>
              )}
              <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
                <div style={{ flex: 1, position: "relative" }}>
                  <textarea
                    value={question}
                    onChange={e => setQuestion(e.target.value)}
                    onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); } }}
                    placeholder={connected ? "Pose ta question en français, arabe ou anglais... (Entrée pour envoyer)" : "Connecte-toi d'abord →"}
                    disabled={!connected || loading}
                    rows={1}
                    style={{
                      width: "100%", background: C.card,
                      border: `1px solid ${connected ? C.blue + "60" : C.border}`,
                      borderRadius: 12, padding: "12px 16px", color: C.text,
                      fontSize: 14, fontFamily: "Syne, sans-serif", resize: "none",
                      lineHeight: 1.5, transition: "border .2s",
                      opacity: connected ? 1 : 0.5,
                    }}
                  />
                </div>
                <button
                  onClick={ask}
                  disabled={!connected || !question.trim() || loading}
                  style={{
                    width: 46, height: 46, borderRadius: 12, border: "none",
                    background: connected && question.trim()
                      ? `linear-gradient(135deg,${C.blue},${C.purple})`
                      : C.muted + "60",
                    color: "#fff", fontSize: 20, cursor: connected ? "pointer" : "not-allowed",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0, transition: "all .2s",
                    opacity: (!connected || !question.trim()) ? 0.5 : 1,
                    boxShadow: connected && question.trim() ? `0 4px 15px ${C.blue}40` : "none",
                  }}
                >
                  {loading ? "⏳" : "↑"}
                </button>
              </div>
              <div style={{ fontSize: 11, color: C.muted, marginTop: 8, textAlign: "center" }}>
                Shift+Entrée pour nouvelle ligne · Entrée pour envoyer · Questions en FR / AR / EN supportées
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

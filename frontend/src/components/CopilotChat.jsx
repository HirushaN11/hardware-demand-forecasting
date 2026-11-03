import React, { useRef, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function CopilotChat({
  chatMessages = [],
  chatInput = '',
  setChatInput,
  chatLoading = false,
  onSendMessage,
  items = [],
  reorderUrgentCount = 0,
  totalSpendLkr = 0,
  leadTimeWeeks = 2
}) {
  const chatBottomRef = useRef(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, chatLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;
    onSendMessage(chatInput);
  };

  const suggestedPresets = [
    "I only have LKR 50,000 to spend this week. Which items should I order first?",
    "Compare the top 4 urgent restock items by their required capital outlay.",
    "Which electrical items are at critical risk of stocking out during lead time?",
    "Compare reorder quantities needed across hardware categories."
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '24px', height: 'calc(100vh - 140px)' }}>

      {/* Left: Interactive Chat Window */}
      <div style={{ backgroundColor: '#FFFFFF', borderRadius: '8px', border: '1px solid #E2E8F0', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>

        {/* Chat Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #E2E8F0', backgroundColor: '#F8FAFC', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 'bold', color: '#0F172A', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🤖</span> AI Supply Chain Copilot
            </h2>
            <div style={{ fontSize: '12px', color: '#64748B', marginTop: '2px' }}>
              Multi-modal visual reasoning over 30 SKUs & 4-week forecasts
            </div>
          </div>
          <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '12px', backgroundColor: '#DCFCE7', color: '#166534', fontWeight: 'bold' }}>
            Live Visual Generation
          </span>
        </div>

        {/* Message History */}
        <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', backgroundColor: '#F8FAFC' }}>
          {chatMessages.map((msg, idx) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: isUser ? 'flex-end' : 'flex-start'
                }}
              >
                <div style={{
                  maxWidth: '85%',
                  padding: '14px 18px',
                  borderRadius: '12px',
                  fontSize: '13px',
                  lineHeight: '1.6',
                  whiteSpace: 'pre-line',
                  backgroundColor: isUser ? '#0284C7' : '#FFFFFF',
                  color: isUser ? '#FFFFFF' : '#1E293B',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                  border: isUser ? 'none' : '1px solid #E2E8F0'
                }}>
                  {/* Text explanation */}
                  <div>{msg.text}</div>

                  {/* Inline Chart with Priority Rationale */}
                  {msg.chart && msg.chart.labels && msg.chart.labels.length > 0 && (
                    <div style={{
                      marginTop: '14px',
                      paddingTop: '12px',
                      borderTop: '1px solid #E2E8F0',
                      backgroundColor: '#F8FAFC',
                      padding: '14px',
                      borderRadius: '8px'
                    }}>
                      <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#0F172A', marginBottom: '8px' }}>
                        📊 {msg.chart.title || 'Copilot Visual Breakdown'}
                      </div>

                      <div style={{ height: '170px' }}>
                        <Bar
                          data={{
                            labels: msg.chart.labels,
                            datasets: [{
                              label: msg.chart.title || 'Amount',
                              data: msg.chart.values,
                              backgroundColor: '#0284C7',
                              borderRadius: 4
                            }]
                          }}
                          options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                              y: {
                                beginAtZero: true,
                                ticks: { font: { size: 10 } }
                              },
                              x: {
                                ticks: { font: { size: 10 } }
                              }
                            }
                          }}
                        />
                      </div>

                      {/* Why this item is prioritized first */}
                      <div style={{
                        marginTop: '12px',
                        padding: '10px 14px',
                        backgroundColor: '#FFFFFF',
                        borderLeft: '4px solid #0284C7',
                        borderRadius: '4px',
                        fontSize: '12px',
                        lineHeight: '1.5',
                        color: '#334155'
                      }}>
                        <span style={{ fontWeight: 'bold', color: '#0F172A' }}>💡 Priority Rationale: </span>
                        {msg.chart.explanation ||
                          `${msg.chart.labels[0]} must be ordered first because on-hand stock has dropped critically below the safety buffer during the 2-week supplier lead window.`}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {chatLoading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{ padding: '12px 18px', borderRadius: '12px', backgroundColor: '#FFFFFF', color: '#64748B', fontSize: '13px', border: '1px solid #E2E8F0', fontStyle: 'italic' }}>
                Synthesizing strategic reasoning and generating visual chart data...
              </div>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Chat Input */}
        <div style={{ padding: '16px 20px', borderTop: '1px solid #E2E8F0', backgroundColor: '#FFFFFF' }}>
          <form
            onSubmit={handleSubmit}
            style={{ display: 'flex', gap: '10px' }}
          >
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask about budget allocations, stockout risk comparisons, or supplier priorities..."
              style={{
                flex: 1,
                padding: '12px 16px',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '13px',
                outline: 'none'
              }}
            />
            <button
              type="submit"
              disabled={chatLoading || !chatInput.trim()}
              style={{
                backgroundColor: '#0F172A',
                color: '#FFFFFF',
                padding: '0 24px',
                borderRadius: '8px',
                border: 'none',
                fontSize: '13px',
                fontWeight: 'bold',
                cursor: chatLoading || !chatInput.trim() ? 'not-allowed' : 'pointer',
                opacity: chatLoading || !chatInput.trim() ? 0.6 : 1,
                transition: 'opacity 0.2s'
              }}
            >
              Send Query
            </button>
          </form>
        </div>

      </div>

      {/* Right: Suggested Prompts & Store Snapshot */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

        {/* Quick Prompt Suggestions */}
        <div style={{ backgroundColor: '#FFFFFF', borderRadius: '8px', border: '1px solid #E2E8F0', padding: '18px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 'bold', color: '#0F172A', margin: '0 0 12px 0' }}>
            💡 Suggested Inquiries
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {suggestedPresets.map((preset, pIdx) => (
              <button
                key={pIdx}
                onClick={() => onSendMessage(preset)}
                style={{
                  textAlign: 'left',
                  padding: '10px 12px',
                  backgroundColor: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  borderRadius: '6px',
                  fontSize: '12px',
                  color: '#334155',
                  cursor: 'pointer',
                  lineHeight: '1.4',
                  transition: 'all 0.15s'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#F1F5F9'}
                onMouseLeave={(e) => e.target.style.backgroundColor = '#F8FAFC'}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* Copilot Grounding Stats */}
        <div style={{ backgroundColor: '#FFFFFF', borderRadius: '8px', border: '1px solid #E2E8F0', padding: '18px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 'bold', color: '#0F172A', margin: '0 0 10px 0' }}>
            📊 In-Memory Store Knowledge
          </h3>
          <div style={{ fontSize: '12px', color: '#64748B', lineHeight: '1.8' }}>
            <div>• Monitored SKUs: <strong>{items.length} Products</strong></div>
            <div>• Critical Stockouts: <strong>{reorderUrgentCount} Items</strong></div>
            <div>• Total Store Capital Needed: <strong>LKR {(totalSpendLkr ?? 0).toLocaleString()}</strong></div>
            <div>• Supplier Lead Time: <strong>{leadTimeWeeks} Weeks</strong></div>
          </div>
        </div>

      </div>

    </div>
  );
}


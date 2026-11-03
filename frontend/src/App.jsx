import React, { useState, useEffect } from 'react';
import axios from 'axios';

import Header from './components/Header';
import MetricsSummary from './components/MetricsSummary';
import InventoryTable from './components/InventoryTable';
import CopilotChat from './components/CopilotChat';
import ClearanceAdvisory from './components/ClearanceAdvisory';

const API_BASE = 'http://127.0.0.1:8000/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('DASHBOARD'); // 'DASHBOARD' | 'COPILOT' | 'RECOMMENDATIONS'
  const [items, setItems] = useState([]);
  const [selectedSku, setSelectedSku] = useState(null);
  const [loading, setLoading] = useState(true);

  // Single SKU AI Advisor States
  const [advisoryText, setAdvisoryText] = useState('');
  const [advisoryLoading, setAdvisoryLoading] = useState(false);

  // Multi-Turn Copilot Chat States
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'assistant',
      text: "Hello! I am your AI Supply Chain Copilot. I have analyzed all 30 SKUs across your electrical, plumbing, and building materials inventory. You can ask me to prioritize orders, compare costs, or recommend budget distributions, and I will generate live visual breakdowns for you.",
      chart: null
    }
  ]);

  // Load Inventory Data
  useEffect(() => {
    axios.get(`${API_BASE}/inventory/recommendations`)
      .then((res) => {
        setItems(res.data);
        if (res.data.length > 0) setSelectedSku(res.data[0].sku_id);
      })
      .catch((err) => console.error("Error loading recommendations:", err))
      .finally(() => setLoading(false));
  }, []);

  const handleSelectSku = (skuId) => {
    setSelectedSku(skuId);
    setAdvisoryText('');
  };

  const selectedItem = items.find((x) => x.sku_id === selectedSku) || items[0];
  const reorderUrgentCount = items.filter((x) => x.reorder_status === 'ORDER NOW').length;
  const totalSpendLkr = items.reduce((acc, x) => acc + (x.capital_outlay_lkr || 0), 0);

  // SKU Advisor API Handler
  const handleGenerateAdvisory = () => {
    if (!selectedItem) return;
    setAdvisoryLoading(true);
    axios.post(`${API_BASE}/advisor/generate`, {
      sku_data: selectedItem,
      api_key: ""
    })
      .then((res) => setAdvisoryText(res.data.advice || res.data.brief || "Advisory generated."))
      .catch((err) => {
        console.error("Advisor error:", err);
        setAdvisoryText("Unable to generate advisory briefing at this time. Please ensure the backend is running.");
      })
      .finally(() => setAdvisoryLoading(false));
  };

  // Strategic Store Copilot Chat Handler
  const handleSendMessage = (messageToSend) => {
    const query = messageToSend || chatInput;
    if (!query.trim() || chatLoading) return;

    const userMsg = { sender: 'user', text: query, chart: null };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);

    axios.post(`${API_BASE}/advisor/chat`, {
      query: query,
      api_key: ""
    })
      .then((res) => {
        setChatMessages((prev) => [
          ...prev,
          {
            sender: 'assistant',
            text: res.data.text || res.data.reply || "Analysis completed.",
            chart: res.data.chart || null
          }
        ]);
      })
      .catch((err) => {
        console.error("Chat error:", err);
        setChatMessages((prev) => [
          ...prev,
          {
            sender: 'assistant',
            text: "Service notice: Unable to contact the reasoning engine. Please ensure your backend is running.",
            chart: null
          }
        ]);
      })
      .finally(() => setChatLoading(false));
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontFamily: 'Segoe UI, sans-serif' }}>
        <h2>Loading Retail Forecasting & Reorder System...</h2>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: 'Segoe UI, -apple-system, sans-serif', backgroundColor: '#F8FAFC', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>

      {/* 1. Global Navigation Header */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main style={{ padding: '24px 28px', flex: 1, maxWidth: '1440px', width: '100%', margin: '0 auto', boxSizing: 'border-box' }}>

        {/* VIEW 1: Operational Reorder Dashboard */}
        {activeTab === 'DASHBOARD' && (
          <div>
            <MetricsSummary
              reorderUrgentCount={reorderUrgentCount}
              totalItems={items.length}
              totalSpendLkr={totalSpendLkr}
              leadTimeWeeks={2}
            />

            <InventoryTable
              items={items}
              selectedSku={selectedSku}
              onSelectSku={handleSelectSku}
              selectedItem={selectedItem}
              advisoryText={advisoryText}
              advisoryLoading={advisoryLoading}
              onGenerateAdvisory={handleGenerateAdvisory}
              onExploreClearance={() => setActiveTab('RECOMMENDATIONS')}
            />
          </div>
        )}

        {/* VIEW 2: Multi-SKU AI Supply Chain Copilot with Dynamic Charts */}
        {activeTab === 'COPILOT' && (
          <CopilotChat
            chatMessages={chatMessages}
            chatInput={chatInput}
            setChatInput={setChatInput}
            chatLoading={chatLoading}
            onSendMessage={handleSendMessage}
            items={items}
            reorderUrgentCount={reorderUrgentCount}
            totalSpendLkr={totalSpendLkr}
            leadTimeWeeks={2}
          />
        )}

        {/* VIEW 3: Smart Merchandising & Clearance Advisory */}
        {activeTab === 'RECOMMENDATIONS' && (
          <ClearanceAdvisory onBackToDashboard={() => setActiveTab('DASHBOARD')} />
        )}

      </main>
    </div>
  );
}

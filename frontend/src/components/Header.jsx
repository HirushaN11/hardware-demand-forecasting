import React from 'react';

export default function Header({ activeTab, setActiveTab }) {
  return (
    <header
      style={{
        backgroundColor: '#0F172A',
        color: '#FFFFFF',
        padding: '16px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}
    >
      <div>
        <div style={{ fontSize: '18px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>📦</span> Sri Lanka Hardware Demand Forecasting & Inventory DSS
        </div>
        <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
          LightGBM Tweedie Engine • (s, S) Reorder Policies • Multi-SKU AI Supply Chain Copilot
        </div>
      </div>

      {/* Tab Switcher */}
      <div style={{ display: 'flex', gap: '8px', backgroundColor: '#1E293B', padding: '4px', borderRadius: '8px' }}>
        <button
          onClick={() => setActiveTab('DASHBOARD')}
          style={{
            padding: '8px 18px',
            borderRadius: '6px',
            border: 'none',
            fontSize: '13px',
            fontWeight: '600',
            cursor: 'pointer',
            backgroundColor: activeTab === 'DASHBOARD' ? '#0284C7' : 'transparent',
            color: '#FFFFFF',
            transition: 'all 0.2s'
          }}
        >
          📊 Operational Dashboard
        </button>
        <button
          onClick={() => setActiveTab('COPILOT')}
          style={{
            padding: '8px 18px',
            borderRadius: '6px',
            border: 'none',
            fontSize: '13px',
            fontWeight: '600',
            cursor: 'pointer',
            backgroundColor: activeTab === 'COPILOT' ? '#0284C7' : 'transparent',
            color: '#FFFFFF',
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <span>💬</span> AI Supply Chain Copilot
        </button>
        <button
          onClick={() => setActiveTab('RECOMMENDATIONS')}
          style={{
            padding: '8px 18px',
            borderRadius: '6px',
            border: 'none',
            fontSize: '13px',
            fontWeight: '600',
            cursor: 'pointer',
            backgroundColor: activeTab === 'RECOMMENDATIONS' ? '#0284C7' : 'transparent',
            color: '#FFFFFF',
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <span>🏷️</span> Clearance & Merchandising
        </button>
      </div>
    </header>
  );
}


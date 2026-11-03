import React from 'react';

export default function MetricsSummary({
  reorderUrgentCount = 0,
  totalItems = 0,
  totalSpendLkr = 0,
  leadTimeWeeks = 2
}) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '20px' }}>
      <div style={{ backgroundColor: '#FFFFFF', padding: '18px', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
        <div style={{ fontSize: '12px', color: '#64748B', fontWeight: '600' }}>PRODUCTS NEEDING IMMEDIATE ORDER</div>
        <div style={{ fontSize: '28px', fontWeight: 'bold', color: reorderUrgentCount > 0 ? '#DC2626' : '#16A34A', marginTop: '4px' }}>
          {reorderUrgentCount} <span style={{ fontSize: '14px', fontWeight: 'normal', color: '#64748B' }}>/ {totalItems} Total SKUs</span>
        </div>
      </div>

      <div style={{ backgroundColor: '#FFFFFF', padding: '18px', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
        <div style={{ fontSize: '12px', color: '#64748B', fontWeight: '600' }}>TOTAL REORDER BUDGET NEEDED</div>
        <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#0F172A', marginTop: '4px' }}>
          LKR {(totalSpendLkr ?? 0).toLocaleString()}
        </div>
      </div>

      <div style={{ backgroundColor: '#FFFFFF', padding: '18px', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
        <div style={{ fontSize: '12px', color: '#64748B', fontWeight: '600' }}>SUPPLIER LEAD TIME BUFFER</div>
        <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#0284C7', marginTop: '4px' }}>
          {leadTimeWeeks} Weeks <span style={{ fontSize: '14px', fontWeight: 'normal', color: '#64748B' }}>Safety Stock Factored</span>
        </div>
      </div>
    </div>
  );
}


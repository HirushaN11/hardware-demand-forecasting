import React, { useState, useMemo } from 'react';
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

export default function InventoryTable({
  items = [],
  selectedSku,
  onSelectSku,
  selectedItem,
  advisoryText,
  advisoryLoading,
  onGenerateAdvisory,
  onExploreClearance
}) {
  const [filterCategory, setFilterCategory] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('URGENT_FIRST');
  const [pageSize, setPageSize] = useState(10); // 10, 15, or 30 (all)
  const [currentPage, setCurrentPage] = useState(1);

  // Filter & Search Logic
  const filteredAndSortedItems = useMemo(() => {
    let result = items.filter((x) => {
      const matchesCategory =
        filterCategory === 'ALL' ||
        (x.category || '').toUpperCase() === filterCategory.toUpperCase();
      const matchesSearch =
        !searchTerm.trim() ||
        (x.sku_id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (x.product_name || '').toLowerCase().includes(searchTerm.toLowerCase());
      return matchesCategory && matchesSearch;
    });

    // Sorting
    result = [...result].sort((a, b) => {
      if (sortBy === 'URGENT_FIRST') {
        const aUrgent = a.reorder_status === 'ORDER NOW' ? 1 : 0;
        const bUrgent = b.reorder_status === 'ORDER NOW' ? 1 : 0;
        if (bUrgent !== aUrgent) return bUrgent - aUrgent;
        return (b.capital_outlay_lkr || 0) - (a.capital_outlay_lkr || 0);
      }
      if (sortBy === 'STOCK_LOW') {
        return (a.current_stock || 0) - (b.current_stock || 0);
      }
      if (sortBy === 'DEMAND_HIGH') {
        return (b.forecast_4w_total || 0) - (a.forecast_4w_total || 0);
      }
      if (sortBy === 'NAME') {
        return (a.product_name || '').localeCompare(b.product_name || '');
      }
      return 0;
    });

    return result;
  }, [items, filterCategory, searchTerm, sortBy]);

  // Pagination calculation
  const totalPages = Math.ceil(filteredAndSortedItems.length / pageSize) || 1;
  const validPage = Math.min(currentPage, totalPages);
  const startIndex = (validPage - 1) * pageSize;
  const paginatedItems = filteredAndSortedItems.slice(startIndex, startIndex + pageSize);

  // Forward 4-Week Bar Chart Data for selected item
  const forecastBarData = {
    labels: ['Next Week (W1)', 'Week 2 (W2)', 'Week 3 (W3)', 'Week 4 (W4)'],
    datasets: [
      {
        label: 'Predicted Sales Demand (Units)',
        data: selectedItem ? [
          selectedItem.forecast_w1 || 0,
          selectedItem.forecast_w2 || 0,
          selectedItem.forecast_w3 || 0,
          selectedItem.forecast_w4 || 0
        ] : [0, 0, 0, 0],
        backgroundColor: '#0284C7',
        borderRadius: 6
      }
    ]
  };

  return (
    <div>
      {/* Quick Action Link to Clearance Strategies */}
      {onExploreClearance && (
        <div style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '8px',
          padding: '14px 20px',
          marginBottom: '20px',
          border: '1px solid #E2E8F0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              fontSize: '20px',
              backgroundColor: '#FEF3C7',
              padding: '8px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              🏷️
            </div>
            <div>
              <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#0F172A' }}>
                Slow-Moving Inventory & Capital Liquidation Strategies
              </div>
              <div style={{ fontSize: '12px', color: '#64748B', marginTop: '2px' }}>
                View AI-generated bundle pairs and promotional clearance markdowns to unblock idle capital.
              </div>
            </div>
          </div>
          <button
            onClick={onExploreClearance}
            style={{
              backgroundColor: '#0F172A',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '6px',
              padding: '9px 16px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#1E293B'}
            onMouseLeave={(e) => e.target.style.backgroundColor = '#0F172A'}
          >
            <span>Explore Clearance Strategies</span>
            <span>→</span>
          </button>
        </div>
      )}

      {/* Split View: Left Catalog + Right Operations */}
      <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '20px' }}>

        {/* Left Column: Filterable & Searchable Catalog List */}
        <div style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '8px',
          border: '1px solid #E2E8F0',
          padding: '16px',
          maxHeight: '820px',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {/* Header & Category Selection */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: 'bold', color: '#0F172A', margin: 0 }}>
              Inventory Catalog ({filteredAndSortedItems.length})
            </h2>
            <select
              value={filterCategory}
              onChange={(e) => {
                setFilterCategory(e.target.value);
                setCurrentPage(1);
              }}
              style={{
                padding: '4px 8px',
                borderRadius: '4px',
                border: '1px solid #CBD5E1',
                fontSize: '12px',
                outline: 'none',
                backgroundColor: '#FFFFFF',
                color: '#334155'
              }}
            >
              <option value="ALL">All Categories</option>
              <option value="Electrical">Electrical</option>
              <option value="Plumbing">Plumbing</option>
              <option value="Fasteners">Fasteners</option>
              <option value="Building Materials">Building Materials</option>
            </select>
          </div>

          {/* Search Input & Sort Controls */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search SKU or name..."
              style={{
                flex: 1,
                padding: '6px 10px',
                borderRadius: '6px',
                border: '1px solid #CBD5E1',
                fontSize: '12px',
                outline: 'none'
              }}
            />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{
                padding: '6px 8px',
                borderRadius: '6px',
                border: '1px solid #CBD5E1',
                fontSize: '12px',
                outline: 'none',
                backgroundColor: '#FFFFFF',
                color: '#334155'
              }}
            >
              <option value="URGENT_FIRST">🚨 Order First</option>
              <option value="STOCK_LOW">📉 Lowest Stock</option>
              <option value="DEMAND_HIGH">📈 High Demand</option>
              <option value="NAME">🔤 Name (A-Z)</option>
            </select>
          </div>

          {/* Scrollable SKU List */}
          <div style={{ overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {paginatedItems.map((item) => {
              const isSelected = item.sku_id === selectedSku;
              const isUrgent = item.reorder_status === 'ORDER NOW';

              return (
                <div
                  key={item.sku_id}
                  onClick={() => onSelectSku(item.sku_id)}
                  style={{
                    padding: '12px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    backgroundColor: isSelected ? '#F0F9FF' : '#FFFFFF',
                    border: isSelected ? '1.5px solid #0284C7' : '1px solid #E2E8F0',
                    transition: 'all 0.15s'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#0F172A' }}>{item.sku_id}</span>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 'bold',
                      backgroundColor: isUrgent ? '#FEE2E2' : '#DCFCE7',
                      color: isUrgent ? '#DC2626' : '#166534'
                    }}>
                      {item.reorder_status}
                    </span>
                  </div>

                  <div style={{ fontSize: '13px', color: '#334155', marginTop: '4px', fontWeight: '500' }}>
                    {item.product_name}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '11px', color: '#64748B' }}>
                    <span>Stock: <strong>{item.current_stock}</strong></span>
                    <span>Reorder Pt: <strong>{item.reorder_point}</strong></span>
                    <span>4-Wk Exp: <strong>{item.forecast_4w_total}</strong></span>
                  </div>
                </div>
              );
            })}

            {paginatedItems.length === 0 && (
              <div style={{ padding: '24px 12px', textAlign: 'center', color: '#94A3B8', fontSize: '13px' }}>
                No items match your search/filter criteria.
              </div>
            )}
          </div>

          {/* Pagination Controls */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingTop: '10px',
            marginTop: '8px',
            borderTop: '1px solid #E2E8F0',
            fontSize: '12px',
            color: '#64748B'
          }}>
            <div>
              <span>Page {validPage} of {totalPages}</span>
              <span style={{ marginLeft: '8px' }}>
                Show:
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  style={{ marginLeft: '4px', padding: '2px 4px', border: '1px solid #CBD5E1', borderRadius: '4px', fontSize: '11px' }}
                >
                  <option value={10}>10</option>
                  <option value={15}>15</option>
                  <option value={30}>All 30</option>
                </select>
              </span>
            </div>

            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={validPage <= 1}
                style={{
                  padding: '3px 8px',
                  borderRadius: '4px',
                  border: '1px solid #CBD5E1',
                  backgroundColor: validPage <= 1 ? '#F1F5F9' : '#FFFFFF',
                  color: validPage <= 1 ? '#94A3B8' : '#334155',
                  cursor: validPage <= 1 ? 'not-allowed' : 'pointer'
                }}
              >
                Prev
              </button>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={validPage >= totalPages}
                style={{
                  padding: '3px 8px',
                  borderRadius: '4px',
                  border: '1px solid #CBD5E1',
                  backgroundColor: validPage >= totalPages ? '#F1F5F9' : '#FFFFFF',
                  color: validPage >= totalPages ? '#94A3B8' : '#334155',
                  cursor: validPage >= totalPages ? 'not-allowed' : 'pointer'
                }}
              >
                Next
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Selected SKU Operational Decision & Forecasts */}
        {selectedItem && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

            {/* Urgent Decision Box */}
            <div style={{
              backgroundColor: selectedItem.reorder_status === 'ORDER NOW' ? '#FEF2F2' : '#F0FDF4',
              border: selectedItem.reorder_status === 'ORDER NOW' ? '1.5px solid #F87171' : '1.5px solid #86EFAC',
              borderRadius: '8px',
              padding: '20px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 'bold',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    backgroundColor: selectedItem.reorder_status === 'ORDER NOW' ? '#EF4444' : '#22C55E',
                    color: '#FFFFFF'
                  }}>
                    {selectedItem.reorder_status === 'ORDER NOW' ? 'CRITICAL REORDER REQUIRED' : 'STOCK LEVEL SUFFICIENT'}
                  </span>
                  <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#0F172A', margin: '8px 0 2px 0' }}>
                    {selectedItem.product_name} ({selectedItem.sku_id})
                  </h2>
                  <div style={{ fontSize: '13px', color: '#475569' }}>
                    Category: {selectedItem.category} | Cost: LKR {(selectedItem.unit_cost_lkr ?? 0).toLocaleString()} | Price: LKR {(selectedItem.selling_price_lkr ?? 0).toLocaleString()}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Recommended Purchase Order</div>
                  <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#0F172A' }}>
                    {selectedItem.suggested_order_units} <span style={{ fontSize: '14px', fontWeight: 'normal' }}>Units</span>
                  </div>
                  <div style={{ fontSize: '13px', color: '#0284C7', fontWeight: '600' }}>
                    Invoice: LKR {(selectedItem.capital_outlay_lkr ?? 0).toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Exact Stock Math */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(0,0,0,0.08)' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#64748B' }}>Physical On-Hand</div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#0F172A' }}>{selectedItem.current_stock} units</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#64748B' }}>Reorder Threshold (s)</div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#0F172A' }}>{selectedItem.reorder_point} units</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#64748B' }}>Safety Buffer</div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#0F172A' }}>{selectedItem.safety_stock} units</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#64748B' }}>Target Stock Level (S)</div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#0F172A' }}>{selectedItem.order_up_to} units</div>
                </div>
              </div>
            </div>

            {/* Single SKU AI Advisor */}
            <div style={{ backgroundColor: '#FFFFFF', borderRadius: '8px', border: '1px solid #E2E8F0', padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '18px' }}>🤖</span>
                  <h3 style={{ fontSize: '15px', fontWeight: 'bold', color: '#0F172A', margin: 0 }}>
                    Item Advisory Briefing
                  </h3>
                </div>
                <button
                  onClick={onGenerateAdvisory}
                  disabled={advisoryLoading}
                  style={{
                    backgroundColor: '#0F172A',
                    color: '#FFFFFF',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '7px 14px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    cursor: advisoryLoading ? 'not-allowed' : 'pointer',
                    opacity: advisoryLoading ? 0.7 : 1,
                    transition: 'opacity 0.2s'
                  }}
                >
                  {advisoryLoading ? 'Analyzing Supply Chain Data...' : '✨ Generate AI Procurement Brief'}
                </button>
              </div>

              {advisoryText ? (
                <div style={{ backgroundColor: '#F1F5F9', borderLeft: '4px solid #0284C7', padding: '14px', borderRadius: '4px', fontSize: '13px', lineHeight: '1.6', color: '#1E293B' }}>
                  {advisoryText}
                </div>
              ) : (
                <div style={{ backgroundColor: '#F8FAFC', border: '1px dashed #CBD5E1', padding: '14px', borderRadius: '6px', fontSize: '12px', color: '#64748B', textAlign: 'center' }}>
                  Click above to run the predictive briefing for <strong>{selectedItem.product_name}</strong>.
                </div>
              )}
            </div>

            {/* Forward-Looking 4-Week Bar Chart */}
            <div style={{ backgroundColor: '#FFFFFF', borderRadius: '8px', border: '1px solid #E2E8F0', padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <h3 style={{ fontSize: '15px', fontWeight: 'bold', color: '#0F172A', margin: 0 }}>
                  Forward 4-Week Demand Predictions
                </h3>
                <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#0284C7' }}>
                  Total 4-Week Demand: {selectedItem.forecast_4w_total} units
                </span>
              </div>

              <div style={{ height: '180px' }}>
                <Bar
                  data={forecastBarData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                      y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Units' }
                      }
                    }
                  }}
                />
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}


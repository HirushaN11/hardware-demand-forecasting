import React, { useState, useEffect } from 'react';

export default function ClearanceAdvisory({ onBackToDashboard }) {
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchRecommendations = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch('http://127.0.0.1:8000/api/recommendations');
            const data = await res.json();
            if (data.status === 'success') {
                setRecommendations(data.recommendations || []);
            } else {
                setError(data.message || 'Failed to load recommendations');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRecommendations();
    }, []);

    return (
        <div style={{
            background: '#1e293b',
            padding: '24px',
            borderRadius: '12px',
            border: '1px solid #334155',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)'
        }}>
            {/* Top Navigation Back Button if provided */}
            {onBackToDashboard && (
                <div style={{ marginBottom: '16px' }}>
                    <button
                        onClick={onBackToDashboard}
                        style={{
                            backgroundColor: '#334155',
                            color: '#F8FAFC',
                            border: '1px solid #475569',
                            borderRadius: '6px',
                            padding: '6px 12px',
                            fontSize: '12px',
                            fontWeight: '600',
                            cursor: 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            transition: 'background-color 0.15s'
                        }}
                        onMouseEnter={(e) => e.target.style.backgroundColor = '#475569'}
                        onMouseLeave={(e) => e.target.style.backgroundColor = '#334155'}
                    >
                        ← Back to Operational Dashboard
                    </button>
                </div>
            )}

            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '20px',
                flexWrap: 'wrap',
                gap: '12px'
            }}>
                <div>
                    <h3 style={{
                        margin: 0,
                        color: '#f8fafc',
                        fontSize: '1.25rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}>
                        🏷️ Smart Merchandising & Clearance Copilot
                    </h3>
                    <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: '0.875rem' }}>
                        Automated bundling and discount strategies for slow-moving inventory to unblock working capital.
                    </p>
                </div>
                <button
                    onClick={fetchRecommendations}
                    disabled={loading}
                    style={{
                        background: '#2563eb',
                        color: '#ffffff',
                        border: 'none',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '500',
                        transition: 'background 0.2s'
                    }}
                >
                    {loading ? 'Analyzing...' : '🔄 Refresh Strategies'}
                </button>
            </div>

            {loading && (
                <div style={{ color: '#94a3b8', textAlign: 'center', padding: '40px 0' }}>
                    Analyzing sales turnover ratios and generating bundling strategies...
                </div>
            )}

            {error && !loading && (
                <div style={{
                    color: '#f87171',
                    background: 'rgba(239, 68, 68, 0.1)',
                    padding: '12px',
                    borderRadius: '6px',
                    border: '1px solid rgba(239, 68, 68, 0.2)'
                }}>
                    ⚠️ {error}
                </div>
            )}

            {!loading && !error && recommendations.length === 0 && (
                <div style={{ color: '#94a3b8', textAlign: 'center', padding: '30px 0' }}>
                    No slow-moving inventory detected. All items have healthy turnover velocity!
                </div>
            )}

            {!loading && !error && recommendations.length > 0 && (
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                    gap: '16px'
                }}>
                    {recommendations.map((rec, index) => {
                        const isBundle = rec.strategy_type?.toLowerCase().includes('bundle');
                        return (
                            <div
                                key={index}
                                style={{
                                    background: '#0f172a',
                                    padding: '18px',
                                    borderRadius: '8px',
                                    border: '1px solid #334155',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    justifyContent: 'space-between'
                                }}
                            >
                                <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{
                                            fontSize: '0.75rem',
                                            fontWeight: '700',
                                            color: '#38bdf8',
                                            background: 'rgba(56, 189, 248, 0.1)',
                                            padding: '3px 8px',
                                            borderRadius: '4px'
                                        }}>
                                            {rec.sku}
                                        </span>
                                        <span style={{
                                            fontSize: '0.75rem',
                                            fontWeight: '600',
                                            color: isBundle ? '#34d399' : '#f59e0b',
                                            background: isBundle ? 'rgba(52, 211, 153, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                                            padding: '3px 8px',
                                            borderRadius: '4px'
                                        }}>
                                            {rec.strategy_type || 'Merchandising'}
                                        </span>
                                    </div>

                                    <h4 style={{ color: '#f1f5f9', margin: '12px 0 8px 0', fontSize: '1.05rem' }}>
                                        {rec.slow_item}
                                    </h4>

                                    {rec.paired_with && rec.paired_with !== 'None' && (
                                        <div style={{
                                            margin: '10px 0',
                                            padding: '10px 12px',
                                            background: '#1e293b',
                                            borderRadius: '6px',
                                            borderLeft: '4px solid #34d399'
                                        }}>
                                            <div style={{ color: '#94a3b8', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                                Recommended Cross-Sell Pair
                                            </div>
                                            <div style={{ color: '#e2e8f0', fontSize: '0.9rem', fontWeight: '500', marginTop: '2px' }}>
                                                🔗 Bundle with <span style={{ color: '#34d399' }}>{rec.paired_with}</span>
                                            </div>
                                        </div>
                                    )}

                                    {rec.discount_pct && (
                                        <div style={{
                                            margin: '10px 0',
                                            padding: '8px 12px',
                                            background: '#1e293b',
                                            borderRadius: '6px',
                                            borderLeft: '4px solid #f59e0b',
                                            color: '#fbbf24',
                                            fontSize: '0.85rem'
                                        }}>
                                            🏷️ Suggested Markdown: <strong>{rec.discount_pct}</strong>
                                        </div>
                                    )}

                                    <p style={{
                                        color: '#94a3b8',
                                        fontSize: '0.85rem',
                                        margin: '12px 0 0 0',
                                        lineHeight: '1.5'
                                    }}>
                                        {rec.reasoning}
                                    </p>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}


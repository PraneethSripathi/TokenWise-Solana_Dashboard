import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api`;

const TOKEN_CONTRACT = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump";

const App = () => {
  const [tokenHolders, setTokenHolders] = useState([]);
  const [dashboardData, setDashboardData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // Centralized error state
  const [wsConnected, setWsConnected] = useState(false);
  const [realtimeTransactions, setRealtimeTransactions] = useState([]);
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [walletTransactions, setWalletTransactions] = useState([]);
  const [protocolStats, setProtocolStats] = useState({}); // Now for selected wallet's protocol usage
  const [activeTab, setActiveTab] = useState('dashboard');

  const startRealtimeMonitoring = async () => {
    try {
      const response = await axios.post(`${API}/realtime/start-monitoring`);
      console.log('Real-time monitoring started:', response.data);
      setError(null); // Clear any previous errors
    } catch (err) {
      console.error('Error starting real-time monitoring:', err);
      setError('Failed to start real-time monitoring. Check backend.');
    }
  };

  const stopRealtimeMonitoring = async () => {
    try {
      const response = await axios.post(`${API}/realtime/stop-monitoring`);
      console.log('Real-time monitoring stopped:', response.data);
      setError(null); // Clear any previous errors
    } catch (err) {
      console.error('Error stopping real-time monitoring:', err);
      setError('Failed to stop real-time monitoring. Check backend.');
    }
  };

  // Fetches token holders from the backend.
  const fetchTokenHolders = useCallback(async () => {
    try {
      setLoading(true);
      // Clear error related to token holders before fetching
      setError(prev => (prev === 'No top token holders found. Please run seed_db.py and restart backend.' ? null : prev));

      const response = await axios.get(`${API}/token-holders/${TOKEN_CONTRACT}`);
      console.log("Response from /api/token-holders:", response.data); 

      const holders = response.data || []; 
      setTokenHolders(holders);
      console.log("tokenHolders state after setting:", holders); 
      
      if (holders.length > 0) {
        console.log(`✅ Successfully loaded ${holders.length} token holders`);
        console.log(`💰 Top holder: ${holders[0].owner.slice(0, 10)}... with ${holders[0].balance?.toFixed(2)} tokens`);
      } else {
        console.log('No token holders found from API. Database might be empty or RPC call failed.');
        setError('No top token holders found. Please run seed_db.py and restart backend.');
      }
    } catch (err) {
      console.error('Error fetching token holders:', err);
      setError('Failed to fetch token holders. Backend endpoint might be down or data not seeded.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetches overall dashboard analytics data from the backend
  const fetchDashboardData = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/analytics/dashboard`);
      setDashboardData(response.data);
      console.log("Dashboard data fetched:", response.data);
      setError(null); // Clear dashboard-related errors if successful
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to fetch dashboard data. Check backend logs.');
    }
  }, []);

  // Fetches transactions for a specific wallet
  const fetchWalletTransactions = async (walletAddress) => {
    try {
      setLoading(true);
      setError(null); // Clear previous errors
      // Call the new backend endpoint for wallet-specific transactions
      const response = await axios.get(`${API}/wallets/${walletAddress}/transactions`);
      setWalletTransactions(response.data.transactions || []);
      setProtocolStats(response.data.protocol_usage || {}); // Correctly getting per-wallet protocol usage
      console.log(`Transactions for ${walletAddress} fetched:`, response.data.transactions);
      console.log(`Protocol stats for ${walletAddress} fetched:`, response.data.protocol_usage);

    } catch (err) {
      console.error('Error fetching wallet transactions:', err);
      setError(`Failed to fetch wallet transactions for ${formatAddress(walletAddress)}. Check backend logs.`);
    } finally {
      setLoading(false);
    }
  };

  // WebSocket connection and message handling for real-time transactions
  useEffect(() => {
    const wsProtocol = BACKEND_URL.startsWith('https://') ? 'wss://' : 'ws://';
    const wsUrl = `${wsProtocol}${BACKEND_URL.split('//')[1]}/ws/transactions`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected - Real-time monitoring active');
      setError(null); // Clear connection errors

      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ command: 'ping' }));
        }
      }, 30000);
      ws.pingInterval = pingInterval; 
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("WebSocket message type received:", data.type);

        switch (data.type) {
          case 'new_transaction':
            setRealtimeTransactions(prev => {
              const newTransaction = {
                ...data.data,
                isNew: true
              };
              return [newTransaction, ...prev.slice(0, 49)];
            });
            if (data.data.action_type !== 'unknown') {
              console.log(`🔥 NEW ${data.data.action_type?.toUpperCase()}: ${data.data.amount?.toFixed(2)} tokens via ${data.data.protocol}`);
            }
            fetchDashboardData(); 
            break;

          case 'connection_established':
            console.log('TokenWise monitoring established for token:', data.monitoring_token);
            break;

          case 'pong':
          case 'keepalive':
            break;

          case 'status':
            console.log('Monitoring status:', data);
            break;

          case 'dashboard_update':
            setDashboardData(data);
            console.log('Dashboard data updated via WebSocket:', data);
            break;

          default:
            console.log('Unknown WebSocket message type:', data.type);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
        setError('Error processing real-time data.');
      }
    };

    ws.onclose = (event) => {
      setWsConnected(false);
      console.log('WebSocket disconnected:', event.code, event.reason);
      if (ws.pingInterval) clearInterval(ws.pingInterval); 
      setError('WebSocket disconnected. Attempting to reconnect...'); 
      setTimeout(() => {
        if (!wsConnected) console.log('Attempting to reconnect...'); 
      }, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
      setError('WebSocket connection error. Check backend and network.');
    };

    return () => {
      if (ws.pingInterval) clearInterval(ws.pingInterval);
      ws.close(); 
    };
  }, [BACKEND_URL, fetchDashboardData]); 

  useEffect(() => {
    console.log("🔥 UI transaction feed updated:", realtimeTransactions);
  }, [realtimeTransactions]);

  // Initial data load on component mount
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchTokenHolders(), 
        fetchDashboardData()  
      ]);
      setLoading(false);
    };

    loadData();
  }, [fetchTokenHolders, fetchDashboardData]); 

  // Handle wallet selection
  const handleWalletSelect = (wallet) => {
    setSelectedWallet(wallet);
    fetchWalletTransactions(wallet.owner); 
    setActiveTab('wallet'); 
  };

  // Utility function to format long addresses for display
  const formatAddress = (address) => {
    if (!address) return 'Unknown';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  // Utility function to format numbers with commas
  const formatNumber = (num) => {
    if (typeof num !== 'number' && typeof num !== 'string') return num; 
    return new Intl.NumberFormat().format(parseFloat(num)); 
  };

  // Utility function to get color based on percentage (for visual cues)
  const getPercentageColor = (percentage) => {
    if (percentage > 5) return 'text-red-500';
    if (percentage > 1) return 'text-yellow-500';
    return 'text-green-500';
  };

  // Display loading spinner while initial data is being fetched
  if (loading && tokenHolders.length === 0 && dashboardData.total_transactions === 0) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading TokenWise Intelligence...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header Section */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-blue-400">🧠 TokenWise</h1>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-300">Real-Time Solana Wallet Intelligence</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-4">
                {/* Live Status Indicator */}
                <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${wsConnected ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                  <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
                  <span className="text-xs">{wsConnected ? 'Live Monitoring' : 'Disconnected'}</span>
                </div>
                {/* Start/Stop Monitoring Buttons */}
                <div className="flex space-x-2">
                  <button
                    onClick={startRealtimeMonitoring}
                    className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-xs font-medium"
                  >
                    ▶ Start
                  </button>
                  <button
                    onClick={stopRealtimeMonitoring}
                    className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-xs font-medium"
                  >
                    ⏹ Stop
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'dashboard' 
                  ? 'border-blue-500 text-blue-400' 
                  : 'border-transparent text-gray-300 hover:text-white hover:border-gray-300'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('holders')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'holders' 
                  ? 'border-blue-500 text-blue-400' 
                  : 'border-transparent text-gray-300 hover:text-white hover:border-gray-300'
              }`}
            >
              Top Holders
            </button>
            <button
              onClick={() => setActiveTab('realtime')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'realtime' 
                  ? 'border-blue-500 text-blue-400' 
                  : 'border-transparent text-gray-300 hover:text-white hover:border-gray-300'
              }`}
            >
              Real-Time Feed
            </button>
            {selectedWallet && (
              <button
                onClick={() => setActiveTab('wallet')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'wallet' 
                    ? 'border-blue-500 text-blue-400' 
                    : 'border-transparent text-gray-300 hover:text-white hover:border-gray-300'
                }`}
              >
                Wallet Analysis
              </button>
            )}
          </nav>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-8 bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Dashboard Tab Content */}
        {activeTab === 'dashboard' && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold mb-2">Token Intelligence Dashboard</h2>
              <p className="text-gray-400">Contract: {formatAddress(TOKEN_CONTRACT)}</p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-900 rounded-lg">
                    <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-400">Total Holders</p>
                    <p className="text-2xl font-bold text-white">{formatNumber(dashboardData.holder_count || 0)}</p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-green-900 rounded-lg">
                    <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-400">Transactions</p>
                    <p className="text-2xl font-bold text-white">{formatNumber(dashboardData.total_transactions || 0)}</p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-900 rounded-lg">
                    <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-400">Tracked Wallets</p>
                    <p className="text-2xl font-bold text-white">{formatNumber(dashboardData.tracked_wallets_count || 0)}</p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-yellow-900 rounded-lg">
                    <svg className="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-400">Live Status</p>
                    <p className="text-2xl font-bold text-white">{wsConnected ? 'Active' : 'Offline'}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Protocol Usage */}
            {dashboardData.protocol_usage && dashboardData.protocol_usage.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Protocol Usage</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {dashboardData.protocol_usage.map((protocol, index) => (
                    <div key={protocol._id || index} className="bg-gray-700 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-300">{protocol._id || 'Unknown'}</span>
                        <span className="text-lg font-bold text-white">{protocol.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Transactions (from dashboardData) */}
            {dashboardData.recent_transactions && dashboardData.recent_transactions.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Recent Transactions (Dashboard)</h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {dashboardData.recent_transactions.map((tx, index) => (
                    <div key={tx.id || index} className="bg-gray-700 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            tx.action_type === 'buy' ? 'bg-green-400' :
                            tx.action_type === 'sell' ? 'bg-red-400' :
                            'bg-blue-400'
                          }`}></div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <p className="text-sm font-medium text-white">{formatAddress(tx.signature)}</p>
                              <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                tx.action_type === 'buy' ? 'bg-green-900 text-green-300' :
                                tx.action_type === 'sell' ? 'bg-red-900 text-red-300' :
                                'bg-blue-900 text-blue-300'
                              }`}>
                                {tx.action_type?.toUpperCase() || 'TRANSFER'}
                              </span>
                            </div>
                            <p className="text-xs text-gray-400">{formatAddress(tx.wallet)}</p>
                            {tx.amount && (
                              <p className="text-xs text-gray-300">Amount: {tx.amount.toFixed(4)} tokens</p>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-300">{tx.protocol || 'Unknown'}</p>
                          <p className="text-xs text-gray-400">{new Date(tx.timestamp).toLocaleTimeString()}</p>
                          {tx.block_time && (
                            <p className="text-xs text-gray-500">Block: {tx.block_time}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Token Holders (from dashboardData) */}
            {dashboardData.top_token_holders && dashboardData.top_token_holders.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Top Token Holders (Dashboard)</h3>
                <div className="space-y-3">
                  {dashboardData.top_token_holders.map((holder, index) => (
                    <div key={holder.owner || index} className="bg-gray-700 rounded-lg p-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-white">{formatAddress(holder.owner)}</p>
                        <p className="text-xs text-gray-400">Balance: {formatNumber(holder.balance?.toFixed(2) || 0)}</p>
                      </div>
                      <div className="text-right">
                        <span className={`font-medium ${getPercentageColor(holder.percentage)}`}>
                          {holder.percentage?.toFixed(3) || 0}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Top Holders Tab Content */}
        {activeTab === 'holders' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Top Token Holders</h2>
              <button
                onClick={fetchTokenHolders}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium"
              >
                Refresh Data
              </button>
            </div>

            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-700">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Rank</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Wallet Address</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Balance</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Percentage</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-gray-800 divide-y divide-gray-700">
                    {/* Conditional rendering based on tokenHolders.length */}
                    {tokenHolders.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="px-6 py-4 text-center text-gray-400">
                          No top holders found. Please ensure the backend is running and data is seeded.
                        </td>
                      </tr>
                    ) : (
                      tokenHolders.map((holder, index) => (
                        <tr key={holder.owner || index} className="hover:bg-gray-700">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                            #{index + 1}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                            <div className="flex items-center">
                              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mr-3">
                                <span className="text-xs font-bold text-white">{index + 1}</span>
                              </div>
                              <div>
                                <div className="text-sm font-medium text-white">{formatAddress(holder.owner)}</div>
                                <div className="text-xs text-gray-400">{formatAddress(holder.address)}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                            {formatNumber(holder.balance?.toFixed(2) || 0)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`font-medium ${getPercentageColor(holder.percentage)}`}>
                              {holder.percentage?.toFixed(3) || 0}%
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                            <button
                              onClick={() => handleWalletSelect(holder)}
                              className="text-blue-400 hover:text-blue-300 font-medium"
                            >
                              Analyze
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Real-time Feed Tab Content */}
        {activeTab === 'realtime' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">Real-Time Transaction Feed</h2>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Live Transactions</h3>
                <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${wsConnected ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                  <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
                  <span className="text-xs">{wsConnected ? 'Live Updates' : 'Disconnected'}</span>
                </div>
              </div>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {realtimeTransactions.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    <div className="mb-4">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                    </div>
                    <p>🔍 Monitoring for real-time transactions...</p>
                    <p className="text-sm mt-2">Contract: {formatAddress(TOKEN_CONTRACT)}</p>
                  </div>
                ) : (
                  realtimeTransactions.map((tx, index) => (
                    <div key={tx.id || index} className={`bg-gray-700 rounded-lg p-4 ${tx.isNew ? 'ring-2 ring-green-500 bg-gray-600' : ''}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            tx.action_type === 'buy' ? 'bg-green-400' :
                            tx.action_type === 'sell' ? 'bg-red-400' :
                            'bg-blue-400'
                          } ${tx.isNew ? 'animate-pulse' : ''}`}></div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <p className="text-sm font-medium text-white">{formatAddress(tx.signature)}</p>
                              <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                tx.action_type === 'buy' ? 'bg-green-900 text-green-300' :
                                tx.action_type === 'sell' ? 'bg-red-900 text-red-300' :
                                'bg-blue-900 text-blue-300'
                              }`}>
                                {tx.action_type?.toUpperCase() || 'TRANSFER'}
                              </span>
                              {tx.isNew && <span className="text-xs bg-yellow-600 text-yellow-200 px-2 py-1 rounded">NEW</span>}
                            </div>
                            <p className="text-xs text-gray-400">{formatAddress(tx.wallet)}</p>
                            {tx.amount && (
                              <p className="text-xs text-gray-300">Amount: {tx.amount.toFixed(4)} tokens</p>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-300">{tx.protocol || 'Unknown'}</p>
                          <p className="text-xs text-gray-400">{new Date(tx.timestamp).toLocaleTimeString()}</p>
                          {tx.block_time && (
                            <p className="text-xs text-gray-500">Block: {tx.block_time}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Wallet Analysis Tab Content */}
        {activeTab === 'wallet' && selectedWallet && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">Wallet Analysis</h2>
                <p className="text-gray-400">{formatAddress(selectedWallet.owner)}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Token Balance</p>
                <p className="text-2xl font-bold text-white">{formatNumber(selectedWallet.balance?.toFixed(2) || 0)}</p>
              </div>
            </div>

            {/* Protocol Usage (for selected wallet) */}
            {Object.keys(protocolStats).length > 0 && (
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Protocol Usage for this Wallet</h3> {/* Updated title */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(protocolStats).map(([protocol, count]) => (
                    <div key={protocol} className="bg-gray-700 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-300">{protocol}</span>
                        <span className="text-lg font-bold text-white">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Transaction History (for selected wallet) */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Recent Transactions for this Wallet</h3> {/* Updated title */}
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {walletTransactions.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    <p>No transactions found for this wallet.</p>
                  </div>
                ) : (
                  walletTransactions.map((tx, index) => (
                    <div key={tx.id || index} className="bg-gray-700 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-white">{formatAddress(tx.signature)}</p>
                          <p className="text-xs text-gray-400">{tx.action_type || 'N/A'}</p> 
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-300">{tx.protocol || 'Unknown'}</p>
                          <p className="text-xs text-gray-400">{new Date(tx.timestamp).toLocaleString()}</p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;

import { useState, useEffect } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, AreaChart, Area, ComposedChart, ReferenceLine
} from 'recharts'

const API = 'http://localhost:8000'

function App() {
  const [view, setView] = useState('build')
  const [step, setStep] = useState(1) // 1: select stocks, 2: assign quantities, 3: choose analysis
  const [stocks, setStocks] = useState([])
  const [selectedSymbols, setSelectedSymbols] = useState([]) // step 1: just symbols
  const [holdings, setHoldings] = useState({}) // step 2: {symbol: quantity}
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  const [analyses, setAnalyses] = useState({
    expected_return: true,
    historical_var: true,
    parametric_var: false,
    monte_carlo: true,
    stress_tests: true,
    volatility_forecast: true
  })

  useEffect(() => {
    fetch(`${API}/api/stocks`)
      .then(r => r.json())
      .then(data => setStocks(data.stocks))
      .catch(console.error)
  }, [])

  const filteredStocks = stocks.filter(s => {
    const matchesFilter = filter === 'all' || s.cap_category === filter
    const matchesSearch = s.symbol.toLowerCase().includes(search.toLowerCase()) ||
                          s.name?.toLowerCase().includes(search.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const toggleStock = (symbol) => {
    if (selectedSymbols.includes(symbol)) {
      setSelectedSymbols(selectedSymbols.filter(s => s !== symbol))
    } else if (selectedSymbols.length < 10) {
      setSelectedSymbols([...selectedSymbols, symbol])
    }
  }

  const goToStep2 = () => {
    // Initialize holdings with 1 share each
    const newHoldings = {}
    selectedSymbols.forEach(symbol => {
      newHoldings[symbol] = holdings[symbol] || 1
    })
    setHoldings(newHoldings)
    setStep(2)
  }

  const updateQuantity = (symbol, quantity) => {
    setHoldings({
      ...holdings,
      [symbol]: Math.max(1, parseInt(quantity) || 1)
    })
  }

  const getStockPrice = (symbol) => {
    const stock = stocks.find(s => s.symbol === symbol)
    if (!stock) return 0
    const priceStr = stock.price?.replace(/,/g, '').replace(' GBX', '').replace(' GBP', '')
    const price = parseFloat(priceStr) || 0
    return stock.price?.includes('GBX') ? price / 100 : price
  }

  const getStockInfo = (symbol) => stocks.find(s => s.symbol === symbol)

  const calculatePortfolioValue = () => {
    return Object.entries(holdings).reduce((total, [symbol, qty]) => {
      return total + (getStockPrice(symbol) * qty)
    }, 0)
  }

  const calculateWeights = () => {
    const total = calculatePortfolioValue()
    if (total === 0) return selectedSymbols.map(() => 1 / selectedSymbols.length)
    return selectedSymbols.map(symbol => (getStockPrice(symbol) * (holdings[symbol] || 1)) / total)
  }

  const toggleAnalysis = (key) => {
    setAnalyses(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const runAnalysis = async () => {
    const selectedAnalyses = Object.entries(analyses)
      .filter(([_, v]) => v)
      .map(([k]) => k)

    if (selectedAnalyses.length === 0) return alert('Select at least 1 analysis')

    const portfolioValue = calculatePortfolioValue()
    const weights = calculateWeights()

    setLoading(true)
    try {
      const res = await fetch(`${API}/api/analysis/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbols: selectedSymbols,
          weights: weights,
          portfolio_value: portfolioValue,
          analyses: selectedAnalyses
        })
      })
      const data = await res.json()
      if (data.detail) {
        alert(data.detail)
      } else {
        setResults(data)
        setView('dashboard')
      }
    } catch (e) {
      console.error(e)
      alert('Error running analysis')
    }
    setLoading(false)
  }

  const analysisOptions = [
    { key: 'expected_return', label: 'Expected Return & Volatility' },
    { key: 'historical_var', label: 'Historical VaR & ES' },
    { key: 'parametric_var', label: 'Parametric VaR' },
    { key: 'monte_carlo', label: 'Monte Carlo Simulation' },
    { key: 'stress_tests', label: 'Stress Tests' },
    { key: 'volatility_forecast', label: 'Volatility Forecast' }
  ]

  const formatCurrency = (val) => {
    if (val >= 0) return `£${val.toFixed(0)}`
    return `-£${Math.abs(val).toFixed(0)}`
  }

  const formatPercent = (val) => `${(val * 100).toFixed(2)}%`

  const startOver = () => {
    setView('build')
    setStep(1)
    setSelectedSymbols([])
    setHoldings({})
    setResults(null)
  }

  return (
    <div className="app">
      <header>
        <div className="logo">
          <div className="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 3v18h18" />
              <path d="M18 9l-5 5-4-4-3 3" />
            </svg>
          </div>
          <div>
            <h1>InvestX</h1>
            <span>portfolio optimization</span>
          </div>
        </div>
        <div className="nav-btns">
          <button
            className={`nav-btn ${view === 'build' ? 'active' : ''}`}
            onClick={() => setView('build')}
          >
            Build Portfolio
          </button>
          <button
            className={`nav-btn ${view === 'dashboard' ? 'active' : ''}`}
            onClick={() => setView('dashboard')}
            disabled={!results}
          >
            Dashboard
          </button>
        </div>
      </header>

      <main>
        {/* STEP 1: Select Stocks */}
        {view === 'build' && step === 1 && (
          <div className="panel">
            <div className="panel-title">Select Stocks</div>

            <div className="search-row">
              <div className="search-box">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#999" strokeWidth="2">
                  <circle cx="11" cy="11" r="8" />
                  <path d="M21 21l-4.35-4.35" />
                </svg>
                <input
                  type="text"
                  placeholder="Search stocks"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>
              <select
                className="filter-dropdown"
                value={filter}
                onChange={e => setFilter(e.target.value)}
              >
                <option value="all">all caps</option>
                <option value="large">large cap</option>
                <option value="mid">mid cap</option>
                <option value="small">small cap</option>
              </select>
            </div>

            <div className="selection-info">
              {selectedSymbols.length} stocks selected
              {selectedSymbols.length > 0 && (
                <span className="selected-chips">
                  {selectedSymbols.map(s => (
                    <span key={s} className="chip" onClick={() => toggleStock(s)}>{s} ×</span>
                  ))}
                </span>
              )}
            </div>

            <div className="stock-list">
              {filteredStocks.map(stock => (
                <div
                  key={stock.symbol}
                  className={`stock-item ${selectedSymbols.includes(stock.symbol) ? 'selected' : ''}`}
                  onClick={() => toggleStock(stock.symbol)}
                >
                  <div className={`stock-checkbox ${selectedSymbols.includes(stock.symbol) ? 'checked' : ''}`} />
                  <div className="stock-info">
                    <div className="stock-ticker">{stock.symbol}</div>
                    <div className="stock-name">{stock.name}</div>
                  </div>
                  <div className="stock-meta">
                    <span className="stock-tag">{stock.sector}</span>
                    <span className="stock-price">£{getStockPrice(stock.symbol).toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="step-footer">
              <button
                className="next-btn"
                disabled={selectedSymbols.length < 1}
                onClick={goToStep2}
              >
                Assign Quantities →
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Assign Quantities */}
        {view === 'build' && step === 2 && (
          <div className="panel">
            <div className="panel-title">Assign Quantities</div>

            <div className="holdings-list">
              {selectedSymbols.map(symbol => {
                const stock = getStockInfo(symbol)
                const price = getStockPrice(symbol)
                const qty = holdings[symbol] || 1
                const value = price * qty
                return (
                  <div key={symbol} className="holding-item">
                    <div className="holding-info">
                      <div className="holding-symbol">{symbol}</div>
                      <div className="holding-name">{stock?.name}</div>
                      <div className="holding-price">£{price.toFixed(2)} per share</div>
                    </div>
                    <div className="holding-qty">
                      <label>Shares</label>
                      <div className="qty-controls">
                        <button className="qty-btn" onClick={() => updateQuantity(symbol, qty - 1)}>−</button>
                        <input
                          type="number"
                          className="qty-input"
                          value={qty}
                          onChange={(e) => updateQuantity(symbol, e.target.value)}
                          min="1"
                        />
                        <button className="qty-btn" onClick={() => updateQuantity(symbol, qty + 1)}>+</button>
                      </div>
                    </div>
                    <div className="holding-value">
                      <label>Value</label>
                      <div className="value-amount">£{value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="portfolio-total">
              <span>Total Portfolio Value:</span>
              <span className="total-value">£{calculatePortfolioValue().toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
            </div>

            <div className="step-footer">
              <button className="back-btn" onClick={() => setStep(1)}>← Back</button>
              <button className="next-btn" onClick={() => setStep(3)}>Choose Analysis →</button>
            </div>
          </div>
        )}

        {/* STEP 3: Choose Analysis */}
        {view === 'build' && step === 3 && (
          <div className="panel">
            <div className="panel-title">Choose Analysis</div>

            <div className="portfolio-summary-bar">
              <span>{selectedSymbols.length} stocks</span>
              <span>•</span>
              <span>£{calculatePortfolioValue().toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
            </div>

            <div className="analysis-grid">
              {analysisOptions.map(opt => (
                <div
                  key={opt.key}
                  className={`analysis-item ${analyses[opt.key] ? 'selected' : ''}`}
                  onClick={() => toggleAnalysis(opt.key)}
                >
                  <span className="analysis-label">{opt.label}</span>
                  <div className={`analysis-check ${analyses[opt.key] ? 'checked' : ''}`} />
                </div>
              ))}
            </div>

            <div className="step-footer">
              <button className="back-btn" onClick={() => setStep(2)}>← Back</button>
              <button className="run-btn" onClick={runAnalysis} disabled={loading}>
                {loading ? 'Fetching data...' : 'RUN'}
              </button>
            </div>
          </div>
        )}

        {/* DASHBOARD */}
        {view === 'dashboard' && results && (
          <div className="dashboard-full">
            <div className="dashboard-header">
              <h2>Your Portfolio Story</h2>
              <span className="dashboard-subtitle">
                {results.symbols?.join(', ')} | Portfolio Value: £{results.portfolio_value?.toLocaleString(undefined, {minimumFractionDigits: 2})}
              </span>
              {results.warning && (
                <div className="dashboard-warning">{results.warning}</div>
              )}
            </div>

            <div className="story-container">
              {/* Summary Card */}
              <div className="story-section summary-section">
                <div className="summary-card">
                  <h3>The Bottom Line</h3>
                  <p className="summary-text">
                    Based on the past year of market data, here's what you can expect from your £{results.portfolio_value?.toLocaleString()} portfolio:
                  </p>
                  {results.expected_return && (
                    <div className="summary-highlights">
                      <div className="highlight-item">
                        <span className="highlight-label">On a typical week, you could make</span>
                        <span className={`highlight-value ${results.expected_return.weekly.expected_profit >= 0 ? 'positive' : 'negative'}`}>
                          {formatCurrency(results.expected_return.weekly.expected_profit)}
                        </span>
                      </div>
                      {results.historical_var && (
                        <div className="highlight-item">
                          <span className="highlight-label">But in a bad week (1 in 20), you might lose up to</span>
                          <span className="highlight-value negative">
                            {formatCurrency(Math.abs(results.historical_var.var_95.loss))}
                          </span>
                        </div>
                      )}
                      {results.monte_carlo && (
                        <div className="highlight-item">
                          <span className="highlight-label">In a great week (top 5%), you could gain</span>
                          <span className="highlight-value positive">
                            {formatCurrency(results.monte_carlo.percentiles['95th'])}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Price History */}
              {results.price_history && (
                <div className="story-section">
                  <div className="section-header">
                    <h3>How Your Stocks Performed This Year</h3>
                    <p className="section-desc">This chart shows how each stock in your portfolio moved over the past 12 months. Look for trends - are they generally going up, down, or sideways?</p>
                  </div>
                  <div className="chart-container large">
                    <ResponsiveContainer width="100%" height={250}>
                      <LineChart data={results.price_history.dates.map((date, i) => {
                        const point = { date: date.slice(5) }
                        Object.keys(results.price_history.prices).forEach(symbol => {
                          point[symbol] = results.price_history.prices[symbol][i]
                        })
                        return point
                      })}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="date" stroke="white" tick={{fontSize: 10}} interval="preserveStartEnd" />
                        <YAxis stroke="white" tick={{fontSize: 10}} />
                        <Tooltip contentStyle={{background: '#1e1b4b', border: '1px solid white'}} />
                        {Object.keys(results.price_history.prices).map((symbol, i) => (
                          <Line key={symbol} type="monotone" dataKey={symbol} stroke={['#4ade80', '#fbbf24', '#f87171', '#60a5fa', '#a78bfa'][i % 5]} dot={false} strokeWidth={2} />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Expected Returns */}
              {results.expected_return && (
                <div className="story-section">
                  <div className="section-header">
                    <h3>What Returns Can You Expect?</h3>
                    <p className="section-desc">Based on historical performance, here's what your portfolio might return. Remember: past performance doesn't guarantee future results!</p>
                  </div>
                  <div className="insight-cards">
                    <div className="insight-card">
                      <div className="insight-icon">W</div>
                      <div className="insight-content">
                        <span className="insight-label">Expected Weekly Return</span>
                        <span className={`insight-value ${results.expected_return.weekly.mean_return >= 0 ? 'positive' : 'negative'}`}>
                          {formatPercent(results.expected_return.weekly.mean_return)}
                        </span>
                        <span className="insight-explain">
                          That's about {formatCurrency(results.expected_return.weekly.expected_profit)} per week on your portfolio
                        </span>
                      </div>
                    </div>
                    <div className="insight-card">
                      <div className="insight-icon">Y</div>
                      <div className="insight-content">
                        <span className="insight-label">Expected Annual Return</span>
                        <span className={`insight-value ${results.expected_return.annual.mean_return >= 0 ? 'positive' : 'negative'}`}>
                          {formatPercent(results.expected_return.annual.mean_return)}
                        </span>
                        <span className="insight-explain">
                          If this continues, you could make {formatCurrency(results.expected_return.annual.expected_profit)} this year
                        </span>
                      </div>
                    </div>
                    <div className="insight-card">
                      <div className="insight-icon">V</div>
                      <div className="insight-content">
                        <span className="insight-label">Volatility (Risk Level)</span>
                        <span className="insight-value">{formatPercent(results.expected_return.annual.volatility)}</span>
                        <span className="insight-explain">
                          {results.expected_return.annual.volatility < 0.15 ? "Low risk - relatively stable" :
                           results.expected_return.annual.volatility < 0.25 ? "Moderate risk - expect some ups and downs" :
                           "High risk - expect significant price swings"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Risk Analysis */}
              {results.historical_var && (
                <div className="story-section">
                  <div className="section-header">
                    <h3>How Much Could You Lose?</h3>
                    <p className="section-desc">Value at Risk (VaR) tells you the worst-case scenario for a normal week. Expected Shortfall tells you the average loss when things go really bad.</p>
                  </div>
                  <div className="risk-explanation">
                    <div className="risk-scenario">
                      <div className="scenario-header">
                        <span className="scenario-label">In 19 out of 20 weeks...</span>
                        <span className="scenario-subtitle">95% confidence</span>
                      </div>
                      <div className="scenario-content">
                        <p>Your losses should stay below <strong className="negative">{formatCurrency(Math.abs(results.historical_var.var_95.loss))}</strong></p>
                      </div>
                    </div>
                    <div className="risk-scenario warning">
                      <div className="scenario-header">
                        <span className="scenario-label">But in that 1 bad week...</span>
                        <span className="scenario-subtitle">When things go wrong</span>
                      </div>
                      <div className="scenario-content">
                        <p>You could lose on average <strong className="negative">{formatCurrency(Math.abs(results.historical_var.expected_shortfall_95.loss))}</strong></p>
                        <p className="scenario-note">This is called "Expected Shortfall" - the average loss during the worst times</p>
                      </div>
                    </div>
                  </div>
                  <div className="chart-container">
                    <p className="chart-title">Distribution of Weekly Returns</p>
                    <p className="chart-subtitle">The red bars show the tail risk - weeks where you'd lose money</p>
                    <ResponsiveContainer width="100%" height={150}>
                      <BarChart data={results.historical_var.weekly_returns_distribution.histogram.map((count, i) => ({
                        bin: i, count, edge: results.historical_var.weekly_returns_distribution.bin_edges[i]
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="bin" stroke="white" tick={false} />
                        <YAxis stroke="white" tick={{fontSize: 10}} />
                        <Bar dataKey="count" fill="#8b5cf6">
                          {results.historical_var.weekly_returns_distribution.histogram.map((_, i) => (
                            <Cell key={i} fill={results.historical_var.weekly_returns_distribution.bin_edges[i] < 0 ? '#f87171' : '#4ade80'} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Monte Carlo */}
              {results.monte_carlo && (
                <div className="story-section">
                  <div className="section-header">
                    <h3>10,000 Possible Futures</h3>
                    <p className="section-desc">We simulated 10,000 different ways next week could play out based on your portfolio's characteristics. Here's what we found:</p>
                  </div>
                  <div className="future-scenarios">
                    <div className="future-card bad">
                      <div className="future-icon">5%</div>
                      <div className="future-label">Bad Week</div>
                      <div className="future-sublabel">Worst 5% of outcomes</div>
                      <div className="future-value">{formatCurrency(results.monte_carlo.percentiles['5th'])}</div>
                    </div>
                    <div className="future-card neutral">
                      <div className="future-icon">AVG</div>
                      <div className="future-label">Typical Week</div>
                      <div className="future-sublabel">Average outcome</div>
                      <div className="future-value">{formatCurrency(results.monte_carlo.statistics.mean)}</div>
                    </div>
                    <div className="future-card good">
                      <div className="future-icon">95%</div>
                      <div className="future-label">Great Week</div>
                      <div className="future-sublabel">Best 5% of outcomes</div>
                      <div className="future-value">{formatCurrency(results.monte_carlo.percentiles['95th'])}</div>
                    </div>
                  </div>
                  <div className="chart-container">
                    <p className="chart-title">Possible Profit/Loss Next Week</p>
                    <p className="chart-subtitle">The yellow line shows break-even (£0)</p>
                    <ResponsiveContainer width="100%" height={180}>
                      <ComposedChart data={results.monte_carlo.distribution.histogram.map((count, i) => ({
                        profit: results.monte_carlo.distribution.bin_edges[i], count
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="profit" stroke="white" tick={{fontSize: 10}} tickFormatter={v => `£${v.toFixed(0)}`} />
                        <YAxis stroke="white" tick={{fontSize: 10}} />
                        <Bar dataKey="count" fill="#8b5cf6" />
                        <ReferenceLine x={0} stroke="#fbbf24" strokeWidth={2} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="chart-container">
                    <p className="chart-title">Sample Portfolio Journeys</p>
                    <p className="chart-subtitle">Each line shows one possible path your portfolio could take over 5 days</p>
                    <ResponsiveContainer width="100%" height={150}>
                      <LineChart>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="day" stroke="white" tick={{fontSize: 10}} label={{ value: 'Day', position: 'bottom', fill: 'white', fontSize: 11 }} />
                        <YAxis stroke="white" tick={{fontSize: 10}} tickFormatter={v => `£${(v/1000).toFixed(1)}k`} />
                        {results.monte_carlo.sample_paths.slice(0, 10).map((path, i) => (
                          <Line key={i} data={path.map((v, day) => ({ day, value: v }))} dataKey="value" stroke={`hsl(${i * 36}, 70%, 60%)`} dot={false} strokeWidth={1.5} opacity={0.7} />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Stress Tests */}
              {results.stress_tests && (
                <div className="story-section">
                  <div className="section-header">
                    <h3>What If Disaster Strikes?</h3>
                    <p className="section-desc">Here's how your portfolio might react to extreme market events. These are worst-case scenarios to help you prepare mentally.</p>
                  </div>
                  <div className="stress-scenarios">
                    <div className="stress-card">
                      <div className="stress-icon">-20%</div>
                      <div className="stress-name">Market Crash</div>
                      <div className="stress-desc">If the market drops 20% (like 2008 or 2020)</div>
                      <div className="stress-loss">{formatCurrency(results.stress_tests.scenarios.market_crash_20pct.portfolio_loss)}</div>
                    </div>
                    <div className="stress-card">
                      <div className="stress-icon">1D</div>
                      <div className="stress-name">Flash Crash</div>
                      <div className="stress-desc">Your worst single day based on history</div>
                      <div className="stress-loss">{formatCurrency(results.stress_tests.scenarios.flash_crash.portfolio_loss)}</div>
                    </div>
                    <div className="stress-card">
                      <div className="stress-icon">5D</div>
                      <div className="stress-name">Prolonged Downturn</div>
                      <div className="stress-desc">A week of consistently bad days</div>
                      <div className="stress-loss">{formatCurrency(results.stress_tests.scenarios.bad_week.portfolio_loss)}</div>
                    </div>
                    <div className="stress-card">
                      <div className="stress-icon">MAX</div>
                      <div className="stress-name">Maximum Drawdown</div>
                      <div className="stress-desc">Biggest peak-to-bottom drop historically</div>
                      <div className="stress-loss">{formatPercent(results.stress_tests.historical_drawdowns.max_drawdown)}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Volatility */}
              {results.volatility_forecast && (
                <div className="story-section">
                  <div className="section-header">
                    <h3>How Bumpy Is The Ride?</h3>
                    <p className="section-desc">Volatility measures how much your portfolio bounces around. Higher volatility means bigger swings - both up and down.</p>
                  </div>
                  <div className="volatility-insight">
                    <div className="vol-stat">
                      <span className="vol-label">Your Daily Volatility</span>
                      <span className="vol-value">{formatPercent(results.volatility_forecast.current_daily_vol)}</span>
                      <span className="vol-explain">
                        Your portfolio typically moves ±{formatPercent(results.volatility_forecast.current_daily_vol)} per day
                      </span>
                    </div>
                    <div className="vol-stat">
                      <span className="vol-label">Annualized Volatility</span>
                      <span className="vol-value">{formatPercent(results.volatility_forecast.current_annual_vol)}</span>
                      <span className="vol-explain">
                        {results.volatility_forecast.current_annual_vol < 0.15 ? "This is considered LOW risk" :
                         results.volatility_forecast.current_annual_vol < 0.25 ? "This is MODERATE risk" :
                         results.volatility_forecast.current_annual_vol < 0.35 ? "This is HIGH risk" : "This is VERY HIGH risk"}
                      </span>
                    </div>
                    <div className="vol-stat">
                      <span className="vol-label">Recent Trend</span>
                      <span className={`vol-value ${results.volatility_forecast.volatility_trend === 'decreasing' ? 'positive' : 'negative'}`}>
                        {results.volatility_forecast.volatility_trend === 'decreasing' ? '↓ Calming Down' : '↑ Getting Choppier'}
                      </span>
                    </div>
                  </div>
                  <div className="chart-container">
                    <p className="chart-title">Volatility Over Time</p>
                    <p className="chart-subtitle">See how the bumpiness has changed recently</p>
                    <ResponsiveContainer width="100%" height={120}>
                      <AreaChart data={results.volatility_forecast.rolling_20d_volatility.map((v, i) => ({ day: i, vol: v * 100 }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="day" stroke="white" tick={{fontSize: 10}} />
                        <YAxis stroke="white" tick={{fontSize: 9}} tickFormatter={v => `${v.toFixed(1)}%`} />
                        <Area type="monotone" dataKey="vol" stroke="#a78bfa" fill="#a78bfa" fillOpacity={0.3} />
                        <Tooltip contentStyle={{background: '#1e1b4b', border: '1px solid white'}} formatter={(v) => [`${v.toFixed(2)}%`, 'Volatility']} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>

            <div className="dashboard-footer">
              <button className="back-btn" onClick={startOver}>← Start New Analysis</button>
            </div>
          </div>
        )}

        {view === 'dashboard' && !results && (
          <div className="dashboard-full">
            <div className="loading">No results yet. Build a portfolio first.</div>
            <button className="back-btn" onClick={() => setView('build')}>← Build Portfolio</button>
          </div>
        )}
      </main>
    </div>
  )
}

export default App

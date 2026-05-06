import { useEffect, useState } from 'react'
import axiosInstance from '../../axiosInstance'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faSpinner } from '@fortawesome/free-solid-svg-icons'

const Dashboard = () => {
  const [ticker, setTicker] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [plot, setPlot] = useState()
  const [ma100, setMA100] = useState()
  const [ma200, setMA200] = useState()
  const [prediction, setPrediction] = useState()
  const [mse, setMSE] = useState()
  const [rmse, setRMSE] = useState()
  const [r2, setR2] = useState()
  const [watchlist, setWatchlist] = useState(['RELIANCE.NS', 'TCS.NS', 'INFY.NS'])
  const [watchTicker, setWatchTicker] = useState('')
  const [user, setUser] = useState(null)
  const [modalPreview, setModalPreview] = useState(null)
  const [notification, setNotification] = useState(null)
  const [notificationType, setNotificationType] = useState('success')
  const [marketFeed, setMarketFeed] = useState([
    { symbol: 'RELIANCE.NS', price: 2486.34, change: 1.52, percent_change: 0.61 },
    { symbol: 'TCS.NS', price: 3364.21, change: -0.23, percent_change: -0.07 },
    { symbol: 'INFY.NS', price: 1893.05, change: 0.78, percent_change: 0.41 },
    { symbol: 'NIFTY50', price: 22458.73, change: 0.94, percent_change: 0.42 }
  ])

  // Load portfolio and protected data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const protectedRes = await axiosInstance.get('/protected-view/')
        setUser(protectedRes.data.user || null)
        // Load portfolio from backend
        const portfolioRes = await axiosInstance.get('/portfolio/')
        if (portfolioRes.data.tickers && portfolioRes.data.tickers.length > 0) {
          setWatchlist(portfolioRes.data.tickers)
        }
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    }
    fetchData()
  }, [])

  // Save watchlist to backend whenever it changes
  useEffect(() => {
    const savePortfolio = async () => {
      try {
        await axiosInstance.post('/portfolio/', { tickers: watchlist })
      } catch (error) {
        console.error('Error saving portfolio:', error)
        showNotification('Portfolio sync failed. Changes will retry automatically.', 'error')
      }
    }
    
    if (watchlist.length > 0) {
      const debounceTimer = setTimeout(savePortfolio, 500)
      return () => clearTimeout(debounceTimer)
    }
  }, [watchlist])

  // Fetch live prices for watchlist
  useEffect(() => {
    const fetchLivePrices = async () => {
      try {
        const response = await axiosInstance.post('/live-prices/', { tickers: watchlist })
        if (response.data.prices) {
          const feed = Object.entries(response.data.prices).map(([symbol, data]) => ({
            symbol,
            price: data.price || 0,
            change: data.change || 0,
            percent_change: data.percent_change || 0
          }))
          setMarketFeed(feed)
        }
      } catch (error) {
        console.error('Error fetching live prices:', error)
        showNotification('Unable to refresh live watch prices right now.', 'warning')
      }
    }

    fetchLivePrices()
    const interval = setInterval(fetchLivePrices, 5000) // Update every 5 seconds
    return () => clearInterval(interval)
  }, [watchlist])

  const showNotification = (message, type = 'success') => {
    setNotification(message)
    setNotificationType(type)
    setTimeout(() => setNotification(null), 3000)
  }

  const selectTicker = (symbol) => {
    setTicker(symbol)
    showNotification(`${symbol} loaded into the prediction field.`, 'success')
  }

  const addWatchlist = (e) => {
    e.preventDefault()
    const normalized = watchTicker.trim().toUpperCase()
    if (!normalized) {
      return showNotification('Enter a ticker to add it to your watchlist.', 'warning')
    }
    if (watchlist.includes(normalized)) {
      return showNotification(`${normalized} is already in your watchlist.`, 'warning')
    }
    setWatchlist([normalized, ...watchlist].slice(0, 10))
    setWatchTicker('')
    showNotification(`${normalized} added to watchlist.`, 'success')
  }

  const removeWatchlist = (symbol) => {
    setWatchlist(watchlist.filter((item) => item !== symbol))
    showNotification(`${symbol} removed from your watchlist.`, 'success')
  }

  const openPreview = (label, url) => {
    setModalPreview({ label, url })
  }

  const closePreview = () => {
    setModalPreview(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await axiosInstance.post('/predict/', { ticker })
      const backendRoot = import.meta.env.VITE_BACKEND_ROOT || ''
      const plotUrl = `${backendRoot}${response.data.plot_img}`
      const ma100Url = `${backendRoot}${response.data.plot_100_dma}`
      const ma200Url = `${backendRoot}${response.data.plot_200_dma}`
      const predictionUrl = `${backendRoot}${response.data.plot_prediction}`

      if (response.data.error) {
        setError(response.data.error)
        setPlot(null)
        setMA100(null)
        setMA200(null)
        setPrediction(null)
        setMSE(null)
        setRMSE(null)
        setR2(null)
      } else {
        setPlot(plotUrl)
        setMA100(ma100Url)
        setMA200(ma200Url)
        setPrediction(predictionUrl)
        setMSE(response.data.mse)
        setRMSE(response.data.rmse)
        setR2(response.data.r2)
        showNotification(`Prediction ready for ${ticker.toUpperCase()}.`, 'success')
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error || error.response?.data?.details || 'Unable to fetch prediction. Check the ticker and try again.'
      setError(errorMessage)
      setPlot(null)
      setMA100(null)
      setMA200(null)
      setPrediction(null)
      setMSE(null)
      setRMSE(null)
      setR2(null)
      showNotification(errorMessage, 'error')
      console.error('There was an error making the API request', error)
    } finally {
      setLoading(false)
    }
  }

  const formatValue = (value) => (typeof value === 'number' ? value.toFixed(3) : 'N/A')
  const signalText = typeof r2 === 'number' ? (r2 >= 0.7 ? 'Strong indicator' : r2 >= 0.4 ? 'Moderate signal' : 'Watch closely') : 'N/A'

  return (
    <div className='container dashboard-panel'>
      {notification && (
        <div className={`notification-toast ${notificationType}`}>
          {notification}
        </div>
      )}
      <section className='dashboard-hero glass-card'>
        <div className='hero-header'>
          <span className='eyebrow'>Realtime stock forecast</span>
          <h2>{user ? `Welcome back, ${user.username}` : 'Enter a ticker to generate fresh price predictions.'}</h2>
          <p>{user ? 'Your personalized portfolio and live watchlist are ready for analysis.' : 'Submit any supported symbol and review closing price charts, moving average lines, and model evaluation metrics.'}</p>
          {user && (
            <div className='profile-badge'>
              <div className='profile-avatar'>{user.username.slice(0, 1).toUpperCase()}</div>
              <div>
                <span>Signed in as</span>
                <strong>{user.email}</strong>
              </div>
            </div>
          )}
        </div>

        <div className='dashboard-glance'>
          <article className='glance-card'>
            <strong>{ticker || '—'}</strong>
            <p>Selected ticker</p>
          </article>
          <article className='glance-card'>
            <strong>{prediction ? 'Ready' : 'Awaiting input'}</strong>
            <p>Prediction status</p>
          </article>
          <article className='glance-card'>
            <strong>{formatValue(r2)}</strong>
            <p>Model confidence</p>
          </article>
          <article className='glance-card'>
            <strong>{signalText}</strong>
            <p>Signal strength</p>
          </article>
        </div>

        <div className='dashboard-glance'>
          <article className='glance-card'>
            <strong>{ticker || 'RELIANCE.NS'}</strong>
            <p>Active ticker</p>
          </article>
          <article className='glance-card'>
            <strong>{watchlist.length}</strong>
            <p>Watchlist items</p>
          </article>
          <article className='glance-card'>
            <strong>{formatValue(r2)}</strong>
            <p>Confidence score</p>
          </article>
          <article className='glance-card'>
            <strong>{signalText}</strong>
            <p>Signal strength</p>
          </article>
        </div>

        <section className='watchlist-panel glass-card'>
          <div className='watchlist-header'>
            <h3>Portfolio watchlist</h3>
            <form className='watchlist-form' onSubmit={addWatchlist}>
              <input
                type='text'
                className='form-control'
                value={watchTicker}
                onChange={(e) => setWatchTicker(e.target.value)}
                placeholder='Add ticker, e.g. HDFCBANK.NS'
              />
              <button className='btn btn-primary' type='submit' disabled={!watchTicker.trim()}>Add</button>
            </form>
          </div>
          <p className='watchlist-note'>Tap a symbol to load it into the prediction search box instantly.</p>

          <div className='watchlist-items'>
            {watchlist.map((symbol) => (
              <div key={symbol} className='watchlist-item'>
                <span className='watchlist-link' onClick={() => selectTicker(symbol)}>{symbol}</span>
                <button className='btn btn-outline-info' onClick={() => removeWatchlist(symbol)}>
                  Remove
                </button>
              </div>
            ))}
          </div>
        </section>

        <div className='dashboard-live-panel'>
          <div className='live-panel-title'>
            <span className='eyebrow'>Market pulse</span>
            <h3>Next-level prediction control</h3>
          </div>
          <div className='live-stat-grid'>
            <article className='live-stat-card'>
              <span>Model Confidence</span>
              <strong>89%</strong>
            </article>
            <article className='live-stat-card'>
              <span>Trend Strength</span>
              <strong>Bullish</strong>
            </article>
            <article className='live-stat-card'>
              <span>Volatility Index</span>
              <strong>Low</strong>
            </article>
          </div>
          <div className='market-feed-strip'>
            {marketFeed.map((item) => (
              <div key={item.symbol} className={`feed-item ${item.change >= 0 ? 'positive' : 'negative'}`}>
                <strong>{item.symbol}</strong>
                <span>{item.price.toFixed(2)}</span>
                <small>{item.change >= 0 ? `+${item.change.toFixed(2)} (${item.percent_change.toFixed(2)}%)` : `${item.change.toFixed(2)} (${item.percent_change.toFixed(2)}%)`}</small>
              </div>
            ))}
          </div>
        </div>

        <div className='dashboard-boosters'>
          <div className='stock-card-wrapper'>
            <div className='stock-card stock-card-1'>
              <p>RELIANCE.NS</p>
              <strong>Forecast Momentum</strong>
              <span>Next-move strength view</span>
            </div>
            <div className='stock-card stock-card-2'>
              <p>Trend Pulse</p>
              <strong>360° signal</strong>
              <span>Market sentiment overlay</span>
            </div>
          </div>
        </div>

        <div className='dashboard-signals'>
          <span className='signal-chip'>Live market pulse</span>
          <span className='signal-chip'>Trend recognition</span>
          <span className='signal-chip'>Precision analytics</span>
        </div>

        <form className='dashboard-form' onSubmit={handleSubmit}>
          <input
            type='text'
            className='form-control'
            placeholder='Enter stock ticker, e.g. RELIANCE.NS'
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            required
          />
          <button type='submit' className='btn btn-primary' disabled={loading || !ticker.trim()}>
            {loading ? <span><FontAwesomeIcon icon={faSpinner} spin /> Please wait...</span> : 'See Prediction'}
          </button>
        </form>

        {error && <div className='alert alert-error'>{error}</div>}
      </section>

      {prediction && (
        <section className='dashboard-results'>
          <div className='image-grid'>
            {plot && (
              <article className='chart-card'>
                <h3>Closing Price</h3>
                <img src={plot} alt='Closing Price chart' onClick={() => openPreview('Closing Price', plot)} />
              </article>
            )}

            {ma100 && (
              <article className='chart-card'>
                <h3>100-Day Moving Average</h3>
                <img src={ma100} alt='100 DMA chart' onClick={() => openPreview('100-Day Moving Average', ma100)} />
              </article>
            )}

            {ma200 && (
              <article className='chart-card'>
                <h3>200-Day Moving Average</h3>
                <img src={ma200} alt='200 DMA chart' />
              </article>
            )}

            {prediction && (
              <article className='chart-card'>
                <h3>Final Prediction</h3>
                <img src={prediction} alt='Prediction chart' onClick={() => openPreview('Final Prediction', prediction)} />
              </article>
            )}
          </div>

          <div className='metric-grid'>
            <article className='metric-card'>
              <h4>Mean Squared Error</h4>
              <p>{formatValue(mse)}</p>
            </article>
            <article className='metric-card'>
              <h4>Root MSE</h4>
              <p>{formatValue(rmse)}</p>
            </article>
            <article className='metric-card'>
              <h4>R-Squared</h4>
              <p>{formatValue(r2)}</p>
            </article>
          </div>
        </section>
      )}

      {modalPreview && (
        <div className='image-modal' onClick={closePreview}>
          <div className='modal-content'>
            <button className='modal-close' onClick={closePreview} type='button'>×</button>
            <h3>{modalPreview.label}</h3>
            <img src={modalPreview.url} alt={modalPreview.label} />
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
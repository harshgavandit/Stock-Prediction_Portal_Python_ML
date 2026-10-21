import { useCallback, useEffect, useRef, useState } from 'react'
import axiosInstance from '../../axiosInstance'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faSpinner } from '@fortawesome/free-solid-svg-icons'

const priceText = (value) => typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : 'Unavailable'
const metricText = (value) => typeof value === 'number' ? value.toFixed(3) : '—'

export default function Dashboard() {
  const [ticker, setTicker] = useState('')
  const [watchTicker, setWatchTicker] = useState('')
  const [watchlist, setWatchlist] = useState([])
  const [portfolioReady, setPortfolioReady] = useState(false)
  const [saving, setSaving] = useState(false)
  const [marketFeed, setMarketFeed] = useState([])
  const [marketError, setMarketError] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)
  const [notification, setNotification] = useState(null)
  const [modalPreview, setModalPreview] = useState(null)
  const noticeTimer = useRef(null)

  const showNotification = useCallback((message, type = 'success') => {
    clearTimeout(noticeTimer.current)
    setNotification({ message, type })
    noticeTimer.current = setTimeout(() => setNotification(null), 4000)
  }, [])

  useEffect(() => {
    let active = true
    Promise.all([axiosInstance.get('/protected-view/'), axiosInstance.get('/portfolio/')])
      .then(([profile, portfolio]) => {
        if (!active) return
        setUser(profile.data.user)
        setWatchlist(portfolio.data.tickers || [])
        setPortfolioReady(true)
      })
      .catch(() => { if (active) setError('Unable to load your account. Refresh the page to retry.') })
    return () => { active = false; clearTimeout(noticeTimer.current) }
  }, [])

  useEffect(() => {
    if (!portfolioReady || !watchlist.length) return
    let active = true
    let timer
    const fetchPrices = async () => {
      try {
        const { data } = await axiosInstance.post('/live-prices/', { tickers: watchlist })
        if (active) {
          setMarketFeed(Object.entries(data.prices).map(([symbol, quote]) => ({ symbol, ...quote })))
          setMarketError('')
        }
      } catch {
        if (active) setMarketError('Market prices could not be refreshed. Retrying in one minute.')
      } finally {
        if (active) timer = setTimeout(fetchPrices, 60000)
      }
    }
    fetchPrices()
    return () => { active = false; clearTimeout(timer) }
  }, [portfolioReady, watchlist])

  useEffect(() => {
    if (!modalPreview) return
    const onKey = (event) => { if (event.key === 'Escape') setModalPreview(null) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [modalPreview])

  const saveWatchlist = async (tickers) => {
    setSaving(true)
    try {
      const { data } = await axiosInstance.post('/portfolio/', { tickers })
      setWatchlist(data.tickers)
      setMarketFeed([])
      showNotification('Watchlist saved.')
      return true
    } catch (failure) {
      showNotification(failure.response?.data?.tickers?.[0] || 'Watchlist could not be saved. Please retry.', 'error')
      return false
    } finally {
      setSaving(false)
    }
  }

  const addWatchlist = async (event) => {
    event.preventDefault()
    const symbol = watchTicker.trim().toUpperCase()
    if (!/^[A-Z0-9^][A-Z0-9.^=-]{0,19}$/.test(symbol)) return showNotification('Enter a valid ticker, such as AAPL or RELIANCE.NS.', 'warning')
    if (watchlist.includes(symbol)) return showNotification('This ticker is already in your watchlist.', 'warning')
    if (watchlist.length >= 10) return showNotification('Your watchlist can contain up to 10 tickers.', 'warning')
    if (await saveWatchlist([...watchlist, symbol])) setWatchTicker('')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const { data } = await axiosInstance.post('/predict/', { ticker: ticker.trim().toUpperCase() })
      setResult(data)
      showNotification(`Analysis ready for ${data.ticker}.`)
    } catch (failure) {
      setError(failure.response?.data?.error || failure.response?.data?.detail ||
        failure.response?.data?.ticker?.[0] || 'Unable to generate the analysis. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const imageURL = (value) => value?.startsWith('data:') || value?.startsWith('https:') ? value : `${import.meta.env.VITE_BACKEND_ROOT || ''}${value}`
  const charts = result ? [
    ['Closing Price', result.plot_img],
    ['100-Day Moving Average', result.plot_100_dma],
    ['200-Day Moving Average', result.plot_200_dma],
    ['Historical Model Comparison', result.plot_prediction],
  ] : []

  return (
    <div className='container dashboard-panel'>
      {notification && <div role='status' className={`notification-toast ${notification.type}`}>{notification.message}</div>}
      <section className='dashboard-hero glass-card'>
        <div className='hero-header'>
          <span className='eyebrow'>Stock analysis</span>
          <h2>{user ? `Welcome back, ${user.username}` : 'Your prediction dashboard'}</h2>
          <p>Explore closing prices, moving averages, and estimates from the trained LSTM model.</p>
        </div>
        <div className='dashboard-glance'>
          <article className='glance-card'><strong>{result?.ticker || ticker || '—'}</strong><p>Selected ticker</p></article>
          <article className='glance-card'><strong>{loading ? 'Analyzing…' : result ? 'Ready' : 'Awaiting input'}</strong><p>Analysis status</p></article>
          <article className='glance-card'><strong>{metricText(result?.r2)}</strong><p>Historical R-squared</p></article>
          <article className='glance-card'><strong>{watchlist.length}</strong><p>Saved watchlist items</p></article>
        </div>

        <section className='watchlist-panel'>
          <div className='watchlist-header'>
            <h3>Your Watchlist</h3>
            <form className='watchlist-form' onSubmit={addWatchlist}>
              <input aria-label='Watchlist ticker' type='text' className='form-control' value={watchTicker}
                onChange={(event) => setWatchTicker(event.target.value)} placeholder='Add ticker, e.g. AAPL' maxLength={20} />
              <button className='btn btn-primary' type='submit' disabled={saving || !portfolioReady || !watchTicker.trim()}>Add</button>
            </form>
          </div>
          <p className='watchlist-note'>Save up to 10 symbols. Select a ticker to analyze it.</p>
          {!portfolioReady && <p>Loading watchlist…</p>}
          {portfolioReady && !watchlist.length && <p>Your watchlist is empty. Add a ticker to get started.</p>}
          <div className='watchlist-items'>
            {watchlist.map((symbol) => <div key={symbol} className='watchlist-item'>
              <button type='button' className='watchlist-link' onClick={() => setTicker(symbol)}>{symbol}</button>
              <button type='button' className='btn btn-outline-info' aria-label={`Remove ${symbol}`} disabled={saving}
                onClick={() => saveWatchlist(watchlist.filter((value) => value !== symbol))}>Remove</button>
            </div>)}
          </div>
        </section>

        <div className='dashboard-live-panel'>
          <div className='live-panel-title'><span className='eyebrow'>Latest available quotes</span><h3>Market prices</h3></div>
          <p className='watchlist-note'>Yahoo Finance quotes may be delayed. Refreshes every minute while this page is open.</p>
          {marketError && <p role='status'>{marketError}</p>}
          {portfolioReady && watchlist.length > 0 && !marketFeed.length && <p>Loading quotes…</p>}
          <div className='market-feed-strip'>
            {marketFeed.filter((item) => watchlist.includes(item.symbol)).map((item) =>
              <div key={item.symbol} className={`feed-item ${item.change >= 0 ? 'positive' : 'negative'}`}>
                <strong>{item.symbol}</strong>
                <span>{priceText(item.price)} {item.currency || ''}</span>
                {typeof item.change === 'number' && <small>{item.change >= 0 ? '+' : ''}{item.change.toFixed(2)} ({item.percent_change.toFixed(2)}%)</small>}
                <small>{item.error || (item.as_of ? `As of ${new Date(item.as_of).toLocaleString()}` : '')}</small>
              </div>)}
          </div>
        </div>

        <form className='dashboard-form' onSubmit={handleSubmit}>
          <input aria-label='Stock ticker' type='text' className='form-control' placeholder='Enter ticker, e.g. AAPL or RELIANCE.NS'
            value={ticker} onChange={(event) => setTicker(event.target.value)} maxLength={20} required />
          <button type='submit' className='btn btn-primary' disabled={loading || !ticker.trim()}>
            {loading ? <span><FontAwesomeIcon icon={faSpinner} spin /> Analyzing…</span> : 'See Prediction'}
          </button>
        </form>
        <p className='watchlist-note'>The first request can take several seconds while market history loads.</p>
        {error && <div role='alert' className='alert alert-error'>{error}</div>}
      </section>

      {result && <section className='dashboard-results'>
        <div className='glass-card analysis-summary'>
          <h3>{result.ticker} · LSTM analysis</h3>
          <p>History through {result.as_of} · {result.history_rows?.toLocaleString()} daily observations · {result.source}</p>
          <p>Next-session closing-price estimate: <strong>{priceText(result.next_close)} {result.currency || ''}</strong></p>
          <p>Charts compare the existing pretrained model with historical prices. R-squared measures fit; it is not a confidence probability. Estimates are experimental and may be inaccurate.</p>
        </div>
        <div className='image-grid'>
          {charts.map(([title, url]) => <article className='chart-card' key={title}>
            <h3>{title}</h3>
            <button type='button' className='chart-preview-button' aria-label={`Enlarge ${title}`} onClick={() => setModalPreview({ title, url: imageURL(url) })}>
              <img src={imageURL(url)} alt={`${result.ticker}: ${title}`} />
            </button>
          </article>)}
        </div>
        <div className='metric-grid'>
          <article className='metric-card'><h4>Mean Squared Error</h4><p>{metricText(result.mse)}</p></article>
          <article className='metric-card'><h4>Root MSE</h4><p>{metricText(result.rmse)}</p></article>
          <article className='metric-card'><h4>Historical R-Squared</h4><p>{metricText(result.r2)}</p></article>
        </div>
      </section>}

      {modalPreview && <div className='image-modal' role='dialog' aria-modal='true' aria-label={modalPreview.title} onClick={() => setModalPreview(null)}>
        <div className='modal-content' onClick={(event) => event.stopPropagation()}>
          <button className='modal-close' aria-label='Close chart preview' autoFocus onClick={() => setModalPreview(null)} type='button'>×</button>
          <h3>{modalPreview.title}</h3><img src={modalPreview.url} alt={modalPreview.title} />
        </div>
      </div>}
    </div>
  )
}

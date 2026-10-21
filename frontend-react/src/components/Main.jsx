import Button from './Button'

const Main = () => {
  return (
    <div className='container'>
      <section className='hero-panel glass-card'>
        <div className='hero-content'>
          <span className='eyebrow'>Machine Learning Meets Trading</span>
          <h1 className='hero-title'>Explore stock history with machine learning.</h1>
          <p className='hero-copy'>Explore intelligent forecasts powered by an LSTM model, moving average analysis, and a polished dashboard experience. Compare historical prices with model estimates and save the symbols you follow.</p>
          <div className='hero-actions'>
            <Button text='Explore Now' class='btn-info' url='/dashboard' />
          </div>

          <div className='stock-banner'>
            <span>RELIANCE.NS example</span> · LSTM forecasting · 100/200 DMA insights · instant chart review
          </div>

          <div className='ticker-tape'>
            <div className='ticker-track'>
              <span>NSE · RELIANCE.NS</span>
              <span>NSE · HDFCBANK.NS</span>
              <span>NSE · INFY.NS</span>
              <span>NASDAQ · AAPL</span>
              <span>NASDAQ · TSLA</span>
            </div>
          </div>

          <div className='news-carousel glass-card'>
            <p className='news-title'>Explore the model</p>
            <div className='news-list'>
              <span>Choose a supported ticker to load its price history.</span>
              <span>Compare closing prices with 100-day and 200-day moving averages.</span>
              <span>Review historical model error and an experimental next-session estimate.</span>
            </div>
          </div>
        </div>

        <div className='hero-visual'>
          <div className='market-globe'>
            <div className='market-pulse'>
              <strong>RELIANCE.NS</strong>
              <p>Historical analysis and LSTM estimates</p>
            </div>
            <div className='market-ring market-ring-1' />
            <div className='market-ring market-ring-2' />
            <div className='market-ring market-ring-3' />
          </div>
        </div>

        <div className='feature-grid'>
          <article className='feature-card'>
            <h4>Visual analytics</h4>
            <p>See past stock behavior and trend lines with crisp charts built to help you decide faster.</p>
          </article>
          <article className='feature-card'>
            <h4>Intelligent forecasting</h4>
            <p>Compare a trained LSTM model with price history alongside 100-day and 200-day moving averages.</p>
          </article>
          <article className='feature-card'>
            <h4>Secure portal</h4>
            <p>Login or register to keep your prediction flow safe and personalized.</p>
          </article>
        </div>
      </section>
    </div>
  )
}

export default Main
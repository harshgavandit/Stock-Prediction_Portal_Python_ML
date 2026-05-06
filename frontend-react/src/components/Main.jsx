import React from 'react'
import Button from './Button'

const Main = () => {
  return (
    <div className='container'>
      <section className='hero-panel glass-card'>
        <div className='hero-content'>
          <span className='eyebrow'>Machine Learning Meets Trading</span>
          <h1 className='hero-title'>Predict stock movement with modern clarity.</h1>
          <p className='hero-copy'>Explore intelligent forecasts powered by an LSTM model, moving average analysis, and a polished dashboard experience. Get instant insights for ticker symbols and visualize stock behavior in a complete prediction flow.</p>
          <div className='hero-actions'>
            <Button text='Explore Now' class='btn-info' url='/dashboard' />
          </div>

          <div className='stock-banner'>
            <span>RELIANCE.NS example</span> · LSTM forecasting · 100/200 DMA insights · instant chart review
          </div>

          <div className='ticker-tape'>
            <div className='ticker-track'>
              <span>RELIANCE.NS 2.34% ▲</span>
              <span>HDFCBANK.NS 1.19% ▲</span>
              <span>INFY.NS 0.87% ▼</span>
              <span>TATAMOTORS.NS 0.42% ▲</span>
              <span>NIFTY50 0.99% ▲</span>
            </div>
          </div>

          <div className='news-carousel glass-card'>
            <p className='news-title'>Market news</p>
            <div className='news-list'>
              <span>RELIANCE.NS set to lead the next energy rebound.</span>
              <span>Global indices calm ahead of the earnings session.</span>
              <span>AI-driven forecasts now delivering tighter confidence ranges.</span>
            </div>
          </div>
        </div>

        <div className='hero-visual'>
          <div className='market-globe'>
            <div className='market-pulse'>
              <strong>RELIANCE.NS</strong>
              <p>Market-ready forecast engine</p>
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
            <p>Generate 100-day and 200-day moving average predictions from a trained Keras model.</p>
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
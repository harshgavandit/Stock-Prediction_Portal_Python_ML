from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import StockPredictionSerializer
from rest_framework import status
from rest_framework.response import Response
from datetime import datetime
import os
from django.conf import settings
from .utils import save_plot
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score


class StockPredictionAPIView(APIView):
    def post(self, request):
        serializer = StockPredictionSerializer(data=request.data)
        if serializer.is_valid():
            ticker = serializer.validated_data['ticker']
            import yfinance as yf
            import pandas as pd
            import numpy as np
            import matplotlib.pyplot as plt

            # Fetch the data from yfinance
            now = datetime.now()
            start = datetime(now.year-10, now.month, now.day)
            end = now
            try:
                df = yf.download(ticker, start, end)
                if df.empty:
                    # Attempt fallback with Ticker.history when download returns empty
                    ticker_obj = yf.Ticker(ticker)
                    df = ticker_obj.history(start=start, end=end)
            except Exception as exc:
                return Response({
                    "error": "Unable to fetch stock data for the given ticker.",
                    "details": str(exc),
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            if df.empty:
                return Response({
                    "error": "No data found for the given ticker.",
                    "details": "Please verify the ticker symbol and exchange suffix (for example, .NS for NSE).",
                    'status': status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            df = df.reset_index()
            # Generate Basic Plot
            plt.switch_backend('AGG')
            plt.figure(figsize=(20, 8), dpi=150)
            plt.plot(df.Close, label='Closing Price')
            plt.title(f'Closing price of {ticker}')
            plt.xlabel('Days')
            plt.ylabel('Price')
            plt.legend()
            # Save the plot to a file
            plot_img_path = f'{ticker}_plot.png'
            plot_img = save_plot(plot_img_path)
            
            # 100 Days moving average
            ma100 = df.Close.rolling(100).mean()
            plt.switch_backend('AGG')
            plt.figure(figsize=(20, 8), dpi=150)
            plt.plot(df.Close, label='Closing Price')
            plt.plot(ma100, 'r', label='100 DMA')
            plt.title(f'100 Days Moving Average of {ticker}')
            plt.xlabel('Days')
            plt.ylabel('Price')
            plt.legend()
            plot_img_path = f'{ticker}_100_dma.png'
            plot_100_dma = save_plot(plot_img_path)

            # 200 Days moving average
            ma200 = df.Close.rolling(200).mean()
            plt.switch_backend('AGG')
            plt.figure(figsize=(20, 8), dpi=150)
            plt.plot(df.Close, label='Closing Price')
            plt.plot(ma100, 'r', label='100 DMA')
            plt.plot(ma200, 'g', label='200 DMA')
            plt.title(f'200 Days Moving Average of {ticker}')
            plt.xlabel('Days')
            plt.ylabel('Price')
            plt.legend()
            plot_img_path = f'{ticker}_200_dma.png'
            plot_200_dma = save_plot(plot_img_path)

            # Splitting data into Training & Testing datasets
            data_training = pd.DataFrame(df.Close[0:int(len(df)*0.7)])
            data_testing = pd.DataFrame(df.Close[int(len(df)*0.7): int(len(df))])

            # Scaling down the data between 0 and 1
            scaler = MinMaxScaler(feature_range=(0,1))

            # Load ML Model lazily to avoid importing Keras at module import time
            from keras.models import load_model
            model = load_model('stock_prediction_model.keras')

            # Preparing Test Data
            past_100_days = data_training.tail(100)
            final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
            input_data = scaler.fit_transform(final_df)

            x_test = []
            y_test = []
            for i in range(100, input_data.shape[0]):
                x_test.append(input_data[i-100: i])
                y_test.append(input_data[i, 0])
            x_test, y_test = np.array(x_test), np.array(y_test)

            # Making Predictions
            y_predicted = model.predict(x_test)

            # Revert the scaled prices to original price
            y_predicted = scaler.inverse_transform(y_predicted.reshape(-1, 1)).flatten()
            y_test = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()

            # Plot the final prediction
            plt.switch_backend('AGG')
            plt.figure(figsize=(20, 8), dpi=150)
            plt.plot(y_test, 'b', label='Original Price')
            plt.plot(y_predicted, 'r', label='Predicted Price')
            plt.title(f'Final Prediction for {ticker}')
            plt.xlabel('Days')
            plt.ylabel('Price')
            plt.legend()
            plot_img_path = f'{ticker}_final_prediction.png'
            plot_prediction = save_plot(plot_img_path)

            # Model Evaluation
            # Mean Squared Error (MSE)
            mse = mean_squared_error(y_test, y_predicted)

            # Root Mean Squared Error (RMSE)
            rmse = np.sqrt(mse)

            # R-Squared
            r2 = r2_score(y_test, y_predicted)


            return Response({
                'status': 'success',
                'plot_img': plot_img,
                'plot_100_dma': plot_100_dma,
                'plot_200_dma': plot_200_dma,
                'plot_prediction': plot_prediction,
                'mse': mse,
                'rmse': rmse,
                'r2': r2
                })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LivePriceAPIView(APIView):
    """Fetch live prices for multiple tickers."""
    
    def post(self, request):
        """
        Fetch current prices for given tickers.
        Expected POST data: {'tickers': ['RELIANCE.NS', 'TCS.NS']}
        """
        import yfinance as yf
        tickers = request.data.get('tickers', [])
        
        if not tickers or not isinstance(tickers, list):
            return Response({
                'error': 'Please provide a list of tickers.',
                'status': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        prices = {}
        for ticker in tickers:
            try:
                ticker_obj = yf.Ticker(ticker)
                hist = ticker_obj.history(period='1d')
                
                if hist.empty:
                    prices[ticker] = {
                        'price': None,
                        'change': None,
                        'error': 'No data found'
                    }
                else:
                    close_price = hist['Close'].iloc[-1]
                    open_price = hist['Open'].iloc[-1]
                    change = close_price - open_price
                    
                    prices[ticker] = {
                        'price': round(float(close_price), 2),
                        'change': round(float(change), 2),
                        'percent_change': round((change / open_price) * 100, 2) if open_price != 0 else 0
                    }
            except Exception as e:
                prices[ticker] = {
                    'price': None,
                    'change': None,
                    'error': str(e)
                }
        
        return Response({
            'status': 'success',
            'prices': prices
                })
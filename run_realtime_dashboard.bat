@echo off
echo ========================================
echo PharmaChain Real-Time IoT Dashboard
echo ========================================
echo.
echo Starting dashboard on http://localhost:5001
echo.
echo Make sure backend is running on port 8000!
echo.
streamlit run realtime_iot_dashboard.py --server.port 5001

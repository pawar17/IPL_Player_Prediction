#!/bin/bash

# Start FastAPI backend
python app.py &

# Start Streamlit frontend
streamlit run frontend.py --server.port 8501 --server.address 0.0.0.0 
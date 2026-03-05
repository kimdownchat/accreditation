#!/bin/bash

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting MedExam app..."
streamlit run app.py

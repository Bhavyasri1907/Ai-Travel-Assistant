@echo off
title AI Travel Assistant Chatbot (NLP Minor Project)
echo =========================================================================
echo  AI Travel Assistant Chatbot Using Natural Language Processing
echo  Department of Computer Science & Engineering - Aditya University
echo  Team Members: N.Bhavya Sri, T.Lavanya, S.Srihasini
echo =========================================================================
echo.
echo Checking dependencies...
python -m pip install -r requirements.txt
echo.
echo Starting AI Travel Assistant Flask server...
echo Access the website at: http://127.0.0.1:5000
echo.
start "" http://127.0.0.1:5000
python app.py
pause

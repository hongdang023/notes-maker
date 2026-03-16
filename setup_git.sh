#!/bin/bash
git init
echo "venv/" >> .gitignore
echo ".env" >> .gitignore
echo "temp_audio/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "ffmpeg" >> .gitignore
echo "ffprobe" >> .gitignore
echo "history.json" >> .gitignore
echo "streamlit.log" >> .gitignore

echo "streamlit==1.32.0" > requirements.txt
echo "google-generativeai==0.4.1" >> requirements.txt
echo "yt-dlp==2024.03.10" >> requirements.txt
echo "python-dotenv==1.0.1" >> requirements.txt
echo "selenium==4.18.1" >> requirements.txt
echo "selenium-wire==5.1.0" >> requirements.txt
echo "webdriver-manager==4.0.1" >> requirements.txt
echo "selenium-stealth==1.0.6" >> requirements.txt
echo "undetected-chromedriver==3.5.5" >> requirements.txt

echo "ffmpeg" > packages.txt

git add .
git commit -m "Initial commit for Streamlit Cloud deployment"

# Gild Tesoro Casino - Telegram Web App

## Overview
This is a Telegram Casino Web App with multiple games including Mines, Limbo, Keno, Hi-Lo, Crash, Coinflip, Blackjack, Baccarat, Roulette, and Slots.

## Project Status
- Web app is running on port 5000
- All packages installed and configured

## Recent Changes
- December 10, 2025: Fixed mobile sidebar navigation - removed conflicting touchend event handlers that were blocking clicks on mobile devices. Improved CSS z-index and pointer-events for better mobile touch response.

## Architecture
- **Language**: Python 3
- **Framework**: Flask with Gunicorn
- **Frontend**: HTML/CSS/JS with Telegram WebApp integration
- **Dependencies**: flask, gunicorn, aiohttp, python-telegram-bot, sqlalchemy, psycopg2-binary, requests

## File Structure
- `webapp/` - Main web application
  - `app.py` - Flask application
  - `templates/` - HTML templates for all pages
  - `static/css/` - CSS stylesheets
  - `static/js/` - JavaScript files
  - `static/images/` - Game card images and logo

## User Preferences
(To be documented as the user works on the project)

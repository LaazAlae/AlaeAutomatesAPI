#!/usr/bin/env python3
"""
Railway compatibility layer
This file exists solely to satisfy Railway's cached start command: app:app
"""

from main import app

if __name__ == "__main__":
    app.run()
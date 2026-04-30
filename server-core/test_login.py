#!/usr/bin/env python3
"""
Test login endpoint directly
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import httpx

async def test_login():
    """Test login endpoint"""
    login_data = {
        "identifier": "temp_admin@faro.pol",
        "password": "admin123",
        "device_id": "web-test",
        "device_model": "Web Browser",
        "os_version": "Win32",
        "app_version": "2.1.4-web"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                json=login_data,
                timeout=30.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())

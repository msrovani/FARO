#!/usr/bin/env python3
"""
Test CORS and connectivity from browser perspective
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import httpx

async def test_cors():
    """Test CORS headers and connectivity"""
    
    # Test OPTIONS request (CORS preflight)
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint first
            response = await client.get(
                "http://localhost:8000/api/v1/health",
                timeout=10.0
            )
            print(f"Health Status: {response.status_code}")
            print(f"Health Headers: {dict(response.headers)}")
            
            # Test CORS preflight for login
            response = await client.options(
                "http://localhost:8000/api/v1/auth/login",
                headers={
                    "Origin": "http://localhost:3002",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type",
                },
                timeout=10.0
            )
            print(f"CORS Status: {response.status_code}")
            print(f"CORS Headers: {dict(response.headers)}")
            
            # Test actual login
            login_data = {
                "identifier": "temp_admin@faro.pol",
                "password": "admin123",
                "device_id": "web-test",
                "device_model": "Web Browser",
                "os_version": "Win32",
                "app_version": "2.1.4-web"
            }
            
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                json=login_data,
                headers={
                    "Origin": "http://localhost:3002",
                    "Content-Type": "application/json",
                },
                timeout=10.0
            )
            print(f"Login Status: {response.status_code}")
            print(f"Login Headers: {dict(response.headers)}")
            print(f"Login Response: {response.text[:200]}...")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_cors())

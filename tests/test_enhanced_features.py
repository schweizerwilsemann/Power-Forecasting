#!/usr/bin/env python3
"""
Test script for enhanced PV Power Forecasting features
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = BASE_URL

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """Test an API endpoint"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"[ERROR] Unsupported method: {method}")
            return False
            
        if response.status_code == expected_status:
            print(f"[OK] {method} {endpoint} - Status: {response.status_code}")
            return True
        else:
            print(f"[FAIL] {method} {endpoint} - Status: {response.status_code}, Expected: {expected_status}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] {method} {endpoint} - Connection Error (Is the server running?)")
        return False
    except Exception as e:
        print(f"[ERROR] {method} {endpoint} - Error: {str(e)}")
        return False

def test_basic_endpoints():
    """Test basic existing endpoints"""
    print("Testing Basic Endpoints...")
    
    tests = [
        ("GET", "/health"),
        ("GET", "/metrics"),
        ("POST", "/forecast/next", {"horizon": 1, "include_components": False}),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, *data in tests:
        payload = data[0] if data else None
        if test_endpoint(method, endpoint, payload):
            passed += 1
    
    print(f"Basic Endpoints: {passed}/{total} passed\n")
    return passed == total

def test_monitoring_endpoints():
    """Test monitoring endpoints"""
    print("[TEST] Testing Monitoring Endpoints...")
    
    tests = [
        ("GET", "/monitoring/health"),
        ("GET", "/monitoring/performance"),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint in tests:
        if test_endpoint(method, endpoint):
            passed += 1
    
    print(f"Monitoring Endpoints: {passed}/{total} passed\n")
    return passed == total

def test_advanced_forecasting():
    """Test advanced forecasting endpoints"""
    print("[TEST] Testing Advanced Forecasting...")
    
    tests = [
        ("POST", "/forecast/advanced", {
            "horizon": 4,
            "include_confidence": True,
            "ensemble_mode": False
        }),
        ("POST", "/forecast/scenarios", [
            {
                "name": "Optimistic",
                "GHI": 800,
                "temp": 25,
                "clouds_all": 20,
                "wind_speed": 3
            },
            {
                "name": "Realistic", 
                "GHI": 600,
                "temp": 22,
                "clouds_all": 40,
                "wind_speed": 4
            }
        ]),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, data in tests:
        if test_endpoint(method, endpoint, data):
            passed += 1
    
    print(f"Advanced Forecasting: {passed}/{total} passed\n")
    return passed == total

def test_data_quality():
    """Test data quality endpoints"""
    print("[TEST] Testing Data Quality...")
    
    tests = [
        ("GET", "/data/quality"),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint in tests:
        if test_endpoint(method, endpoint):
            passed += 1
    
    print(f"Data Quality: {passed}/{total} passed\n")
    return passed == total

def test_model_management():
    """Test model management endpoints"""
    print("[TEST] Testing Model Management...")
    
    tests = [
        ("GET", "/models/status"),
        ("POST", "/models/retrain"),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint in tests:
        if test_endpoint(method, endpoint):
            passed += 1
    
    print(f"Model Management: {passed}/{total} passed\n")
    return passed == total

def test_historical_analysis():
    """Test historical analysis endpoints"""
    print("[TEST] Testing Historical Analysis...")
    
    tests = [
        ("POST", "/analysis/historical", {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "aggregation": "day",
            "metrics": ["mae", "rmse"]
        }),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, data in tests:
        if test_endpoint(method, endpoint, data):
            passed += 1
    
    print(f"Historical Analysis: {passed}/{total} passed\n")
    return passed == total

def get_system_status():
    """Get overall system status"""
    try:
        response = requests.get(f"{API_BASE}/monitoring/health")
        if response.status_code == 200:
            data = response.json()
            print("[STATS] System Status:")
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Model Loaded: {data.get('model_loaded', False)}")
            print(f"   Database Connected: {data.get('database_connected', False)}")
            print(f"   CPU Usage: {data.get('cpu_usage', 0):.1f}%")
            print(f"   Uptime: {data.get('uptime', 0):.1f} seconds")
            return True
        else:
            print("[ERROR] Could not get system status")
            return False
    except Exception as e:
        print(f"[ERROR] Error getting system status: {e}")
        return False

def main():
    """Run all tests"""
    print("Enhanced PV Power Forecasting - Feature Test")
    print("=" * 50)
    print(f"Testing API at: {API_BASE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("[ERROR] Server is not responding properly")
            return
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to server. Please make sure the backend is running:")
        print("   cd backend && python run.py --reload")
        print("   or from project root: python backend/run.py --reload")
        return
    except Exception as e:
        print(f"[ERROR] Error connecting to server: {e}")
        return
    
    print("[OK] Server is running\n")
    
    # Run tests
    results = []
    
    results.append(("Basic Endpoints", test_basic_endpoints()))
    results.append(("Monitoring", test_monitoring_endpoints()))
    results.append(("Advanced Forecasting", test_advanced_forecasting()))
    results.append(("Data Quality", test_data_quality()))
    results.append(("Model Management", test_model_management()))
    results.append(("Historical Analysis", test_historical_analysis()))
    
    # Get system status
    get_system_status()
    
    # Summary
    print("\n" + "=" * 50)
    print("[SUMMARY] Test Summary:")
    
    passed_tests = 0
    total_tests = len(results)
    
    for test_name, passed in results:
        status = "[OK] PASS" if passed else "[ERROR] FAIL"
        print(f"   {test_name}: {status}")
        if passed:
            passed_tests += 1
    
    print(f"\nOverall: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("[SUCCESS] All tests passed! The enhanced features are working correctly.")
    else:
        print("[WARNING]  Some tests failed. Please check the server logs and configuration.")
    
    print("\n[WEB] Frontend should be available at: http://localhost:5173")
    print("[DOCS] API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()

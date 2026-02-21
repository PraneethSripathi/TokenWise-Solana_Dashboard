#!/usr/bin/env python3
import requests
import json
import sys

# Get the backend URL from frontend/.env
BACKEND_URL = "https://4b2f521a-72bf-4693-8286-b441140c6d8b.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

# Test token address
TOKEN_ADDRESS = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"

# Test wallet address (a known Solana wallet with transactions)
TEST_WALLET = "DYw8jMTrZqRbV3VgM4SxFPYx6HNbBEdxmFVLFBJZYPg"

def test_api_health():
    """Test the basic API health endpoint"""
    print("\n=== Testing API Health Check ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_token_holders():
    """Test the token holders discovery endpoint"""
    print("\n=== Testing Token Holder Discovery ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/token-holders/{TOKEN_ADDRESS}")
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Holder Count: {len(data.get('holders', []))}")
            if data.get('holders') and len(data.get('holders')) > 0:
                print(f"First Holder: {data['holders'][0]}")
        else:
            print(f"Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_wallet_tracking():
    """Test the wallet tracking endpoint"""
    print("\n=== Testing Wallet Tracking ===")
    
    try:
        # Data for tracking a wallet
        wallet_data = {
            "address": TEST_WALLET
        }
        
        response = requests.post(
            f"{API_BASE_URL}/wallets/track", 
            json=wallet_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Now test getting tracked wallets
        tracked_response = requests.get(f"{API_BASE_URL}/wallets/tracked")
        
        print(f"Tracked Wallets Status Code: {tracked_response.status_code}")
        if tracked_response.status_code == 200:
            tracked_data = tracked_response.json()
            print(f"Tracked Wallets Count: {len(tracked_data.get('wallets', []))}")
        
        return response.status_code == 200 and tracked_response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_wallet_transactions():
    """Test the wallet transactions endpoint"""
    print("\n=== Testing Transaction Monitoring ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/transactions/{TEST_WALLET}")
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Transaction Count: {len(data.get('transactions', []))}")
            if data.get('transactions') and len(data.get('transactions')) > 0:
                print(f"First Transaction: {data['transactions'][0]}")
        else:
            print(f"Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_protocol_detection():
    """Test the protocol detection endpoint"""
    print("\n=== Testing Protocol Detection ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/protocols/{TEST_WALLET}")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_dashboard_analytics():
    """Test the dashboard analytics endpoint"""
    print("\n=== Testing Dashboard Analytics ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/dashboard")
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total Wallets: {data.get('total_wallets')}")
            print(f"Total Transactions: {data.get('total_transactions')}")
            print(f"Recent Transactions Count: {len(data.get('recent_transactions', []))}")
        else:
            print(f"Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_token_insights():
    """Test the token insights endpoint"""
    print("\n=== Testing Token Insights ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/insights/token/{TOKEN_ADDRESS}")
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total Holders: {data.get('total_holders')}")
            print(f"Total Supply: {data.get('total_supply')}")
            print(f"Top Holders Count: {len(data.get('top_holders', []))}")
        else:
            print(f"Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    print(f"Starting TokenWise Solana Backend Tests")
    print(f"Backend URL: {API_BASE_URL}")
    print(f"Test Token Address: {TOKEN_ADDRESS}")
    print(f"Test Wallet Address: {TEST_WALLET}")
    
    results = {}
    
    # Test 1: API Health Check
    results["API Health Check"] = test_api_health()
    
    # Test 2: Token Holder Discovery
    results["Token Holder Discovery"] = test_token_holders()
    
    # Test 3: Wallet Tracking
    results["Wallet Tracking"] = test_wallet_tracking()
    
    # Test 4: Transaction Monitoring
    results["Transaction Monitoring"] = test_wallet_transactions()
    
    # Test 5: Protocol Detection
    results["Protocol Detection"] = test_protocol_detection()
    
    # Test 6: Dashboard Analytics
    results["Dashboard Analytics"] = test_dashboard_analytics()
    
    # Test 7: Token Insights
    results["Token Insights"] = test_token_insights()
    
    # Print summary
    print("\n=== TEST RESULTS SUMMARY ===")
    
    all_passed = True
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print(f"\nOVERALL STATUS: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
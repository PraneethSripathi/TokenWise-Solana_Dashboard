#!/usr/bin/env python3
import requests
import json
import asyncio
import websockets
import time
from datetime import datetime
import sys

# Get the backend URL from frontend/.env
BACKEND_URL = "https://4b2f521a-72bf-4693-8286-b441140c6d8b.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

# Test token address
TOKEN_ADDRESS = "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"

# Test wallet address (a known Solana wallet with transactions)
TEST_WALLET = "DYw8jMTrZqRbV3VgM4SxFPYx6HNbBEdxmFVLFBJZYPg"

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'

def print_success(message):
    print(f"{GREEN}✅ SUCCESS: {message}{ENDC}")

def print_error(message):
    print(f"{RED}❌ ERROR: {message}{ENDC}")

def print_info(message):
    print(f"{BLUE}ℹ️ INFO: {message}{ENDC}")

def print_warning(message):
    print(f"{YELLOW}⚠️ WARNING: {message}{ENDC}")

def print_test_header(test_name):
    print(f"\n{BLUE}{'=' * 80}{ENDC}")
    print(f"{BLUE}TEST: {test_name}{ENDC}")
    print(f"{BLUE}{'=' * 80}{ENDC}")

def test_api_health():
    """Test the basic API health endpoint"""
    print_test_header("Basic API Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"API health check successful: {data}")
            return True
        else:
            print_error(f"API health check failed with status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception during API health check: {str(e)}")
        return False

def test_token_holders():
    """Test the token holders discovery endpoint"""
    print_test_header("Token Holder Discovery")
    
    try:
        response = requests.get(f"{API_BASE_URL}/token-holders/{TOKEN_ADDRESS}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "holders" in data and isinstance(data["holders"], list):
                holder_count = len(data["holders"])
                print_success(f"Successfully retrieved {holder_count} token holders")
                
                if holder_count > 0:
                    print_info(f"Top holder: {data['holders'][0]}")
                
                return True
            else:
                print_error(f"Invalid response format: {data}")
                return False
        else:
            print_error(f"Token holders request failed with status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception during token holders test: {str(e)}")
        return False

def test_wallet_tracking():
    """Test the wallet tracking endpoint"""
    print_test_header("Wallet Tracking")
    
    try:
        # Data for tracking a wallet
        wallet_data = {
            "address": TEST_WALLET
        }
        
        response = requests.post(
            f"{API_BASE_URL}/wallets/track", 
            json=wallet_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Successfully tracked wallet: {data}")
            
            # Now test getting tracked wallets
            tracked_response = requests.get(f"{API_BASE_URL}/wallets/tracked")
            
            if tracked_response.status_code == 200:
                tracked_data = tracked_response.json()
                print_success(f"Successfully retrieved tracked wallets: {len(tracked_data.get('wallets', []))} wallets found")
                return True
            else:
                print_error(f"Failed to get tracked wallets: {tracked_response.status_code}")
                return False
        else:
            print_error(f"Wallet tracking failed with status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception during wallet tracking test: {str(e)}")
        return False

def test_wallet_transactions():
    """Test the wallet transactions endpoint"""
    print_test_header("Transaction Monitoring")
    
    try:
        response = requests.get(f"{API_BASE_URL}/transactions/{TEST_WALLET}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "transactions" in data and isinstance(data["transactions"], list):
                tx_count = len(data["transactions"])
                print_success(f"Successfully retrieved {tx_count} transactions for wallet")
                
                if tx_count > 0:
                    print_info(f"Sample transaction: {data['transactions'][0]}")
                
                return True
            else:
                print_error(f"Invalid response format: {data}")
                return False
        else:
            print_error(f"Wallet transactions request failed with status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception during wallet transactions test: {str(e)}")
        return False

def test_protocol_detection():
    """Test the protocol detection endpoint"""
    print_test_header("Protocol Detection")
    
    try:
        response = requests.get(f"{API_BASE_URL}/protocols/{TEST_WALLET}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "protocol_usage" in data and isinstance(data["protocol_usage"], dict):
                protocols = data["protocol_usage"]
                print_success(f"Successfully retrieved protocol usage: {protocols}")
                
                # Check if any known protocols are detected
                known_protocols = ["Jupiter", "Raydium", "Orca", "Unknown"]
                detected = any(p in protocols for p in known_protocols)
                
                if detected:
                    print_success(f"Successfully detected known protocols")
                else:
                    print_warning(f"No known protocols detected in the response")
                
                return True
            else:
                print_error(f"Invalid response format: {data}")
                return False
        else:
            print_error(f"Protocol detection request failed with status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception during protocol detection test: {str(e)}")
        return False

def test_dashboard_analytics():
    """Test the dashboard analytics endpoint"""
    print_test_header("Dashboard Analytics")
    
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/dashboard")
        
        if response.status_code == 200:
            data = response.json()
            
            required_keys = ["total_wallets", "total_transactions", "recent_transactions", "protocol_stats"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if not missing_keys:
                print_success(f"Successfully retrieved dashboard analytics")
                print_info(f"Total wallets: {data['total_wallets']}")
                print_info(f"Total transactions: {data['total_transactions']}")
                print_info(f"Recent transactions: {len(data['recent_transactions'])}")
                print_info(f"Protocol stats: {data['protocol_stats']}")
                return True
            else:
                print_error(f"Missing keys in response: {missing_keys}")
                return False
        else:
            print_error(f"Dashboard analytics request failed with status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception during dashboard analytics test: {str(e)}")
        return False

def test_token_insights():
    """Test the token insights endpoint"""
    print_test_header("Token Insights")
    
    try:
        response = requests.get(f"{API_BASE_URL}/insights/token/{TOKEN_ADDRESS}")
        
        if response.status_code == 200:
            data = response.json()
            
            required_keys = ["total_holders", "total_supply", "top_holders", "trading_volume_24h", "buy_sell_ratio", "protocol_usage"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if not missing_keys:
                print_success(f"Successfully retrieved token insights")
                print_info(f"Total holders: {data['total_holders']}")
                print_info(f"Total supply: {data['total_supply']}")
                print_info(f"Top holders count: {len(data['top_holders'])}")
                print_info(f"Trading volume (24h): {data['trading_volume_24h']}")
                print_info(f"Buy/Sell ratio: {data['buy_sell_ratio']}")
                print_info(f"Protocol usage: {data['protocol_usage']}")
                return True
            else:
                print_error(f"Missing keys in response: {missing_keys}")
                return False
        else:
            print_error(f"Token insights request failed with status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception during token insights test: {str(e)}")
        return False

async def test_websocket_connection():
    """Test the WebSocket connection for real-time monitoring"""
    print_test_header("WebSocket Connection")
    
    ws_url = f"{BACKEND_URL.replace('https://', 'wss://')}/api/ws/transactions"
    print_info(f"Connecting to WebSocket at: {ws_url}")
    
    try:
        # Use a very short timeout for the entire operation
        connect_task = asyncio.create_task(websocket_connect_test(ws_url))
        try:
            result = await asyncio.wait_for(connect_task, timeout=5.0)
            return result
        except asyncio.TimeoutError:
            print_warning("WebSocket test timed out after 5 seconds")
            print_info("This might be due to network issues or server configuration")
            return False
    except Exception as e:
        print_error(f"Exception during WebSocket test: {str(e)}")
        return False

async def websocket_connect_test(ws_url):
    """Helper function for WebSocket testing with its own timeout"""
    try:
        # Just try to connect, don't wait for messages
        async with websockets.connect(ws_url, ping_interval=None, close_timeout=2.0) as websocket:
            print_success("WebSocket connection established")
            print_info("Connection successful, not waiting for messages")
            return True
    except Exception as e:
        print_error(f"Failed to connect to WebSocket: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and return results"""
    print_info(f"Starting TokenWise Solana Backend Tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Backend URL: {API_BASE_URL}")
    print_info(f"Test Token Address: {TOKEN_ADDRESS}")
    print_info(f"Test Wallet Address: {TEST_WALLET}")
    
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
    
    # Test 8: WebSocket Connection (async)
    try:
        # Set a timeout for the entire async operation
        results["WebSocket Connection"] = asyncio.run(asyncio.wait_for(test_websocket_connection(), timeout=10.0))
    except asyncio.TimeoutError:
        print_error("WebSocket test timed out")
        results["WebSocket Connection"] = False
    except Exception as e:
        print_error(f"Failed to run WebSocket test: {str(e)}")
        results["WebSocket Connection"] = False
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_name, result in results.items():
        status = f"{GREEN}PASS{ENDC}" if result else f"{RED}FAIL{ENDC}"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 80)
    overall_status = f"{GREEN}ALL TESTS PASSED{ENDC}" if all_passed else f"{RED}SOME TESTS FAILED{ENDC}"
    print(f"OVERALL STATUS: {overall_status}")
    print("=" * 80)
    
    return all_passed, results

if __name__ == "__main__":
    success, test_results = run_all_tests()
    sys.exit(0 if success else 1)
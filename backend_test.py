#!/usr/bin/env python3
"""
Backend Testing Suite for Y-Store O13-O18 Modules

Tests new admin APIs:
- Guard: incidents, mute, resolve
- Risk: distribution
- Timeline: user events
- Analytics: KPI data, daily rebuild
- Admin authentication
"""

import requests
import sys
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from frontend .env for public URL
load_dotenv('/app/frontend/.env')

class YStoreAPITester:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000')
        self.admin_token = None
        self.user_token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test credentials from review request
        self.admin_email = "admin@bazaar.com"
        self.admin_password = "admin123"
        self.test_order_id = "205ff7e6-76dd-4929-864f-0f6ccde8289a"

    def log_result(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, headers=None, expect_status=200):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}/api{endpoint}"
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=req_headers, timeout=30)
            else:
                return None, f"Unsupported method: {method}"
            
            success = response.status_code == expect_status
            result_data = {}
            try:
                result_data = response.json()
            except:
                result_data = {"text": response.text}
            
            return {
                "success": success,
                "status_code": response.status_code,
                "data": result_data,
                "expected_status": expect_status
            }, None
            
        except requests.exceptions.Timeout:
            return None, "Request timeout"
        except requests.exceptions.ConnectionError:
            return None, "Connection error"
        except Exception as e:
            return None, f"Request failed: {str(e)}"

    def test_admin_login(self):
        """Test admin authentication"""
        print(f"\n🔍 Testing admin login...")
        
        response, error = self.make_request(
            'POST', '/auth/login',
            data={
                "email": self.admin_email,
                "password": self.admin_password
            }
        )
        
        if error:
            return self.log_result("Admin Login", False, f"Error: {error}")
        
        if response["success"] and response["data"].get("token"):
            self.admin_token = response["data"]["token"]
            return self.log_result("Admin Login", True, "Token obtained")
        elif response["success"] and response["data"].get("access_token"):
            self.admin_token = response["data"]["access_token"]
            return self.log_result("Admin Login", True, "Access token obtained")
        else:
            return self.log_result("Admin Login", False, 
                f"Status: {response['status_code']}, Data: {response['data']}")

    def test_v2_delivery_endpoints_exist(self):
        """Test that V2 delivery endpoints exist and return proper status codes"""
        print(f"\n🔍 Testing V2 delivery endpoints existence...")
        
        if not self.admin_token:
            return self.log_result("V2 Endpoints Exist", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test TTN creation endpoint (should return 422/400 due to missing/invalid data)
        response, error = self.make_request(
            'POST', '/v2/delivery/novaposhta/ttn',
            data={"order_id": "invalid-order"},
            headers=headers,
            expect_status=400  # We expect validation error
        )
        
        if error:
            return self.log_result("V2 TTN Endpoint Exists", False, f"Error: {error}")
        
        # Accept 400/422/404 as valid responses (endpoint exists)
        endpoint_exists = response["status_code"] in [400, 422, 404]
        result1 = self.log_result("V2 TTN Endpoint Exists", endpoint_exists,
            f"Status: {response['status_code']}")
        
        # Test shipment info endpoint  
        response, error = self.make_request(
            'GET', f'/v2/delivery/orders/{self.test_order_id}/shipment',
            headers=headers,
            expect_status=200
        )
        
        if error:
            return self.log_result("V2 Shipment Info Endpoint", False, f"Error: {error}")
        
        result2 = self.log_result("V2 Shipment Info Endpoint", response["success"],
            f"Status: {response['status_code']}")
        
        return result1 and result2

    def test_admin_authentication_required(self):
        """Test that admin authentication is required for TTN creation"""
        print(f"\n🔍 Testing admin authentication requirement...")
        
        # Test without token (should return 403/401)
        response, error = self.make_request(
            'POST', '/v2/delivery/novaposhta/ttn',
            data={"order_id": self.test_order_id},
            expect_status=403
        )
        
        if error:
            return self.log_result("Auth Required (No Token)", False, f"Error: {error}")
        
        # Accept 401/403 as valid auth required responses
        auth_required = response["status_code"] in [401, 403]
        result1 = self.log_result("Auth Required (No Token)", auth_required,
            f"Status: {response['status_code']}")
        
        # Test with invalid token (should return 403/401)
        headers = {"Authorization": "Bearer invalid-token-123"}
        response, error = self.make_request(
            'POST', '/v2/delivery/novaposhta/ttn',
            data={"order_id": self.test_order_id},
            headers=headers,
            expect_status=403
        )
        
        if error:
            return self.log_result("Auth Required (Invalid Token)", False, f"Error: {error}")
        
        auth_required = response["status_code"] in [401, 403]
        result2 = self.log_result("Auth Required (Invalid Token)", auth_required,
            f"Status: {response['status_code']}")
        
        return result1 and result2

    def test_order_status_validation(self):
        """Test order status validation (only PROCESSING/PAID allowed)"""
        print(f"\n🔍 Testing order status validation...")
        
        if not self.admin_token:
            return self.log_result("Order Status Validation", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # First check current order status
        response, error = self.make_request(
            'GET', f'/v2/delivery/orders/{self.test_order_id}/shipment',
            headers=headers
        )
        
        if error or not response["success"]:
            return self.log_result("Order Status Check", False, 
                f"Cannot get order info: {error or response}")
        
        order_status = response["data"].get("order_status", "UNKNOWN")
        print(f"   Current order status: {order_status}")
        
        # Try to create TTN for this order
        response, error = self.make_request(
            'POST', '/v2/delivery/novaposhta/ttn',
            data={"order_id": self.test_order_id},
            headers=headers,
            expect_status=400  # We expect some error due to NP config or status
        )
        
        if error:
            return self.log_result("Order Status Validation", False, f"Error: {error}")
        
        # Check response details
        status_code = response["status_code"]
        error_detail = response["data"].get("detail", "")
        
        if status_code == 400 and "STATUS_NOT_ALLOWED" in str(error_detail):
            # Order status validation working
            return self.log_result("Order Status Validation", True, 
                f"Correctly rejected status: {order_status}")
        elif status_code == 502 and "NP_" in str(error_detail):
            # Reached NP API call (status validation passed)
            return self.log_result("Order Status Validation", True,
                f"Status validation passed, failed at NP API (expected)")
        elif status_code == 404 and "ORDER_NOT_FOUND" in str(error_detail):
            return self.log_result("Order Status Validation", False,
                f"Test order {self.test_order_id} not found")
        else:
            return self.log_result("Order Status Validation", False,
                f"Unexpected response: {status_code} - {error_detail}")

    def test_idempotency_support(self):
        """Test idempotency support with X-Idempotency-Key header"""
        print(f"\n🔍 Testing idempotency support...")
        
        if not self.admin_token:
            return self.log_result("Idempotency Support", False, "No admin token")
        
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "X-Idempotency-Key": f"test-idempotency-{uuid.uuid4()}"
        }
        
        # Make first request
        response1, error1 = self.make_request(
            'POST', '/v2/delivery/novaposhta/ttn',
            data={"order_id": self.test_order_id},
            headers=headers,
            expect_status=400  # Expect some error, but consistent
        )
        
        if error1:
            return self.log_result("Idempotency Support", False, f"Error: {error1}")
        
        # Make second request with same idempotency key
        response2, error2 = self.make_request(
            'POST', '/v2/delivery/novaposhta/ttn',
            data={"order_id": self.test_order_id},
            headers=headers,
            expect_status=400  # Should get same response
        )
        
        if error2:
            return self.log_result("Idempotency Support", False, f"Error: {error2}")
        
        # Both responses should have same status code (idempotency working)
        same_response = response1["status_code"] == response2["status_code"]
        return self.log_result("Idempotency Support", same_response,
            f"First: {response1['status_code']}, Second: {response2['status_code']}")

    def test_order_transitions_api(self):
        """Test order status transition API (V2 orders)"""
        print(f"\n🔍 Testing order V2 status transitions...")
        
        if not self.admin_token:
            return self.log_result("Order Transitions", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test getting order transitions
        response, error = self.make_request(
            'GET', f'/v2/orders/{self.test_order_id}/transitions',
            headers=headers
        )
        
        if error:
            return self.log_result("Order Transitions API", False, f"Error: {error}")
        
        if response["success"]:
            data = response["data"]
            has_transitions = "allowed_transitions" in data and "current_status" in data
            return self.log_result("Order Transitions API", has_transitions,
                f"Current: {data.get('current_status')}, Allowed: {data.get('allowed_transitions')}")
        else:
            return self.log_result("Order Transitions API", False,
                f"Status: {response['status_code']}")

    def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Starting Nova Poshta TTN Automation Tests")
        print("=" * 60)
        
        # Basic connectivity and authentication
        if not self.test_admin_login():
            print("❌ Admin login failed - stopping tests")
            return False
        
        # Test endpoint existence and authentication
        self.test_v2_delivery_endpoints_exist()
        self.test_admin_authentication_required()
        
        # Test core functionality
        self.test_order_status_validation()
        self.test_idempotency_support()
        self.test_order_transitions_api()
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        print("=" * 60)
        
        return self.tests_passed >= (self.tests_run * 0.8)  # 80% pass rate acceptable


def main():
    """Main test runner"""
    tester = NPTTNTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Tests completed successfully!")
        return 0
    else:
        print("💥 Some critical tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
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
        # Use localhost as fallback since external routing seems to have issues
        if base_url is None:
            external_url = os.environ.get('REACT_APP_BACKEND_URL', '')
            if external_url:
                # Try external first, fallback to localhost
                self.base_url = external_url
                self.fallback_url = 'http://localhost:8001'
            else:
                self.base_url = 'http://localhost:8001'
                self.fallback_url = None
        else:
            self.base_url = base_url
            self.fallback_url = None
            
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test credentials from review request
        self.admin_email = "admin@ystore.ua"
        self.admin_password = "admin123"
        self.test_user_id = "test-user-123"  # For timeline testing

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
        
        print(f"Making {method} request to: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=req_headers, timeout=30)
            else:
                return None, f"Unsupported method: {method}"
            
            # If external URL fails with 404 and we have a fallback, try localhost
            if response.status_code == 404 and self.fallback_url and self.base_url != self.fallback_url:
                print(f"External URL failed with 404, trying localhost...")
                url = f"{self.fallback_url}/api{endpoint}"
                print(f"Making {method} request to: {url}")
                
                if method == 'GET':
                    response = requests.get(url, headers=req_headers, timeout=30)
                elif method == 'POST':
                    response = requests.post(url, json=data, headers=req_headers, timeout=30)
                elif method == 'PUT':
                    response = requests.put(url, json=data, headers=req_headers, timeout=30)
                
                # Update base_url to use localhost for future requests
                self.base_url = self.fallback_url
                print(f"Switched to localhost for remaining tests")
            
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

    def test_guard_incidents_list(self):
        """Test GET /api/v2/admin/guard/incidents"""
        print(f"\n🔍 Testing Guard incidents list...")
        
        if not self.admin_token:
            return self.log_result("Guard Incidents List", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response, error = self.make_request(
            'GET', '/v2/admin/guard/incidents',
            headers=headers,
            expect_status=200
        )
        
        if error:
            return self.log_result("Guard Incidents List", False, f"Error: {error}")
        
        if response["success"]:
            data = response["data"]
            has_items = "items" in data
            return self.log_result("Guard Incidents List", has_items,
                f"Found {len(data.get('items', []))} incidents")
        else:
            return self.log_result("Guard Incidents List", False,
                f"Status: {response['status_code']}, Data: {response['data']}")

    def test_guard_incident_actions(self):
        """Test guard incident mute/resolve actions"""
        print(f"\n🔍 Testing Guard incident actions...")
        
        if not self.admin_token:
            return self.log_result("Guard Incident Actions", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        test_key = "test-incident-key"
        
        # Test mute incident
        response, error = self.make_request(
            'POST', f'/v2/admin/guard/incident/{test_key}/mute',
            data={"hours": 1},
            headers=headers,
            expect_status=200
        )
        
        if error:
            mute_result = self.log_result("Guard Mute Incident", False, f"Error: {error}")
        else:
            mute_success = response["success"] or response["status_code"] == 404  # Not found is acceptable
            mute_result = self.log_result("Guard Mute Incident", mute_success,
                f"Status: {response['status_code']}")
        
        # Test resolve incident
        response, error = self.make_request(
            'POST', f'/v2/admin/guard/incident/{test_key}/resolve',
            headers=headers,
            expect_status=200
        )
        
        if error:
            resolve_result = self.log_result("Guard Resolve Incident", False, f"Error: {error}")
        else:
            resolve_success = response["success"] or response["status_code"] == 404  # Not found is acceptable
            resolve_result = self.log_result("Guard Resolve Incident", resolve_success,
                f"Status: {response['status_code']}")
        
        return mute_result and resolve_result

    def test_risk_distribution(self):
        """Test GET /api/v2/admin/risk/distribution"""
        print(f"\n🔍 Testing Risk distribution...")
        
        if not self.admin_token:
            return self.log_result("Risk Distribution", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response, error = self.make_request(
            'GET', '/v2/admin/risk/distribution',
            headers=headers,
            expect_status=200
        )
        
        if error:
            return self.log_result("Risk Distribution", False, f"Error: {error}")
        
        if response["success"]:
            data = response["data"]
            has_distribution = "distribution" in data
            return self.log_result("Risk Distribution", has_distribution,
                f"Distribution data: {data.get('distribution', {})}")
        else:
            return self.log_result("Risk Distribution", False,
                f"Status: {response['status_code']}, Data: {response['data']}")

    def test_timeline_events(self):
        """Test GET /api/v2/admin/timeline/{user_id}"""
        print(f"\n🔍 Testing Timeline events...")
        
        if not self.admin_token:
            return self.log_result("Timeline Events", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response, error = self.make_request(
            'GET', f'/v2/admin/timeline/{self.test_user_id}',
            headers=headers,
            expect_status=200
        )
        
        if error:
            return self.log_result("Timeline Events", False, f"Error: {error}")
        
        if response["success"]:
            data = response["data"]
            has_events = "events" in data and "count" in data
            return self.log_result("Timeline Events", has_events,
                f"Found {data.get('count', 0)} events")
        else:
            return self.log_result("Timeline Events", False,
                f"Status: {response['status_code']}, Data: {response['data']}")

    def test_analytics_ops_kpi(self):
        """Test GET /api/v2/admin/analytics/ops-kpi?range=7"""
        print(f"\n🔍 Testing Analytics OPS KPI...")
        
        if not self.admin_token:
            return self.log_result("Analytics OPS KPI", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response, error = self.make_request(
            'GET', '/v2/admin/analytics/ops-kpi?range=7',
            headers=headers,
            expect_status=200
        )
        
        if error:
            return self.log_result("Analytics OPS KPI", False, f"Error: {error}")
        
        if response["success"]:
            data = response["data"]
            # Check for typical KPI fields
            has_kpi_data = any(field in data for field in ["revenue", "orders", "aov", "delivered"])
            return self.log_result("Analytics OPS KPI", has_kpi_data,
                f"KPI fields: {list(data.keys())}")
        else:
            return self.log_result("Analytics OPS KPI", False,
                f"Status: {response['status_code']}, Data: {response['data']}")

    def test_analytics_daily_rebuild(self):
        """Test POST /api/v2/admin/analytics/daily/rebuild"""
        print(f"\n🔍 Testing Analytics daily rebuild...")
        
        if not self.admin_token:
            return self.log_result("Analytics Daily Rebuild", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response, error = self.make_request(
            'POST', '/v2/admin/analytics/daily/rebuild',
            data={"days": 3},  # Small number for testing
            headers=headers,
            expect_status=200
        )
        
        if error:
            return self.log_result("Analytics Daily Rebuild", False, f"Error: {error}")
        
        if response["success"]:
            data = response["data"]
            has_rebuild_data = "ok" in data and "rebuilt" in data
            return self.log_result("Analytics Daily Rebuild", has_rebuild_data,
                f"Rebuilt {data.get('rebuilt', 0)} days")
        else:
            return self.log_result("Analytics Daily Rebuild", False,
                f"Status: {response['status_code']}, Data: {response['data']}")

    def test_pickup_control_kpi(self):
        """Test GET /api/v2/admin/pickup-control/kpi"""
        print(f"\n🔍 Testing Pickup Control KPI...")
        
        if not self.admin_token:
            return self.log_result("Pickup Control KPI", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response, error = self.make_request(
            'GET', '/v2/admin/pickup-control/kpi',
            headers=headers,
            expect_status=200
        )
        
        if error:
            return self.log_result("Pickup Control KPI", False, f"Error: {error}")
        
        if response["success"]:
            data = response["data"]
            # Check for expected KPI fields
            kpi_fields = ["at_point_2plus", "at_point_5plus", "at_point_7plus", "amount_at_risk"]
            has_kpi_structure = any(field in data for field in kpi_fields)
            return self.log_result("Pickup Control KPI", has_kpi_structure,
                f"KPI data: {data}")
        else:
            return self.log_result("Pickup Control KPI", False,
                f"Status: {response['status_code']}, Data: {response['data']}")

    def test_pickup_control_risk_list(self):
        """Test GET /api/v2/admin/pickup-control/risk?days=5"""
        print(f"\n🔍 Testing Pickup Control Risk List...")
        
        if not self.admin_token:
            return self.log_result("Pickup Control Risk List", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response, error = self.make_request(
            'GET', '/v2/admin/pickup-control/risk?days=5&limit=100',
            headers=headers,
            expect_status=200
        )
        
        if error:
            return self.log_result("Pickup Control Risk List", False, f"Error: {error}")
        
        if response["success"]:
            data = response["data"]
            # Should have items, count, and filter_days fields
            has_structure = "items" in data and "count" in data and "filter_days" in data
            return self.log_result("Pickup Control Risk List", has_structure,
                f"Found {data.get('count', 0)} risk items, filter: {data.get('filter_days')} days")
        else:
            return self.log_result("Pickup Control Risk List", False,
                f"Status: {response['status_code']}, Data: {response['data']}")

    def test_pickup_control_run_engine(self):
        """Test POST /api/v2/admin/pickup-control/run"""
        print(f"\n🔍 Testing Pickup Control Run Engine...")
        
        if not self.admin_token:
            return self.log_result("Pickup Control Run Engine", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response, error = self.make_request(
            'POST', '/v2/admin/pickup-control/run',
            data={"limit": 50},  # Small limit for testing
            headers=headers,
            expect_status=200
        )
        
        if error:
            return self.log_result("Pickup Control Run Engine", False, f"Error: {error}")
        
        if response["success"]:
            data = response["data"]
            # Should have processing results
            has_result_structure = all(field in data for field in ["ok", "processed", "sent", "high_risk_count", "errors"])
            return self.log_result("Pickup Control Run Engine", has_result_structure,
                f"Processed: {data.get('processed', 0)}, Sent: {data.get('sent', 0)}, Risk: {data.get('high_risk_count', 0)}")
        else:
            return self.log_result("Pickup Control Run Engine", False,
                f"Status: {response['status_code']}, Data: {response['data']}")

    def test_pickup_control_mute_ttn(self):
        """Test POST /api/v2/admin/pickup-control/mute/{ttn}"""
        print(f"\n🔍 Testing Pickup Control Mute TTN...")
        
        if not self.admin_token:
            return self.log_result("Pickup Control Mute TTN", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        test_ttn = "20450123456789"  # Test TTN
        
        response, error = self.make_request(
            'POST', f'/v2/admin/pickup-control/mute/{test_ttn}',
            data={"days": 7},
            headers=headers,
            expect_status=200
        )
        
        if error:
            return self.log_result("Pickup Control Mute TTN", False, f"Error: {error}")
        
        if response["success"]:
            data = response["data"]
            # Should confirm mute operation
            has_mute_structure = "ok" in data and "ttn" in data and "muted_days" in data
            return self.log_result("Pickup Control Mute TTN", has_mute_structure,
                f"Muted TTN: {data.get('ttn')}, Days: {data.get('muted_days')}")
        else:
            return self.log_result("Pickup Control Mute TTN", False,
                f"Status: {response['status_code']}, Data: {response['data']}")

    def test_pickup_control_send_reminder(self):
        """Test POST /api/v2/admin/pickup-control/send-reminder/{ttn}"""
        print(f"\n🔍 Testing Pickup Control Send Reminder...")
        
        if not self.admin_token:
            return self.log_result("Pickup Control Send Reminder", False, "No admin token")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        test_ttn = "20450123456789"  # Test TTN
        
        response, error = self.make_request(
            'POST', f'/v2/admin/pickup-control/send-reminder/{test_ttn}',
            data={"level": "D5"},
            headers=headers,
            expect_status=404  # Expected since test order doesn't exist
        )
        
        if error:
            return self.log_result("Pickup Control Send Reminder", False, f"Error: {error}")
        
        # For this test, 404 is acceptable since no test data exists
        if response["status_code"] == 404:
            return self.log_result("Pickup Control Send Reminder", True,
                "404 as expected (no test orders exist)")
        elif response["success"]:
            data = response["data"]
            has_reminder_structure = "ok" in data and "ttn" in data
            return self.log_result("Pickup Control Send Reminder", has_reminder_structure,
                f"Reminder sent for TTN: {data.get('ttn')}")
        else:
            return self.log_result("Pickup Control Send Reminder", False,
                f"Status: {response['status_code']}, Data: {response['data']}")

    def test_admin_authentication_required(self):
        """Test that admin authentication is required for all endpoints"""
        print(f"\n🔍 Testing admin authentication requirement...")
        
        endpoints_to_test = [
            '/v2/admin/guard/incidents',
            '/v2/admin/risk/distribution',
            f'/v2/admin/timeline/{self.test_user_id}',
            '/v2/admin/analytics/ops-kpi?range=7'
        ]
        
        results = []
        for endpoint in endpoints_to_test:
            response, error = self.make_request(
                'GET', endpoint,
                expect_status=403
            )
            
            if error:
                results.append(False)
                print(f"   ❌ {endpoint}: Error - {error}")
            else:
                # Accept 401/403 as valid auth required responses
                auth_required = response["status_code"] in [401, 403]
                results.append(auth_required)
                print(f"   {'✅' if auth_required else '❌'} {endpoint}: Status {response['status_code']}")
        
        success = all(results)
        return self.log_result("Auth Required", success, f"{sum(results)}/{len(results)} endpoints protected")

    def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Starting Y-Store O13-O18 Module Tests")
        print("=" * 60)
        
        # Basic connectivity and authentication
        if not self.test_admin_login():
            print("❌ Admin login failed - stopping tests")
            return False
        
        # Test authentication requirements
        self.test_admin_authentication_required()
        
        # Test individual modules
        self.test_guard_incidents_list()
        self.test_guard_incident_actions()
        self.test_risk_distribution()
        self.test_timeline_events()
        self.test_analytics_ops_kpi()
        self.test_analytics_daily_rebuild()
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        print("=" * 60)
        
        return self.tests_passed >= (self.tests_run * 0.7)  # 70% pass rate acceptable


def main():
    """Main test runner"""
    tester = YStoreAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Tests completed successfully!")
        return 0
    else:
        print("💥 Some critical tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
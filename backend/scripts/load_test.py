#!/usr/bin/env python3
"""
Load Testing Script for CyberX Scaled API
Tests the ability to handle 1000-2000 concurrent users
"""

import asyncio
import aiohttp
import time
import json
import argparse
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any
import statistics

@dataclass
class TestResult:
    """Individual test result"""
    endpoint: str
    status_code: int
    response_time: float
    success: bool
    error: str = None

class LoadTester:
    """Comprehensive load testing for the scaled API"""
    
    def __init__(self, base_url: str = "https://cyberx.icu"):
        self.base_url = base_url
        self.session = None
        self.results: List[TestResult] = []
        
        # Test endpoints
        self.endpoints = {
            'health': '/api/health',
            'news': '/api/news',
            'news_sources': '/api/news/sources',
            'stats': '/api/stats',
            'search': '/api/news/search?q=security'
        }
    
    async def create_session(self):
        """Create aiohttp session with optimized settings"""
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(
            limit=2000,  # Total connection limit
            limit_per_host=500,  # Per-host connection limit
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'CyberX-LoadTester/1.0',
                'Accept': 'application/json'
            }
        )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str, endpoint_path: str) -> TestResult:
        """Make a single HTTP request"""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}{endpoint_path}"
            async with self.session.get(url, ssl=False) as response:
                response_time = time.time() - start_time
                
                # Read response to ensure full request completion
                await response.read()
                
                return TestResult(
                    endpoint=endpoint,
                    status_code=response.status,
                    response_time=response_time,
                    success=response.status == 200
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=endpoint,
                status_code=0,
                response_time=response_time,
                success=False,
                error=str(e)
            )
    
    async def simulate_user_session(self, user_id: int, requests_per_user: int = 10):
        """Simulate a single user session with multiple requests"""
        user_results = []
        
        for i in range(requests_per_user):
            # Vary endpoints to simulate real usage
            endpoint_weights = {
                'health': 0.1,    # 10% health checks
                'news': 0.4,      # 40% news requests
                'news_sources': 0.1,  # 10% source requests
                'stats': 0.1,     # 10% stats requests
                'search': 0.3,    # 30% search requests
            }
            
            # Simple weighted selection
            import random
            endpoint = random.choices(
                list(endpoint_weights.keys()),
                weights=list(endpoint_weights.values())
            )[0]
            
            result = await self.make_request(endpoint, self.endpoints[endpoint])
            user_results.append(result)
            
            # Add realistic delay between requests (0.5-2 seconds)
            await asyncio.sleep(random.uniform(0.5, 2.0))
        
        return user_results
    
    async def run_load_test(self, concurrent_users: int = 1000, requests_per_user: int = 10):
        """Run load test with specified concurrent users"""
        print(f"🚀 Starting load test with {concurrent_users} concurrent users")
        print(f"📊 Each user will make {requests_per_user} requests")
        print(f"📈 Total expected requests: {concurrent_users * requests_per_user}")
        print("=" * 60)
        
        await self.create_session()
        
        start_time = time.time()
        
        # Create tasks for all users
        tasks = [
            self.simulate_user_session(user_id, requests_per_user)
            for user_id in range(concurrent_users)
        ]
        
        # Run all user sessions concurrently
        print("⏳ Running concurrent user sessions...")
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        for user_result in user_results:
            if isinstance(user_result, Exception):
                print(f"❌ User session failed: {user_result}")
                continue
            self.results.extend(user_result)
        
        total_time = time.time() - start_time
        
        await self.close_session()
        
        return self.analyze_results(total_time, concurrent_users)
    
    def analyze_results(self, total_time: float, concurrent_users: int) -> Dict[str, Any]:
        """Analyze test results and generate report"""
        if not self.results:
            return {"error": "No results to analyze"}
        
        # Basic statistics
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r.success)
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests) * 100
        
        # Response time statistics
        response_times = [r.response_time for r in self.results if r.success]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        # Requests per second
        rps = total_requests / total_time if total_time > 0 else 0
        
        # Status code distribution
        status_codes = {}
        for result in self.results:
            status_codes[result.status_code] = status_codes.get(result.status_code, 0) + 1
        
        # Endpoint performance
        endpoint_stats = {}
        for endpoint in self.endpoints.keys():
            endpoint_results = [r for r in self.results if r.endpoint == endpoint]
            if endpoint_results:
                endpoint_response_times = [r.response_time for r in endpoint_results if r.success]
                endpoint_stats[endpoint] = {
                    'total_requests': len(endpoint_results),
                    'successful_requests': sum(1 for r in endpoint_results if r.success),
                    'avg_response_time': statistics.mean(endpoint_response_times) if endpoint_response_times else 0,
                    'success_rate': (sum(1 for r in endpoint_results if r.success) / len(endpoint_results)) * 100
                }
        
        # Error analysis
        errors = {}
        for result in self.results:
            if not result.success and result.error:
                errors[result.error] = errors.get(result.error, 0) + 1
        
        return {
            'test_summary': {
                'concurrent_users': concurrent_users,
                'total_time': round(total_time, 2),
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': round(success_rate, 2),
                'requests_per_second': round(rps, 2)
            },
            'response_times': {
                'average': round(avg_response_time, 3),
                'median': round(median_response_time, 3),
                'min': round(min_response_time, 3),
                'max': round(max_response_time, 3),
                'p95': round(p95_response_time, 3),
                'p99': round(p99_response_time, 3)
            },
            'status_codes': status_codes,
            'endpoint_performance': endpoint_stats,
            'errors': errors
        }
    
    def print_report(self, analysis: Dict[str, Any]):
        """Print formatted test report"""
        print("\n" + "=" * 60)
        print("📊 LOAD TEST RESULTS")
        print("=" * 60)
        
        # Test Summary
        summary = analysis['test_summary']
        print(f"\n🎯 Test Summary:")
        print(f"   Concurrent Users: {summary['concurrent_users']}")
        print(f"   Total Time: {summary['total_time']}s")
        print(f"   Total Requests: {summary['total_requests']}")
        print(f"   Successful: {summary['successful_requests']}")
        print(f"   Failed: {summary['failed_requests']}")
        print(f"   Success Rate: {summary['success_rate']}%")
        print(f"   Requests/Second: {summary['requests_per_second']}")
        
        # Performance Assessment
        print(f"\n⚡ Performance Assessment:")
        if summary['success_rate'] >= 99:
            print("   ✅ EXCELLENT - 99%+ success rate")
        elif summary['success_rate'] >= 95:
            print("   ✅ GOOD - 95%+ success rate")
        elif summary['success_rate'] >= 90:
            print("   ⚠️  ACCEPTABLE - 90%+ success rate")
        else:
            print("   ❌ POOR - <90% success rate")
        
        if summary['requests_per_second'] >= 500:
            print("   ✅ HIGH THROUGHPUT - 500+ RPS")
        elif summary['requests_per_second'] >= 200:
            print("   ✅ GOOD THROUGHPUT - 200+ RPS")
        elif summary['requests_per_second'] >= 100:
            print("   ⚠️  MODERATE THROUGHPUT - 100+ RPS")
        else:
            print("   ❌ LOW THROUGHPUT - <100 RPS")
        
        # Response Times
        times = analysis['response_times']
        print(f"\n⏱️  Response Times:")
        print(f"   Average: {times['average']}s")
        print(f"   Median: {times['median']}s")
        print(f"   95th Percentile: {times['p95']}s")
        print(f"   99th Percentile: {times['p99']}s")
        print(f"   Min: {times['min']}s")
        print(f"   Max: {times['max']}s")
        
        # Status Codes
        print(f"\n📈 Status Code Distribution:")
        for code, count in analysis['status_codes'].items():
            percentage = (count / summary['total_requests']) * 100
            print(f"   {code}: {count} ({percentage:.1f}%)")
        
        # Endpoint Performance
        print(f"\n🎯 Endpoint Performance:")
        for endpoint, stats in analysis['endpoint_performance'].items():
            print(f"   {endpoint}:")
            print(f"     Requests: {stats['total_requests']}")
            print(f"     Success Rate: {stats['success_rate']:.1f}%")
            print(f"     Avg Response Time: {stats['avg_response_time']:.3f}s")
        
        # Errors (if any)
        if analysis['errors']:
            print(f"\n❌ Error Analysis:")
            for error, count in analysis['errors'].items():
                print(f"   {error}: {count} occurrences")
        
        print(f"\n🎉 Load test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main function to run load tests"""
    parser = argparse.ArgumentParser(description='CyberX API Load Tester')
    parser.add_argument('--users', type=int, default=1000, help='Number of concurrent users (default: 1000)')
    parser.add_argument('--requests', type=int, default=10, help='Requests per user (default: 10)')
    parser.add_argument('--url', type=str, default='https://cyberx.icu', help='Base URL to test')
    
    args = parser.parse_args()
    
    # Create load tester
    tester = LoadTester(base_url=args.url)
    
    # Run tests
    analysis = await tester.run_load_test(
        concurrent_users=args.users,
        requests_per_user=args.requests
    )
    
    # Print results
    tester.print_report(analysis)
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'load_test_results_{timestamp}.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n💾 Results saved to: load_test_results_{timestamp}.json")

if __name__ == "__main__":
    # Run the load test
    asyncio.run(main())

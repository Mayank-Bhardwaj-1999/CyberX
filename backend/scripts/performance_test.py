#!/usr/bin/env python3
"""
Performance Load Testing Script for CyberX Backend
Tests concurrent user load to validate 1000-2000 user capacity
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Tuple
import argparse

class LoadTester:
    def __init__(self, base_url: str = "http://localhost:8090"):
        self.base_url = base_url
        self.results = []
        
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str) -> Dict:
        """Make a single HTTP request and measure response time"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # ms
                content = await response.text()
                
                return {
                    'status_code': response.status,
                    'response_time': response_time,
                    'success': response.status == 200,
                    'endpoint': endpoint,
                    'content_length': len(content)
                }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # ms
            return {
                'status_code': 0,
                'response_time': response_time,
                'success': False,
                'endpoint': endpoint,
                'error': str(e),
                'content_length': 0
            }
    
    async def run_concurrent_requests(self, num_requests: int, endpoint: str = "/health") -> List[Dict]:
        """Run multiple concurrent requests"""
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [self.make_request(session, endpoint) for _ in range(num_requests)]
            results = await asyncio.gather(*tasks)
            return results
    
    async def simulate_user_session(self, session: aiohttp.ClientSession, user_id: int) -> List[Dict]:
        """Simulate a typical user session with multiple endpoints"""
        endpoints = [
            "/health",
            "/api/health", 
            "/api/news",
            "/api/news?q=cybersecurity",
            "/api/news?category=security"
        ]
        
        results = []
        for endpoint in endpoints:
            result = await self.make_request(session, endpoint)
            result['user_id'] = user_id
            results.append(result)
            # Small delay between requests to simulate real user behavior
            await asyncio.sleep(0.1)
        
        return results
    
    async def run_user_simulation(self, num_users: int) -> List[Dict]:
        """Simulate concurrent users with realistic session patterns"""
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [self.simulate_user_session(session, user_id) for user_id in range(num_users)]
            user_results = await asyncio.gather(*tasks)
            
            # Flatten results
            all_results = []
            for user_result in user_results:
                all_results.extend(user_result)
            
            return all_results
    
    def analyze_results(self, results: List[Dict]) -> Dict:
        """Analyze test results and generate statistics"""
        if not results:
            return {"error": "No results to analyze"}
        
        response_times = [r['response_time'] for r in results if 'response_time' in r]
        successful_requests = [r for r in results if r.get('success', False)]
        failed_requests = [r for r in results if not r.get('success', False)]
        
        stats = {
            'total_requests': len(results),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': (len(successful_requests) / len(results)) * 100,
            'response_times': {
                'min': min(response_times) if response_times else 0,
                'max': max(response_times) if response_times else 0,
                'mean': statistics.mean(response_times) if response_times else 0,
                'median': statistics.median(response_times) if response_times else 0,
                'p95': self.percentile(response_times, 95) if response_times else 0,
                'p99': self.percentile(response_times, 99) if response_times else 0
            }
        }
        
        # Group by endpoint
        endpoint_stats = {}
        for result in results:
            endpoint = result.get('endpoint', 'unknown')
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {'requests': 0, 'success': 0, 'response_times': []}
            
            endpoint_stats[endpoint]['requests'] += 1
            if result.get('success', False):
                endpoint_stats[endpoint]['success'] += 1
            if 'response_time' in result:
                endpoint_stats[endpoint]['response_times'].append(result['response_time'])
        
        stats['endpoints'] = {}
        for endpoint, data in endpoint_stats.items():
            stats['endpoints'][endpoint] = {
                'requests': data['requests'],
                'success_rate': (data['success'] / data['requests']) * 100,
                'avg_response_time': statistics.mean(data['response_times']) if data['response_times'] else 0
            }
        
        return stats
    
    @staticmethod
    def percentile(data: List[float], p: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (p / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

async def main():
    parser = argparse.ArgumentParser(description='Load test CyberX Backend')
    parser.add_argument('--users', type=int, default=100, help='Number of concurrent users')
    parser.add_argument('--requests', type=int, default=500, help='Number of simple concurrent requests')
    parser.add_argument('--url', default='http://localhost:8090', help='Base URL to test')
    parser.add_argument('--test-type', choices=['simple', 'users', 'both'], default='both', help='Type of test to run')
    
    args = parser.parse_args()
    
    tester = LoadTester(args.url)
    
    print(f"🚀 Starting Load Tests for CyberX Backend")
    print(f"📍 Target URL: {args.url}")
    print("=" * 60)
    
    if args.test_type in ['simple', 'both']:
        print(f"\n📊 Test 1: Simple Concurrent Requests ({args.requests} requests)")
        print("-" * 40)
        
        start_time = time.time()
        simple_results = await tester.run_concurrent_requests(args.requests, "/health")
        simple_duration = time.time() - start_time
        
        simple_stats = tester.analyze_results(simple_results)
        
        print(f"✅ Completed {simple_stats['total_requests']} requests in {simple_duration:.2f}s")
        print(f"📈 Requests/sec: {simple_stats['total_requests'] / simple_duration:.2f}")
        print(f"✅ Success Rate: {simple_stats['success_rate']:.1f}%")
        print(f"⚡ Response Times (ms):")
        print(f"   - Average: {simple_stats['response_times']['mean']:.2f}")
        print(f"   - Median: {simple_stats['response_times']['median']:.2f}")
        print(f"   - 95th percentile: {simple_stats['response_times']['p95']:.2f}")
        print(f"   - 99th percentile: {simple_stats['response_times']['p99']:.2f}")
    
    if args.test_type in ['users', 'both']:
        print(f"\n👥 Test 2: Realistic User Simulation ({args.users} concurrent users)")
        print("-" * 40)
        
        start_time = time.time()
        user_results = await tester.run_user_simulation(args.users)
        user_duration = time.time() - start_time
        
        user_stats = tester.analyze_results(user_results)
        
        print(f"✅ Simulated {args.users} users making {user_stats['total_requests']} total requests")
        print(f"⏱️  Total Duration: {user_duration:.2f}s")
        print(f"📈 Requests/sec: {user_stats['total_requests'] / user_duration:.2f}")
        print(f"✅ Success Rate: {user_stats['success_rate']:.1f}%")
        print(f"⚡ Response Times (ms):")
        print(f"   - Average: {user_stats['response_times']['mean']:.2f}")
        print(f"   - Median: {user_stats['response_times']['median']:.2f}")
        print(f"   - 95th percentile: {user_stats['response_times']['p95']:.2f}")
        print(f"   - 99th percentile: {user_stats['response_times']['p99']:.2f}")
        
        print(f"\n📊 Endpoint Performance:")
        for endpoint, stats in user_stats['endpoints'].items():
            print(f"   {endpoint}: {stats['requests']} req, {stats['success_rate']:.1f}% success, {stats['avg_response_time']:.2f}ms avg")
    
    print("\n" + "=" * 60)
    print("🎯 Load Test Summary:")
    
    if args.test_type in ['simple', 'both']:
        throughput = simple_stats['total_requests'] / simple_duration
        if throughput > 100:
            print(f"✅ High throughput: {throughput:.0f} req/s - Excellent for target load")
        elif throughput > 50:
            print(f"✅ Good throughput: {throughput:.0f} req/s - Suitable for target load") 
        else:
            print(f"⚠️  Low throughput: {throughput:.0f} req/s - May need optimization")
    
    if args.test_type in ['users', 'both']:
        if user_stats['success_rate'] > 99:
            print(f"✅ Excellent reliability: {user_stats['success_rate']:.1f}% success rate")
        elif user_stats['success_rate'] > 95:
            print(f"✅ Good reliability: {user_stats['success_rate']:.1f}% success rate")
        else:
            print(f"⚠️  Reliability concerns: {user_stats['success_rate']:.1f}% success rate")
        
        avg_response = user_stats['response_times']['mean']
        if avg_response < 100:
            print(f"✅ Fast responses: {avg_response:.0f}ms average - Excellent user experience")
        elif avg_response < 500:
            print(f"✅ Good responses: {avg_response:.0f}ms average - Good user experience")
        else:
            print(f"⚠️  Slow responses: {avg_response:.0f}ms average - Consider optimization")
    
    print("\n🎯 Capacity Assessment:")
    if args.test_type in ['users', 'both']:
        if args.users >= 100 and user_stats['success_rate'] > 95:
            estimated_capacity = (args.users * 1000) / user_stats['response_times']['mean']
            print(f"📊 Estimated capacity: ~{estimated_capacity:.0f} concurrent users")
            if estimated_capacity >= 1000:
                print("✅ Target capacity (1000-2000 users) - ACHIEVABLE")
            else:
                print("⚠️  Below target capacity - Consider adding more instances")

if __name__ == "__main__":
    asyncio.run(main())

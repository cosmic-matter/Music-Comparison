#!/usr/bin/env python3
"""
Backend API Testing for Spotify Music Taste Comparison App
Tests all backend endpoints and functionality
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from unittest.mock import patch, AsyncMock
import uuid

# Get backend URL from frontend .env
BACKEND_URL = "https://beat-buddy-3.preview.emergentagent.com/api"

class SpotifyBackendTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        self.mock_spotify_data = self._create_mock_data()
        
    def _create_mock_data(self):
        """Create realistic mock data for testing"""
        return {
            "user_profile": {
                "id": "spotify_user_123",
                "display_name": "Taylor Swift Fan",
                "email": "taylor.fan@example.com",
                "images": [{"url": "https://example.com/profile.jpg"}]
            },
            "top_artists": {
                "items": [
                    {
                        "id": "06HL4z0CvFAxyc27GXpf02",
                        "name": "Taylor Swift",
                        "genres": ["pop", "country pop"],
                        "popularity": 100
                    },
                    {
                        "id": "1Xyo4u8uXC1ZmMpatF05PJ",
                        "name": "The Weeknd", 
                        "genres": ["canadian contemporary r&b", "pop"],
                        "popularity": 95
                    }
                ]
            },
            "top_tracks": {
                "items": [
                    {
                        "id": "1BxfuPKGuaTgP7aM0Bbdwr",
                        "name": "Cruel Summer",
                        "artists": [{"id": "06HL4z0CvFAxyc27GXpf02", "name": "Taylor Swift"}]
                    },
                    {
                        "id": "0VjIjW4GlUZAMYd2vXMi3b",
                        "name": "Blinding Lights",
                        "artists": [{"id": "1Xyo4u8uXC1ZmMpatF05PJ", "name": "The Weeknd"}]
                    }
                ]
            },
            "audio_features": {
                "audio_features": [
                    {
                        "id": "1BxfuPKGuaTgP7aM0Bbdwr",
                        "danceability": 0.552,
                        "energy": 0.702,
                        "speechiness": 0.0319,
                        "acousticness": 0.117,
                        "instrumentalness": 0.0,
                        "liveness": 0.106,
                        "valence": 0.564,
                        "tempo": 169.994
                    },
                    {
                        "id": "0VjIjW4GlUZAMYd2vXMi3b",
                        "danceability": 0.514,
                        "energy": 0.730,
                        "speechiness": 0.0598,
                        "acousticness": 0.00146,
                        "instrumentalness": 0.000009,
                        "liveness": 0.0897,
                        "valence": 0.334,
                        "tempo": 171.009
                    }
                ]
            },
            "token_response": {
                "access_token": "mock_access_token_123",
                "refresh_token": "mock_refresh_token_123",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }

    async def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")

    async def test_spotify_auth_endpoint(self):
        """Test Spotify OAuth initiation endpoint"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/auth/spotify")
            
            if response.status_code == 200:
                data = response.json()
                if "auth_url" in data and "state" in data:
                    if "accounts.spotify.com/authorize" in data["auth_url"]:
                        await self.log_result("Spotify Auth Initiation", True, 
                                            f"Auth URL generated successfully with state: {data['state'][:10]}...")
                        return data["state"]
                    else:
                        await self.log_result("Spotify Auth Initiation", False, 
                                            "Auth URL doesn't contain Spotify authorize endpoint")
                else:
                    await self.log_result("Spotify Auth Initiation", False, 
                                        "Missing auth_url or state in response")
            else:
                await self.log_result("Spotify Auth Initiation", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            await self.log_result("Spotify Auth Initiation", False, f"Exception: {str(e)}")
        
        return None

    async def test_spotify_callback_endpoint(self):
        """Test Spotify OAuth callback endpoint with mocked Spotify API"""
        try:
            # Mock the Spotify API calls
            with patch('httpx.AsyncClient.post') as mock_post, \
                 patch('httpx.AsyncClient.get') as mock_get:
                
                # Mock token exchange
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = self.mock_spotify_data["token_response"]
                
                # Mock user profile fetch
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.mock_spotify_data["user_profile"]
                
                # Test callback
                response = await self.client.post(
                    f"{BACKEND_URL}/auth/spotify/callback",
                    params={
                        "code": "mock_auth_code_123",
                        "state": "mock_state_456"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and "user_id" in data and "display_name" in data:
                        await self.log_result("Spotify OAuth Callback", True, 
                                            f"User created: {data['display_name']} (ID: {data['user_id'][:10]}...)")
                        return data["user_id"]
                    else:
                        await self.log_result("Spotify OAuth Callback", False, 
                                            "Missing success, user_id, or display_name in response")
                else:
                    await self.log_result("Spotify OAuth Callback", False, 
                                        f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            await self.log_result("Spotify OAuth Callback", False, f"Exception: {str(e)}")
        
        return None

    async def test_user_profile_endpoint(self, user_id: str):
        """Test user profile data fetching endpoint"""
        try:
            # Mock Spotify API calls for profile data
            with patch('httpx.AsyncClient.get') as mock_get:
                
                def mock_spotify_response(url, **kwargs):
                    mock_response = AsyncMock()
                    mock_response.status_code = 200
                    
                    if "me/top/artists" in url:
                        mock_response.json.return_value = self.mock_spotify_data["top_artists"]
                    elif "me/top/tracks" in url:
                        mock_response.json.return_value = self.mock_spotify_data["top_tracks"]
                    elif "audio-features" in url:
                        mock_response.json.return_value = self.mock_spotify_data["audio_features"]
                    else:
                        mock_response.json.return_value = {}
                    
                    return mock_response
                
                mock_get.side_effect = mock_spotify_response
                
                response = await self.client.get(f"{BACKEND_URL}/user/{user_id}/profile")
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["id", "spotify_id", "display_name", "top_artists", 
                                     "top_tracks", "audio_features", "genres"]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        artists_count = len(data.get("top_artists", []))
                        tracks_count = len(data.get("top_tracks", []))
                        genres_count = len(data.get("genres", []))
                        
                        await self.log_result("User Profile Data Fetching", True, 
                                            f"Profile loaded: {artists_count} artists, {tracks_count} tracks, {genres_count} genres")
                        return data
                    else:
                        await self.log_result("User Profile Data Fetching", False, 
                                            f"Missing required fields: {missing_fields}")
                else:
                    await self.log_result("User Profile Data Fetching", False, 
                                        f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            await self.log_result("User Profile Data Fetching", False, f"Exception: {str(e)}")
        
        return None

    async def test_comparison_endpoint(self, user1_id: str, user2_id: str):
        """Test music taste comparison endpoint"""
        try:
            # Mock Spotify API calls for both users
            with patch('httpx.AsyncClient.get') as mock_get:
                
                def mock_spotify_response(url, **kwargs):
                    mock_response = AsyncMock()
                    mock_response.status_code = 200
                    
                    if "me/top/artists" in url:
                        mock_response.json.return_value = self.mock_spotify_data["top_artists"]
                    elif "me/top/tracks" in url:
                        mock_response.json.return_value = self.mock_spotify_data["top_tracks"]
                    elif "audio-features" in url:
                        mock_response.json.return_value = self.mock_spotify_data["audio_features"]
                    else:
                        mock_response.json.return_value = {}
                    
                    return mock_response
                
                mock_get.side_effect = mock_spotify_response
                
                response = await self.client.post(
                    f"{BACKEND_URL}/compare",
                    params={
                        "user1_id": user1_id,
                        "user2_id": user2_id
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["user1", "user2", "similarity_score", "shared_artists", 
                                     "shared_tracks", "shared_genres", "audio_features_comparison", 
                                     "recommendations"]
                    
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        similarity_score = data.get("similarity_score", 0)
                        shared_artists = len(data.get("shared_artists", []))
                        shared_tracks = len(data.get("shared_tracks", []))
                        
                        await self.log_result("Music Taste Comparison", True, 
                                            f"Similarity: {similarity_score}%, {shared_artists} shared artists, {shared_tracks} shared tracks")
                        return data
                    else:
                        await self.log_result("Music Taste Comparison", False, 
                                            f"Missing required fields: {missing_fields}")
                else:
                    await self.log_result("Music Taste Comparison", False, 
                                        f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            await self.log_result("Music Taste Comparison", False, f"Exception: {str(e)}")
        
        return None

    async def test_get_all_users_endpoint(self):
        """Test get all users endpoint"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/users")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    await self.log_result("Get All Users", True, 
                                        f"Retrieved {len(data)} users from database")
                    return data
                else:
                    await self.log_result("Get All Users", False, 
                                        "Response is not a list")
            else:
                await self.log_result("Get All Users", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            await self.log_result("Get All Users", False, f"Exception: {str(e)}")
        
        return None

    async def test_database_connectivity(self):
        """Test database connectivity by checking users endpoint"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/users")
            
            if response.status_code == 200:
                await self.log_result("Database Connectivity", True, 
                                    "Successfully connected to MongoDB")
                return True
            else:
                await self.log_result("Database Connectivity", False, 
                                    f"Database connection failed: HTTP {response.status_code}")
                
        except Exception as e:
            await self.log_result("Database Connectivity", False, f"Exception: {str(e)}")
        
        return False

    async def test_cors_configuration(self):
        """Test CORS configuration"""
        try:
            # Test preflight request
            response = await self.client.options(
                f"{BACKEND_URL}/auth/spotify",
                headers={
                    "Origin": "https://beat-buddy-3.preview.emergentagent.com",
                    "Access-Control-Request-Method": "GET"
                }
            )
            
            if response.status_code in [200, 204]:
                await self.log_result("CORS Configuration", True, 
                                    "CORS preflight request successful")
                return True
            else:
                await self.log_result("CORS Configuration", False, 
                                    f"CORS preflight failed: HTTP {response.status_code}")
                
        except Exception as e:
            await self.log_result("CORS Configuration", False, f"Exception: {str(e)}")
        
        return False

    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Spotify Backend API Tests...")
        print("=" * 60)
        
        # Test 1: Database connectivity
        await self.test_database_connectivity()
        
        # Test 2: CORS configuration
        await self.test_cors_configuration()
        
        # Test 3: Spotify auth initiation
        state = await self.test_spotify_auth_endpoint()
        
        # Test 4: Spotify OAuth callback (with mocked Spotify API)
        user_id = await self.test_spotify_callback_endpoint()
        
        if user_id:
            # Test 5: User profile data fetching
            profile_data = await self.test_user_profile_endpoint(user_id)
            
            # Test 6: Create second user for comparison
            user2_id = await self.test_spotify_callback_endpoint()
            
            if user2_id and user_id != user2_id:
                # Test 7: Music taste comparison
                await self.test_comparison_endpoint(user_id, user2_id)
            else:
                await self.log_result("Music Taste Comparison", False, 
                                    "Could not create second user for comparison")
        
        # Test 8: Get all users
        await self.test_get_all_users_endpoint()
        
        await self.client.aclose()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        return self.test_results

async def main():
    """Main test runner"""
    tester = SpotifyBackendTester()
    results = await tester.run_all_tests()
    
    # Return results for analysis
    return results

if __name__ == "__main__":
    asyncio.run(main())
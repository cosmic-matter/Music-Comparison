from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import httpx
import base64
import json
from urllib.parse import urlencode, parse_qs
import secrets

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Spotify config
SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
SPOTIFY_REDIRECT_URI = os.environ['SPOTIFY_REDIRECT_URI']

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class SpotifyUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    spotify_id: str
    display_name: str
    email: Optional[str] = None
    profile_image: Optional[str] = None
    access_token: str
    refresh_token: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserProfile(BaseModel):
    id: str
    spotify_id: str
    display_name: str
    profile_image: Optional[str] = None
    top_artists: List[Dict[str, Any]] = []
    top_tracks: List[Dict[str, Any]] = []
    audio_features: Dict[str, float] = {}
    genres: List[str] = []

class ComparisonResult(BaseModel):
    user1: UserProfile
    user2: UserProfile
    similarity_score: float
    shared_artists: List[Dict[str, Any]] = []
    shared_tracks: List[Dict[str, Any]] = []
    shared_genres: List[str] = []
    audio_features_comparison: Dict[str, Dict[str, float]] = {}
    recommendations: List[str] = []

# Helper functions
def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = prepare_for_mongo(value)
            elif isinstance(value, list):
                data[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
    return data

def parse_from_mongo(item):
    if isinstance(item, dict):
        for key, value in item.items():
            if key == 'created_at' and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value)
                except:
                    pass
            elif isinstance(value, dict):
                item[key] = parse_from_mongo(value)
            elif isinstance(value, list):
                item[key] = [parse_from_mongo(subitem) if isinstance(subitem, dict) else subitem for subitem in value]
    return item

async def get_spotify_token(code: str):
    """Exchange authorization code for access token"""
    token_url = "https://accounts.spotify.com/api/token"
    
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=400, detail="Failed to get Spotify token")

async def refresh_spotify_token(refresh_token: str):
    """Refresh Spotify access token"""
    token_url = "https://accounts.spotify.com/api/token"
    
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=400, detail="Failed to refresh Spotify token")

async def get_spotify_user_profile(access_token: str):
    """Get Spotify user profile"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.spotify.com/v1/me", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=400, detail="Failed to get user profile")

async def get_user_top_items(access_token: str, item_type: str, limit: int = 20, time_range: str = "medium_term"):
    """Get user's top artists or tracks"""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/me/top/{item_type}?limit={limit}&time_range={time_range}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"items": []}

async def get_audio_features(access_token: str, track_ids: List[str]):
    """Get audio features for tracks"""
    if not track_ids:
        return {"audio_features": []}
    
    headers = {"Authorization": f"Bearer {access_token}"}
    ids = ",".join(track_ids[:100])  # API limit is 100
    url = f"https://api.spotify.com/v1/audio-features?ids={ids}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"audio_features": []}

def calculate_similarity(user1_data: Dict, user2_data: Dict) -> Dict:
    """Calculate similarity between two users"""
    
    # Get shared artists
    user1_artists = {artist['id']: artist for artist in user1_data['top_artists']}
    user2_artists = {artist['id']: artist for artist in user2_data['top_artists']}
    shared_artists = []
    
    for artist_id, artist in user1_artists.items():
        if artist_id in user2_artists:
            shared_artists.append(artist)
    
    # Get shared tracks
    user1_tracks = {track['id']: track for track in user1_data['top_tracks']}
    user2_tracks = {track['id']: track for track in user2_data['top_tracks']}
    shared_tracks = []
    
    for track_id, track in user1_tracks.items():
        if track_id in user2_tracks:
            shared_tracks.append(track)
    
    # Get shared genres
    shared_genres = list(set(user1_data['genres']).intersection(set(user2_data['genres'])))
    
    # Calculate audio features similarity
    audio_features_comparison = {}
    features = ['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
    
    for feature in features:
        user1_avg = user1_data['audio_features'].get(feature, 0)
        user2_avg = user2_data['audio_features'].get(feature, 0)
        
        # Calculate similarity (1 - absolute difference)
        if feature == 'tempo':
            # Normalize tempo (typical range 60-200)
            user1_norm = min(max(user1_avg / 200, 0), 1)
            user2_norm = min(max(user2_avg / 200, 0), 1)
            similarity = 1 - abs(user1_norm - user2_norm)
        else:
            similarity = 1 - abs(user1_avg - user2_avg)
        
        audio_features_comparison[feature] = {
            'user1': user1_avg,
            'user2': user2_avg,
            'similarity': similarity
        }
    
    # Calculate overall similarity score
    artist_similarity = len(shared_artists) / max(len(user1_data['top_artists']), 1)
    track_similarity = len(shared_tracks) / max(len(user1_data['top_tracks']), 1)
    genre_similarity = len(shared_genres) / max(len(set(user1_data['genres']).union(set(user2_data['genres']))), 1)
    
    # Average audio features similarity
    avg_audio_similarity = sum(comp['similarity'] for comp in audio_features_comparison.values()) / len(audio_features_comparison)
    
    # Weighted overall similarity
    overall_similarity = (
        artist_similarity * 0.3 +
        track_similarity * 0.3 +
        genre_similarity * 0.2 +
        avg_audio_similarity * 0.2
    )
    
    return {
        'similarity_score': round(overall_similarity * 100, 1),
        'shared_artists': shared_artists,
        'shared_tracks': shared_tracks,
        'shared_genres': shared_genres,
        'audio_features_comparison': audio_features_comparison
    }

@api_router.get("/auth/spotify")
async def spotify_auth():
    """Initiate Spotify OAuth"""
    state = secrets.token_urlsafe(16)
    scope = "user-read-private user-read-email user-top-read"
    
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": scope,
        "state": state
    }
    
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    return {"auth_url": auth_url, "state": state}

from fastapi import Query

@api_router.post("/auth/spotify/callback")
async def spotify_callback(code: str = Query(...), state: str = Query(...)):
    """Handle Spotify OAuth callback"""
    try:
        # Exchange code for tokens
        token_data = await get_spotify_token(code)
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        
        # Get user profile
        profile = await get_spotify_user_profile(access_token)
        
        # Create user data
        user_data = {
            "spotify_id": profile["id"],
            "display_name": profile["display_name"],
            "email": profile.get("email"),
            "profile_image": profile["images"][0]["url"] if profile.get("images") else None,
            "access_token": access_token,
            "refresh_token": refresh_token
        }
        
        user = SpotifyUser(**user_data)
        user_dict = prepare_for_mongo(user.dict())
        
        # Save or update user
        await db.spotify_users.update_one(
            {"spotify_id": user.spotify_id},
            {"$set": user_dict},
            upsert=True
        )
        
        return {"success": True, "user_id": user.id, "display_name": user.display_name}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/user/{user_id}/profile")
async def get_user_full_profile(user_id: str):
    """Get complete user profile with music data"""
    try:
        # Find user
        user_doc = await db.spotify_users.find_one({"id": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_doc = parse_from_mongo(user_doc)
        access_token = user_doc["access_token"]
        
        # Get top artists
        top_artists_response = await get_user_top_items(access_token, "artists", 20)
        top_artists = top_artists_response.get("items", [])
        
        # Get top tracks
        top_tracks_response = await get_user_top_items(access_token, "tracks", 20)
        top_tracks = top_tracks_response.get("items", [])
        
        # Extract genres from artists
        genres = []
        for artist in top_artists:
            genres.extend(artist.get("genres", []))
        genres = list(set(genres))  # Remove duplicates
        
        # Get audio features for top tracks
        track_ids = [track["id"] for track in top_tracks]
        audio_features_response = await get_audio_features(access_token, track_ids)
        audio_features_list = audio_features_response.get("audio_features", [])
        
        # Calculate average audio features
        features = ['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
        avg_features = {}
        
        valid_features = [af for af in audio_features_list if af is not None]
        if valid_features:
            for feature in features:
                values = [af[feature] for af in valid_features if af.get(feature) is not None]
                avg_features[feature] = sum(values) / len(values) if values else 0
        
        profile = UserProfile(
            id=user_doc["id"],
            spotify_id=user_doc["spotify_id"],
            display_name=user_doc["display_name"],
            profile_image=user_doc.get("profile_image"),
            top_artists=top_artists,
            top_tracks=top_tracks,
            audio_features=avg_features,
            genres=genres
        )
        
        return profile
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/compare")
async def compare_users(user1_id: str, user2_id: str):
    """Compare two users' music tastes"""
    try:
        # Get both user profiles
        user1_profile = await get_user_full_profile(user1_id)
        user2_profile = await get_user_full_profile(user2_id)
        
        # Convert to dict for comparison
        user1_data = user1_profile.dict()
        user2_data = user2_profile.dict()
        
        # Calculate similarity
        comparison_data = calculate_similarity(user1_data, user2_data)
        
        # Generate recommendations
        recommendations = []
        if comparison_data['similarity_score'] > 70:
            recommendations.append("You have very similar music tastes! You'd probably enjoy each other's playlists.")
        elif comparison_data['similarity_score'] > 40:
            recommendations.append("You have some great overlaps in your music taste with room to discover new favorites.")
        else:
            recommendations.append("Your music tastes are quite different - perfect for discovering new music together!")
        
        if comparison_data['shared_genres']:
            recommendations.append(f"You both love {', '.join(comparison_data['shared_genres'][:3])} music.")
        
        result = ComparisonResult(
            user1=user1_profile,
            user2=user2_profile,
            similarity_score=comparison_data['similarity_score'],
            shared_artists=comparison_data['shared_artists'],
            shared_tracks=comparison_data['shared_tracks'],
            shared_genres=comparison_data['shared_genres'],
            audio_features_comparison=comparison_data['audio_features_comparison'],
            recommendations=recommendations
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/users")
async def get_all_users():
    """Get all users for selection"""
    users = await db.spotify_users.find({}, {"id": 1, "display_name": 1, "profile_image": 1, "spotify_id": 1}).to_list(100)
    return [parse_from_mongo(user) for user in users]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
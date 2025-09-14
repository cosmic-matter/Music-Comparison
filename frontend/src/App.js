import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Components
const SpotifyLogin = ({ onLogin, userLabel }) => {
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/auth/spotify`);
      const { auth_url } = response.data;
      
      // Open Spotify auth in popup
      const popup = window.open(auth_url, 'spotify-auth', 'width=500,height=600');
      
      // Listen for popup to close and get the code
      const checkClosed = setInterval(async () => {
        if (popup.closed) {
          clearInterval(checkClosed);
          // Check URL for auth code (this is simplified)
          // In a real app, you'd handle this differently
          const urlParams = new URLSearchParams(window.location.search);
          const code = urlParams.get('code');
          
          if (code) {
            try {
              const callbackResponse = await axios.post(`${API}/auth/spotify/callback`, {
                code,
                state: 'state'
              });
              
              if (callbackResponse.data.success) {
                onLogin({
                  id: callbackResponse.data.user_id,
                  name: callbackResponse.data.display_name
                });
              }
            } catch (error) {
              console.error('Callback error:', error);
            }
          }
          setLoading(false);
        }
      }, 1000);
    } catch (error) {
      console.error('Login error:', error);
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 text-center">
      <div className="mb-4">
        <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-3">
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.859-.179-.982-.599-.122-.421.18-.861.599-.982 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02l.024.142zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-800 mb-2">{userLabel}</h3>
        <p className="text-gray-600 text-sm">Connect your Spotify account to analyze your music taste</p>
      </div>
      
      <button
        onClick={handleLogin}
        disabled={loading}
        className="w-full bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center"
      >
        {loading ? (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
        ) : (
          <>
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.859-.179-.982-.599-.122-.421.18-.861.599-.982 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02l.024.142zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
            </svg>
            Connect with Spotify
          </>
        )}
      </button>
    </div>
  );
};

const UserCard = ({ user, label }) => (
  <div className="bg-white rounded-xl shadow-lg p-6">
    <div className="text-center">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
        {user.profile_image ? (
          <img src={user.profile_image} alt={user.name} className="w-16 h-16 rounded-full" />
        ) : (
          <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
        )}
      </div>
      <h3 className="text-lg font-semibold text-gray-800">{label}</h3>
      <p className="text-green-600 font-medium">{user.name}</p>
      <div className="mt-3 inline-flex items-center px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
        Connected
      </div>
    </div>
  </div>
);

const ComparisonResults = ({ comparison, onReset }) => {
  const getScoreColor = (score) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score) => {
    if (score >= 70) return 'bg-green-100';
    if (score >= 40) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-4">Music Taste Comparison</h2>
        <div className="flex items-center justify-center space-x-4">
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-2">
              {comparison.user1.profile_image ? (
                <img src={comparison.user1.profile_image} alt="" className="w-16 h-16 rounded-full" />
              ) : (
                <svg className="w-8 h-8 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
              )}
            </div>
            <p className="font-medium text-gray-800">{comparison.user1.display_name}</p>
          </div>
          
          <div className="text-center mx-8">
            <div className={`inline-flex items-center px-6 py-3 ${getScoreBg(comparison.similarity_score)} rounded-full`}>
              <span className={`text-2xl font-bold ${getScoreColor(comparison.similarity_score)}`}>
                {comparison.similarity_score}%
              </span>
            </div>
            <p className="text-gray-600 mt-2">Similarity Score</p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
              {comparison.user2.profile_image ? (
                <img src={comparison.user2.profile_image} alt="" className="w-16 h-16 rounded-full" />
              ) : (
                <svg className="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
              )}
            </div>
            <p className="font-medium text-gray-800">{comparison.user2.display_name}</p>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {comparison.recommendations.length > 0 && (
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl p-6 text-white">
          <h3 className="text-xl font-bold mb-3">💡 Insights</h3>
          <ul className="space-y-2">
            {comparison.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start">
                <span className="mr-2">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Shared Content */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Shared Artists */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            Shared Artists ({comparison.shared_artists.length})
          </h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {comparison.shared_artists.slice(0, 10).map((artist, index) => (
              <div key={index} className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded">
                {artist.images && artist.images[0] && (
                  <img src={artist.images[0].url} alt="" className="w-10 h-10 rounded-full" />
                )}
                <div>
                  <p className="font-medium text-gray-800">{artist.name}</p>
                  <p className="text-sm text-gray-600">Popularity: {artist.popularity}</p>
                </div>
              </div>
            ))}
            {comparison.shared_artists.length === 0 && (
              <p className="text-gray-500 text-center py-4">No shared artists found</p>
            )}
          </div>
        </div>

        {/* Shared Tracks */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
              <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v6.114A4.369 4.369 0 005 11a4 4 0 104 4V5.114l8-1.6v4.372A4.37 4.37 0 0016 7a4 4 0 104 4V3z"/>
            </svg>
            Shared Tracks ({comparison.shared_tracks.length})
          </h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {comparison.shared_tracks.slice(0, 10).map((track, index) => (
              <div key={index} className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded">
                {track.album.images && track.album.images[0] && (
                  <img src={track.album.images[0].url} alt="" className="w-10 h-10 rounded" />
                )}
                <div>
                  <p className="font-medium text-gray-800">{track.name}</p>
                  <p className="text-sm text-gray-600">{track.artists[0].name}</p>
                </div>
              </div>
            ))}
            {comparison.shared_tracks.length === 0 && (
              <p className="text-gray-500 text-center py-4">No shared tracks found</p>
            )}
          </div>
        </div>

        {/* Shared Genres */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd"/>
            </svg>
            Shared Genres ({comparison.shared_genres.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {comparison.shared_genres.slice(0, 15).map((genre, index) => (
              <span key={index} className="px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full">
                {genre}
              </span>
            ))}
            {comparison.shared_genres.length === 0 && (
              <p className="text-gray-500 text-center py-4 w-full">No shared genres found</p>
            )}
          </div>
        </div>
      </div>

      {/* Audio Features Comparison */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center">
          <svg className="w-5 h-5 mr-2 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
          </svg>
          Audio Features Comparison
        </h3>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(comparison.audio_features_comparison).map(([feature, data]) => (
            <div key={feature} className="text-center">
              <h4 className="font-medium text-gray-800 capitalize mb-2">{feature}</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-purple-600">{comparison.user1.display_name}</span>
                  <span>{(data.user1 * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-purple-500 h-2 rounded-full" 
                    style={{width: `${data.user1 * 100}%`}}
                  ></div>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-blue-600">{comparison.user2.display_name}</span>
                  <span>{(data.user2 * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full" 
                    style={{width: `${data.user2 * 100}%`}}
                  ></div>
                </div>
                <div className="text-center">
                  <span className="text-xs text-gray-600">
                    {(data.similarity * 100).toFixed(0)}% similar
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Reset Button */}
      <div className="text-center">
        <button
          onClick={onReset}
          className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors duration-200"
        >
          Compare Different Users
        </button>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [user1, setUser1] = useState(null);
  const [user2, setUser2] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUser1Login = (userData) => {
    setUser1(userData);
    setError(null);
  };

  const handleUser2Login = (userData) => {
    setUser2(userData);
    setError(null);
  };

  const handleCompare = async () => {
    if (!user1 || !user2) {
      setError("Please connect both users first");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API}/compare`, null, {
        params: {
          user1_id: user1.id,
          user2_id: user2.id
        }
      });
      
      setComparison(response.data);
    } catch (error) {
      console.error('Comparison error:', error);
      setError('Failed to compare users. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setUser1(null);
    setUser2(null);
    setComparison(null);
    setError(null);
  };

  // Handle callback
  useEffect(() => {
    const handleCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      
      if (code) {
        try {
          const response = await axios.post(`${API}/auth/spotify/callback`, {
            code,
            state: state || 'state'
          });
          
          if (response.data.success) {
            const userData = {
              id: response.data.user_id,
              name: response.data.display_name
            };
            
            // Determine which user to set based on current state
            if (!user1) {
              setUser1(userData);
            } else if (!user2) {
              setUser2(userData);
            }
            
            // Clear URL params
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        } catch (error) {
          console.error('Callback error:', error);
          setError('Authentication failed. Please try again.');
        }
      }
    };

    handleCallback();
  }, [user1, user2]);

  if (comparison) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 py-8 px-4">
        <ComparisonResults comparison={comparison} onReset={handleReset} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Header */}
      <div className="text-center pt-12 pb-8">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-4">
          🎵 Spotify Music Taste Comparison
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto px-4">
          Compare your music taste with friends and discover how similar your musical preferences are!
        </p>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 pb-12">
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-300 text-red-700 rounded-lg text-center">
            {error}
          </div>
        )}

        {/* User Connection Section */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          <div>
            {user1 ? (
              <UserCard user={user1} label="User 1" />
            ) : (
              <SpotifyLogin onLogin={handleUser1Login} userLabel="Connect User 1" />
            )}
          </div>
          
          <div>
            {user2 ? (
              <UserCard user={user2} label="User 2" />
            ) : (
              <SpotifyLogin onLogin={handleUser2Login} userLabel="Connect User 2" />
            )}
          </div>
        </div>

        {/* Compare Button */}
        {user1 && user2 && (
          <div className="text-center">
            <button
              onClick={handleCompare}
              disabled={loading}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-gray-400 disabled:to-gray-400 text-white font-bold py-4 px-12 rounded-full text-lg transition-all duration-200 transform hover:scale-105 disabled:transform-none flex items-center justify-center mx-auto"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
              ) : (
                <svg className="w-6 h-6 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                </svg>
              )}
              {loading ? 'Analyzing Music Tastes...' : 'Compare Music Tastes'}
            </button>
          </div>
        )}

        {/* Instructions */}
        {!user1 || !user2 ? (
          <div className="mt-12 bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4 text-center">How it works</h3>
            <div className="grid md:grid-cols-3 gap-6 text-center">
              <div>
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-green-600 font-bold">1</span>
                </div>
                <h4 className="font-semibold text-gray-800 mb-2">Connect Accounts</h4>
                <p className="text-gray-600 text-sm">Both users connect their Spotify accounts securely</p>
              </div>
              <div>
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 font-bold">2</span>
                </div>
                <h4 className="font-semibold text-gray-800 mb-2">Analyze Data</h4>
                <p className="text-gray-600 text-sm">We compare top artists, tracks, genres, and audio features</p>
              </div>
              <div>
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-purple-600 font-bold">3</span>
                </div>
                <h4 className="font-semibold text-gray-800 mb-2">Get Results</h4>
                <p className="text-gray-600 text-sm">See your compatibility score and shared music preferences</p>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default App;
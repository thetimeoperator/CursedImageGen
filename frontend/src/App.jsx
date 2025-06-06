import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { openDB } from 'idb';

// Determine the base API URL. In development, it might be proxied, 
// but in production, it must be set via the environment variable.
// Fallback to /api which relies on proxy in dev, but requires proper setup in prod if served from same domain (not our case here).
const API_BASE_URL = process.env.REACT_APP_API_URL || ''; // Use REACT_APP_API_URL in Vercel

// Basic Modal Styles (can be moved to CSS file)
const modalOverlayStyle = {
  position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.7)', display: 'flex',
  alignItems: 'center', justifyContent: 'center', zIndex: 1000
};
const modalContentStyle = {
  background: 'white', padding: '30px', borderRadius: '8px',
  position: 'relative', minWidth: '300px', textAlign: 'center',
  color: '#333' // Ensure text is visible on white background
};
const closeButtonStyle = {
  position: 'absolute', top: '10px', right: '15px', background: 'none',
  border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: '#666'
};
const modalButtonStyle = {
  display: 'block', width: '100%', padding: '12px',
  margin: '10px 0', fontSize: '1rem', cursor: 'pointer',
  borderRadius: '5px', border: 'none', backgroundColor: '#f0c040', color: 'black'
};

// --- IndexedDB Setup ---
const DB_NAME = 'JJKImageGenDB';
const STORE_NAME = 'generatedImages';
const DB_VERSION = 1;
const INITIAL_CREDITS = 0; // Set desired initial credits here

async function initDB() {
  console.log('[initDB] Attempting to open IndexedDB...');
  const db = await openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      console.log('[initDB] Upgrade needed. Creating object store:', STORE_NAME);
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
      }
    },
  });
  console.log('[initDB] Database opened successfully.');
  return db;
}
// ----------------------

function App() {
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState('');
  // Enhanced credit initialization from localStorage with more robust parsing
  const [credits, setCredits] = useState(() => {
    try {
      const storedCredits = localStorage.getItem('credits');
      if (storedCredits === null) return INITIAL_CREDITS;
      const parsedCredits = parseInt(storedCredits);
      return isNaN(parsedCredits) ? INITIAL_CREDITS : parsedCredits;
    } catch (e) {
      console.error('Error loading credits from localStorage:', e);
      return INITIAL_CREDITS;
    }
  });
  
  // Initialize gallery state as empty array.
  const [gallery, setGallery] = useState([]); 
  
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false); // State for modal visibility

  // Load initial credits from localStorage or default to 0
  useEffect(() => {
    const storedCredits = localStorage.getItem('credits');
    console.log('[Credits Load] Retrieved from localStorage:', storedCredits);
    if (storedCredits) {
      const numCredits = parseInt(storedCredits, 10);
      if (!isNaN(numCredits)) {
        setCredits(numCredits);
        console.log('[Credits Load] Set credits state to:', numCredits);
      } else {
        console.error('[Credits Load] Invalid number found in localStorage, resetting to default.');
        localStorage.setItem('credits', INITIAL_CREDITS.toString()); // Reset if invalid
        setCredits(INITIAL_CREDITS);
        console.log('[Credits Load] Set credits state to default:', INITIAL_CREDITS);
      }
    } else {
      // If no credits in localStorage, initialize with default
      localStorage.setItem('credits', INITIAL_CREDITS.toString());
      setCredits(INITIAL_CREDITS);
      console.log('[Credits Load] No credits found in localStorage, initialized to default:', INITIAL_CREDITS);
    }
  }, []);

  // Enhanced localStorage updates with error handling
  useEffect(() => { 
    try {
      localStorage.setItem('credits', credits.toString()); 
      console.log(`Credits saved to localStorage: ${credits}`);
    } catch (e) {
      console.error('Error saving credits to localStorage:', e);
    }
  }, [credits]);
  
  // --- Load Gallery from IndexedDB on Mount ---
  useEffect(() => {
    async function loadGalleryFromDB() {
      console.log('[loadGalleryFromDB] Starting...');
      let objectUrls = []; // Define outside try block
      try {
        const db = await initDB();
        console.log('[loadGalleryFromDB] DB handle obtained.');
        const blobs = await db.getAll(STORE_NAME);
        console.log(`[loadGalleryFromDB] Retrieved ${blobs.length} items from DB.`);
        objectUrls = blobs.map(item => {
          let url = null;
          try {
            url = URL.createObjectURL(item.blob);
            // console.log(`[loadGalleryFromDB] Created object URL for ID ${item.id}: ${url}`); // Optional: Too verbose?
          } catch(e) {
            console.error(`[loadGalleryFromDB] Error creating object URL for ID ${item.id}:`, e); 
          }
          return {
            id: item.id, 
            url: url 
          };
        }).filter(item => item.url !== null); // Filter out items where URL creation failed

        // Reverse to show newest first
        setGallery(objectUrls.reverse()); 
        console.log(`[loadGalleryFromDB] Set gallery state with ${objectUrls.length} valid images.`);
      } catch (e) {
        console.error('Error loading gallery from IndexedDB:', e);
      }
    }
    loadGalleryFromDB();

    // Cleanup object URLs on unmount to prevent memory leaks
    return () => {
      objectUrls.forEach(item => { // Use the locally scoped URLs before reversal
          if (item.url) URL.revokeObjectURL(item.url);
      });
    };
  }, []); // Run only once on mount

  // --- Add useEffect for Stripe Confirmation ---
  useEffect(() => {
    const confirmPurchase = async () => {
      const queryParams = new URLSearchParams(window.location.search);
      const sessionId = queryParams.get('session_id');

      if (sessionId) {
        setLoading(true); // Show loading indicator during confirmation
        try {
          console.log(`Found session_id: ${sessionId}, confirming purchase...`);
          const res = await axios.get(`${API_BASE_URL}/api/confirm`, { params: { session_id: sessionId } });
          
          if (res.data && res.data.credits) {
            const purchasedCredits = parseInt(res.data.credits, 10);
            if (!isNaN(purchasedCredits) && purchasedCredits > 0) {
              console.log(`Purchase confirmed! Adding ${purchasedCredits} credits.`);
              setCredits(prev => {
                  const newTotal = prev + purchasedCredits;
                  localStorage.setItem('credits', newTotal.toString()); // Update localStorage
                  console.log(`New credit total: ${newTotal}`);
                  return newTotal;
              });
              alert(`Successfully added ${purchasedCredits} credits!`);
            } else {
               console.warn('Confirmation successful but received invalid credit amount:', res.data.credits);
               alert('Purchase confirmed, but there was an issue adding credits.');
            }
          } else {
            console.error('Confirmation failed or no credits returned:', res.data);
            alert(`Failed to confirm purchase. ${res.data?.error || 'Unknown error'}`);
          }
        } catch (error) {
          console.error('Error confirming purchase:', error);
          alert(`Error confirming purchase: ${error.response?.data?.error || error.message}`);
        } finally {
          // Clean up URL by removing the session_id query parameter
          const url = new URL(window.location);
          url.searchParams.delete('session_id');
          window.history.replaceState({}, document.title, url.toString());
          setLoading(false);
        }
      }
    };

    confirmPurchase();
  }, []); // Run only once on component mount
  // --- End useEffect ---

  // Callback to revoke object URL when component unmounts or gallery updates
  const revokeObjectUrls = useCallback(() => {
      gallery.forEach(item => URL.revokeObjectURL(item.url));
  }, [gallery]);

  useEffect(() => {
      // Cleanup on component unmount
      return () => revokeObjectUrls();
  }, [revokeObjectUrls]);
  // ----------------------------------------------

  // --- Generate Image and Save to IndexedDB ---
  const handleGenerate = async () => {
    if (!file) {
      alert('Please upload a photo first');
      return;
    }
    if (!prompt || prompt.trim() === '') {
      alert('Please add a prompt describing what you want in your JJK image');
      return;
    }
    if (credits <= 0) {
      alert('You need credits to generate images. Please purchase credits.');
      return;
    }
    
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('prompt', prompt);
    
    try {
      console.log('Sending image to backend, file size:', file.size);
      const response = await axios.post(`${API_BASE_URL}/api/generate`, formData, {
        responseType: 'blob' // Ensure we get a Blob back
      });
      
      console.log('Raw Axios Response:', response);
      const imageBlob = response.data;
      console.log('Response Data:', imageBlob);
      console.log('Type of Response Data:', typeof imageBlob, imageBlob instanceof Blob);
      console.log('Check: Is Blob and size > 0?', imageBlob && imageBlob.size > 0);
      
      // --- Save Blob to IndexedDB and update state --- 
      if (imageBlob && imageBlob.size > 0) {
          const db = await initDB();
          const newItemId = await db.add(STORE_NAME, { blob: imageBlob });
          console.log(`Image blob saved to IndexedDB with ID: ${newItemId}`);

          let objectUrl = null;
          try {
              objectUrl = URL.createObjectURL(imageBlob);
              console.log('Created Object URL:', objectUrl); 
          } catch(e) {
              console.error('Error creating object URL during generation:', e);
          }
           
          if (objectUrl) { // Only update state if URL was created
              // Add to gallery state (newest first) and update credits
              setGallery(prev => {
                  const newState = [{ id: newItemId, url: objectUrl }, ...prev];
                  console.log('Updated gallery state with new item. New length:', newState.length); // Log state update
                  return newState;
              });
              setCredits(prev => {
                const newTotal = prev - 1;
                localStorage.setItem('credits', newTotal.toString()); // Update localStorage on use
                console.log(`Credits updated and saved to localStorage: ${newTotal}`); 
                return newTotal;
              });
              setFile(null); // Clear the uploaded file state
          } else {
              alert('Image was generated and saved, but failed to create a display URL.');
          }
      } else {
          console.error('Received invalid/empty data from backend. Response data:', imageBlob);
          alert('Failed to generate image: Received invalid or empty data from server.');
      }
      // ------------------------------------------------

    } catch (err) {
      console.error("Generation Error:", err);
      
      // More detailed error logging
      if (err.response) {
        // The request was made and the server responded with a status code outside of 2xx
        console.error("Error Response:", err.response.data);
        console.error("Error Status:", err.response.status);
        console.error("Error Headers:", err.response.headers);
        alert(`API Error (${err.response.status}): ${JSON.stringify(err.response.data)}`);
      } else if (err.request) {
        // The request was made but no response was received
        console.error("Error Request:", err.request);
        alert(`Network Error: No response received from server. Check if the backend is running.`);
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error("Error Message:", err.message);
        alert(`Request Error: ${err.message}`);
      }
    } finally {
      setLoading(false);
      document.getElementById('photo-upload').value = '';
      setPrompt('');
    }
  };

  // Opens the pricing modal
  const handleBuy = () => {
    setShowModal(true);
  };

  // Handles the selection from the modal, calls backend
  const handlePurchaseOption = async (priceId) => {
    setLoading(true);
    setShowModal(false);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/checkout`, { params: { price_id: priceId } });
      if (res.data && res.data.url) {
        window.location.href = res.data.url;
      } else {
        alert('Could not initiate purchase. Please try again.');
        setLoading(false);
      }
    } catch (err) {
      console.error("Error initiating checkout:", err);
      alert('Error initiating checkout. Please check console.');
      setLoading(false);
    }
    // Note: setLoading(false) is mostly handled by page redirect or error
  };

  return (
    <>
      {/* Log moved inside render */}
      {console.log('Rendering App component with gallery state:', gallery)}
      {/* Modal Structure */}
      {showModal && (
        <div style={modalOverlayStyle}>
          <div style={modalContentStyle}>
            <button style={closeButtonStyle} onClick={() => setShowModal(false)}>&times;</button>
            <h2>Choose Your Credits Pack</h2>
            <button
              style={modalButtonStyle}
              onClick={() => handlePurchaseOption('price_3')}
              disabled={loading}
            >
              $3 for 10 Photos
            </button>
            <button
              style={modalButtonStyle}
              onClick={() => handlePurchaseOption('price_10')}
              disabled={loading}
            >
              $10 for 50 Photos
            </button>
            {loading && <p>Processing...</p>}
          </div>
        </div>
      )}

      <header>
        <h1 className="cursed-title">Cursed Image Generation</h1>
      </header>
      <main style={{ padding: '20px' }}>
        <section className="upload-section" style={{ marginBottom: '20px' }}>
          <label htmlFor="photo-upload">Upload Photo</label>
          <input id="photo-upload" type="file" accept="image/*" onChange={e => setFile(e.target.files[0])} />
          <label htmlFor="prompt">Add a prompt (required)</label>
          <textarea 
            id="prompt" 
            rows={4} 
            placeholder="Describe what you want in your Jujutsu Kaisen style image... Style elements will be added automatically." 
            value={prompt} 
            onChange={e => setPrompt(e.target.value)}
            required
          />
          <button className="generate-btn" onClick={handleGenerate} disabled={loading || credits <= 0}>
            {loading ? 'Generating...' : `Generate (${credits} credit${credits !== 1 ? 's' : ''} left)`}
          </button>
           {credits <= 0 && !loading && <p style={{color: 'orange', marginTop: '5px'}}>You need credits to generate!</p>}
        </section>
        <section className="pricing-section" style={{ marginBottom: '20px' }}>
          <h2>Pricing</h2>
          {/* Updated pricing text */}
          <p>1 Credit = 1 Photo</p>
          <p>$3 for 10 Photos</p>
          <p>$10 for 50 Photos</p>
          {/* Removed old list */}
          <button className="buy-btn" onClick={handleBuy} disabled={loading}>
             {loading ? 'Processing...' : 'Buy Credits'}
          </button>
        </section>
        {gallery.length > 0 && (
          <section className="generated-section">
            <h2>Generated Image</h2>
            <div className="generated-image-container">
              <img src={gallery[0].url} alt="latest generated" className="generated-image" />
            </div>
          </section>
        )}
        <section className="history-section">
          <h2>Image Generations</h2>
          <div className="gallery">
            {gallery.length === 0 ? (
              <div className="no-history">No image generations yet. Your last generations will appear here.</div>
            ) : (
              gallery.map((item) => (
                <div key={item.id} className="gallery-item" style={{ marginBottom: '20px', position: 'relative' }}>
                  <img src={item.url} alt={`gen-${item.id}`} style={{ width: '100%', borderRadius: '8px' }} />
                  <a 
                    href={item.url} 
                    download={`jujutsu-kaisen-image-${item.id}.png`}
                    style={{
                      display: 'block',
                      marginTop: '10px',
                      padding: '8px 15px',
                      backgroundColor: '#e91e63',
                      color: 'white',
                      textAlign: 'center',
                      borderRadius: '5px',
                      textDecoration: 'none',
                      fontWeight: 'bold'
                    }}
                  >
                    Download
                  </a>
                </div>
              ))
            )}
          </div>
        </section>
      </main>
      <footer></footer>
    </>
  );
}

export default App;

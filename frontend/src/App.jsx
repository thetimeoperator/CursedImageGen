import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [credits, setCredits] = useState(() => parseInt(localStorage.getItem('credits') || '0'));
  const [gallery, setGallery] = useState(() => JSON.parse(localStorage.getItem('gallery') || '[]'));
  const [loading, setLoading] = useState(false);

  useEffect(() => { localStorage.setItem('credits', credits); }, [credits]);
  useEffect(() => { localStorage.setItem('gallery', JSON.stringify(gallery)); }, [gallery]);

  const handleGenerate = async () => {
    if (!file) return alert('Select a file');
    if (credits <= 0) return alert('No credits left');
    setLoading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('prompt', prompt);
      const res = await axios.post('/api/generate', form);
      const { url } = res.data;
      setGallery([url, ...gallery]);
      setCredits(credits - 1);
      setFile(null);
      setPrompt('');
    } catch(err) {
      console.error(err);
      alert('Generation failed');
    } finally { setLoading(false); }
  };

  const handleBuy = async () => {
  try {
    const res = await axios.get('/api/checkout');
    if(res.data && res.data.url) {
      window.location.href = res.data.url;
    } else if(res.request && res.request.responseURL) {
      window.location.href = res.request.responseURL;
    } else {
      alert('Stripe session failed.');
    }
  } catch (err) {
    alert('Stripe checkout error');
  }
};

  return (
    <>
      <header>
        <h1 className="cursed-title">Cursed Image Generation</h1>
      </header>
      <main style={{ padding: '20px' }}>
        <section className="upload-section" style={{ marginBottom: '20px' }}>
          <label htmlFor="photo-upload">Upload Photo</label>
          <input id="photo-upload" type="file" accept="image/*" onChange={e => setFile(e.target.files[0])} />
          <label htmlFor="prompt">Add a prompt (optional)</label>
          <textarea id="prompt" rows={4} placeholder="Add optional prompt details..." value={prompt} onChange={e => setPrompt(e.target.value)} />
          <button className="generate-btn" onClick={handleGenerate} disabled={loading || credits <= 0}>
            {loading ? 'Generating...' : 'Generate'}
          </button>
        </section>
        <section className="pricing-section" style={{ marginBottom: '20px' }}>
          <h2>Pricing</h2>
          <div className="credits">Photos Owned: {credits}</div>
          <ul>
            <li>$3 — 10 photos</li>
            <li>$10 — 50 photos</li>
            <li>$20 — 120 photos</li>
            <li>$30 — 200 photos</li>
          </ul>
          <button className="buy-btn" onClick={handleBuy}>Buy Photos</button>
        </section>
        {gallery.length > 0 && (
          <section className="generated-section">
            <h2>Generated Image</h2>
            <div className="generated-image-container">
              <img src={gallery[0]} alt="latest generated" className="generated-image" />
            </div>
          </section>
        )}
        <section className="history-section">
          <h2>History</h2>
          <div className="gallery">
            {gallery.length === 0 ? (
              <div className="no-history">No history yet. Your last generations will appear here.</div>
            ) : (
              gallery.map((url, i) => <img key={i} src={url} alt={`gen-${i}`} />)
            )}
          </div>
        </section>
      </main>
      <footer></footer>
    </>
  );
}

export default App;

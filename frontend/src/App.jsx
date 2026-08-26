import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [jobDesc, setJobDesc] = useState('');
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFiles(e.target.files);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!jobDesc || files.length === 0) {
      alert("Please enter the job description and select at least 1 CV!");
      return;
    }

    setLoading(true);
    
    const formData = new FormData();
    formData.append('job_description', jobDesc);
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const response = await axios.post('http://127.0.0.1:8000/evaluate-batch/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResults(response.data.leaderboard);
    } catch (error) {
      console.error(error);
      alert("An error occurred. Please ensure the backend server is running.");
    }
    
    setLoading(false);
  };

  return (
    <div className="container">
      <header>
        <h1>MyATS Leaderboard</h1>
        <p>AI-Powered Dynamic CV Matching Engine</p>
      </header>

      <form onSubmit={handleSubmit} className="upload-form">
        <textarea 
          placeholder="Paste the job description here (The system will automatically extract keywords)..."
          value={jobDesc}
          onChange={(e) => setJobDesc(e.target.value)}
          rows="5"
        />
        
        <input 
          type="file" 
          multiple 
          accept=".pdf"
          onChange={handleFileChange} 
        />
        
        <button type="submit" disabled={loading}>
          {loading ? "🧠 AI is Analyzing..." : "Rank Candidates"}
        </button>
      </form>

      {results && (
        <div className="results-container">
          <h2>🏆 Top Candidates</h2>
          {results.map((candidate, index) => (
            <div key={index} className="candidate-card">
              <div className="card-header">
                <h3>#{candidate.rank} - {candidate.candidate_file}</h3>
                <span className="score">{candidate.match_score}</span>
              </div>
              <p><strong>Status:</strong> {candidate.evaluation_status}</p>
              <p><strong>Matched Skills:</strong> {candidate.matched_skills.join(", ") || "None found"}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default App;
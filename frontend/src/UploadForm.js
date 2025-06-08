import React, { useState } from 'react';

const UploadForm = () => {
  const [email, setEmail] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [responseMessage, setResponseMessage] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  const BACKEND_API_URL = process.env.REACT_APP_BACKEND_API_URL; // Declare and use it

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!email || !file) {
      alert('Please provide both email and a file.');
      return;
    }

    // Create a FormData object
    const formData = new FormData();
    formData.append('email', email);
    formData.append('file', file);

    try {
      setLoading(true);
      setResponseMessage('');
      setDownloadUrl('');

      // Replace this URL with your backend API endpoint
      const response = await fetch(`${BACKEND_API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      // Handle response
      if (response.ok) {
        const result = await response.json();
        setResponseMessage('File uploaded successfully!');

        // Fetch the download link using the returned file name
        // THIS IS THE LINE TO FIX for the download link fetch
        const linkResponse = await fetch(`${BACKEND_API_URL}/get-download-link?file_name=${result.file_name}`); // <--- CORRECTED LINE
        if (linkResponse.ok) {
          const linkResult = await linkResponse.json();
          setDownloadUrl(linkResult.download_url);
        } else {
          setResponseMessage('Failed to generate download link.');
        }
      } else {
        setResponseMessage('File upload failed.');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setResponseMessage('An error occurred during file upload.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="email">Email:</label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <div>
        <label htmlFor="file">Upload File:</label>
        <input
          type="file"
          id="file"
          onChange={(e) => setFile(e.target.files[0])}
          required
        />
      </div>
      <button type="submit" disabled={loading}>
        {loading ? 'Uploading...' : 'Submit'}
      </button>
      {responseMessage && <p>{responseMessage}</p>}
      {downloadUrl && (
        <div>
          <p>Your download link:</p>
          <a href={downloadUrl} target="_blank" rel="noopener noreferrer">{downloadUrl}</a>
        </div>
      )}
    </form>
  );
};

export default UploadForm;
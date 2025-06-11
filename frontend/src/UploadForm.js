import React, { useState } from 'react';

const UploadForm = () => {
  const [email, setEmail] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [responseMessage, setResponseMessage] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');

  // This will now hold your CloudFront domain (e.g., "https://cf.aws.lupan.ca")
  // and will be set during the `npm run build` process via REACT_APP_BACKEND_API_URL
  const BACKEND_BASE_URL = process.env.REACT_APP_BACKEND_API_URL;

  // Optional: For debugging, you can log this value
  // console.log("Frontend is configured to use API base URL:", BACKEND_BASE_URL);

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

      // Construct the API URL by appending the /api/ prefix and the specific endpoint
      const uploadUrl = `${BACKEND_BASE_URL}/api/upload`;
      const response = await fetch(uploadUrl, {
        method: 'POST',
        body: formData,
      });

      // Handle response
      if (response.ok) {
        const result = await response.json();
        setResponseMessage('File uploaded successfully!');

        // Fetch the download link using the returned file name
        const downloadLinkUrl = `${BACKEND_BASE_URL}/api/get-download-link?file_name=${result.file_name}`;
        const linkResponse = await fetch(downloadLinkUrl); // <--- CORRECTED LINE (again, just ensuring the prefix)

        if (linkResponse.ok) {
          const linkResult = await linkResponse.json();
          setDownloadUrl(linkResult.download_url);
        } else {
          // It's good practice to log the full error response for debugging
          const errorText = await linkResponse.text();
          console.error('Failed to generate download link. Response Status:', linkResponse.status, 'Response Body:', errorText);
          setResponseMessage(`Failed to generate download link. Status: ${linkResponse.status}`);
        }
      } else {
        // Log the full error response for debugging
        const errorText = await response.text();
        console.error('File upload failed. Response Status:', response.status, 'Response Body:', errorText);
        setResponseMessage(`File upload failed. Status: ${response.status}`);
      }
    } catch (error) {
      // Catch network errors, CORS preflight errors, etc.
      console.error('An error occurred during file operation:', error);
      setResponseMessage('An error occurred during file operation.');
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
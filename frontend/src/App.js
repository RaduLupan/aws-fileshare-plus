import React, { useState, useEffect } from 'react';

// --- Imports for modern AWS Amplify ---
import { Amplify } from 'aws-amplify';
import { fetchAuthSession } from 'aws-amplify/auth';
import { withAuthenticator, Button, Heading, Text, Flex, Card } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';


// --- UPDATED: Debugging and Configuration ---
const amplifyConfig = {
  Auth: {
    Cognito: {
      region: process.env.REACT_APP_AWS_REGION,
      userPoolId: process.env.REACT_APP_USER_POOL_ID,
      userPoolWebClientId: process.env.REACT_APP_USER_POOL_CLIENT_ID,
    }
  }
};

// Log the configuration to the console for debugging purposes.
// This will show up in your browser's Developer Tools console (F12).
console.log("Attempting to configure Amplify with:", amplifyConfig.Auth.Cognito);

Amplify.configure(amplifyConfig);

// The `signOut` and `user` props are automatically passed in by withAuthenticator
function App({ signOut, user }) {
  const [file, setFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  const [tier, setTier] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  // --- Function to get the user's tier from their JWT ---
  useEffect(() => {
    const getUserTier = async () => {
        try {
            // Use the new fetchAuthSession function to get the current session details
            const { tokens } = await fetchAuthSession();
            // The groups are in the 'cognito:groups' claim of the access token's payload
            const userGroups = tokens?.accessToken.payload['cognito:groups'] || [];
            if (userGroups.includes('premium-tier')) {
                setTier('Premium');
            } else {
                setTier('Free');
            }
        } catch (err) {
            console.log('Error fetching user session:', err);
            setTier('Free'); // Default to Free tier if there's an error
        }
    };
    getUserTier();
  }, [user]); // Rerun this effect if the user object changes

  const onFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadMessage('');
    setDownloadUrl('');
  };

  // --- Using the modern fetchAuthSession function ---
  const getJwtToken = async () => {
    try {
      const { tokens } = await fetchAuthSession();
      // The accessToken object has a toString() method which returns the JWT string
      return tokens?.accessToken.toString();
    } catch (error) {
      console.error("Error getting JWT token", error);
      // It's good practice to sign the user out if their session is invalid
      signOut();
      return null;
    }
  };

  const onFileUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setUploadMessage('Uploading...');
    setDownloadUrl('');

    const token = await getJwtToken();
    if (!token) {
      setUploadMessage('Authentication error. Please sign in again.');
      setIsUploading(false);
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const apiUrl = process.env.REACT_APP_CLOUDFRONT_CUSTOM_DOMAIN_URL;
      
      const uploadResponse = await fetch(`${apiUrl}/api/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}` // Add the Authorization header
        },
        body: formData,
      });

      const uploadData = await uploadResponse.json();
      if (!uploadResponse.ok) throw new Error(uploadData.message || 'Upload failed');

      setUploadMessage('Upload successful! Generating download link...');
      
      const fileName = uploadData.file_name;
      const downloadResponse = await fetch(`${apiUrl}/api/get-download-link?file_name=${fileName}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const downloadData = await downloadResponse.json();
      if (!downloadResponse.ok) throw new Error(downloadData.message || 'Could not get download link');

      setDownloadUrl(downloadData.download_url);
      setUploadMessage(`Success! Link for ${tier} tier users (expires in ${Math.round(downloadData.expires_in_seconds / 86400)} days):`);

    } catch (error) {
      console.error('An error occurred:', error);
      setUploadMessage(`Error: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  // --- Function to handle the tier upgrade ---
  const handleUpgrade = async () => {
    setUploadMessage('Upgrading...');
    const token = await getJwtToken();
    if (!token) {
      setUploadMessage('Authentication error. Please sign in again.');
      return;
    }

    try {
      const apiUrl = process.env.REACT_APP_CLOUDFRONT_CUSTOM_DOMAIN_URL;
      const response = await fetch(`${apiUrl}/api/upgrade`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.message || 'Upgrade failed');

      setUploadMessage('Upgrade successful! Please sign out and sign back in to see the change.');
      // NOTE: For the new tier to reflect in the token, the user must get a new session.
      
    } catch (error) {
      console.error('An error occurred during upgrade:', error);
      setUploadMessage(`Error: ${error.message}`);
    }
  };

  return (
    <Flex direction="column" alignItems="center" justifyContent="center" minHeight="100vh" padding="2rem" background="var(--amplify-colors-background-secondary)">
      <Card variation="elevated" width="100%" maxWidth="500px">
        <Flex direction="row" justifyContent="space-between" alignItems="center">
            <Heading level={3}>FileShare</Heading>
            <Button onClick={signOut} variation="primary" size="small">Sign Out</Button>
        </Flex>

        <Text marginTop="1rem">Welcome, <strong>{user.attributes.email}</strong></Text>
        <Text>Your current tier: <strong>{tier}</strong></Text>

        <Flex as="form" direction="column" marginTop="2rem" gap="1rem">
          <input type="file" onChange={onFileChange} />
          <Button onClick={onFileUpload} variation="primary" isDisabled={!file || isUploading} isLoading={isUploading}>Upload File</Button>
        </Flex>

        {uploadMessage && <Text marginTop="1rem">{uploadMessage}</Text>}
        {downloadUrl && <Text as="a" href={downloadUrl} target="_blank" rel="noopener noreferrer" wordBreak="break-all">{downloadUrl}</Text>}

        {tier === 'Free' && (
          <Button onClick={handleUpgrade} marginTop="2rem" isFullWidth={true}>
            Upgrade to Premium (Free for now)
          </Button>
        )}
      </Card>
    </Flex>
  );
}

// --- UPDATED: Export the App component wrapped in the Authenticator ---
// This customization makes the UI explicitly ask for an "Email" address.
export default withAuthenticator(App, {
  loginMechanisms: ['email'],
});

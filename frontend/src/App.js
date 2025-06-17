import React, { useState, useEffect } from 'react';

import { Amplify } from 'aws-amplify';
import { fetchAuthSession } from 'aws-amplify/auth';
import { Authenticator, Button, Heading, Text, Flex, Card } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';


// --- FOR DEBUGGING ONLY: Hardcoding configuration values ---
// This bypasses the entire process.env system to isolate the problem.
const amplifyConfig = {
  Auth: {
    Cognito: {
      // Replace these placeholder strings with your actual values
      region: "us-east-2",
      userPoolId: "us-east-2_1R3fvhChs",
      userPoolWebClientId: "6kbrftjpkm3t7l5hcnv7c0vpaa",
    }
  }
};

console.log("HARDCODED CONFIG: Configuring Amplify with:", amplifyConfig.Auth.Cognito);
Amplify.configure(amplifyConfig);


// This is the inner component that will be rendered ONLY after a successful login.
const AppContent = ({ user, signOut }) => {
  const [file, setFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  const [tier, setTier] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  // Function to get the user's tier from their JWT
  useEffect(() => {
    const getUserTier = async () => {
        try {
            const { tokens } = await fetchAuthSession();
            const userGroups = tokens?.accessToken.payload['cognito:groups'] || [];
            if (userGroups.includes('premium-tier')) {
                setTier('Premium');
            } else {
                setTier('Free');
            }
        } catch (err) {
            console.log('Error fetching user session:', err);
            setTier('Free');
        }
    };
    getUserTier();
  }, [user]);

  const onFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadMessage('');
    setDownloadUrl('');
  };

  const getJwtToken = async () => {
    try {
      const { tokens } = await fetchAuthSession();
      return tokens?.accessToken.toString();
    } catch (error) {
      console.error("Error getting JWT token", error);
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
      // NOTE: We still use process.env for the API URL, as that part is working.
      const apiUrl = process.env.REACT_APP_CLOUDFRONT_CUSTOM_DOMAIN_URL;
      const uploadResponse = await fetch(`${apiUrl}/api/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
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
};


// The main App component is now a wrapper that uses the Authenticator component
export default function App() {
  return (
    // The Authenticator component provides the entire UI flow.
    <Authenticator loginMechanisms={['email']}>
      {/* This is a "render prop". Once the user is signed in, */}
      {/* this function is called with the `signOut` function and `user` object. */}
      {({ signOut, user }) => (
        <AppContent signOut={signOut} user={user} />
      )}
    </Authenticator>
  );
}

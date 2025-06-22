import React, { useState, useEffect } from 'react';

// Import necessary Amplify v6 components and utilities
import { fetchAuthSession, signOut as amplifySignOut, signUp, signIn, confirmSignUp, getCurrentUser } from 'aws-amplify/auth';
import { Button, Heading, Text, Flex, Card } from '@aws-amplify/ui-react';
import { Amplify } from 'aws-amplify';
import '@aws-amplify/ui-react/styles.css';

// Import the configuration from the separate module
import { configureAmplify } from './amplifyConfig.js';

// Configure Amplify - must be done before any Amplify functions are called
try {
  configureAmplify();
  console.log("Amplify initial configuration completed in App.jsx");
} catch (error) {
  console.error("Failed to configure Amplify in App.jsx:", error);
}

// Custom Authentication Component
const CustomAuth = ({ onAuthenticated }) => {
  const [isSignUp, setIsSignUp] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [confirmationCode, setConfirmationCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [needsConfirmation, setNeedsConfirmation] = useState(false);
  const [generatedUsername, setGeneratedUsername] = useState('');  const handleSignUp = async (e) => {
    e.preventDefault();
    console.log('=== CUSTOM SIGNUP FUNCTION CALLED ===');
    console.log('Email:', email);
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    setIsLoading(true);
    setError('');
      try {
      // Generate a unique username from email (remove @ and . and add timestamp)
      const username = email.replace(/[@.]/g, '') + Date.now().toString().slice(-4);
      console.log('Generated username:', username);
      setGeneratedUsername(username);
      
      const result = await signUp({
        username: username,
        password: password,
        attributes: {
          email: email,
        },
        autoSignIn: {
          enabled: true,
        }
      });      console.log('SignUp successful:', result);
      
      // Check if auto sign-in worked
      if (result.isSignUpComplete && result.nextStep?.signInStep === 'DONE') {
        console.log('Auto sign-in successful!');
        onAuthenticated();      } else if (result.isSignUpComplete) {
        console.log('Signup completed successfully! User can now sign in.');
        setError(`Account created successfully! Username: ${username}. You can sign in with your email or this username.`);
        setIsSignUp(false); // Switch to sign-in mode
      } else {
        console.log('Signup requires additional steps:', result.nextStep);
        setError('Account created! Please check the console for next steps.');
        setIsSignUp(false);
      }
    } catch (error) {
      console.error('SignUp error:', error);
      setError(error.message || 'Sign up failed');
    } finally {
      setIsLoading(false);
    }
  };
  const handleSignIn = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      // Try signing in with email first (alias), then fall back to generated username
      let result;
      let loginMethod = 'email';
      
      try {
        result = await signIn({
          username: email,
          password: password,
        });
        console.log('SignIn with email successful:', result);
      } catch (emailError) {
        console.log('Sign in with email failed, trying with generated username:', emailError.message);
        
        if (generatedUsername) {
          loginMethod = 'username';
          result = await signIn({
            username: generatedUsername,
            password: password,
          });
          console.log('SignIn with generated username successful:', result);
        } else {
          throw emailError;
        }
      }
      
      console.log(`SignIn successful using ${loginMethod}:`, result);
      if (result.isSignedIn) {
        onAuthenticated();
      }
    } catch (error) {
      console.error('SignIn error:', error);
      setError(error.message || 'Sign in failed');
    } finally {
      setIsLoading(false);
    }
  };
  const handleConfirmSignUp = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      await confirmSignUp({
        username: generatedUsername, // Use the generated username for confirmation
        confirmationCode: confirmationCode,
      });
      
      console.log('Confirmation successful');
      setNeedsConfirmation(false);
      // Now try to sign in with email (since email alias is enabled)
      await handleSignIn(e);
    } catch (error) {
      console.error('Confirmation error:', error);
      setError(error.message || 'Confirmation failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (needsConfirmation) {
    return (
      <Card style={{ maxWidth: '400px', margin: '2rem auto', padding: '2rem' }}>
        <Heading level={2}>Confirm Your Account</Heading>
        <Text>Please check your email for a confirmation code.</Text>
        <form onSubmit={handleConfirmSignUp}>
          <div style={{ marginBottom: '1rem' }}>
            <label>Confirmation Code:</label>
            <input
              type="text"
              value={confirmationCode}
              onChange={(e) => setConfirmationCode(e.target.value)}
              required
              style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
            />
          </div>
          {error && <Text color="red" style={{ marginBottom: '1rem' }}>{error}</Text>}
          <Button type="submit" isLoading={isLoading} style={{ width: '100%' }}>
            Confirm Account
          </Button>
        </form>
      </Card>
    );
  }

  return (
    <Card style={{ maxWidth: '400px', margin: '2rem auto', padding: '2rem' }}>
      <Heading level={2}>{isSignUp ? 'Create Account' : 'Sign In'}</Heading>
      <form onSubmit={isSignUp ? handleSignUp : handleSignIn}>
        <div style={{ marginBottom: '1rem' }}>
          <label>Email:</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
          />
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
          />
        </div>
        {isSignUp && (
          <div style={{ marginBottom: '1rem' }}>
            <label>Confirm Password:</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
            />
          </div>
        )}
        {error && <Text color="red" style={{ marginBottom: '1rem' }}>{error}</Text>}
        <Button type="submit" isLoading={isLoading} style={{ width: '100%', marginBottom: '1rem' }}>
          {isSignUp ? 'Create Account' : 'Sign In'}
        </Button>
      </form>
      <Button
        variation="link"
        onClick={() => {
          setIsSignUp(!isSignUp);
          setError('');
        }}
        style={{ width: '100%' }}
      >
        {isSignUp ? 'Already have an account? Sign In' : 'Need an account? Sign Up'}
      </Button>
    </Card>
  );
};

// This is the inner component that will be rendered ONLY after a successful login.
const AppContent = ({ user, signOut }) => {
  const [file, setFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  const [tier, setTier] = useState('Free');
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
        } catch (error) {
            console.error('Error getting user tier:', error);
            setTier('Free'); // Default to free on error
        }
    };

    getUserTier();
  }, []);

  // Function to get JWT token for backend requests
  const getJwtToken = async () => {
    try {
      const { tokens } = await fetchAuthSession();
      return tokens?.idToken?.toString();
    } catch (error) {
      console.error('Error getting JWT token:', error);
      return null;
    }
  };

  const onFileChange = (event) => {
    setFile(event.target.files[0]);
    setUploadMessage('');
    setDownloadUrl('');
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

    try {
      const apiUrl = import.meta.env.VITE_CLOUDFRONT_CUSTOM_DOMAIN_URL;
      const formData = new FormData();
      formData.append('file', file);

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
      const apiUrl = import.meta.env.VITE_CLOUDFRONT_CUSTOM_DOMAIN_URL;
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
        <Flex direction="column" padding="2rem">
          <Heading level={1} textAlign="center">FileShare Plus</Heading>
          <Text textAlign="center" marginTop="0.5rem" color="var(--amplify-colors-font-secondary)">
            Upload and share files securely ({tier} tier)
          </Text>
          <Button onClick={signOut} variation="link" alignSelf="flex-end" marginTop="1rem">Sign Out</Button>
        </Flex>
        
        <Flex direction="column" gap="1rem" padding="0 2rem 2rem">
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

// The main App component uses custom authentication instead of Authenticator
export default function App() {
  const [isAmplifyConfigured, setIsAmplifyConfigured] = useState(false);
  const [configError, setConfigError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    const initializeAmplify = async () => {
      try {
        console.log("Initializing Amplify configuration...");
        
        // Verify the configuration is present
        const config = Amplify.getConfig();
        console.log("Current Amplify config in App.jsx:", config);
        
        if (config?.Auth?.Cognito?.userPoolId) {
          setIsAmplifyConfigured(true);
          console.log("Amplify is properly configured with UserPool");
          
          // Check if user is already signed in
          try {
            const currentUser = await getCurrentUser();
            console.log("Current user found:", currentUser);
            setUser(currentUser);
            setIsAuthenticated(true);
          } catch (error) {
            console.log("No current user session");
          }
        } else {
          throw new Error("Amplify Auth configuration is missing or incomplete");
        }
      } catch (error) {
        console.error("Failed to verify Amplify configuration in App.jsx:", error);
        setConfigError(error.message);
      } finally {
        setIsCheckingAuth(false);
      }
    };

    initializeAmplify();
  }, []);

  const handleAuthenticated = async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setIsAuthenticated(true);
    } catch (error) {
      console.error("Error getting current user after authentication:", error);
    }
  };

  const handleSignOut = async () => {
    try {
      await amplifySignOut();
      setIsAuthenticated(false);
      setUser(null);
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  if (configError) {
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <h2>Configuration Error</h2>
        <p>{configError}</p>
        <p>Please check your environment variables and try again.</p>
      </div>
    );
  }

  if (!isAmplifyConfigured || isCheckingAuth) {
    return (
      <div style={{ padding: '20px' }}>
        <h2>Loading...</h2>
        <p>Configuring authentication...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <CustomAuth onAuthenticated={handleAuthenticated} />;
  }

  return <AppContent signOut={handleSignOut} user={user} />;
}

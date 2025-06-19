import React, { useState, useEffect } from 'react';

// --- NEW: Import AWS SDK v3 Cognito Client ---
import {
  CognitoIdentityProviderClient,
  SignUpCommand,
  ConfirmSignUpCommand,
  InitiateAuthCommand,
  RespondToAuthChallengeCommand,
  GlobalSignOutCommand,
  GetUserCommand,
  // --- ADDED: These were missing for handleUpgrade ---
  AdminAddUserToGroupCommand,
  AdminRemoveUserFromGroupCommand,
} from "@aws-sdk/client-cognito-identity-provider";

// Basic styling for the custom forms
const formContainerStyle = { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', gap: '15px' };
const inputStyle = { padding: '10px', fontSize: '16px', width: '300px' };
const buttonStyle = { padding: '10px 20px', fontSize: '16px', cursor: 'pointer' };

// --- NEW: Cognito Client Initialization ---
// These values come from environment variables injected by the CI/CD pipeline.
// Note: These are now accessed directly, not via Amplify.configure
const COGNITO_REGION = process.env.VITE_AWS_REGION;
const COGNITO_USER_POOL_ID = process.env.VITE_USER_POOL_ID;
const COGNITO_USER_POOL_CLIENT_ID = process.env.VITE_USER_POOL_CLIENT_ID;

// Initialize the Cognito Identity Provider Client
const cognitoClient = new CognitoIdentityProviderClient({ region: COGNITO_REGION });

// --- Main App Component ---
export default function App() {
  // CORRECTED: Added variable names for useState
  const = useState('loading'); // Initial state to check current user
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');

  // Check for a logged-in user when the app loads
  useEffect(() => {
    const checkUser = async () => {
      try {
        // Attempt to get current user session from local storage
        const storedSession = localStorage.getItem('cognitoSession');
        if (storedSession) {
          const session = JSON.parse(storedSession);
          // Basic check if token is expired (needs more robust validation and refresh logic for production)
          if (session.AccessToken && session.ExpiresIn > Date.now() / 1000) {
            const getUserCommand = new GetUserCommand({
              AccessToken: session.AccessToken,
            });
            const userData = await cognitoClient.send(getUserCommand);
            setUser({ username: userData.Username, attributes: { email: userData.UserAttributes.find(attr => attr.Name === 'email')?.Value } });
            setAuthState('authenticated');
          } else {
            setAuthState('signIn');
          }
        } else {
          setAuthState('signIn');
        }
      } catch (err) {
        console.error('Error checking user session:', err);
        setAuthState('signIn');
      }
    };
    checkUser();
  },); // Empty dependency array means this runs once on mount

  const handleSignOut = async () => {
    try {
      const storedSession = localStorage.getItem('cognitoSession');
      if (storedSession) {
        const session = JSON.parse(storedSession);
        const globalSignOutCommand = new GlobalSignOutCommand({
          AccessToken: session.AccessToken,
        });
        await cognitoClient.send(globalSignOutCommand);
      }
      localStorage.removeItem('cognitoSession');
      setUser(null);
      setAuthState('signIn');
    } catch (err) {
      console.error('Error signing out: ', err);
      setError('Error signing out. Please try again.');
    }
  };

  // Conditionally render the correct component based on authState
  if (authState === 'loading') {
    return <div style={formContainerStyle}>Loading...</div>;
  }
  if (authState === 'authenticated' && user) {
    return <AppContent user={user} signOut={handleSignOut} />;
  }
  if (authState === 'confirmSignUp') {
    return <ConfirmSignUpForm setAuthState={setAuthState} setError={setError} />;
  }
  if (authState === 'signIn') {
    return <SignInForm setAuthState={setAuthState} setUser={setUser} error={error} setError={setError} />;
  }
  return <SignUpForm setAuthState={setAuthState} error={error} setError={setError} />;
}


// --- Custom Sign-In Component ---
const SignInForm = ({ setAuthState, setUser, error, setError }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [challengeName, setChallengeName] = useState('');
  // CORRECTED: Added variable name for useState
  const = useState(''); // Used for MFA challenges

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const initiateAuthCommand = new InitiateAuthCommand({
        AuthFlow: "USER_PASSWORD_AUTH",
        ClientId: COGNITO_USER_POOL_CLIENT_ID,
        AuthParameters: {
          USERNAME: email,
          PASSWORD: password,
        },
      });
      const response = await cognitoClient.send(initiateAuthCommand);

      if (response.ChallengeName) {
        setChallengeName(response.ChallengeName);
        setSession(response.Session);
        setError(`MFA required: ${response.ChallengeName}`);
      } else if (response.AuthenticationResult) {
        const authResult = response.AuthenticationResult;
        localStorage.setItem('cognitoSession', JSON.stringify({
          AccessToken: authResult.AccessToken,
          IdToken: authResult.IdToken,
          RefreshToken: authResult.RefreshToken,
          ExpiresIn: Date.now() / 1000 + authResult.ExpiresIn, // Store expiration timestamp
        }));
        const getUserCommand = new GetUserCommand({ AccessToken: authResult.AccessToken });
        const userData = await cognitoClient.send(getUserCommand);
        setUser({ username: userData.Username, attributes: { email: userData.UserAttributes.find(attr => attr.Name === 'email')?.Value } });
        setAuthState('authenticated');
      }
    } catch (err) {
      console.error('Error signing in:', err);
      setError(err.message |
| 'An error occurred during sign in.');
    }
  };

  const handleMfaSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const respondToAuthChallengeCommand = new RespondToAuthChallengeCommand({
        ChallengeName: challengeName,
        ClientId: COGNITO_USER_POOL_CLIENT_ID,
        Session: session,
        ChallengeResponses: {
          USERNAME: email,
          // For SMS_MFA, the key is 'SMS_MFA_CODE'
          // For SOFTWARE_TOKEN_MFA, the key is 'SOFTWARE_TOKEN_MFA_CODE'
          // This example assumes SMS_MFA or a generic code
          'SMS_MFA_CODE': mfaCode, // Adjust key based on challengeName if needed
        },
      });
      const response = await cognitoClient.send(respondToAuthChallengeCommand);
      if (response.AuthenticationResult) {
        const authResult = response.AuthenticationResult;
        localStorage.setItem('cognitoSession', JSON.stringify({
          AccessToken: authResult.AccessToken,
          IdToken: authResult.IdToken,
          RefreshToken: authResult.RefreshToken,
          ExpiresIn: Date.now() / 1000 + authResult.ExpiresIn,
        }));
        const getUserCommand = new GetUserCommand({ AccessToken: authResult.AccessToken });
        const userData = await cognitoClient.send(getUserCommand);
        setUser({ username: userData.Username, attributes: { email: userData.UserAttributes.find(attr => attr.Name === 'email')?.Value } });
        setAuthState('authenticated');
      }
    } catch (err) {
      console.error('Error submitting MFA:', err);
      setError(err.message |
| 'An error occurred during MFA submission.');
    }
  };

  return (
    <div style={formContainerStyle}>
      <h2>Sign In</h2>
      {challengeName? (
        <form onSubmit={handleMfaSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <p>Enter your {challengeName === 'SMS_MFA'? 'SMS' : 'MFA'} code:</p>
          <input type="text" value={mfaCode} onChange={(e) => setMfaCode(e.target.value)} placeholder="MFA Code" style={inputStyle} />
          <button type="submit" style={buttonStyle}>Submit MFA</button>
        </form>
      ) : (
        <form onSubmit={handleSignIn} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" style={inputStyle} />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" style={inputStyle} />
          <button type="submit" style={buttonStyle}>Sign In</button>
        </form>
      )}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <button onClick={() => setAuthState('signUp')} style={{ background: 'none', border: 'none', color: 'blue', cursor: 'pointer' }}>
        Don't have an account? Sign Up
      </button>
    </div>
  );
};


// --- Custom Sign-Up Component ---
const SignUpForm = ({ setAuthState, error, setError }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const signUpCommand = new SignUpCommand({
        ClientId: COGNITO_USER_POOL_CLIENT_ID,
        Username: email,
        Password: password,
        UserAttributes: [{ Name: 'email', Value: email }],
      });
      await cognitoClient.send(signUpCommand);
      sessionStorage.setItem('tempUsername', email); // Store username for confirmation
      setAuthState('confirmSignUp');
    } catch (err) {
      console.error('Error signing up:', err);
      setError(err.message |
| 'An error occurred during sign up.');
    }
  };

  return (
    <div style={formContainerStyle}>
      <h2>Create Account</h2>
      <form onSubmit={handleSignUp} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" style={inputStyle} />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" style={inputStyle} />
        <button type="submit" style={buttonStyle}>Create Account</button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <button onClick={() => setAuthState('signIn')} style={{ background: 'none', border: 'none', color: 'blue', cursor: 'pointer' }}>
        Already have an account? Sign In
      </button>
    </div>
  );
};


// --- Custom Confirmation Component ---
const ConfirmSignUpForm = ({ setAuthState, setError }) => {
  const [code, setCode] = useState('');
  const [localError, setLocalError] = useState(''); // Use local error state

  const handleConfirmSignUp = async (e) => {
    e.preventDefault();
    setLocalError('');
    const username = sessionStorage.getItem('tempUsername');
    if (!username) {
      setLocalError('Could not find username for confirmation. Please try signing up again.');
      return;
    }
    try {
      const confirmSignUpCommand = new ConfirmSignUpCommand({
        ClientId: COGNITO_USER_POOL_CLIENT_ID,
        Username: username,
        ConfirmationCode: code,
      });
      await cognitoClient.send(confirmSignUpCommand);
      sessionStorage.removeItem('tempUsername');
      setAuthState('signIn');
    } catch (err) {
      console.error('Error confirming sign up:', err);
      setLocalError(err.message |
| 'An error occurred during confirmation.');
    }
  };

  return (
    <div style={formContainerStyle}>
      <h2>Confirm Your Account</h2>
      <p>A confirmation code has been sent to your email.</p>
      <form onSubmit={handleConfirmSignUp} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <input type="text" value={code} onChange={(e) => setCode(e.target.value)} placeholder="Confirmation Code" style={inputStyle} />
        <button type="submit" style={buttonStyle}>Confirm</button>
      </form>
      {localError && <p style={{ color: 'red' }}>{localError}</p>} {/* Display local error */}
    </div>
  );
};


// --- Your original App Content, now its own component ---
const AppContent = ({ user, signOut }) => {
  const [file, setFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  // CORRECTED: Added variable names for useState
  const = useState('');
  const = useState('');
  const [isUploading, setIsUploading] = useState(false);

  // Function to get the user's tier from their JWT
  useEffect(() => {
    const getUserTier = async () => {
        try {
            // Retrieve session from local storage
            const storedSession = localStorage.getItem('cognitoSession');
            if (storedSession) {
                const session = JSON.parse(storedSession);
                // Decode JWT to get claims, including groups
                const base64Url = session.AccessToken.split('.')[1];
                const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                const payload = JSON.parse(window.atob(base64));
                
                const userGroups = payload['cognito:groups'] ||; // Corrected empty array default
                if (userGroups.includes('premium-tier')) { setTier('Premium'); } else { setTier('Free'); }
            } else {
                setTier('Free');
            }
        } catch (err) { console.log('Error fetching user session:', err); setTier('Free'); }
    };
    getUserTier();
  }, [user]);

  const onFileChange = (e) => { setFile(e.target.files); setUploadMessage(''); setDownloadUrl(''); }; // Corrected to get single file

  // Function to get the JWT token (ID Token) from local storage
  const getJwtToken = async () => {
    const storedSession = localStorage.getItem('cognitoSession');
    if (storedSession) {
      const session = JSON.parse(storedSession);
      // Basic check for expiration (needs refresh logic for production)
      if (session.ExpiresIn > Date.now() / 1000) {
        return session.IdToken; // Use ID Token for backend validation
      }
    }
    signOut(); // Sign out if no valid session
    return null;
  };

  const onFileUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setUploadMessage('Uploading...');
    setDownloadUrl('');
    const token = await getJwtToken();
    if (!token) { setUploadMessage('Authentication error. Please sign in again.'); setIsUploading(false); return; }
    const formData = new FormData();
    formData.append('file', file);
    try {
      const apiUrl = process.env.VITE_CLOUDFRONT_CUSTOM_DOMAIN_URL; // Use VITE_ prefix
      const uploadResponse = await fetch(`${apiUrl}/api/upload`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: formData });
      const uploadData = await uploadResponse.json();
      if (!uploadResponse.ok) throw new Error(uploadData.message |
| 'Upload failed');
      setUploadMessage('Upload successful! Generating download link...');
      const fileName = uploadData.file_name;
      const downloadResponse = await fetch(`${apiUrl}/api/get-download-link?file_name=${fileName}`, { headers: { 'Authorization': `Bearer ${token}` } });
      const downloadData = await downloadResponse.json();
      if (!downloadResponse.ok) throw new Error(downloadData.message |
| 'Could not get download link');
      setDownloadUrl(downloadData.download_url);
      setUploadMessage(`Success! Link for ${tier} tier users (expires in ${Math.round(downloadData.expires_in_seconds / 86400)} days):`);
    } catch (error) { console.error('An error occurred:', error); setUploadMessage(`Error: ${error.message}`);
    } finally { setIsUploading(false); }
  };

  const handleUpgrade = async () => {
    setUploadMessage('Upgrading...');
    const token = await getJwtToken();
    if (!token) { setUploadMessage('Authentication error. Please sign in again.'); return; }
    try {
      // --- IMPORTANT: Call your Flask backend's /api/upgrade endpoint ---
      // The backend will then use Boto3 to update Cognito groups securely.
      const apiUrl = process.env.VITE_CLOUDFRONT_CUSTOM_DOMAIN_URL;
      const response = await fetch(`${apiUrl}/api/upgrade`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message |
| 'Upgrade failed');
      setUploadMessage('Upgrade successful! Please sign out and sign back in to see the change.');
    } catch (error) { console.error('An error occurred during upgrade:', error); setUploadMessage(`Error: ${error.message}`); }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', padding: '2rem', backgroundColor: '#f0f2f5' }}>
        <div style={{ width: '100%', maxWidth: '500px', padding: '2rem', backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ margin: 0 }}>FileShare</h2>
                <button onClick={signOut} style={{...buttonStyle, padding: '8px 12px'}}>Sign Out</button>
            </div>
            <p style={{ marginTop: '1rem' }}>Welcome, <strong>{user.username}</strong></p>
            <p>Your current tier: <strong>{tier}</strong></p>
            <div style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <input type="file" onChange={onFileChange} />
                <button onClick={onFileUpload} disabled={!file |
| isUploading} style={buttonStyle}>{isUploading? 'Uploading...' : 'Upload File'}</button>
            </div>
            {uploadMessage && <p style={{ marginTop: '1rem' }}>{uploadMessage}</p>}
            {downloadUrl && <a href={downloadUrl} target="_blank" rel="noopener noreferrer" style={{ wordBreak: 'break-all', display: 'block', marginTop: '1rem' }}>{downloadUrl}</a>}
            {tier === 'Free' && (
                <button onClick={handleUpgrade} style={{...buttonStyle, marginTop: '2rem', width: '100%' }}>
                    Upgrade to Premium (Free for now)
                </button>
            )}
        </div>
    </div>
  );
};

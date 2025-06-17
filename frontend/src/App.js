import React, { useState, useEffect } from 'react';

// --- UPDATED: Imports for custom auth flow ---
import { Amplify } from 'aws-amplify';
// We now import the specific functions we need from the auth category
import { signUp, confirmSignUp, signIn, signOut, fetchAuthSession, getCurrentUser } from 'aws-amplify/auth';

// Basic styling for the new forms
const formContainerStyle = { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', gap: '15px' };
const inputStyle = { padding: '10px', fontSize: '16px', width: '300px' };
const buttonStyle = { padding: '10px 20px', fontSize: '16px', cursor: 'pointer' };

// --- Configuration is still loaded once at the top ---
Amplify.configure({
  Auth: {
    Cognito: {
      region: process.env.REACT_APP_AWS_REGION,
      userPoolId: process.env.REACT_APP_USER_POOL_ID,
      userPoolWebClientId: process.env.REACT_APP_USER_POOL_CLIENT_ID,
    }
  }
});

// --- Main App Component ---
export default function App() {
  const [authState, setAuthState] = useState('unauthenticated');
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');

  // Check for a logged-in user when the app loads
  useEffect(() => {
    const checkUser = async () => {
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        setAuthState('authenticated');
      } catch (err) {
        setAuthState('signIn'); // No user found, show sign-in form
      }
    };
    checkUser();
  }, []);

  const handleSignOut = async () => {
    try {
      await signOut();
      setUser(null);
      setAuthState('signIn');
    } catch (err) {
      console.error('Error signing out: ', err);
      setError('Error signing out. Please try again.');
    }
  };

  // Conditionally render the correct component based on authState
  if (authState === 'authenticated' && user) {
    return <AppContent user={user} signOut={handleSignOut} />;
  }
  if (authState === 'confirmSignUp') {
    return <ConfirmSignUpForm setAuthState={setAuthState} />;
  }
  if (authState === 'signIn') {
    return <SignInForm setAuthState={setAuthState} setUser={setUser} error={error} setError={setError} />;
  }
  // Default to showing the SignUp form
  return <SignUpForm setAuthState={setAuthState} error={error} setError={setError} />;
}


// --- Custom Sign-In Component ---
const SignInForm = ({ setAuthState, setUser, error, setError }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const { isSignedIn, nextStep } = await signIn({ username: email, password });
      if (isSignedIn) {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        setAuthState('authenticated');
      }
    } catch (err) {
      console.error('Error signing in:', err);
      setError(err.message || 'An error occurred during sign in.');
    }
  };

  return (
    <div style={formContainerStyle}>
      <h2>Sign In</h2>
      <form onSubmit={handleSignIn} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" style={inputStyle} />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" style={inputStyle} />
        <button type="submit" style={buttonStyle}>Sign In</button>
      </form>
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
      const { isSignUpComplete, userId, nextStep } = await signUp({
        username: email,
        password,
        options: { userAttributes: { email } }
      });
      if (nextStep.signUpStep === 'CONFIRM_SIGN_UP') {
        // Pass the username to the confirmation form
        sessionStorage.setItem('tempUsername', email);
        setAuthState('confirmSignUp');
      }
    } catch (err) {
      console.error('Error signing up:', err);
      setError(err.message || 'An error occurred during sign up.');
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
const ConfirmSignUpForm = ({ setAuthState }) => {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');

  const handleConfirmSignUp = async (e) => {
    e.preventDefault();
    setError('');
    const username = sessionStorage.getItem('tempUsername');
    if (!username) {
      setError('Could not find username for confirmation. Please try signing up again.');
      return;
    }
    try {
      const { isSignUpComplete, nextStep } = await confirmSignUp({ username, confirmationCode: code });
      if (isSignUpComplete) {
        sessionStorage.removeItem('tempUsername');
        setAuthState('signIn');
      }
    } catch (err) {
      console.error('Error confirming sign up:', err);
      setError(err.message || 'An error occurred during confirmation.');
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
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
};


// --- Your original App Content, now its own component ---
const AppContent = ({ user, signOut }) => {
  const [file, setFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  const [tier, setTier] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    const getUserTier = async () => {
        try {
            const { tokens } = await fetchAuthSession();
            const userGroups = tokens?.accessToken.payload['cognito:groups'] || [];
            if (userGroups.includes('premium-tier')) { setTier('Premium'); } else { setTier('Free'); }
        } catch (err) { console.log('Error fetching user session:', err); setTier('Free'); }
    };
    getUserTier();
  }, [user]);

  const onFileChange = (e) => { setFile(e.target.files[0]); setUploadMessage(''); setDownloadUrl(''); };

  const getJwtToken = async () => {
    try {
      const { tokens } = await fetchAuthSession();
      return tokens?.accessToken.toString();
    } catch (error) { console.error("Error getting JWT token", error); signOut(); return null; }
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
      const apiUrl = process.env.REACT_APP_CLOUDFRONT_CUSTOM_DOMAIN_URL;
      const uploadResponse = await fetch(`${apiUrl}/api/upload`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: formData });
      const uploadData = await uploadResponse.json();
      if (!uploadResponse.ok) throw new Error(uploadData.message || 'Upload failed');
      setUploadMessage('Upload successful! Generating download link...');
      const fileName = uploadData.file_name;
      const downloadResponse = await fetch(`${apiUrl}/api/get-download-link?file_name=${fileName}`, { headers: { 'Authorization': `Bearer ${token}` } });
      const downloadData = await downloadResponse.json();
      if (!downloadResponse.ok) throw new Error(downloadData.message || 'Could not get download link');
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
      const apiUrl = process.env.REACT_APP_CLOUDFRONT_CUSTOM_DOMAIN_URL;
      const response = await fetch(`${apiUrl}/api/upgrade`, { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || 'Upgrade failed');
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
                <button onClick={onFileUpload} disabled={!file || isUploading} style={buttonStyle}>{isUploading ? 'Uploading...' : 'Upload File'}</button>
            </div>
            {uploadMessage && <p style={{ marginTop: '1rem' }}>{uploadMessage}</p>}
            {downloadUrl && <a href={downloadUrl} target="_blank" rel="noopener noreferrer" style={{ wordBreak: 'break-all', display: 'block', marginTop: '1rem' }}>{downloadUrl}</a>}
            {tier === 'Free' && (
                <button onClick={handleUpgrade} style={{ ...buttonStyle, marginTop: '2rem', width: '100%' }}>
                    Upgrade to Premium (Free for now)
                </button>
            )}
        </div>
    </div>
  );
};
// --- End of App Component ---
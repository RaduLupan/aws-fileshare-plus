import React, { useState, useEffect } from 'react';

// Import necessary Amplify v6 components and utilities
import { fetchAuthSession, signOut as amplifySignOut, signUp, signIn, confirmSignUp, getCurrentUser, resetPassword, confirmResetPassword } from 'aws-amplify/auth';
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
  const [generatedUsername, setGeneratedUsername] = useState('');
  const [forgotPasswordMode, setForgotPasswordMode] = useState(false);
  const [resetCode, setResetCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [showResetCodeForm, setShowResetCodeForm] = useState(false);  const handleSignUp = async (e) => {
    e.preventDefault();
    console.log('=== CUSTOM SIGNUP FUNCTION CALLED ===');
    console.log('Email:', email);
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    setIsLoading(true);
    setError('');      try {
      // Use email directly as username since alias_attributes = ["email"] is enabled
      console.log('Using email as username:', email);
      setGeneratedUsername(email); // Store email as the "generated" username for consistency
      
      const result = await signUp({
        username: email, // Use email directly as username
        password: password,
        attributes: {
          email: email,
        },
        autoSignIn: {
          enabled: true,
        }
      });console.log('SignUp successful:', result);
      
      // Check if auto sign-in worked
      if (result.isSignUpComplete && result.nextStep?.signInStep === 'DONE') {
        console.log('Auto sign-in successful!');
        onAuthenticated();      } else if (result.isSignUpComplete) {
        console.log('Signup completed successfully! User can now sign in.');
        setError(`Account created successfully! You can sign in with your email: ${email}`);
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
  };  const handleSignIn = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      // Sign in with email (which is now the username)
      const result = await signIn({
        username: email,
        password: password,
      });
      
      console.log('SignIn successful:', result);
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

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      await resetPassword({
        username: email,
      });
      
      console.log('Password reset code sent successfully');
      setShowResetCodeForm(true);
      setResetCode(''); // Explicitly clear the reset code field
      setError(''); // Clear any previous errors
    } catch (error) {
      console.error('Reset password error:', error);
      setError(error.message || 'Failed to send reset code. Please check your email address.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmResetPassword = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    if (newPassword !== confirmNewPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }
    
    try {
      await confirmResetPassword({
        username: email,
        confirmationCode: resetCode,
        newPassword: newPassword,
      });
      
      console.log('Password reset successful');
      // Reset form and go back to sign in
      setForgotPasswordMode(false);
      setShowResetCodeForm(false);
      setIsSignUp(false);
      setResetCode('');
      setNewPassword('');
      setConfirmNewPassword('');
      setError('Password reset successful! You can now sign in with your new password.');
    } catch (error) {
      console.error('Confirm reset password error:', error);
      setError(error.message || 'Failed to reset password');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle resending reset code
  const handleResendResetCode = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      await resetPassword({
        username: email,
      });
      
      console.log('Password reset code resent successfully');
      setError('Reset code resent! Check your email.');
    } catch (error) {
      console.error('Resend reset code error:', error);
      setError(error.message || 'Failed to resend reset code.');
    } finally {
      setIsLoading(false);
    }
  };

  // Forgot Password Flow
  if (forgotPasswordMode) {
    if (showResetCodeForm) {
      return (
        <Card style={{ maxWidth: '400px', margin: '2rem auto', padding: '2rem' }}>
          <Heading level={2}>Reset Password</Heading>
          <Text style={{ marginBottom: '1rem', color: 'green' }}>
            Reset code sent to {email}! Check your email and enter the code below.
          </Text>
          <form onSubmit={handleConfirmResetPassword}>
            {/* Dummy hidden fields to confuse autofill */}
            <input type="text" style={{ display: 'none' }} autoComplete="username" />
            <input type="password" style={{ display: 'none' }} autoComplete="current-password" />
            
            <div style={{ marginBottom: '1rem' }}>
              <label>Reset Code:</label>
              <input
                type="text"
                value={resetCode}
                onChange={(e) => setResetCode(e.target.value)}
                onFocus={(e) => {
                  // Force clear the field if it contains email-like content
                  if (resetCode.includes('@') || resetCode.includes('.com')) {
                    setResetCode('');
                  }
                }}
                required
                placeholder="Enter the code from your email"
                autoComplete="new-password"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck="false"
                name="reset-verification-code"
                id="reset-verification-code"
                data-lpignore="true"
                data-form-type=""
                style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label>New Password:</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label>Confirm New Password:</label>
              <input
                type="password"
                value={confirmNewPassword}
                onChange={(e) => setConfirmNewPassword(e.target.value)}
                required
                style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
              />
            </div>
            {error && <Text color="red" style={{ marginBottom: '1rem' }}>{error}</Text>}
            <Button type="submit" isLoading={isLoading} style={{ width: '100%', marginBottom: '1rem' }}>
              Reset Password
            </Button>
          </form>
          <Button
            variation="link"
            onClick={handleResendResetCode}
            isLoading={isLoading}
            style={{ width: '100%', marginBottom: '1rem' }}
          >
            Resend Code
          </Button>
          <Button
            variation="link"
            onClick={() => {
              setForgotPasswordMode(false);
              setShowResetCodeForm(false);
              setResetCode(''); // Clear reset code
              setNewPassword(''); // Clear password fields
              setConfirmNewPassword('');
              setError('');
            }}
            style={{ width: '100%' }}
          >
            Back to Sign In
          </Button>
        </Card>
      );
    } else {
      return (
        <Card style={{ maxWidth: '400px', margin: '2rem auto', padding: '2rem' }}>
          <Heading level={2}>Forgot Password</Heading>
          <Text style={{ marginBottom: '1rem' }}>Enter your email address and we'll send you a reset code.</Text>
          <form onSubmit={handleForgotPassword}>
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
            {error && <Text color="red" style={{ marginBottom: '1rem' }}>{error}</Text>}
            <Button type="submit" isLoading={isLoading} style={{ width: '100%', marginBottom: '1rem' }}>
              Send Reset Code
            </Button>
          </form>
          <Button
            variation="link"
            onClick={() => {
              setForgotPasswordMode(false);
              setShowResetCodeForm(false);
              setResetCode(''); // Clear reset code
              setNewPassword(''); // Clear password fields
              setConfirmNewPassword('');
              setError('');
            }}
            style={{ width: '100%' }}
          >
            Back to Sign In
          </Button>
        </Card>
      );
    }
  }

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
          setForgotPasswordMode(false);
          setShowResetCodeForm(false);
          setError('');
        }}
        style={{ width: '100%' }}
      >
        {isSignUp ? 'Already have an account? Sign In' : 'Need an account? Sign Up'}
      </Button>
      {!isSignUp && (
        <Button
          variation="link"
          onClick={() => {
            setForgotPasswordMode(true);
            setResetCode(''); // Clear reset code when entering forgot password mode
            setNewPassword(''); // Clear new password fields too
            setConfirmNewPassword('');
            setShowResetCodeForm(false); // Start with email form, not code form
            setError('');
          }}
          style={{ width: '100%', marginTop: '0.5rem' }}
        >
          Forgot your password?
        </Button>
      )}
    </Card>
  );
};

// This is the inner component that will be rendered ONLY after a successful login.
// Premium File Explorer Component
const PremiumFileExplorer = ({ signOut, user, tier, getJwtToken }) => {
  const [files, setFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  // Load files on component mount
  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const token = await getJwtToken();
      if (!token) {
        setError('Authentication error. Please sign in again.');
        return;
      }

      const apiUrl = import.meta.env.VITE_BACKEND_API_URL;
      const response = await fetch(`${apiUrl}/api/files`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to load files');
      }

      setFiles(data.files || []);
      setMessage(`Found ${data.total_count} files`);
      setTimeout(() => setMessage(''), 3000);
      
    } catch (error) {
      console.error('Error loading files:', error);
      setError(error.message || 'Failed to load files');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setIsUploading(true);
    setMessage('Uploading...');
    setError('');

    try {
      const token = await getJwtToken();
      if (!token) {
        setError('Authentication error. Please sign in again.');
        return;
      }

      const apiUrl = import.meta.env.VITE_BACKEND_API_URL;
      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await fetch(`${apiUrl}/api/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      const uploadData = await uploadResponse.json();
      
      if (!uploadResponse.ok) {
        throw new Error(uploadData.message || 'Upload failed');
      }

      setMessage('File uploaded successfully!');
      setFile(null);
      
      // Reload files to show the new upload
      setTimeout(() => {
        loadFiles();
      }, 1000);

    } catch (error) {
      console.error('Error uploading file:', error);
      setError(error.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const generateNewLink = async (fileKey) => {
    try {
      const token = await getJwtToken();
      if (!token) {
        setError('Authentication error. Please sign in again.');
        return;
      }

      const apiUrl = import.meta.env.VITE_BACKEND_API_URL;
      const response = await fetch(`${apiUrl}/api/files/new-link`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_key: fileKey })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to generate new link');
      }

      // Copy link to clipboard
      await navigator.clipboard.writeText(data.download_url);
      setMessage(`New download link generated and copied to clipboard! (Expires in ${data.expires_in_days} days)`);
      setTimeout(() => setMessage(''), 5000);

    } catch (error) {
      console.error('Error generating new link:', error);
      setError(error.message || 'Failed to generate new link');
    }
  };

  const deleteFile = async (fileKey, filename) => {
    if (!confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const token = await getJwtToken();
      if (!token) {
        setError('Authentication error. Please sign in again.');
        return;
      }

      const apiUrl = import.meta.env.VITE_BACKEND_API_URL;
      const response = await fetch(`${apiUrl}/api/files/${encodeURIComponent(fileKey)}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to delete file');
      }

      setMessage(`File "${filename}" deleted successfully!`);
      setTimeout(() => setMessage(''), 3000);
      
      // Reload files to reflect the deletion
      loadFiles();

    } catch (error) {
      console.error('Error deleting file:', error);
      setError(error.message || 'Failed to delete file');
    }
  };

  return (
    <Flex direction="column" alignItems="center" padding="2rem">
      <Card style={{ maxWidth: '800px', width: '100%', padding: '2rem' }}>
        <Flex direction="row" justifyContent="space-between" alignItems="center" marginBottom="2rem">
          <Heading level={1}>Premium File Manager</Heading>
          <Button onClick={signOut} variation="primary">Sign Out</Button>
        </Flex>

        <Text marginBottom="1rem">
          Welcome {user?.username}! You have <strong>{tier}</strong> tier access.
        </Text>

        {/* Upload Section */}
        <Card variation="outlined" padding="1.5rem" marginBottom="2rem">
          <Heading level={3} marginBottom="1rem">Upload New File</Heading>
          <form onSubmit={handleFileUpload}>
            <Flex direction="row" alignItems="end" gap="1rem">
              <Flex direction="column" flex="1">
                <Text fontWeight="600" marginBottom="0.5rem">Select File:</Text>
                <input
                  type="file"
                  onChange={(e) => setFile(e.target.files[0])}
                  style={{ padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                />
              </Flex>
              <Button 
                type="submit" 
                isLoading={isUploading}
                isDisabled={!file}
                variation="primary"
              >
                Upload
              </Button>
            </Flex>
          </form>
        </Card>

        {/* Messages */}
        {error && (
          <Text color="red" marginBottom="1rem" fontWeight="600">{error}</Text>
        )}
        {message && (
          <Text color="green" marginBottom="1rem" fontWeight="600">{message}</Text>
        )}

        {/* Files Section */}
        <Card variation="outlined" padding="1.5rem">
          <Flex direction="row" justifyContent="space-between" alignItems="center" marginBottom="1rem">
            <Heading level={3}>Your Files</Heading>
            <Button onClick={loadFiles} variation="link" isLoading={isLoading}>
              Refresh
            </Button>
          </Flex>

          {isLoading && <Text>Loading files...</Text>}

          {!isLoading && files.length === 0 && (
            <Text color="gray">No files uploaded yet. Upload your first file above!</Text>
          )}

          {!isLoading && files.length > 0 && (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #eee' }}>
                    <th style={{ textAlign: 'left', padding: '0.75rem', fontWeight: '600' }}>File Name</th>
                    <th style={{ textAlign: 'left', padding: '0.75rem', fontWeight: '600' }}>Size</th>
                    <th style={{ textAlign: 'left', padding: '0.75rem', fontWeight: '600' }}>Upload Date</th>
                    <th style={{ textAlign: 'center', padding: '0.75rem', fontWeight: '600' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {files.map((file, index) => (
                    <tr key={file.key} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '0.75rem' }}>
                        <Text fontWeight="500">{file.filename}</Text>
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <Text>{file.size_display}</Text>
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <Text>{file.upload_date}</Text>
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                        <Flex direction="row" justifyContent="center" gap="0.5rem">
                          <Button 
                            size="small" 
                            variation="primary"
                            onClick={() => generateNewLink(file.key)}
                          >
                            New Link
                          </Button>
                          <Button 
                            size="small" 
                            variation="destructive"
                            onClick={() => deleteFile(file.key, file.filename)}
                          >
                            Delete
                          </Button>
                        </Flex>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </Card>
    </Flex>
  );
};

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
      console.log('=== GETTING JWT TOKEN ===');
      const authSession = await fetchAuthSession();
      console.log('Auth session:', authSession);
      const token = authSession?.tokens?.idToken?.toString();
      console.log('JWT token retrieved:', token ? 'Token found' : 'No token');
      console.log('JWT token preview:', token ? token.substring(0, 50) + '...' : 'null');
      return token;
    } catch (error) {
      console.error('Error getting JWT token:', error);
      return null;
    }
  };

  // Show Premium File Explorer for Premium users
  if (tier === 'Premium') {
    return <PremiumFileExplorer signOut={signOut} user={user} tier={tier} getJwtToken={getJwtToken} />;
  }

  // Function to copy text to clipboard
  const copyToClipboard = async (text) => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        // Use the modern Clipboard API if available
        await navigator.clipboard.writeText(text);
        setUploadMessage('Download link copied to clipboard!');
      } else {
        // Fallback for older browsers or non-secure contexts
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        setUploadMessage('Download link copied to clipboard!');
      }
      // Clear the message after 3 seconds
      setTimeout(() => {
        setUploadMessage('');
      }, 3000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      setUploadMessage('Failed to copy link. Please copy manually.');
      setTimeout(() => {
        setUploadMessage('');
      }, 3000);
    }
  };

  // Function to open email client with pre-filled download link
  const handleEmailLink = (downloadUrl) => {
    const subject = encodeURIComponent('File Download Link - FileShare Plus');
    const body = encodeURIComponent(`Hi there!

I've shared a file with you through FileShare Plus. You can download it using the link below:

${downloadUrl}

This is a secure download link that will allow you to access the file directly.

Best regards!

---
Powered by FileShare Plus - Secure file sharing made simple`);

    const mailtoUrl = `mailto:?subject=${subject}&body=${body}`;
    
    try {
      window.open(mailtoUrl, '_blank');
      setUploadMessage('Email client opened! Please add recipient and send.');
      setTimeout(() => {
        setUploadMessage('');
      }, 4000);
    } catch (error) {
      console.error('Error opening email client:', error);
      setUploadMessage('Unable to open email client. Please copy the link manually.');
      setTimeout(() => {
        setUploadMessage('');
      }, 4000);
    }
  };

  const onFileChange = (event) => {
    setFile(event.target.files[0]);
    setUploadMessage('');
    setDownloadUrl('');
  };

  const onFileUpload = async () => {
    console.log('=== FILE UPLOAD FUNCTION CALLED ===');
    if (!file) {
      console.log('No file selected');
      return;
    }

    setIsUploading(true);
    setUploadMessage('Uploading...');
    setDownloadUrl('');

    console.log('Getting JWT token...');
    const token = await getJwtToken();
    console.log('Token result:', token ? 'Token received' : 'No token received');
    if (!token) {
      setUploadMessage('Authentication error. Please sign in again.');
      setIsUploading(false);
      return;
    }    try {
      const apiUrl = import.meta.env.VITE_BACKEND_API_URL;
      console.log('API URL:', apiUrl);
      console.log('Preparing FormData with file:', file.name);
      
      const formData = new FormData();
      formData.append('file', file);

      console.log('Making upload request with token:', token.substring(0, 20) + '...');
      const uploadResponse = await fetch(`${apiUrl}/api/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      console.log('Upload response status:', uploadResponse.status);
      const uploadData = await uploadResponse.json();
      console.log('Upload response data:', uploadData);
      
      if (!uploadResponse.ok) throw new Error(uploadData.message || 'Upload failed');

      setUploadMessage('Upload successful! Generating download link...');
      
      const fileName = uploadData.file_name;
      console.log('File name from upload response:', fileName);
      
      // Simple approach: just pass the filename directly (already sanitized by backend)
      const downloadResponse = await fetch(`${apiUrl}/api/get-download-link?file_name=${encodeURIComponent(fileName)}`, {
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
    }    try {
      const apiUrl = import.meta.env.VITE_BACKEND_API_URL;
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
        {downloadUrl && (
          <Flex direction="column" gap="0.5rem" marginTop="1rem" padding="1rem" backgroundColor="var(--amplify-colors-background-primary)" borderRadius="8px">
            <Text fontSize="0.9rem" fontWeight="600" color="var(--amplify-colors-font-primary)">Download Link:</Text>
            <Flex direction="row" alignItems="center" gap="0.5rem">
              <Text 
                as="a" 
                href={downloadUrl} 
                target="_blank" 
                rel="noopener noreferrer" 
                flex="1"
                fontSize="0.8rem"
                color="var(--amplify-colors-brand-primary-60)"
                textDecoration="none"
                style={{
                  maxWidth: '200px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}
                title={downloadUrl}
              >
                {downloadUrl}
              </Text>
              <Button 
                size="small" 
                variation="link" 
                onClick={() => copyToClipboard(downloadUrl)}
                fontSize="0.8rem"
                padding="0.25rem 0.5rem"
              >
                Copy Link
              </Button>
              <Button 
                size="small" 
                variation="link" 
                onClick={() => handleEmailLink(downloadUrl)}
                fontSize="0.8rem"
                padding="0.25rem 0.5rem"
                title="Open email client to share this download link"
              >
                Email Link
              </Button>
            </Flex>
          </Flex>
        )}

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

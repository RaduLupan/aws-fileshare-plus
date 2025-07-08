import React, { useState, useEffect } from 'react';

// Import necessary Amplify v6 components and utilities
import { fetchAuthSession, signOut as amplifySignOut, signUp, signIn, confirmSignUp, getCurrentUser, fetchUserAttributes, resetPassword, confirmResetPassword } from 'aws-amplify/auth';
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
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    setIsLoading(true);
    setError('');      try {
      // Use email directly as username since alias_attributes = ["email"] is enabled
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
      });
      
      // Check if auto sign-in worked
      if (result.isSignUpComplete && result.nextStep?.signInStep === 'DONE') {
        onAuthenticated();      } else if (result.isSignUpComplete) {
        setError(`Account created successfully! You can sign in with your email: ${email}`);
        setIsSignUp(false); // Switch to sign-in mode
      } else {
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
const PremiumFileExplorer = ({ signOut, user, tier, userStatus, getJwtToken }) => {
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
      console.log('Starting Premium file upload...');
      const token = await getJwtToken();
      console.log('Retrieved token for Premium upload:', token ? `${token.substring(0, 20)}...` : 'null');
      
      if (!token) {
        setError('Authentication error. Please sign in again.');
        return;
      }

      const apiUrl = import.meta.env.VITE_BACKEND_API_URL;
      console.log('Using API URL for Premium upload:', apiUrl);
      
      const formData = new FormData();
      formData.append('file', file);

      console.log('Making Premium upload request...');
      const uploadResponse = await fetch(`${apiUrl}/api/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      console.log('Premium upload response status:', uploadResponse.status);
      const uploadData = await uploadResponse.json();
      console.log('Premium upload response data:', uploadData);
      
      if (!uploadResponse.ok) {
        throw new Error(uploadData.message || 'Upload failed');
      }

      setMessage('File uploaded successfully! Generating 3-day download link...');
      setFile(null);
      
      // Auto-generate a 3-day link for Premium uploads
      if (uploadData.file_name) {
        try {
          await generateNewLink(uploadData.file_name, 3);
        } catch (linkError) {
          console.error('Error auto-generating link:', linkError);
          setMessage('File uploaded successfully! (Link generation failed - you can create one manually)');
        }
      }
      
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

  // Helper function to calculate expiration status
  const getExpirationInfo = (file) => {
    if (!file.short_code || !file.expires_at) {
      return { text: 'No active link', color: 'gray', isExpired: null };
    }

    const now = new Date();
    const expiresAt = new Date(file.expires_at);
    const diffTime = expiresAt - now;
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

    if (diffTime <= 0) {
      const daysAgo = Math.abs(diffDays);
      return {
        text: daysAgo === 0 ? 'Expired today' : `${daysAgo} day${daysAgo === 1 ? '' : 's'} ago`,
        color: '#d73502', // Red for expired
        isExpired: true
      };
    } else {
      return {
        text: diffDays === 1 ? '1 day' : `${diffDays} days`,
        color: '#057a52', // Green for valid
        isExpired: false
      };
    }
  };

  // Component for the New Link dropdown
  const NewLinkDropdown = ({ fileKey, onGenerateLink }) => {
    const [selectedDays, setSelectedDays] = useState(3);
    const [isGenerating, setIsGenerating] = useState(false);

    const handleGenerateLink = async () => {
      setIsGenerating(true);
      await onGenerateLink(fileKey, selectedDays);
      setIsGenerating(false);
    };

    return (
      <div className="new-link-dropdown">
        <select
          value={selectedDays}
          onChange={(e) => setSelectedDays(parseInt(e.target.value))}
          className="expiration-select"
        >
          <option value={1}>1</option>
          <option value={3}>3</option>
          <option value={5}>5</option>
          <option value={7}>7</option>
        </select>
        <Button
          size="small"
          variation="primary"
          onClick={handleGenerateLink}
          isLoading={isGenerating}
          style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
        >
          New Link
        </Button>
      </div>
    );
  };

  const generateNewLink = async (fileKey, expirationDays = 3) => {
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
        body: JSON.stringify({ 
          file_key: fileKey,
          expiration_days: expirationDays
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to generate new link');
      }

      // Copy link to clipboard
      await navigator.clipboard.writeText(data.download_url);
      setMessage(`New download link generated and copied to clipboard! (Expires in ${data.expires_in_days} days)`);
      setTimeout(() => setMessage(''), 5000);

      // Reload files to update the expiration info
      loadFiles();

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

  const emailLink = async (fileKey, filename) => {
    try {
      const token = await getJwtToken();
      if (!token) {
        setError('Authentication error. Please sign in again.');
        return;
      }

      // Generate a new download link first (with default 3 days expiration)
      const apiUrl = import.meta.env.VITE_BACKEND_API_URL;
      const response = await fetch(`${apiUrl}/api/files/new-link`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          file_key: fileKey,
          expiration_days: 3
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to generate download link');
      }

      // Create email content
      const subject = `🔗 File shared with you via FileShare Plus: ${filename}`;
      const body = `Hello!

I hope this message finds you well! I wanted to share an important file with you using FileShare Plus, a secure file sharing platform.

📁 File Details:
• File Name: ${filename}
• Shared via: FileShare Plus Premium
• Secure Download Link: ${data.download_url}

🔒 Security Information:
• This is a secure, encrypted download link
• The link will automatically expire in ${data.expires_in_days} days for your security
• No registration required - just click and download

🚀 About FileShare Plus:
FileShare Plus is a professional file sharing service that prioritizes your privacy and security. All files are encrypted and stored securely in the cloud, with automatic expiration for added protection.

Simply click the download link above to access your file. If you have any questions or need assistance, please don't hesitate to reach out!

Best regards,
Shared via FileShare Plus
🌐 https://cf.aws.lupan.ca

---
This message was sent using FileShare Plus Premium. Experience secure file sharing at its finest!`;

      // Create mailto URL
      const mailtoUrl = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      
      // Use the same method as free tier
      try {
        window.open(mailtoUrl, '_blank');
        setMessage(`Email client opened with download link for "${filename}"`);
        setTimeout(() => setMessage(''), 4000);
        
        // Reload files to update the expiration info
        loadFiles();
      } catch (emailError) {
        console.error('Error opening email client:', emailError);
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(data.download_url).then(() => {
          setMessage(`Email client couldn't open. Download link copied to clipboard for: ${filename}`);
        }).catch(() => {
          setMessage(`Email client couldn't open. Manual link: ${data.download_url}`);
        });
        setTimeout(() => setMessage(''), 6000);
      }

    } catch (error) {
      console.error('Error creating email link:', error);
      setError(error.message || 'Failed to create email link');
    }
  };

  return (
    <Flex direction="column" alignItems="center" padding="2rem">
      <Card style={{ maxWidth: '800px', width: '100%', padding: '2rem' }}>
        <Flex direction="row" justifyContent="space-between" alignItems="center" marginBottom="2rem">
          <Flex direction="column">
            <Heading level={1}>
              Premium File Manager{userStatus?.tier === 'premium-trial' ? ' (Trial)' : ''}
            </Heading>
            {userStatus?.tier === 'premium-trial' && userStatus?.trialDaysRemaining && (
              <Text fontSize="0.9rem" color="var(--amplify-colors-orange-60)" marginTop="0.25rem">
                ⏰ {userStatus.trialDaysRemaining} days remaining in your trial
              </Text>
            )}
          </Flex>
          <Button onClick={signOut} variation="primary">Sign Out</Button>
        </Flex>

        <Text marginBottom="1rem">
          Welcome {user?.displayName || user?.email || user?.username}! You have <strong>{tier}</strong> tier access.
        </Text>

        {userStatus?.tier === 'premium-trial' && (
          <Flex justifyContent="center" marginBottom="1rem">
            <Button variation="primary" size="small">
              Upgrade to Premium
            </Button>
          </Flex>
        )}

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
              <table className="premium-table">
                <thead>
                  <tr>
                    <th>File Name</th>
                    <th>Size</th>
                    <th>Upload Date</th>
                    <th>Expires On</th>
                    <th style={{ textAlign: 'center' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {files.map((file, index) => {
                    const expirationInfo = getExpirationInfo(file);
                    return (
                      <tr key={file.key}>
                        <td>
                          <Text fontWeight="500">{file.filename}</Text>
                        </td>
                        <td>
                          <Text>{file.size_display}</Text>
                        </td>
                        <td>
                          <Text>{file.upload_date}</Text>
                        </td>
                        <td>
                          <Text 
                            className={
                              expirationInfo.isExpired === true ? 'expiration-expired' : 
                              expirationInfo.isExpired === false ? 'expiration-valid' : 
                              'expiration-none'
                            }
                          >
                            {expirationInfo.text}
                          </Text>
                        </td>
                        <td style={{ textAlign: 'center' }}>
                          <Flex direction="row" justifyContent="center" gap="0.5rem">
                            <NewLinkDropdown 
                              fileKey={file.key} 
                              onGenerateLink={generateNewLink}
                            />
                            <Button 
                              size="small" 
                              variation="warning"
                              onClick={() => emailLink(file.key, file.filename)}
                              title="Open email client to share this download link"
                            >
                              📧 Email Link
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
                    );
                  })}
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
  const [userStatus, setUserStatus] = useState({
    tier: 'Free',
    trialDaysRemaining: null,
    canStartTrial: true,
    trialExpiresAt: null
  });

  // Function to fetch user status from backend
  const fetchUserStatus = async () => {
    try {
      const token = await getJwtToken();
      if (!token) {
        console.error('No token available for user status check');
        return;
      }

      const apiUrl = import.meta.env.VITE_BACKEND_API_URL;
      const response = await fetch(`${apiUrl}/api/user-status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const statusData = await response.json();
        console.log('User status:', statusData);
        
        setUserStatus({
          tier: statusData.tier,
          trialDaysRemaining: statusData.trial_days_remaining,
          canStartTrial: statusData.can_start_trial,
          trialExpiresAt: statusData.trial_expires_at
        });
        
        // Update tier for backward compatibility
        setTier(statusData.tier === 'premium-trial' ? 'Premium' : statusData.tier);
      } else {
        console.error('Failed to fetch user status:', response.status);
        // Fallback to JWT-based tier detection
        await getUserTierFromJWT();
      }
    } catch (error) {
      console.error('Error fetching user status:', error);
      // Fallback to JWT-based tier detection
      await getUserTierFromJWT();
    }
  };

  // Function to get the user's tier from their JWT (fallback)
  const getUserTierFromJWT = async () => {
    try {
      const { tokens } = await fetchAuthSession();
      const userGroups = tokens?.accessToken.payload['cognito:groups'] || [];
      if (userGroups.includes('premium-tier') || userGroups.includes('premium-trial')) {
        setTier('Premium');
      } else {
        setTier('Free');
      }
    } catch (error) {
      console.error('Error getting user tier:', error);
      setTier('Free'); // Default to free on error
    }
  };

  // Function to get the user's tier and trial status on component mount
  useEffect(() => {
    // Use fetchUserStatus instead of the old JWT-only method
    fetchUserStatus();
  }, []);

  // Function to get JWT token for backend requests
  const getJwtToken = async () => {
    try {
      console.log('Getting JWT token...');
      const authSession = await fetchAuthSession();
      console.log('Auth session:', authSession);
      console.log('Tokens:', authSession?.tokens);
      console.log('ID Token:', authSession?.tokens?.idToken);
      const token = authSession?.tokens?.idToken?.toString();
      console.log('Final token:', token ? `${token.substring(0, 20)}...` : 'null');
      return token;
    } catch (error) {
      console.error('Error getting JWT token:', error);
      return null;
    }
  };

  // Show Premium File Explorer for Premium users
  if (tier === 'Premium') {
    return <PremiumFileExplorer signOut={signOut} user={user} tier={tier} userStatus={userStatus} getJwtToken={getJwtToken} />;
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
    const subject = encodeURIComponent('🔗 File shared with you via FileShare Plus');
    const body = encodeURIComponent(`Hello!

I hope this message finds you well! I wanted to share a file with you using FileShare Plus, a secure file sharing platform.

📁 Download Information:
• Secure Download Link: ${downloadUrl}
• Shared via: FileShare Plus (Free Tier)
• Simply click the link above to download your file

🔒 Security Features:
• Encrypted file storage and transmission
• Secure, time-limited download links
• No registration required for download

🚀 About FileShare Plus:
FileShare Plus is a professional file sharing service that prioritizes your privacy and security. All files are encrypted and stored securely in the cloud with automatic expiration for added protection.

✨ Upgrade to Premium for enhanced features:
• Extended link expiration (up to 7 days)
• File management dashboard
• Generate multiple download links
• Advanced sharing options

Simply click the download link above to access your file. If you have any questions or need assistance, please don't hesitate to reach out!

Best regards,
Shared via FileShare Plus
🌐 https://cf.aws.lupan.ca

---
This message was sent using FileShare Plus. Experience secure file sharing today!`);

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
    if (!file) {
      return;
    }

    setIsUploading(true);
    setUploadMessage('Uploading...');
    setDownloadUrl('');

    console.log('Starting file upload...');
    const token = await getJwtToken();
    console.log('Retrieved token for upload:', token ? `${token.substring(0, 20)}...` : 'null');
    
    if (!token) {
      setUploadMessage('Authentication error. Please sign in again.');
      setIsUploading(false);
      return;
    }
    
    try {
      const apiUrl = import.meta.env.VITE_BACKEND_API_URL;
      console.log('Using API URL:', apiUrl);
      
      const formData = new FormData();
      formData.append('file', file);

      console.log('Making upload request...');
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
      
      // Simple approach: just pass the filename directly (already sanitized by backend)
      console.log('Making download link request with token:', token ? `${token.substring(0, 20)}...` : 'null');
      console.log('Download link URL:', `${apiUrl}/api/get-download-link?file_name=${encodeURIComponent(fileName)}`);
      const downloadResponse = await fetch(`${apiUrl}/api/get-download-link?file_name=${encodeURIComponent(fileName)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      console.log('Download response status:', downloadResponse.status);
      
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

  const handleStartTrial = async () => {
    setUploadMessage('Starting your Premium trial...');
    const token = await getJwtToken();
    if (!token) {
      setUploadMessage('Authentication error. Please sign in again.');
      return;
    }
    
    try {
      const apiUrl = import.meta.env.VITE_BACKEND_API_URL;
      const response = await fetch(`${apiUrl}/api/start-trial`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (!response.ok) throw new Error(data.message || 'Failed to start trial');
      
      // Update user status after successful trial start
      await fetchUserStatus();
      setUploadMessage(`Premium trial started! You have ${data.days_remaining} days of Premium features.`);
      
    } catch (error) {
      console.error('An error occurred during trial start:', error);
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
          <Flex direction="column" gap="1rem" marginTop="2rem" padding="1rem" backgroundColor="var(--amplify-colors-background-primary)" borderRadius="8px">
            <Text fontSize="1rem" fontWeight="600" textAlign="center" color="var(--amplify-colors-font-primary)">
              🎉 Try Premium Features - Free for 30 days!
            </Text>
            <Text fontSize="0.9rem" textAlign="center" color="var(--amplify-colors-font-secondary)">
              • Advanced link expiration management<br/>
              • File organization and search<br/>
              • Priority support
            </Text>
            <Flex direction="column" gap="0.75rem">
              <Button 
                onClick={handleStartTrial} 
                variation="primary" 
                isFullWidth={true}
                isDisabled={!userStatus.canStartTrial}
              >
                {userStatus.canStartTrial ? 'Try Premium - Free for 30 days' : 'Trial Already Used'}
              </Button>
              <Button 
                onClick={handleUpgrade} 
                variation="outlined" 
                isFullWidth={true}
                isDisabled={true}
                style={{ 
                  backgroundColor: 'var(--amplify-colors-neutral-20)',
                  color: 'var(--amplify-colors-neutral-60)',
                  cursor: 'not-allowed'
                }}
              >
                Upgrade to Premium
              </Button>
            </Flex>
          </Flex>
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
            
            // Fetch user attributes to get email
            const userAttributes = await fetchUserAttributes();
            console.log("User attributes:", userAttributes);
            
            // Create enhanced user object with email
            const enhancedUser = {
              ...currentUser,
              email: userAttributes.email,
              displayName: userAttributes.email // Use email as display name
            };
            
            setUser(enhancedUser);
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
      console.log("Current user after authentication:", currentUser);
      
      // Fetch user attributes to get email
      const userAttributes = await fetchUserAttributes();
      console.log("User attributes after authentication:", userAttributes);
      
      // Create enhanced user object with email
      const enhancedUser = {
        ...currentUser,
        email: userAttributes.email,
        displayName: userAttributes.email // Use email as display name
      };
      
      setUser(enhancedUser);
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

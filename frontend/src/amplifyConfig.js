// amplifyConfig.js
import { Amplify } from 'aws-amplify';

export const configureAmplify = () => {
  // Extract environment variables
  const region = import.meta.env.VITE_AWS_REGION;
  const userPoolId = import.meta.env.VITE_USER_POOL_ID;
  const userPoolWebClientId = import.meta.env.VITE_USER_POOL_CLIENT_ID;
  
  // Validate required configuration
  if (!region || !userPoolId || !userPoolWebClientId) {
    console.error('Amplify configuration missing required values:', {
      region,
      userPoolId: userPoolId ? 'present' : 'missing',
      userPoolWebClientId: userPoolWebClientId ? 'present' : 'missing',
    });
    throw new Error('Missing required Amplify configuration values');
  }  // Minimal configuration for AWS Amplify v6 - no verification required
  const amplifyConfig = {
    Auth: {
      Cognito: {
        userPoolId: userPoolId,
        userPoolClientId: userPoolWebClientId,
        region: region,
        signUpVerificationMethod: 'none'
      }
    }
  };
  
  // Log configuration for debugging
  console.log("Configuring Amplify with:", {
    region,
    userPoolId: userPoolId ? `${userPoolId.substring(0, 10)}...` : undefined,
    userPoolWebClientId: userPoolWebClientId ? `${userPoolWebClientId.substring(0, 10)}...` : undefined,
  });
  
  console.log("Full Amplify config:", amplifyConfig);
  
  try {
    // Configure Amplify with the settings
    Amplify.configure(amplifyConfig);
    console.log("Amplify configuration completed successfully");
    
    // Verify the configuration was applied
    const currentConfig = Amplify.getConfig();
    console.log("Current Amplify config after configure:", currentConfig);
  } catch (error) {
    console.error("Error configuring Amplify:", error);
    throw error;
  }
};

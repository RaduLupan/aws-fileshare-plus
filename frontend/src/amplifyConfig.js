// amplifyConfig.js
import { Amplify } from 'aws-amplify';
import { cognitoUserPoolsTokenProvider } from 'aws-amplify/auth/cognito';

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
  }
  
  // Configuration for AWS Amplify v6
  const amplifyConfig = {
    Auth: {
      Cognito: {
        userPoolId,
        userPoolClientId: userPoolWebClientId,
        loginWith: {
          email: true
        }
      }
    },
    // Required to properly set region
    aws_project_region: region,
    aws_cognito_region: region
  };
  
  // Log configuration for debugging
  console.log("Configuring Amplify with:", {
    region,
    userPoolId: userPoolId ? `${userPoolId.substring(0, 5)}...` : undefined,
    userPoolWebClientId: userPoolWebClientId ? `${userPoolWebClientId.substring(0, 5)}...` : undefined,
  });
  
  // Configure Amplify with the settings
  Amplify.configure(amplifyConfig);
};

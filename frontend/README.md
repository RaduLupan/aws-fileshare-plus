# FileShare Plus - Frontend

This React application provides the user interface for the FileShare Plus application. It uses AWS Amplify for authentication with Cognito and communicates with the Flask backend API.

## Environment Setup

The application requires the following environment variables:

```
VITE_USER_POOL_ID=<your-cognito-user-pool-id>
VITE_USER_POOL_CLIENT_ID=<your-cognito-user-pool-client-id>
VITE_AWS_REGION=<your-aws-region>
VITE_CLOUDFRONT_CUSTOM_DOMAIN_URL=<your-backend-domain>
```

These can be provided in several ways:

1. For local development, create a `.env` file in the frontend directory
2. For GitHub Actions deployments, they are fetched from SSM Parameter Store
3. For Docker builds, they can be passed as build arguments

## Available Scripts

In the project directory, you can run:

### `npm start` or `npm run dev`

Runs the app in the development mode using Vite.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

**Note:** Make sure your `.env` file is properly set up with the required environment variables.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `dist` folder using Vite.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed to S3 and served through CloudFront!

**Note:** Ensure that environment variables are properly set during the build process.

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

## Troubleshooting Amplify Authentication

If you encounter issues with AWS Amplify authentication:

1. **Check Environment Variables**: Ensure all required environment variables are set correctly
   - Run `console.log(import.meta.env)` in your app to verify values are loaded
   - For local development, make sure `.env` file exists and contains valid values

2. **Cognito User Pool Configuration**:
   - Verify that the Cognito User Pool is properly configured
   - Check that the App Client has the right settings for your app

3. **Browser Console Errors**:
   - Look for authentication errors in the browser console
   - Amplify provides detailed error messages that can help diagnose the issue

4. **Common Issues**:
   - CORS errors: Ensure your Cognito domain is properly configured
   - Missing user pool ID: Make sure environment variables are correctly passed to the build
   - Invalid token: Check if the token is correctly formatted and not expired

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

## Docker Deployment

To build and run using Docker:

```bash
# Fetch environment variables from AWS SSM (or set them manually)
./scripts/get_cognito_env_values.ps1

# Build the Docker image with build arguments
docker build \
  --build-arg VITE_USER_POOL_ID=$(grep VITE_USER_POOL_ID .env | cut -d '=' -f2) \
  --build-arg VITE_USER_POOL_CLIENT_ID=$(grep VITE_USER_POOL_CLIENT_ID .env | cut -d '=' -f2) \
  --build-arg VITE_AWS_REGION=$(grep VITE_AWS_REGION .env | cut -d '=' -f2) \
  --build-arg VITE_CLOUDFRONT_CUSTOM_DOMAIN_URL=$(grep VITE_CLOUDFRONT_CUSTOM_DOMAIN_URL .env | cut -d '=' -f2) \
  -t fileshare-frontend .

# Run the container
docker run -p 8080:80 fileshare-frontend
```

Now access the application at http://localhost:8080

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)

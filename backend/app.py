# backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import os
import jwt
import requests
from functools import wraps

app = Flask(__name__)

# Configure CORS to allow localhost for development
CORS(app, origins=[
    "https://cf.aws.lupan.ca",           # Production frontend
    "http://localhost:3000",             # Local development
    "https://localhost:3000",            # Local development with HTTPS
    "http://127.0.0.1:3000",            # Alternative localhost
    "https://127.0.0.1:3000"            # Alternative localhost with HTTPS
])

# --- NEW: Cognito Configuration ---
# These will be loaded from environment variables set in the ECS Task Definition.
AWS_REGION = os.environ.get('AWS_REGION')
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')

# Construct the URL for the JSON Web Key Set (JWKS)
# This is used to get the public keys needed to verify the JWTs.
JWKS_URL = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
# Fetch the JWKS once when the application starts.
# In a real production app, you might cache this with a TTL.
try:
    jwks = requests.get(JWKS_URL).json()["keys"]
except requests.exceptions.RequestException as e:
    print(f"Error fetching JWKS: {e}")
    jwks = []


# --- NEW: JWT Validation Decorator ---
# A decorator is a clean, reusable way to protect Flask routes.
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check for the 'Authorization' header
        if 'Authorization' in request.headers:
            # The header should be in the format "Bearer <token>"
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Bearer token malformed'}), 401

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Get the unverified header from the token
            unverified_header = jwt.get_unverified_header(token)
            
            # Find the correct public key to use for validation
            rsa_key = {}
            for key in jwks:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
            
            if not rsa_key:
                 return jsonify({'message': 'Public key not found'}), 401
            
            # Verify the token's signature and claims
            decoded_token = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=None, # In a stricter setup, you would validate the 'aud' (client_id)
                issuer=f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
            )

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.PyJWTError as e:
            print(f"Token validation error: {e}")
            return jsonify({'message': 'Token is invalid!'}), 401
        
        # Pass the decoded token (which contains user claims) to the route
        return f(decoded_token=decoded_token, *args, **kwargs)

    return decorated


# --- Existing S3 Configuration ---
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
s3 = boto3.client('s3', region_name=AWS_REGION)
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)

@app.route("/")
def health_check():
    return jsonify({"status": "ok", "message": "Backend is healthy"})

# --- UPDATED: This endpoint is now protected ---
@app.route("/api/upload", methods=['POST'])
@token_required
def upload_file(decoded_token): # The decoded token is passed by the decorator
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': 'No file selected for uploading'}), 400

    if file and S3_BUCKET_NAME:
        try:
            # You could use the user's ID from the token to create user-specific folders in S3
            user_id = decoded_token.get('sub')
            file_key = f"{user_id}/{file.filename}"

            s3.upload_fileobj(file, S3_BUCKET_NAME, file_key)
            return jsonify({
                'message': 'File successfully uploaded',
                'file_name': file_key # Return the full key
            }), 200
        except Exception as e:
            return jsonify({'message': f'An error occurred: {e}'}), 500
    
    return jsonify({'message': 'S3 bucket not configured'}), 500

# --- UPDATED: This endpoint is protected and has tiered logic ---
@app.route("/api/get-download-link", methods=['GET'])
@token_required
def get_download_link(decoded_token):
    file_name = request.args.get('file_name')
    if not file_name:
        return jsonify({'message': 'Missing file_name parameter'}), 400
    
    # Determine expiration time based on user's group
    user_groups = decoded_token.get('cognito:groups', [])
    
    if 'premium-tier' in user_groups:
        expiration_seconds = 2592000 # 30 days
        tier = 'premium'
    else: # Default to free tier
        expiration_seconds = 259200  # 3 days
        tier = 'free'

    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': file_name},
            ExpiresIn=expiration_seconds
        )
        return jsonify({
            'download_url': url,
            'tier': tier,
            'expires_in_seconds': expiration_seconds
        })
    except Exception as e:
        return jsonify({'message': f'Could not generate presigned URL: {e}'}), 500

# --- NEW: Endpoint to handle tier upgrade ---
@app.route("/api/upgrade", methods=['POST'])
@token_required
def upgrade_tier(decoded_token):
    user_pool_id = decoded_token['iss'].split('/')[-1]
    user_name = decoded_token['username'] # Or 'cognito:username' depending on your setup

    try:
        # For this demo, we just upgrade. In a real app, you'd verify a payment webhook first.
        print(f"Upgrading user '{user_name}' to premium tier.")
        
        # Remove from free tier first (optional, but good practice)
        cognito_client.admin_remove_user_from_group(
            UserPoolId=user_pool_id,
            Username=user_name,
            GroupName='free-tier'
        )

        # Add to premium tier
        cognito_client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=user_name,
            GroupName='premium-tier'
        )
        
        return jsonify({'message': 'User successfully upgraded to premium tier.'}), 200

    except Exception as e:
        print(f"Error upgrading user tier: {e}")
        return jsonify({'message': f'An error occurred during upgrade: {e}'}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

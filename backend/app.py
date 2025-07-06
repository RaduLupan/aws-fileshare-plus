# backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import os
import jwt
import requests
import json
from functools import wraps
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import base64

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
COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')

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


def rsa_key_to_pem(rsa_key_dict):
    """Convert RSA key components (n, e) to PEM format for PyJWT"""
    try:
        # Decode base64url encoded values
        n = base64.urlsafe_b64decode(rsa_key_dict['n'] + '==')  # Add padding if needed
        e = base64.urlsafe_b64decode(rsa_key_dict['e'] + '==')  # Add padding if needed
        
        # Convert bytes to integers
        n_int = int.from_bytes(n, byteorder='big')
        e_int = int.from_bytes(e, byteorder='big')
        
        # Create RSA public key
        public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key()
        
        # Serialize to PEM format
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return pem.decode('utf-8')
    except Exception as e:
        print(f"Error converting RSA key to PEM: {e}")
        return None


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
              # Convert RSA key components to PEM format
            pem_key = rsa_key_to_pem(rsa_key)
            if not pem_key:
                return jsonify({'message': 'Failed to process public key'}), 401
            
            # Add comprehensive debug logging
            unverified_header = jwt.get_unverified_header(token)
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            
            print("=== JWT DEBUG INFO ===")
            print(f"Token header: {json.dumps(unverified_header, indent=2)}")
            print(f"Token payload: {json.dumps(unverified_payload, indent=2)}")
            print(f"Token audience (aud): {unverified_payload.get('aud')}")
            print(f"Token issuer (iss): {unverified_payload.get('iss')}")
            print(f"Token expiration (exp): {unverified_payload.get('exp')}")
            print(f"Token use (token_use): {unverified_payload.get('token_use')}")
            print(f"Expected audience (COGNITO_CLIENT_ID): {COGNITO_CLIENT_ID}")
            print(f"Expected issuer: https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}")
            print("=== END JWT DEBUG INFO ===")
            
            # Simplify JWT validation - ONLY verify signature for now
            decoded_token = jwt.decode(
                token,
                pem_key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_aud": False,  # Explicitly disable audience validation
                    "verify_iss": False,  # Explicitly disable issuer validation
                    "verify_exp": False   # Explicitly disable expiration validation
                }
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
def sanitize_filename(filename):
    """Sanitize filename by replacing problematic characters"""
    # Replace common problematic characters
    sanitized = filename.replace('&', '-')  # Replace & with -
    sanitized = sanitized.replace('#', '-')  # Replace # with -
    sanitized = sanitized.replace('?', '-')  # Replace ? with -
    sanitized = sanitized.replace('%', '-')  # Replace % with -
    sanitized = sanitized.replace('+', '-')  # Replace + with -
    # Remove any other potentially problematic characters but keep spaces
    import re
    sanitized = re.sub(r'[<>:"|*]', '-', sanitized)
    return sanitized

def get_user_folder_name(decoded_token):
    """Extract user folder name from JWT token - uses email for clean structure"""
    # Try to get email first (most reliable)
    user_email = decoded_token.get('email')
    if user_email:
        return user_email
    
    # Fallback to username (which should be email in our setup)
    username = decoded_token.get('username')
    if username:
        return username
    
    # Last resort: use user ID (should not happen with current setup)
    user_id = decoded_token.get('sub')
    print(f"Warning: Using user ID as folder name - email not found in token")
    return user_id

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
            # Sanitize the filename to avoid issues with special characters
            sanitized_filename = sanitize_filename(file.filename)
            print(f"Original filename: {file.filename}")
            print(f"Sanitized filename: {sanitized_filename}")
            
            # Use email address for cleaner, more intuitive folder structure
            user_folder = get_user_folder_name(decoded_token)
            if not user_folder:
                return jsonify({'message': 'User identification not found in token'}), 400
                
            print(f"User folder: {user_folder}")
            file_key = f"{user_folder}/{sanitized_filename}"
            print(f"S3 file key: {file_key}")

            s3.upload_fileobj(file, S3_BUCKET_NAME, file_key)
            return jsonify({
                'message': 'File successfully uploaded',
                'file_name': file_key # Return the full key with sanitized name
            }), 200
        except Exception as e:
            return jsonify({'message': f'An error occurred: {e}'}), 500
    
    return jsonify({'message': 'S3 bucket not configured'}), 500

# --- UPDATED: This endpoint is protected and has tiered logic ---
@app.route("/api/get-download-link", methods=['GET'])
@token_required
def get_download_link(decoded_token):
    # Simple approach: use URL decoding
    from urllib.parse import unquote
    encoded_file_name = request.args.get('file_name')
    if not encoded_file_name:
        return jsonify({'message': 'Missing file_name parameter'}), 400
    
    file_name = unquote(encoded_file_name)
    print(f"Encoded file_name: {encoded_file_name}")
    print(f"Decoded file_name: {file_name}")
    
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
        print(f"Generated presigned URL for S3 key: {file_name}")
        return jsonify({
            'download_url': url,
            'tier': tier,
            'expires_in_seconds': expiration_seconds
        })
    except Exception as e:
        print(f"Error generating presigned URL for key '{file_name}': {e}")
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


# --- NEW: Premium File Management Endpoints ---

@app.route("/api/files", methods=['GET'])
@token_required
def list_user_files(decoded_token):
    """List all files for the authenticated user with metadata (Premium feature)"""
    
    # Check if user has premium access
    user_groups = decoded_token.get('cognito:groups', [])
    if 'premium-tier' not in user_groups:
        return jsonify({'message': 'Premium feature - please upgrade your account'}), 403
    
    user_folder = get_user_folder_name(decoded_token)
    if not user_folder:
        return jsonify({'message': 'User identification not found in token'}), 400
    
    try:
        print(f"Listing files for user folder: {user_folder}")
        
        # List S3 objects with metadata for the user's folder
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix=f"{user_folder}/"
        )
        
        files = []
        for obj in response.get('Contents', []):
            # Skip the folder itself (empty key)
            if obj['Key'] == f"{user_folder}/":
                continue
                
            # Extract filename from S3 key (remove folder prefix)
            filename = obj['Key'].replace(f"{user_folder}/", "")
            
            # Format file size in human-readable format
            size_bytes = obj['Size']
            if size_bytes < 1024:
                size_display = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_display = f"{size_bytes / 1024:.1f} KB"
            else:
                size_display = f"{size_bytes / (1024 * 1024):.1f} MB"
            
            files.append({
                'key': obj['Key'],
                'filename': filename,
                'size_bytes': size_bytes,
                'size_display': size_display,
                'last_modified': obj['LastModified'].isoformat(),
                'upload_date': obj['LastModified'].strftime('%b %d, %Y')
            })
        
        # Sort files by last modified (newest first)
        files.sort(key=lambda x: x['last_modified'], reverse=True)
        
        print(f"Found {len(files)} files for user {user_folder}")
        return jsonify({
            'files': files,
            'total_count': len(files),
            'user_folder': user_folder
        })
        
    except Exception as e:
        print(f"Error listing files for user {user_folder}: {e}")
        return jsonify({'message': f'Error retrieving files: {e}'}), 500


@app.route("/api/files/new-link", methods=['POST'])
@token_required  
def generate_new_download_link(decoded_token):
    """Generate a new download link for an existing file (Premium feature)"""
    
    # Check if user has premium access
    user_groups = decoded_token.get('cognito:groups', [])
    if 'premium-tier' not in user_groups:
        return jsonify({'message': 'Premium feature - please upgrade your account'}), 403
    
    data = request.get_json()
    if not data or 'file_key' not in data:
        return jsonify({'message': 'Missing file_key parameter'}), 400
    
    file_key = data['file_key']
    user_folder = get_user_folder_name(decoded_token)
    
    # Security check: ensure file belongs to the authenticated user
    if not file_key.startswith(f"{user_folder}/"):
        return jsonify({'message': 'Access denied - file does not belong to user'}), 403
    
    try:
        print(f"Generating new link for file: {file_key}")
        
        # Check if file exists in S3
        s3.head_object(Bucket=S3_BUCKET_NAME, Key=file_key)
        
        # Determine expiration time based on user's tier
        if 'premium-tier' in user_groups:
            expiration_seconds = 2592000  # 30 days
            tier = 'premium'
        else:
            expiration_seconds = 259200   # 3 days (fallback)
            tier = 'free'
        
        # Generate new presigned URL
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': file_key},
            ExpiresIn=expiration_seconds
        )
        
        print(f"Generated new presigned URL for: {file_key}")
        return jsonify({
            'download_url': url,
            'file_key': file_key,
            'tier': tier,
            'expires_in_seconds': expiration_seconds,
            'expires_in_days': expiration_seconds // 86400
        })
        
    except s3.exceptions.NoSuchKey:
        return jsonify({'message': 'File not found'}), 404
    except Exception as e:
        print(f"Error generating new link for {file_key}: {e}")
        return jsonify({'message': f'Error generating download link: {e}'}), 500


@app.route("/api/files/<path:file_key>", methods=['DELETE'])
@token_required
def delete_user_file(decoded_token, file_key):
    """Delete a specific file from S3 (Premium feature)"""
    
    # Check if user has premium access
    user_groups = decoded_token.get('cognito:groups', [])
    if 'premium-tier' not in user_groups:
        return jsonify({'message': 'Premium feature - please upgrade your account'}), 403
    
    user_folder = get_user_folder_name(decoded_token)
    
    # Security check: ensure file belongs to the authenticated user
    if not file_key.startswith(f"{user_folder}/"):
        return jsonify({'message': 'Access denied - file does not belong to user'}), 403
    
    try:
        print(f"Deleting file: {file_key}")
        
        # Check if file exists before trying to delete
        s3.head_object(Bucket=S3_BUCKET_NAME, Key=file_key)
        
        # Delete the file from S3
        s3.delete_object(Bucket=S3_BUCKET_NAME, Key=file_key)
        
        print(f"Successfully deleted file: {file_key}")
        return jsonify({
            'message': 'File successfully deleted',
            'deleted_file': file_key
        })
        
    except s3.exceptions.NoSuchKey:
        return jsonify({'message': 'File not found'}), 404
    except Exception as e:
        print(f"Error deleting file {file_key}: {e}")
        return jsonify({'message': f'Error deleting file: {e}'}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

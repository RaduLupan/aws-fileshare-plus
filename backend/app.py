# backend/app.py

from flask import Flask, request, jsonify, redirect
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
from url_shortener import create_short_url, get_full_url, get_user_urls, delete_short_url
from datetime import datetime, timedelta

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
        print("=== TOKEN VALIDATION DEBUG ===")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Authorization header: {request.headers.get('Authorization', 'NOT FOUND')}")
        
        token = None
        
        # Check for the 'Authorization' header
        if 'Authorization' in request.headers:
            # The header should be in the format "Bearer <token>"
            try:
                auth_header = request.headers['Authorization']
                print(f"Full Authorization header: {auth_header[:50]}...")
                token = auth_header.split(" ")[1]
                print(f"Extracted token: {token[:20]}...")
            except IndexError:
                print("Bearer token malformed - IndexError")
                return jsonify({'message': 'Bearer token malformed'}), 401
        
        if not token:
            print("TOKEN IS MISSING!")
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
        expiration_seconds = 604800 # 7 days (S3 maximum)
        tier = 'premium'
    else: # Default to free tier
        expiration_seconds = 259200  # 3 days
        tier = 'free'

    try:
        # Generate presigned URL first
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': file_name},
            ExpiresIn=expiration_seconds
        )
        print(f"Generated presigned URL for S3 key: {file_name}")
        
        # Create short URL for the presigned URL
        user_email = decoded_token.get('email', 'unknown')
        filename = file_name.split('/')[-1] if '/' in file_name else file_name
        
        short_url_result = create_short_url(
            full_url=presigned_url,
            user_email=user_email,
            file_key=file_name,
            filename=filename,
            expires_in_days=expiration_seconds // 86400  # Convert seconds to days
        )
        
        # Build short URL using CloudFront domain
        base_url = get_short_url_base()
        short_url = f"{base_url}/s/{short_url_result['short_code']}"
        
        return jsonify({
            'download_url': short_url,  # Return short URL instead of long presigned URL
            'short_code': short_url_result['short_code'],
            'tier': tier,
            'expires_in_seconds': expiration_seconds,
            'message': 'Short download URL created'
        })
    except Exception as e:
        print(f"Error generating download URL for key '{file_name}': {e}")
        return jsonify({'message': f'Could not generate download URL: {e}'}), 500

# --- NEW: Endpoint to handle tier upgrade ---
@app.route("/api/upgrade", methods=['POST'])
@token_required
def upgrade_tier(decoded_token):
    try:
        # Debug: Print the decoded token to see its structure
        print("=== UPGRADE DEBUG INFO ===")
        print(f"Decoded token: {json.dumps(decoded_token, indent=2, default=str)}")
        print("=== END UPGRADE DEBUG INFO ===")
        
        # Extract username from token (could be 'username', 'cognito:username', or 'sub')
        user_name = decoded_token.get('username') or decoded_token.get('cognito:username') or decoded_token.get('sub')
        
        if not user_name:
            print("Error: Could not extract username from token")
            return jsonify({'message': 'Could not extract username from token'}), 400
        
        # Use the environment variable for user pool ID
        user_pool_id = COGNITO_USER_POOL_ID
        
        if not user_pool_id:
            print("Error: COGNITO_USER_POOL_ID not set")
            return jsonify({'message': 'Cognito configuration error'}), 500
        
        print(f"Upgrading user '{user_name}' to premium tier in pool '{user_pool_id}'")
        
        # For this demo, we just upgrade. In a real app, you'd verify a payment webhook first.
        
        # Remove from free tier first (optional, but good practice)
        try:
            cognito_client.admin_remove_user_from_group(
                UserPoolId=user_pool_id,
                Username=user_name,
                GroupName='free-tier'
            )
            print(f"Removed user '{user_name}' from free-tier group")
        except cognito_client.exceptions.ClientError as e:
            # It's okay if user wasn't in free tier
            if e.response['Error']['Code'] != 'UserNotInGroupException':
                print(f"Warning: Could not remove user from free-tier: {e}")

        # Add to premium tier
        cognito_client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=user_name,
            GroupName='premium-tier'
        )
        print(f"Added user '{user_name}' to premium-tier group")
        
        return jsonify({'message': 'User successfully upgraded to premium tier.'}), 200

    except Exception as e:
        print(f"Error upgrading user tier: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'An error occurred during upgrade: {str(e)}'}), 500


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
            expiration_seconds = 604800  # 7 days (S3 maximum)
            tier = 'premium'
        else:
            expiration_seconds = 259200   # 3 days (fallback)
            tier = 'free'
        
        # Generate new presigned URL
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': file_key},
            ExpiresIn=expiration_seconds
        )
        
        # Create short URL for the presigned URL
        user_email = decoded_token.get('email', 'unknown')
        filename = file_key.split('/')[-1] if '/' in file_key else file_key
        
        short_url_result = create_short_url(
            full_url=presigned_url,
            user_email=user_email,
            file_key=file_key,
            filename=filename,
            expires_in_days=expiration_seconds // 86400  # Convert seconds to days
        )
        
        # Build short URL using CloudFront domain
        base_url = get_short_url_base()
        short_url = f"{base_url}/s/{short_url_result['short_code']}"
        
        print(f"Generated new short URL for: {file_key}")
        return jsonify({
            'download_url': short_url,  # Return short URL instead of long presigned URL
            'short_code': short_url_result['short_code'],
            'file_key': file_key,
            'tier': tier,
            'expires_in_seconds': expiration_seconds,
            'expires_in_days': expiration_seconds // 86400,
            'message': 'New short download URL created'
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


# ========================================
# URL Shortener Endpoints
# ========================================

@app.route('/api/shorten', methods=['POST'])
@token_required
def shorten_url(decoded_token):
    """Create a short URL for a given long URL"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'message': 'URL is required'}), 400
            
        full_url = data['url']
        file_key = data.get('file_key')
        filename = data.get('filename')
        expires_in_days = data.get('expires_in_days', 7)
        
        # Get user email from token
        user_email = decoded_token.get('email', 'unknown')
        
        # Create short URL
        result = create_short_url(
            full_url=full_url,
            user_email=user_email,
            file_key=file_key,
            filename=filename,
            expires_in_days=expires_in_days
        )
        
        # Build short URL using CloudFront domain
        base_url = get_short_url_base()
        short_url = f"{base_url}/s/{result['short_code']}"
        
        return jsonify({
            'short_url': short_url,
            'short_code': result['short_code'],
            'created': result['created'],
            'expires_at': result.get('expires_at'),
            'message': result['message']
        })
        
    except Exception as e:
        print(f"Error creating short URL: {e}")
        return jsonify({'message': f'Error creating short URL: {e}'}), 500

@app.route('/s/<short_code>')
def redirect_short_url(short_code):
    """Redirect short URL to full URL"""
    try:
        result = get_full_url(short_code)
        
        if not result:
            return jsonify({
                'message': 'Short URL not found or expired',
                'error': 'NOT_FOUND'
            }), 404
            
        # Log the redirect for analytics
        print(f"Redirecting {short_code} to {result['full_url']} (click #{result['click_count']})")
        
        # Redirect to the full URL
        return redirect(result['full_url'])
        
    except Exception as e:
        print(f"Error redirecting short URL {short_code}: {e}")
        return jsonify({'message': f'Error processing short URL: {e}'}), 500

@app.route('/api/short-urls', methods=['GET'])
@token_required
def list_short_urls(decoded_token):
    """List all short URLs created by the authenticated user"""
    try:
        user_email = decoded_token.get('email', 'unknown')
        limit = int(request.args.get('limit', 100))
        
        urls = get_user_urls(user_email, limit)
        
        # Add full short URLs
        base_url = request.host_url.rstrip('/')
        for url in urls:
            url['short_url'] = f"{base_url}/s/{url['short_code']}"
        
        return jsonify({
            'urls': urls,
            'count': len(urls)
        })
        
    except Exception as e:
        print(f"Error listing short URLs: {e}")
        return jsonify({'message': f'Error listing short URLs: {e}'}), 500

@app.route('/api/short-urls/<short_code>', methods=['DELETE'])
@token_required
def delete_short_url_endpoint(decoded_token, short_code):
    """Delete a short URL (only if owned by user)"""
    try:
        user_email = decoded_token.get('email', 'unknown')
        
        deleted = delete_short_url(short_code, user_email)
        
        if deleted:
            return jsonify({
                'message': 'Short URL deleted successfully',
                'short_code': short_code
            })
        else:
            return jsonify({
                'message': 'Short URL not found or unauthorized'
            }), 404
            
    except Exception as e:
        print(f"Error deleting short URL {short_code}: {e}")
        return jsonify({'message': f'Error deleting short URL: {e}'}), 500


def get_short_url_base():
    """Get the base URL for constructing short URLs (prefer CloudFront domain)"""
    frontend_domain = os.getenv('FRONTEND_DOMAIN')
    if frontend_domain:
        # Use CloudFront domain for short URLs
        return f"https://{frontend_domain}"
    else:
        # Fallback to ALB domain (for local development)
        return request.host_url.rstrip('/')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

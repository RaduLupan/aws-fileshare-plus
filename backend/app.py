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
import re
from url_shortener import create_short_url, get_full_url, get_user_urls, delete_short_url, scheduled_cleanup
from database import init_database
# NOTE: user_management imports moved to runtime to prevent startup crashes
# from user_management import (
#     initialize_user, 
#     get_user_info, 
#     start_user_trial, 
#     get_user_trial_status,
#     validate_trial_eligibility,
#     process_expired_trials
# )
from datetime import datetime, timedelta

app = Flask(__name__)

# Initialize database on app startup
try:
    init_database()
    print("Database initialized successfully on startup")
    
    # TODO: Now that tables exist, ensure trial columns and Cognito groups
    # ensure_premium_trial_group()
    # ensure_trial_columns()
    print("Database initialization completed - trial system setup pending")
    
except Exception as e:
    print(f"ERROR: Failed to initialize database on startup: {e}")
    # Continue anyway - app might still work for basic functions

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
    print(f"Fetching JWKS from: {JWKS_URL}")
    jwks_response = requests.get(JWKS_URL)
    jwks_response.raise_for_status()
    jwks_data = jwks_response.json()
    print(f"JWKS response: {jwks_data}")
    jwks = jwks_data["keys"]
    print(f"Successfully loaded {len(jwks)} keys from JWKS")
except requests.exceptions.RequestException as e:
    print(f"Error fetching JWKS: {e}")
    jwks = []
except KeyError as e:
    print(f"Error parsing JWKS response - missing 'keys' field: {e}")
    jwks = []
except Exception as e:
    print(f"Unexpected error fetching JWKS: {e}")
    jwks = []


def rsa_key_to_pem(rsa_key_dict):
    """Convert RSA key components (n, e) to PEM format for PyJWT"""
    try:
        # Properly pad base64url encoded values
        def pad_base64(s):
            """Add proper padding to base64 string"""
            return s + '=' * ((4 - len(s) % 4) % 4)
        
        # Decode base64url encoded values with proper padding
        n = base64.urlsafe_b64decode(pad_base64(rsa_key_dict['n']))
        e = base64.urlsafe_b64decode(pad_base64(rsa_key_dict['e']))
        
        # Convert bytes to integers
        n_int = int.from_bytes(n, byteorder='big')
        e_int = int.from_bytes(e, byteorder='big')
        
        # Create RSA public key - note: RSAPublicNumbers takes (e, n) not (e_int, n_int)
        public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key()
        
        # Serialize to PEM format
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return pem.decode('utf-8')
    except Exception as e:
        print(f"Error converting RSA key to PEM: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
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
            
            # Proper JWT validation with security checks enabled
            expected_issuer = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
            
            decoded_token = jwt.decode(
                token,
                pem_key,
                algorithms=["RS256"],
                audience=COGNITO_CLIENT_ID,
                issuer=expected_issuer,
                options={
                    "verify_signature": True,
                    "verify_aud": True,   # Enable audience validation
                    "verify_iss": True,   # Enable issuer validation
                    "verify_exp": True    # Enable expiration validation
                }
            )

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.PyJWTError as e:
            print(f"Token validation error: {e}")
            return jsonify({'message': 'Token is invalid!'}), 401
        
        # Check for expired trials on each authenticated request
        try:
            user_email = decoded_token.get('email')
            user_id = decoded_token.get('sub')
            user_groups = decoded_token.get('cognito:groups', [])
            
            if user_email and user_id and 'premium-trial' in user_groups:
                # Check if this trial user's trial has expired
                try:
                    from user_management import get_user_trial_status
                    trial_status = get_user_trial_status(user_email, user_id)
                    if trial_status['trial_status'] == 'expired':
                        # Process this expired trial
                        from cognito_utils import move_user_to_free_group
                        move_user_to_free_group(user_email)
                        print(f"Processed expired trial for user {user_email}")
                except ImportError as ie:
                    print(f"Warning: Could not import user_management: {ie}")
                except Exception as e:
                    print(f"Warning: Trial status check failed: {e}")
        except Exception as e:
            # Don't fail the request if trial checking fails
            print(f"Warning: Trial expiration check failed: {e}")
        
        # Pass the decoded token (which contains user claims) to the route
        return f(decoded_token=decoded_token, *args, **kwargs)

    return decorated


# --- Existing S3 Configuration ---
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
s3 = boto3.client('s3', region_name=AWS_REGION)
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)

@app.route("/")
def root_health_check():
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
    
    if 'premium-tier' in user_groups or 'premium-trial' in user_groups:
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
    
    try:
        print("=== FILES API DEBUG ===")
        print(f"Decoded token: {decoded_token}")
        print(f"User groups: {decoded_token.get('cognito:groups', [])}")
        
        # Check if user has premium access
        user_groups = decoded_token.get('cognito:groups', [])
        if 'premium-tier' not in user_groups and 'premium-trial' not in user_groups:
            print(f"User denied access - groups: {user_groups}")
            return jsonify({'message': 'Premium feature - please upgrade your account'}), 403
        
        user_folder = get_user_folder_name(decoded_token)
        if not user_folder:
            print("User folder not found in token")
            return jsonify({'message': 'User identification not found in token'}), 400
            
        print(f"User folder: {user_folder}")
        
    except Exception as e:
        print(f"Error in files API pre-processing: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'message': f'Error processing request: {str(e)}'}), 500
    
    try:
        print(f"Listing files for user folder: {user_folder}")
        
        # List S3 objects with metadata for the user's folder
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix=f"{user_folder}/"
        )
        print(f"S3 response received: {response.get('ResponseMetadata', {}).get('HTTPStatusCode')}")
        
        files = []
        user_email = decoded_token.get('email', 'unknown')
        
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
            
            # Get short URL info for this file
            short_url_info = None
            try:
                # Get user's URLs and find the one for this file
                user_urls = get_user_urls(user_email, limit=1000)  # Get more URLs to find the right one
                for url_data in user_urls:
                    if url_data.get('file_key') == obj['Key']:
                        short_url_info = url_data
                        break
            except Exception as url_error:
                print(f"Error getting short URL info for {obj['Key']}: {url_error}")
            
            file_data = {
                'key': obj['Key'],
                'filename': filename,
                'size_bytes': size_bytes,
                'size_display': size_display,
                'last_modified': obj['LastModified'].isoformat(),
                'upload_date': obj['LastModified'].strftime('%b %d, %Y')
            }
            
            # Add short URL information if available
            if short_url_info:
                file_data.update({
                    'short_code': short_url_info.get('short_code'),
                    'click_count': short_url_info.get('click_count', 0),
                    'url_created_at': short_url_info.get('created_at'),
                    'expires_at': short_url_info.get('expires_at'),
                    'expires_in_days': short_url_info.get('expires_in_days', 7)
                })
            else:
                # No short URL exists for this file yet
                file_data.update({
                    'short_code': None,
                    'click_count': 0,
                    'url_created_at': None,
                    'expires_at': None,
                    'expires_in_days': None
                })
            
            files.append(file_data)
        
        # Sort files by last modified (newest first)
        files.sort(key=lambda x: x['last_modified'], reverse=True)
        
        result = {
            'files': files,
            'total_count': len(files),
            'user_folder': user_folder
        }
        
        print(f"Found {len(files)} files for user {user_folder}")
        print(f"Returning JSON response: {json.dumps(result, indent=2)}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error listing files for user {user_folder}: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        error_response = {'message': f'Error retrieving files: {str(e)}'}
        print(f"Returning error JSON: {json.dumps(error_response)}")
        return jsonify(error_response), 500


@app.route("/api/files/new-link", methods=['POST'])
@token_required  
def generate_new_download_link(decoded_token):
    """Generate a new download link for an existing file (Premium feature)"""
    
    # Check if user has premium access
    user_groups = decoded_token.get('cognito:groups', [])
    if 'premium-tier' not in user_groups and 'premium-trial' not in user_groups:
        return jsonify({'message': 'Premium feature - please upgrade your account'}), 403
    
    data = request.get_json()
    if not data or 'file_key' not in data:
        return jsonify({'message': 'Missing file_key parameter'}), 400
    
    file_key = data['file_key']
    
    # Get expiration_days from request, default to 3 days, validate range 1-7
    expiration_days = data.get('expiration_days', 3)
    try:
        expiration_days = int(expiration_days)
        if expiration_days < 1 or expiration_days > 7:
            expiration_days = 3  # Default to 3 days if invalid
    except (ValueError, TypeError):
        expiration_days = 3  # Default to 3 days if invalid
    
    print(f"New link request: file_key={file_key}, expiration_days={expiration_days}")
    
    user_folder = get_user_folder_name(decoded_token)
    
    # Security check: ensure file belongs to the authenticated user
    if not file_key.startswith(f"{user_folder}/"):
        return jsonify({'message': 'Access denied - file does not belong to user'}), 403
    
    try:
        print(f"Generating new link for file: {file_key}")
        
        # Check if file exists in S3
        s3.head_object(Bucket=S3_BUCKET_NAME, Key=file_key)
        
        # Use user-specified expiration days (1-7 days for Premium)
        expiration_seconds = expiration_days * 86400  # Convert days to seconds
        tier = 'premium'
        
        print(f"Generating presigned URL with {expiration_days} days ({expiration_seconds} seconds) expiration")
        
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
            expires_in_days=expiration_days  # Use user-specified days
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
    if 'premium-tier' not in user_groups and 'premium-trial' not in user_groups:
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

# --- NEW: Premium Trial API Endpoints ---

# OLD start-trial endpoint removed - replaced with enhanced debug version below

@app.route('/api/user-status', methods=['GET'])
@token_required
def user_status_endpoint(decoded_token):
    """Get comprehensive user status including trial information"""
    try:
        user_email = decoded_token.get('email')
        user_id = decoded_token.get('sub')
        user_groups = decoded_token.get('cognito:groups', [])
        
        if not user_email or not user_id:
            return jsonify({
                'error': 'User identification not found in token'
            }), 400
        
        # Get trial status from database
        try:
            from user_management import get_user_trial_status
            trial_status = get_user_trial_status(user_email, user_id)
        except ImportError:
            # Fallback if user_management can't be imported
            trial_status = {
                'user_tier': 'Free',
                'trial_status': 'not_started',
                'days_remaining': 0,
                'can_start_trial': True
            }
        
        # Determine user tier - prioritize database over JWT groups
        database_tier = trial_status.get('user_tier', 'Free')
        
        if database_tier == 'Premium-Trial':
            current_tier = 'Premium-Trial'
        elif database_tier == 'Premium' or 'premium-tier' in user_groups:
            current_tier = 'Premium'
        elif 'premium-trial' in user_groups:
            current_tier = 'Premium-Trial'
        else:
            current_tier = 'Free'
        
        # Build response
        response = {
            'user_email': user_email,
            'tier': current_tier,
            'cognito_groups': user_groups,
            'trial_status': trial_status['trial_status'],
            'can_start_trial': trial_status['can_start_trial'],
            'days_remaining': trial_status['days_remaining'],
            'trial_expires_at': trial_status['trial_expires_at'],
            'trial_started_at': trial_status['trial_started_at']
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error getting user status: {e}")
        return jsonify({
            'error': f'Failed to get user status: {str(e)}'
        }), 500

@app.route('/api/trial-eligibility', methods=['GET'])
@token_required
def trial_eligibility_endpoint(decoded_token):
    """Check if user is eligible to start a Premium trial"""
    try:
        user_email = decoded_token.get('email')
        user_id = decoded_token.get('sub')
        
        if not user_email or not user_id:
            return jsonify({
                'eligible': False,
                'reason': 'User identification not found in token'
            }), 400
        
        eligibility = validate_trial_eligibility(user_email, user_id)
        return jsonify(eligibility)
        
    except Exception as e:
        print(f"Error checking trial eligibility: {e}")
        return jsonify({
            'eligible': False,
            'reason': f'Error: {str(e)}'
        }), 500

@app.route('/api/admin/expire-trials', methods=['POST'])
@token_required
def expire_trials_endpoint(decoded_token):
    """Admin endpoint to manually process expired trials"""
    try:
        user_groups = decoded_token.get('cognito:groups', [])
        
        # Check if user has admin privileges (you can modify this logic)
        if 'admin' not in user_groups and 'premium-tier' not in user_groups:
            return jsonify({
                'success': False,
                'error': 'Insufficient privileges'
            }), 403
        
        result = process_expired_trials()
        return jsonify(result)
        
    except Exception as e:
        print(f"Error processing expired trials: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to process expired trials: {str(e)}'
        }), 500

# --- NEW: Debug and Health Check Endpoints ---

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'v0.7.0-debug'
    })

@app.route('/api/debug/test-imports', methods=['GET'])
def test_imports():
    """Test if all modules can be imported properly"""
    results = {}
    
    # Test database imports
    try:
        from database import create_or_update_user, get_user_by_email
        results['database'] = 'SUCCESS'
    except Exception as e:
        results['database'] = f'FAILED: {str(e)}'
    
    # Test user_management imports  
    try:
        from user_management import start_user_trial, validate_trial_eligibility
        results['user_management'] = 'SUCCESS'
    except Exception as e:
        results['user_management'] = f'FAILED: {str(e)}'
    
    # Test cognito_utils imports
    try:
        from cognito_utils import add_user_to_group
        results['cognito_utils'] = 'SUCCESS'
    except Exception as e:
        results['cognito_utils'] = f'FAILED: {str(e)}'
    
    # Test simple trial functions
    try:
        from simple_trial_functions import simple_start_trial, simple_add_user_to_group
        results['simple_trial_functions'] = 'SUCCESS'
    except Exception as e:
        results['simple_trial_functions'] = f'FAILED: {str(e)}'
    
    # Test the simple_start_trial_fallback function
    try:
        # Just test if we can call the function (don't actually execute it)
        fallback_callable = callable(simple_start_trial_fallback)
        results['fallback_function'] = f'SUCCESS - callable: {fallback_callable}'
    except Exception as e:
        results['fallback_function'] = f'FAILED: {str(e)}'
    
    return jsonify({
        'success': True,
        'imports': results
    })

@app.route('/api/start-trial', methods=['POST'])
@token_required
def start_trial_endpoint(decoded_token):
    """Start a 30-day Premium trial for the user"""
    # Enhanced logging for debugging
    print(f"[DEBUG] start_trial_endpoint called at {datetime.now()}")
    print(f"[DEBUG] decoded_token type: {type(decoded_token)}")
    print(f"[DEBUG] decoded_token keys: {list(decoded_token.keys()) if decoded_token else 'None'}")
    
    try:
        user_email = decoded_token.get('email')
        user_id = decoded_token.get('sub')
        
        print(f"[DEBUG] Extracted - user_email: {user_email}, user_id: {user_id}")
        
        if not user_email or not user_id:
            print(f"[ERROR] Missing user identification in token")
            print(f"[ERROR] Token contents: {decoded_token}")
            return jsonify({
                'success': False,
                'error': 'User identification not found in token',
                'debug_info': {
                    'token_keys': list(decoded_token.keys()) if decoded_token else [],
                    'email_present': bool(user_email),
                    'id_present': bool(user_id)
                }
            }), 400

        # Always use fallback approach since original imports are broken
        print(f"[DEBUG] About to call fallback for {user_email}")
        try:
            result = simple_start_trial_fallback(user_email, user_id)
            print(f"[DEBUG] Fallback returned: {result}")
        except Exception as fallback_error:
            print(f"[FALLBACK ERROR] Exception in fallback: {fallback_error}")
            import traceback
            print(f"[FALLBACK ERROR] Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': f'Fallback function failed: {str(fallback_error)}',
                'fallback_traceback': traceback.format_exc()
            }), 500
        
        if result and result.get('success'):
            print(f"[SUCCESS] Trial started successfully for {user_email}")
            return jsonify({
                'success': True,
                'message': result['message'],
                'trial_expires_at': result['trial_status']['trial_expires_at'],
                'days_remaining': result['trial_status']['days_remaining']
            })
        else:
            print(f"[ERROR] Trial start failed: {result}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error in trial start'),
                'debug_result': result
            }), 400
            
    except Exception as e:
        print(f"[EXCEPTION] Error starting trial for user: {e}")
        print(f"[EXCEPTION] Exception type: {type(e).__name__}")
        import traceback
        print(f"[EXCEPTION] Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Failed to start trial: {str(e)}',
            'exception_type': type(e).__name__
        }), 500

# --- Fallback functions in case of import issues ---
def simple_start_trial_fallback(user_email, user_id):
    """Simple fallback trial starter for debugging"""
    try:
        # Use the simple trial functions
        from simple_trial_functions import simple_start_trial, simple_add_user_to_group, simple_remove_user_from_group, simple_get_user_by_email
        
        print(f"[FALLBACK] Starting trial for {user_email} using simple functions")
        
        # Basic eligibility check - see if user already has trial
        existing_user = simple_get_user_by_email(user_email)
        if existing_user and existing_user.get('trial_used'):
            print(f"[FALLBACK] User {user_email} has already used trial")
            return {
                'success': False,
                'error': 'Trial already used for this account'
            }
        
        # Start the trial in database
        result = simple_start_trial(user_id, user_email)
        
        if result['success']:
            # Try to update Cognito groups
            try:
                simple_remove_user_from_group(user_email, 'free-tier')
                simple_add_user_to_group(user_email, 'premium-trial')
                print(f"[FALLBACK] Cognito groups updated for {user_email}")
            except Exception as cognito_err:
                print(f"[WARNING] Cognito group update failed: {cognito_err}")
                
            return {
                'success': True,
                'message': 'Trial started successfully (fallback method)',
                'trial_status': {
                    'trial_expires_at': result['trial_expires_at'],
                    'days_remaining': result['days_remaining']
                }
            }
        else:
            return result
            
    except Exception as e:
        print(f"[FALLBACK ERROR] {e}")
        return {
            'success': False,
            'error': f'Fallback trial start failed: {str(e)}'
        }

# --- Existing error handlers ---
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with JSON response"""
    return jsonify({'message': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors with JSON response"""
    return jsonify({'message': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with JSON response"""
    return jsonify({'message': 'Internal server error occurred'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all other exceptions with JSON response"""
    # Log the actual error for debugging
    import traceback
    print(f"Unhandled exception: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    
    # Return a generic JSON error response
    return jsonify({'message': 'An unexpected error occurred'}), 500

# --- Setup and Initialization Functions ---

def ensure_premium_trial_group():
    """Ensure the premium-trial Cognito group exists"""
    try:
        from cognito_utils import ensure_trial_group_exists, validate_cognito_setup
        
        # Create premium-trial group if it doesn't exist
        ensure_trial_group_exists()
        
        # Validate all required groups exist
        validation = validate_cognito_setup()
        if validation['valid']:
            print("✅ All required Cognito groups are available")
        else:
            print(f"⚠️ Missing Cognito groups: {validation.get('missing_groups', [])}")
            
    except Exception as e:
        print(f"Warning: Could not validate Cognito setup: {e}")

# Database migration check for trial columns
def ensure_trial_columns():
    """Ensure trial columns exist in users table"""
    try:
        from database import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if trial columns exist
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            
            missing_columns = []
            required_columns = ['trial_started_at', 'trial_expires_at', 'trial_used']
            
            for col in required_columns:
                if col not in columns:
                    missing_columns.append(col)
            
            # Add missing columns
            if missing_columns:
                print(f"[MIGRATION] Adding missing trial columns: {missing_columns}")
                
                if 'trial_started_at' in missing_columns:
                    cursor.execute('ALTER TABLE users ADD COLUMN trial_started_at TIMESTAMP NULL')
                
                if 'trial_expires_at' in missing_columns:
                    cursor.execute('ALTER TABLE users ADD COLUMN trial_expires_at TIMESTAMP NULL')
                
                if 'trial_used' in missing_columns:
                    cursor.execute('ALTER TABLE users ADD COLUMN trial_used BOOLEAN DEFAULT FALSE')
                
                conn.commit()
                print(f"[MIGRATION] Trial columns added successfully")
            
            return True
            
    except Exception as e:
        print(f"[ERROR] Failed to ensure trial columns: {e}")
        return False

@app.route('/api/debug/test-fallback', methods=['GET'])
def test_fallback():
    """Test the fallback trial logic without authentication"""
    try:
        # Test the fallback function directly
        test_email = "test@example.com"
        test_user_id = "test-user-123"
        
        result = simple_start_trial_fallback(test_email, test_user_id)
        
        return jsonify({
            'success': True,
            'fallback_test': result,
            'message': 'Fallback function test completed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Fallback test failed: {str(e)}',
            'exception_type': type(e).__name__
        }), 500

@app.route('/api/debug/check-db-tables', methods=['GET'])
def check_db_tables():
    """Check if database tables exist"""
    try:
        import sqlite3
        import os
        
        db_path = os.path.join(os.path.dirname(__file__), 'url_shortener.db')
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Check users table specifically
            users_table_exists = 'users' in tables
            
            # If users table exists, check its structure
            table_info = {}
            if users_table_exists:
                cursor.execute("PRAGMA table_info(users)")
                table_info = {row[1]: row[2] for row in cursor.fetchall()}
            
            return jsonify({
                'success': True,
                'database_path': db_path,
                'database_exists': os.path.exists(db_path),
                'all_tables': tables,
                'users_table_exists': users_table_exists,
                'users_table_columns': table_info,
                'message': 'Database table check completed'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Database check failed: {str(e)}',
            'exception_type': type(e).__name__
        }), 500

@app.route('/api/admin/cleanup-expired-urls', methods=['POST'])
def cleanup_expired_urls_endpoint():
    """Administrative endpoint for cleaning up expired URLs - should be called by scheduled tasks"""
    try:
        deleted_count = scheduled_cleanup()
        return jsonify({
            'message': f'Cleanup completed successfully',
            'deleted_count': deleted_count
        }), 200
    except Exception as e:
        return jsonify({
            'message': f'Cleanup failed: {str(e)}',
            'deleted_count': 0
        }), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

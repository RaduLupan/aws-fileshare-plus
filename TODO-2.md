# URL Shortening Service Implementation Guide

## Steps to Implement URL Shortening Service

### Choose a Database
- Use a database to store the mapping between short URLs (or codes) and the original pre-signed URLs
- Common choices include relational databases like PostgreSQL, MySQL, or NoSQL options like DynamoDB

### Generate Short URLs
- Create a function to generate a unique identifier for each URL. This could be a hash or a random string
- Ensure the identifier is short and unique

### Create a Mapping Endpoint
- Set up a new endpoint in your Flask app to generate short URLs. This will take a full URL from the client and return a shortened code
- This code will be stored in the database with its corresponding full URL

### Redirect Handling
- Implement a mechanism to handle requests to the shortened URL, retrieve the full URL from the database, and redirect the user to the original link

## Example Implementation

Here's a high-level example, assuming you're using a key-value database like Redis or DynamoDB (I'll use a simple dictionary for illustration):

```python
import os
import boto3
import logging
import random
import string
from flask import Flask, request, jsonify, redirect, abort
from botocore.exceptions import BotoCoreError, NoCredentialsError, PartialCredentialsError, ClientError

# Load environment variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'my-wetransfer-clone-bucket-2d3865bcce5e')

# Mock database (use a real database in production)
url_mapping = {}

# Initialize the Flask application
app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    welcome_message = {
        'message': 'Welcome to We Transfer Clone API',
        'description': 'This API allows you to upload files to S3.',
    }
    return jsonify(welcome_message), 200

def generate_presigned_url(file_name, expiration=3600):
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': S3_BUCKET_NAME,
                                                            'Key': file_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logger.error(e)
        return None

    return response

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    try:
        # Using the boto3 client for S3
        s3_client = boto3.client('s3')
        s3_client.upload_fileobj(file, S3_BUCKET_NAME, file.filename)

        # Generate the short code (e.g., a simple hash or random string)
        short_code = generate_short_code(file.filename)

        # Store the mapping of short code to the presigned URL in the mock database
        download_url = generate_presigned_url(file.filename)
        url_mapping[short_code] = download_link

        # Return the short link
        return jsonify({'message': 'File successfully uploaded', 'short_url': f"http://flask-app-lb-526872237.us-east-1.elb.amazonaws.com/{short_code}"}), 200

    except (BotoCoreError, NoCredentialsError, PartialCredentialsError) as e:
        logger.error(f"S3 client error: {e}")
        return jsonify({'error': 'File upload failed', 'message': str(e)}), 500
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        return jsonify({'error': 'An unexpected error occurred', 'message': str(e)}), 500

@app.route('/get-download-link', methods=['GET'])
def get_download_link():
    file_name = request.args.get('file_name')
    if not file_name:
        return jsonify({'error': 'No file name provided'}), 400

    # Generate a short URL (code)
    short_code = generate_short_code(file_name)
    
    url = generate_presigned_url(file_name)
    if url:
        # Store the short URL mapping
        url_mapping[short_code] = url
        return jsonify({'download_url': f"http://flask-app-lb-526872237.us-east-1.elb.amazonaws.com/{short_code}"}), 200
    else:
        return jsonify({'error': 'Failed to generate download link'}), 500

@app.route('/<short_code>', methods=['GET'])
def redirect_to_original_url(short_code):
    # Look up the short code in the database
    original_url = url_mapping.get(short_code)
    if original_url:
        return jsonify({'redirect_url': original_url}), 200
    else:
        return jsonify({'error': 'Invalid short code'}), 404

def generate_short_code(file_name):
    # Example placeholder implementation for generating short codes
    import hashlib
    hash_object = hashlib.md5(file_name.encode())
    short_code = hash_object.hexdigest()[:6]  # Take the first few characters for the short code
    return short_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Implementation Details

### Generating Short Codes
- This code uses an MD5 hash truncated to six characters as a short code, which you can adjust
- Ensure collision prevention with a consistent hashing strategy

### Redirection
- The app supports dynamic routing with URLs such as `http://flask-app-lb-526872237.us-east-1.elb.amazonaws.com/abc123` redirecting to the respective pre-signed URL
- This enables easy sharing of short links

### Database Setup
- For production, integrate a database-backed storage solution such as Redis, PostgreSQL, or DynamoDB
- Use this to consistently store and map short codes to pre-signed URLs

## Next Steps

1. Implement a mechanism to check short code uniqueness to avoid collision (you can do this with random IDs or using a more sophisticated system)

2. Set up API calls in your React app to connect with these endpoints

3. Consider implementing a user-friendly interface for handling files, managing links, and enhancing security

4. Look into existing URL shortening libraries and services (like bit.ly) if you want a simpler setup for shortening URLs without maintaining a custom database solution, although this might not be free
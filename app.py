import os
import logging
from flask import Flask, request, jsonify, render_template, flash, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils.decoder import ClassPlusDecoder
from utils.classplus_client import ClassPlusClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "classplus-decoder-secret-key")

# Configure rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

# Initialize decoder and client
decoder = ClassPlusDecoder()
classplus_client = ClassPlusClient()

@app.route('/')
def index():
    """Main page with API testing interface"""
    return render_template('index.html')

@app.route('/api/decode', methods=['POST'])
@limiter.limit("10 per minute")
def decode_video_url():
    """
    Decode ClassPlus encrypted video URL
    
    Expected JSON payload:
    {
        "token": "classplus_token",
        "encrypted_url": "base64_encoded_url",
        "video_id": "optional_video_id"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Invalid JSON payload",
                "code": "INVALID_JSON"
            }), 400
        
        token = data.get('token')
        encrypted_url = data.get('encrypted_url')
        video_id = data.get('video_id')
        
        # Validate required fields
        if not token:
            return jsonify({
                "error": "Token is required",
                "code": "MISSING_TOKEN"
            }), 400
        
        if not encrypted_url:
            return jsonify({
                "error": "Encrypted URL is required",
                "code": "MISSING_URL"
            }), 400
        
        logger.info(f"Decoding request for video_id: {video_id}")
        
        # Validate token with ClassPlus
        if not classplus_client.validate_token(token):
            return jsonify({
                "error": "Invalid or expired token",
                "code": "INVALID_TOKEN"
            }), 401
        
        # Decode the encrypted URL
        decoded_url = decoder.decode_url(encrypted_url, token)
        
        if not decoded_url:
            return jsonify({
                "error": "Failed to decode URL",
                "code": "DECODE_FAILED"
            }), 400
        
        # Generate playable URL
        playable_url = decoder.generate_playable_url(decoded_url, token)
        
        response_data = {
            "status": "ok",
            "success": True,
            "url": playable_url,
            "decoded_url": decoded_url,
            "video_id": video_id
        }
        
        logger.info(f"Successfully decoded URL for video_id: {video_id}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error decoding video URL: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": str(e) if app.debug else None
        }), 500

@app.route('/api/batch-decode', methods=['POST'])
@limiter.limit("5 per minute")
def batch_decode_urls():
    """
    Batch decode multiple ClassPlus encrypted video URLs
    
    Expected JSON payload:
    {
        "token": "classplus_token",
        "urls": [
            {
                "encrypted_url": "base64_encoded_url",
                "video_id": "optional_video_id"
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Invalid JSON payload",
                "code": "INVALID_JSON"
            }), 400
        
        token = data.get('token')
        urls = data.get('urls', [])
        
        if not token:
            return jsonify({
                "error": "Token is required",
                "code": "MISSING_TOKEN"
            }), 400
        
        if not urls or not isinstance(urls, list):
            return jsonify({
                "error": "URLs array is required",
                "code": "MISSING_URLS"
            }), 400
        
        # Validate token
        if not classplus_client.validate_token(token):
            return jsonify({
                "error": "Invalid or expired token",
                "code": "INVALID_TOKEN"
            }), 401
        
        results = []
        
        for url_data in urls:
            try:
                encrypted_url = url_data.get('encrypted_url')
                video_id = url_data.get('video_id')
                
                if not encrypted_url:
                    results.append({
                        "video_id": video_id,
                        "success": False,
                        "error": "Missing encrypted_url"
                    })
                    continue
                
                decoded_url = decoder.decode_url(encrypted_url, token)
                
                if decoded_url:
                    playable_url = decoder.generate_playable_url(decoded_url, token)
                    results.append({
                        "video_id": video_id,
                        "success": True,
                        "video_url": playable_url,
                        "decoded_url": decoded_url
                    })
                else:
                    results.append({
                        "video_id": video_id,
                        "success": False,
                        "error": "Failed to decode URL"
                    })
                    
            except Exception as e:
                results.append({
                    "video_id": url_data.get('video_id'),
                    "success": False,
                    "error": str(e)
                })
        
        return jsonify({
            "success": True,
            "results": results,
            "total": len(urls),
            "successful": len([r for r in results if r.get('success')]),
            "timestamp": decoder.get_timestamp()
        })
        
    except Exception as e:
        logger.error(f"Error in batch decode: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": str(e) if app.debug else None
        }), 500

@app.route('/api/validate-token', methods=['POST'])
@limiter.limit("20 per minute")
def validate_token():
    """Validate ClassPlus token"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Invalid JSON payload",
                "code": "INVALID_JSON"
            }), 400
        
        token = data.get('token')
        
        if not token:
            return jsonify({
                "error": "Token is required",
                "code": "MISSING_TOKEN"
            }), 400
        
        is_valid = classplus_client.validate_token(token)
        
        if is_valid:
            token_info = classplus_client.get_token_info(token)
            return jsonify({
                "valid": True,
                "token_info": token_info,
                "timestamp": decoder.get_timestamp()
            })
        else:
            return jsonify({
                "valid": False,
                "error": "Invalid or expired token",
                "timestamp": decoder.get_timestamp()
            }), 401
            
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": str(e) if app.debug else None
        }), 500

@app.route('/api', methods=['GET'])
@limiter.limit("20 per minute")
def decode_video_url_simple():
    """
    Simple decode endpoint similar to external API
    
    Expected URL parameters:
    ?url=video_url&token=classplus_token
    """
    try:
        video_url = request.args.get('url')
        token = request.args.get('token')
        
        if not video_url:
            return jsonify({
                "status": "error",
                "success": False,
                "error": "URL parameter is required"
            }), 400
        
        if not token:
            return jsonify({
                "status": "error", 
                "success": False,
                "error": "Token parameter is required"
            }), 400
        
        logger.info(f"Simple decode request for URL: {video_url}")
        
        # Validate token with ClassPlus
        if not classplus_client.validate_token(token):
            return jsonify({
                "status": "error",
                "success": False,
                "error": "Invalid or expired token"
            }), 401
        
        # Generate playable URL directly (URL is already decoded)
        playable_url = decoder.generate_playable_url(video_url, token)
        
        response_data = {
            "status": "ok",
            "success": True,
            "url": playable_url
        }
        
        logger.info(f"Successfully generated authenticated URL")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in simple decode endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "success": False,
            "error": "Internal server error"
        }), 500


@app.route('/api/docs')
def api_docs():
    """API documentation"""
    docs = {
        "title": "ClassPlus Video URL Decoder API",
        "version": "1.0.0",
        "endpoints": {
            "/api/decode": {
                "method": "POST",
                "description": "Decode a single encrypted video URL",
                "payload": {
                    "token": "string (required) - ClassPlus authentication token",
                    "encrypted_url": "string (required) - Base64 encoded video URL",
                    "video_id": "string (optional) - Video identifier"
                },
                "response": {
                    "success": "boolean",
                    "video_url": "string - Playable video URL",
                    "decoded_url": "string - Decoded URL",
                    "video_id": "string",
                    "timestamp": "string"
                }
            },
            "/api/batch-decode": {
                "method": "POST",
                "description": "Decode multiple encrypted video URLs",
                "payload": {
                    "token": "string (required) - ClassPlus authentication token",
                    "urls": "array (required) - Array of URL objects"
                }
            },
            "/api/validate-token": {
                "method": "POST",
                "description": "Validate ClassPlus token",
                "payload": {
                    "token": "string (required) - ClassPlus authentication token"
                }
            }
        },
        "error_codes": {
            "INVALID_JSON": "Request payload is not valid JSON",
            "MISSING_TOKEN": "Authentication token is missing",
            "MISSING_URL": "Encrypted URL is missing",
            "INVALID_TOKEN": "Token is invalid or expired",
            "DECODE_FAILED": "Failed to decode the encrypted URL",
            "INTERNAL_ERROR": "Server internal error"
        }
    }
    
    return jsonify(docs)

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error": "Rate limit exceeded",
        "code": "RATE_LIMIT_EXCEEDED",
        "description": str(e.description)
    }), 429

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "Endpoint not found",
        "code": "NOT_FOUND"
    }), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

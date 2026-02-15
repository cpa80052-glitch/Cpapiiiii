# Overview

ClassPlus Video URL Decoder is a Flask-based web application that provides an API for decoding encrypted ClassPlus video URLs. The application serves as a middleware service that takes base64-encoded video URLs from ClassPlus and converts them into playable video URLs using authentication tokens. It features a web interface for testing API endpoints, rate limiting for security, and caching mechanisms for performance optimization.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Web Framework
- **Flask Application**: Uses Flask as the primary web framework with a modular structure separating API logic from utility functions
- **Template Engine**: Implements Jinja2 templating with a base template system for consistent UI rendering
- **Static Assets**: Uses Bootstrap for styling and Feather Icons for UI elements, with custom CSS overrides

## API Design
- **RESTful Endpoints**: Provides `/api/decode` endpoint for video URL decoding with JSON request/response format
- **Rate Limiting**: Implements Flask-Limiter with tiered limits (200 per day, 50 per hour, 10 per minute for decode endpoint)
- **Error Handling**: Structured error responses with appropriate HTTP status codes

## Security Architecture
- **Authentication Token Validation**: Validates ClassPlus tokens against the official ClassPlus API before processing decode requests
- **Token Caching**: Implements in-memory caching for token validation results with 5-minute TTL to reduce API calls
- **Input Validation**: Validates base64 encoding and URL format before processing

## Core Components
- **ClassPlusDecoder**: Handles base64 decoding of encrypted video URLs and URL validation
- **ClassPlusClient**: Manages API communication with ClassPlus services for token validation
- **Request Processing**: Processes decode requests with token validation, URL decoding, and playable URL generation

## Frontend Architecture
- **Single Page Interface**: Provides a testing interface for API endpoints with real-time response display
- **JavaScript Client**: Implements API client functionality with form handling and response formatting
- **Responsive Design**: Uses Bootstrap for mobile-friendly interface design

# External Dependencies

## Web Framework Stack
- **Flask**: Core web framework for routing and request handling
- **Flask-Limiter**: Rate limiting middleware for API protection

## Frontend Libraries
- **Bootstrap**: UI framework for responsive design and component styling
- **Feather Icons**: Icon library for user interface elements

## Python Libraries
- **requests**: HTTP client for ClassPlus API communication
- **base64**: Built-in library for URL decoding operations
- **hashlib/hmac**: Cryptographic functions for signature generation and validation

## ClassPlus Integration
- **ClassPlus API**: External service for token validation and user authentication
- **API Endpoints**: Integrates with ClassPlus user profile endpoints for token verification

## Configuration Dependencies
- **Environment Variables**: Uses SESSION_SECRET and CLASSPLUS_API_KEY for configuration
- **Logging System**: Python's built-in logging for debugging and monitoring
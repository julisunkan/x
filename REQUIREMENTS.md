# DigitalSkeletonCoin (DSC) Requirements Documentation

## Python Dependencies (Installed via packager_tool)

### Core Framework
- **flask**: Web framework providing HTTP request handling, routing, templating
- **gunicorn**: WSGI HTTP server for production deployment

### Database & ORM
- **flask-sqlalchemy**: SQLAlchemy integration with Flask for database operations
- **sqlalchemy**: Python SQL toolkit and Object-Relational Mapping library
- **psycopg2-binary**: PostgreSQL adapter for Python (production database)

### Authentication & Security
- **flask-login**: User authentication and session management
- **werkzeug**: WSGI utility library (password hashing, security)
- **flask-wtf**: Integration of Flask and WTForms for form handling and CSRF protection
- **wtforms**: Forms validation and rendering library

### Forms & Validation
- **email-validator**: Email address validation for forms

### Internationalization
- **flask-babel**: Internationalization and localization support
- **babel**: Python internationalization library

### Email Services
- **sendgrid**: Email delivery service API client

## System Dependencies

All core system dependencies are managed by the Replit environment and are automatically available:
- Python 3.11+ runtime
- SQLite3 (development database)
- SSL/TLS certificates for HTTPS
- File system permissions for uploads

## Development vs Production

### Development (Current)
- Uses SQLite database (`instance/digitalskeletoncoin.db`)
- Debug mode enabled with hot reload
- File uploads stored locally in `static/uploads/`
- Environment variables managed by Replit

### Production Requirements
- PostgreSQL database (configured via `DATABASE_URL`)
- SendGrid API key for email functionality (`SENDGRID_API_KEY`)
- Session secret key (`SESSION_SECRET`)
- File storage solution (AWS S3, Google Cloud Storage, etc.)
- CDN for static assets
- Load balancer for high availability

## Installation Notes

Dependencies are installed via Replit's packager_tool which automatically:
- Installs Python packages using pip
- Manages virtual environment
- Handles dependency resolution
- Creates necessary configuration files

## Architecture Dependencies

The application follows these architectural patterns:
- **Flask Blueprints**: Modular application structure
- **SQLAlchemy ORM**: Database abstraction layer
- **Jinja2 Templates**: Server-side HTML rendering
- **Bootstrap 5**: Frontend CSS framework
- **Font Awesome**: Icon library
- **Progressive Web App**: Service worker for offline functionality

## Security Dependencies

- **CSRF Protection**: Flask-WTF provides form token validation
- **Password Hashing**: Werkzeug's secure password hashing
- **Session Management**: Flask-Login handles secure user sessions
- **Input Validation**: WTForms validates all user inputs
- **File Upload Security**: Restricted file types and secure filename handling
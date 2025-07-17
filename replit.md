# RoseCoin Mining Platform

## Overview

RoseCoin is a gamified cryptocurrency mining platform built with Flask, featuring tap-to-mine mechanics, social media tasks, referral systems, and airdrops. The platform provides an engaging way for users to earn virtual coins through various activities while building a community around social media engagement.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- **SMTP Email System Implementation (July 17, 2025)**: Completely replaced SendGrid with SMTP-based email system using database configuration. Added connection testing functionality in admin panel with success/error feedback. All emails (verification, password reset) now use SMTP with proper error handling and configuration validation.
- **Admin User Management Enhancement (July 17, 2025)**: Added comprehensive user deletion functionality with cascading deletion of related records (mining sessions, tasks, withdrawals, referrals, airdrops). Added safety checks preventing self-deletion and admin account deletion. Enhanced user management interface with better action buttons and confirmation dialogs.
- **Admin Email Verification & Code Review (July 17, 2025)**: Added admin functionality to manually verify user emails with "Verify Email" button in admin users panel. Completed comprehensive code review fixing duplicate properties in User model, missing function calls in auth.py, and streamlined email sending functions. All components verified working correctly with proper error handling.
- **Replit Agent Migration Completed (July 17, 2025)**: Successfully migrated from Replit Agent to standard Replit environment with proper security configurations. Fixed missing AppSettings import in auth.py that was causing registration internal server errors. All functionality verified working correctly.
- **Dropdown Navigation Implementation (July 2025)**: Converted navigation from horizontal overflow to clean dropdown approach with essential links visible and overflow items in organized dropdown menus.
- **Replit Agent Migration (July 2025)**: Successfully migrated project from Replit Agent to standard Replit environment with proper security configurations and maintenance mode admin access fix.
- **Navigation System Overhaul (July 2025)**: Completely redesigned navigation with proper header, collapsible sidebar, and mobile responsiveness.
- **PWA Implementation**: Added Progressive Web App functionality with service worker, manifest, and mobile app installation capability.
- **Responsive Layout Fix**: Fixed footer visibility issues and implemented proper sidebar collapse functionality for desktop and mobile.
- **Mobile Touch Support**: Added swipe gestures and proper touch navigation for mobile devices.
- **Enhanced User Experience**: Improved header with balance display, user avatar, and smooth animations.
- **UI/UX Improvements (July 2025)**: Enhanced platform with responsive, colorful design and improved user experience.
- **Dynamic Theme System**: Implemented real-time color scheme changes that reflect across the entire platform.
- **Customizable Branding**: Added ability to edit app name "RoseCoin" from admin panel with dynamic template updates.
- **Database Download Fix**: Fixed database export functionality with proper file download handling.
- **Responsive Design**: Improved mobile responsiveness with better card layouts and grid systems.
- **Enhanced Visual Design**: Added gradient backgrounds, circular icons, and modern UI elements.
- **Replit Environment Migration (July 2025)**: Successfully migrated from Replit Agent to standard Replit environment with proper security configurations.
- **Database Configuration**: Fixed SQLite database setup with proper fallback handling for development environment.
- **Admin Panel Routing**: Resolved all admin dashboard routing errors and template compatibility issues.
- **Security Updates**: Implemented proper session secrets and CSRF protection for Replit environment.
- **SQL Compatibility**: Updated database export/import functions for SQLite compatibility with proper error handling.

## System Architecture

The application follows a modular Flask architecture with clear separation of concerns:

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM
- **Database**: SQLite for development (configured for easy PostgreSQL migration)
- **Authentication**: Flask-Login with session management
- **Security**: CSRF protection via Flask-WTF, password hashing with Werkzeug
- **Internationalization**: Flask-Babel for multi-language support (English, Spanish, French, German, Chinese)

### Frontend Architecture
- **Templates**: Jinja2 templating with Bootstrap 5 dark theme
- **Styling**: Custom CSS with CSS variables for theming, responsive design
- **JavaScript**: Vanilla JS with modular class-based architecture
- **UI Components**: Bootstrap components with custom RoseCoin branding

### Database Schema
The application uses SQLAlchemy with a well-structured relational model:
- **Users**: Core user management with gaming stats (balance, XP, level, mining power)
- **Mining**: Session tracking with anti-fraud measures (IP, user agent tracking)
- **Tasks**: Social media task system with proof verification
- **Referrals**: Multi-level referral system with earnings tracking
- **Withdrawals**: Payment processing with admin approval workflow
- **Airdrops**: Event-based coin distribution system

## Key Components

### Core Modules
1. **Authentication System** (`core/auth.py`)
   - User registration/login with CAPTCHA protection
   - Session management and security controls
   - Referral code integration during signup

2. **Mining System** (`core/mining.py`)
   - Tap-based mining with cooldown mechanisms
   - Level progression and mining power scaling
   - Special events and bonuses
   - Daily missions system

3. **Task System** (`core/tasks.py`)
   - Social media task creation and management
   - Proof submission and verification workflow
   - AI-based verification simulation (ready for real AI integration)
   - Platform-specific task types (Twitter, Telegram, YouTube, etc.)

4. **Admin Panel** (`core/admin.py`)
   - User management and moderation
   - Task creation and approval workflow
   - Withdrawal processing
   - Airdrop management
   - Platform settings configuration

### Gaming Features
- **Level System**: XP-based progression affecting mining rewards
- **Daily Missions**: Recurring challenges for engagement
- **Mining Events**: Temporary bonuses and multipliers
- **Referral Rewards**: Commission-based earnings from referred users

### Security Features
- **Anti-fraud**: IP tracking, cooldown systems, session validation
- **CAPTCHA**: Math-based verification for critical actions
- **CSRF Protection**: Form token validation
- **Input Validation**: Comprehensive form validation with WTForms

## Data Flow

### User Registration Flow
1. User submits registration form with optional referral code
2. CAPTCHA verification and form validation
3. Password hashing and user creation
4. Referral relationship establishment (if applicable)
5. Welcome bonus allocation

### Mining Flow
1. User clicks mine button (with anti-spam protection)
2. Server validates mining eligibility (cooldown, session)
3. Coin calculation based on level and active events
4. Balance and XP updates with transaction logging
5. Referral commission distribution (if applicable)

### Task Completion Flow
1. User selects available task and visits external link
2. User submits proof (text description and/or image)
3. AI verification system scores the submission
4. Admin review for final approval (if required)
5. Reward distribution and referral commissions

### Withdrawal Flow
1. User submits withdrawal request with payment details
2. Balance validation and temporary freeze
3. Admin review and verification
4. Payment processing and status updates
5. Transaction completion or rejection handling

## External Dependencies

### Core Dependencies
- **Flask**: Web framework and extensions (Login, WTF, Babel)
- **SQLAlchemy**: Database ORM with relationship management
- **Bootstrap 5**: Frontend framework with dark theme
- **Font Awesome**: Icon library for UI elements

### Planned Integrations
- **AI Verification**: OpenAI GPT for task proof analysis
- **Social Media APIs**: Twitter, Telegram, YouTube for verification
- **Payment Systems**: PayPal, bank transfers, cryptocurrency wallets
- **Image Processing**: Computer vision for image proof verification

### File Upload System
- Secure file handling with extension validation
- Organized storage in uploads directory
- Image optimization ready for implementation

## Deployment Strategy

### Development Setup
- SQLite database for rapid development
- Environment variable configuration
- Debug mode with comprehensive logging
- Hot reload capability

### Production Considerations
- Database migration to PostgreSQL supported
- Environment-based configuration management
- Session secret and security key management
- Proxy handling for reverse proxy deployments
- Connection pooling and optimization configured

### Scalability Features
- Modular blueprint architecture for easy feature addition
- Database relationship optimization
- Caching strategies ready for implementation
- Background task support preparedness

The application is designed for easy deployment on cloud platforms with minimal configuration changes, supporting both development and production environments through environment variable configuration.
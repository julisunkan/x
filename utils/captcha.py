import random
import string
from flask import session

def generate_captcha():
    """Generate a visual text CAPTCHA challenge"""
    # Generate random alphanumeric string (easier to read)
    chars = 'ABCDEFGHIJKLMNPQRSTUVWXYZ23456789'  # Exclude confusing chars like 0, O, 1, I
    captcha_text = ''.join(random.choices(chars, k=5))
    
    # Store answer in session (case-insensitive)
    session['captcha_answer'] = captcha_text.lower()
    
    # Generate SVG image
    svg_captcha = generate_captcha_svg(captcha_text)
    
    return svg_captcha

def verify_captcha(user_answer):
    """Verify CAPTCHA answer"""
    if 'captcha_answer' not in session:
        return False
    
    try:
        correct_answer = session['captcha_answer']
        user_answer = str(user_answer).lower().strip()
        
        # Clear the CAPTCHA from session after verification
        del session['captcha_answer']
        
        return user_answer == correct_answer
    except (ValueError, TypeError):
        return False

def generate_text_captcha():
    """Generate a text-based CAPTCHA"""
    # Generate random string
    chars = string.ascii_uppercase + string.digits
    captcha_text = ''.join(random.choices(chars, k=5))
    
    # Store in session
    session['text_captcha'] = captcha_text.lower()
    
    return captcha_text

def verify_text_captcha(user_input):
    """Verify text CAPTCHA"""
    if 'text_captcha' not in session:
        return False
    
    correct_answer = session['text_captcha']
    user_input = user_input.lower().strip()
    
    # Clear the CAPTCHA from session
    del session['text_captcha']
    
    return user_input == correct_answer

def generate_captcha_svg(text):
    """Generate SVG CAPTCHA image with better visual effects"""
    # Generate random colors and positions for each character
    colors = ['#2c3e50', '#34495e', '#7f8c8d', '#95a5a6', '#16a085', '#27ae60', '#2980b9', '#8e44ad', '#f39c12', '#e74c3c']
    
    svg_parts = []
    svg_parts.append('<svg width="200" height="80" xmlns="http://www.w3.org/2000/svg">')
    
    # Background with gradient
    svg_parts.append('''
    <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#f8f9fa;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#e9ecef;stop-opacity:1" />
        </linearGradient>
        <filter id="shadow">
            <feDropShadow dx="2" dy="2" stdDeviation="2" flood-color="#00000040"/>
        </filter>
    </defs>
    ''')
    
    # Background rectangle
    svg_parts.append('<rect width="200" height="80" fill="url(#bg)" stroke="#dee2e6" stroke-width="2" rx="8"/>')
    
    # Add noise lines
    for i in range(3):
        x1 = random.randint(10, 190)
        y1 = random.randint(10, 70)
        x2 = random.randint(10, 190)
        y2 = random.randint(10, 70)
        color = random.choice(colors)
        svg_parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1" opacity="0.3"/>')
    
    # Add characters with random positioning and rotation
    char_width = 30
    start_x = 25
    
    for i, char in enumerate(text):
        x = start_x + (i * char_width) + random.randint(-5, 5)
        y = 50 + random.randint(-8, 8)
        rotation = random.randint(-15, 15)
        color = random.choice(colors)
        font_size = random.randint(22, 28)
        
        svg_parts.append(f'''
        <text x="{x}" y="{y}" 
              font-family="Arial, sans-serif" 
              font-size="{font_size}" 
              font-weight="bold" 
              fill="{color}" 
              transform="rotate({rotation} {x} {y})"
              filter="url(#shadow)">{char}</text>
        ''')
    
    # Add some noise dots
    for i in range(8):
        cx = random.randint(15, 185)
        cy = random.randint(15, 65)
        r = random.randint(1, 3)
        color = random.choice(colors)
        svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="0.4"/>')
    
    svg_parts.append('</svg>')
    
    return ''.join(svg_parts)

# For development/testing - simple implementation
# In production, consider using libraries like:
# - python-captcha
# - recaptcha
# - hcaptcha

class SimpleCaptcha:
    """Simple CAPTCHA implementation for development"""
    
    @staticmethod
    def generate():
        """Generate a simple CAPTCHA"""
        return generate_captcha()
    
    @staticmethod
    def verify(answer):
        """Verify CAPTCHA answer"""
        return verify_captcha(answer)
    
    @staticmethod
    def generate_image_captcha():
        """Generate image-based CAPTCHA"""
        text = generate_text_captcha()
        svg = get_captcha_svg(text)
        return svg, text
    
    @staticmethod
    def verify_image_captcha(answer):
        """Verify image CAPTCHA"""
        return verify_text_captcha(answer)

# Initialize default CAPTCHA handler
captcha = SimpleCaptcha()

"""
Image processing utilities for automatic compression and optimization
"""

import os
import io
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
import logging

# Configure logging
logger = logging.getLogger(__name__)

def compress_image(image_file, max_size_kb=15, quality_start=85):
    """
    Compress an image to a target file size or smaller
    
    Args:
        image_file: File object or file path
        max_size_kb: Maximum file size in KB (default: 15KB)
        quality_start: Starting JPEG quality (default: 85)
    
    Returns:
        tuple: (compressed_image_bytes, file_extension)
    """
    try:
        # Open and process the image
        if hasattr(image_file, 'read'):
            # It's a file-like object
            image_file.seek(0)
            image = Image.open(image_file)
        else:
            # It's a file path
            image = Image.open(image_file)
        
        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Auto-orient based on EXIF data
        image = ImageOps.exif_transpose(image)
        
        # Calculate max dimensions to keep aspect ratio
        max_width, max_height = 1200, 1200  # Reasonable max dimensions
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Start with high quality and reduce until we meet size requirements
        quality = quality_start
        max_size_bytes = max_size_kb * 1024
        
        while quality > 10:  # Don't go below 10% quality
            # Save to bytes buffer
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            buffer.seek(0)
            
            # Check file size
            size = len(buffer.getvalue())
            
            if size <= max_size_bytes:
                logger.info(f"Image compressed to {size} bytes ({size/1024:.1f}KB) at quality {quality}")
                return buffer.getvalue(), '.jpg'
            
            # Reduce quality and try again
            quality -= 5
        
        # If we still can't meet the size, try reducing dimensions
        while image.size[0] > 200 and image.size[1] > 200:
            # Reduce image dimensions by 10%
            new_width = int(image.size[0] * 0.9)
            new_height = int(image.size[1] * 0.9)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Try with moderate quality
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=70, optimize=True)
            buffer.seek(0)
            
            size = len(buffer.getvalue())
            if size <= max_size_bytes:
                logger.info(f"Image compressed to {size} bytes ({size/1024:.1f}KB) with dimension reduction")
                return buffer.getvalue(), '.jpg'
        
        # Final attempt with minimum settings
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=10, optimize=True)
        buffer.seek(0)
        
        logger.warning(f"Image compressed to {len(buffer.getvalue())} bytes at minimum quality")
        return buffer.getvalue(), '.jpg'
        
    except Exception as e:
        logger.error(f"Error compressing image: {str(e)}")
        raise


def save_compressed_image(image_file, upload_folder, filename_prefix="", max_size_kb=15):
    """
    Save a compressed image to the specified folder
    
    Args:
        image_file: Uploaded file object
        upload_folder: Destination folder path
        filename_prefix: Optional prefix for the filename
        max_size_kb: Maximum file size in KB
    
    Returns:
        str: Saved filename
    """
    try:
        # Ensure upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Get original filename and create secure version
        original_filename = secure_filename(image_file.filename)
        name_part = os.path.splitext(original_filename)[0]
        
        # Compress the image
        compressed_data, extension = compress_image(image_file, max_size_kb)
        
        # Generate final filename
        if filename_prefix:
            final_filename = f"{filename_prefix}_{name_part}{extension}"
        else:
            final_filename = f"{name_part}{extension}"
        
        # Ensure filename is unique
        counter = 1
        base_filename = final_filename
        while os.path.exists(os.path.join(upload_folder, final_filename)):
            name_without_ext = os.path.splitext(base_filename)[0]
            final_filename = f"{name_without_ext}_{counter}{extension}"
            counter += 1
        
        # Save the compressed image
        file_path = os.path.join(upload_folder, final_filename)
        with open(file_path, 'wb') as f:
            f.write(compressed_data)
        
        # Log the result
        file_size = len(compressed_data)
        logger.info(f"Saved compressed image: {final_filename} ({file_size/1024:.1f}KB)")
        
        return final_filename
        
    except Exception as e:
        logger.error(f"Error saving compressed image: {str(e)}")
        raise


def get_image_info(file_path):
    """
    Get information about an image file
    
    Args:
        file_path: Path to the image file
    
    Returns:
        dict: Image information
    """
    try:
        with Image.open(file_path) as img:
            file_size = os.path.getsize(file_path)
            return {
                'size': img.size,
                'mode': img.mode,
                'format': img.format,
                'file_size_bytes': file_size,
                'file_size_kb': file_size / 1024
            }
    except Exception as e:
        logger.error(f"Error getting image info: {str(e)}")
        return None


def validate_image_file(file):
    """
    Validate if uploaded file is a valid image
    
    Args:
        file: Uploaded file object
    
    Returns:
        bool: True if valid image, False otherwise
    """
    if not file or not file.filename:
        return False
    
    # Check file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    file_ext = os.path.splitext(file.filename.lower())[1]
    
    if file_ext not in allowed_extensions:
        return False
    
    # Try to open with PIL to verify it's a valid image
    try:
        file.seek(0)
        with Image.open(file) as img:
            img.verify()
        file.seek(0)  # Reset file pointer
        return True
    except Exception:
        return False
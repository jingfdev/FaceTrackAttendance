/**
 * Camera and Image Processing Utilities
 * For Face Detection Attendance System
 */

class CameraManager {
    constructor() {
        this.stream = null;
        this.video = null;
        this.canvas = null;
        this.context = null;
        this.isStreaming = false;
        
        this.init();
    }
    
    init() {
        // Initialize camera elements if they exist
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        
        if (this.canvas) {
            this.context = this.canvas.getContext('2d');
        }
        
        // Bind event listeners
        this.bindEvents();
    }
    
    bindEvents() {
        // Form submission loading states
        const forms = document.querySelectorAll('form[enctype="multipart/form-data"]');
        forms.forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        });
        
        // File input preview
        const fileInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', this.handleFileSelect.bind(this));
        });
    }
    
    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                } 
            });
            
            if (this.video) {
                this.video.srcObject = this.stream;
                this.video.play();
                this.isStreaming = true;
                
                // Wait for video to load
                return new Promise((resolve) => {
                    this.video.addEventListener('loadedmetadata', () => {
                        resolve();
                    });
                });
            }
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.showAlert('Error accessing camera: ' + error.message, 'error');
            throw error;
        }
    }
    
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            this.isStreaming = false;
        }
        
        if (this.video) {
            this.video.srcObject = null;
        }
    }
    
    capturePhoto() {
        if (!this.video || !this.canvas || !this.context || !this.isStreaming) {
            throw new Error('Camera not initialized or not streaming');
        }
        
        // Set canvas dimensions to match video
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        
        // Draw current video frame to canvas
        this.context.drawImage(this.video, 0, 0);
        
        // Return data URL
        return this.canvas.toDataURL('image/png');
    }
    
    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file type
        if (!file.type.match('image.*')) {
            this.showAlert('Please select a valid image file', 'error');
            event.target.value = '';
            return;
        }
        
        // Validate file size (max 16MB)
        const maxSize = 16 * 1024 * 1024; // 16MB
        if (file.size > maxSize) {
            this.showAlert('File size too large. Please select an image under 16MB', 'error');
            event.target.value = '';
            return;
        }
        
        // Create preview
        this.createImagePreview(file, event.target);
    }
    
    createImagePreview(file, input) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            // Find or create preview container
            let previewContainer = input.parentNode.querySelector('.image-preview');
            if (!previewContainer) {
                previewContainer = document.createElement('div');
                previewContainer.className = 'image-preview mt-3 text-center';
                input.parentNode.appendChild(previewContainer);
            }
            
            // Create preview image
            previewContainer.innerHTML = `
                <img src="${e.target.result}" alt="Preview" 
                     class="img-thumbnail" style="max-width: 300px; max-height: 300px;">
                <div class="mt-2">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        ${file.name} (${this.formatFileSize(file.size)})
                    </small>
                </div>
            `;
        };
        
        reader.readAsDataURL(file);
    }
    
    handleFormSubmit(event) {
        const submitButton = event.target.querySelector('button[type="submit"]');
        if (submitButton) {
            // Add loading state
            submitButton.classList.add('loading');
            submitButton.disabled = true;
            
            // Store original text
            const originalText = submitButton.innerHTML;
            
            // Set loading text
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
            
            // Reset on form completion (timeout fallback)
            setTimeout(() => {
                submitButton.classList.remove('loading');
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            }, 30000); // 30 second timeout
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showAlert(message, type = 'info') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of main container
        const container = document.querySelector('main.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
    
    // Utility method to convert canvas to blob
    canvasToBlob(canvas, callback, type = 'image/png', quality = 0.8) {
        if (canvas.toBlob) {
            canvas.toBlob(callback, type, quality);
        } else {
            // Fallback for older browsers
            const dataURL = canvas.toDataURL(type, quality);
            const byteString = atob(dataURL.split(',')[1]);
            const mimeString = dataURL.split(',')[0].split(':')[1].split(';')[0];
            const ab = new ArrayBuffer(byteString.length);
            const ia = new Uint8Array(ab);
            
            for (let i = 0; i < byteString.length; i++) {
                ia[i] = byteString.charCodeAt(i);
            }
            
            callback(new Blob([ab], { type: mimeString }));
        }
    }
    
    // Method to validate image contains face (client-side basic check)
    async validateImageHasFace(imageElement) {
        // This is a basic client-side check
        // The real validation happens on the server
        
        try {
            // Check if image loaded properly
            if (!imageElement.complete || imageElement.naturalHeight === 0) {
                throw new Error('Image failed to load');
            }
            
            // Basic dimension check
            if (imageElement.naturalWidth < 100 || imageElement.naturalHeight < 100) {
                throw new Error('Image too small for face detection');
            }
            
            return true;
        } catch (error) {
            this.showAlert('Image validation failed: ' + error.message, 'error');
            return false;
        }
    }
}

// Initialize camera manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.cameraManager = new CameraManager();
});

// Additional utility functions
function detectWebCamSupport() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
}

function showCameraNotSupported() {
    const cameraSection = document.getElementById('cameraSection');
    if (cameraSection) {
        cameraSection.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Camera not supported in this browser. Please upload a photo instead.
            </div>
        `;
    }
}

// Check camera support on load
if (!detectWebCamSupport()) {
    document.addEventListener('DOMContentLoaded', showCameraNotSupported);
}

// Export for use in other scripts
window.CameraUtils = {
    CameraManager,
    detectWebCamSupport,
    showCameraNotSupported
};

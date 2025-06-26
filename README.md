

# Face Detection Attendance System

A comprehensive web-based attendance management system that uses computer vision and face detection technology to automatically track student attendance. Built with Flask, OpenCV, and modern web technologies.

## Features

### Core Functionality
- **Student Registration**: Register students with photos and personal information
- **Face Detection**: Automatic face detection using OpenCV Haar Cascade classifiers
- **Real-time Camera Capture**: Use webcam to capture photos for attendance marking
- **Attendance Tracking**: Automatic attendance marking based on face recognition
- **Manual Override**: Manual attendance marking option for backup scenarios

### Dashboard & Analytics
- **Interactive Dashboard**: Overview of student statistics and recent attendance
- **Attendance Records**: Comprehensive view of all attendance records with filtering
- **Real-time Statistics**: Live updates of attendance rates and student counts
- **Export Ready**: Database structure ready for CSV/Excel export functionality

### User Experience
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Theme**: Modern dark-themed interface using Bootstrap
- **Real-time Feedback**: Instant alerts and notifications for user actions
- **Photo Preview**: Live preview of uploaded images before processing

## Technology Stack

### Backend
- **Flask**: Python web framework for the backend API
- **SQLAlchemy**: Database ORM for data management
- **PostgreSQL**: Primary database for production
- **OpenCV**: Computer vision library for face detection
- **Gunicorn**: WSGI HTTP server for production deployment

### Frontend
- **Bootstrap 5**: CSS framework with dark theme
- **JavaScript ES6**: Modern JavaScript for interactive features
- **Font Awesome**: Icon library for UI elements
- **HTML5**: Semantic markup and camera API integration

### Computer Vision
- **Haar Cascade Classifiers**: Pre-trained models for face detection
- **Histogram Comparison**: Face similarity matching algorithm
- **Template Matching**: Additional face comparison method
- **Multi-scale Detection**: Robust face detection at different scales

## Requirements

### System Requirements
- Python 3.11+
- PostgreSQL database
- Webcam (optional, for camera capture)
- Modern web browser with camera support

### Python Dependencies
```
flask==3.1.0
flask-sqlalchemy==3.1.1
opencv-contrib-python==4.11.0.86
opencv-python==4.11.0.86
numpy==2.3.1
pillow==11.2.1
torch==2.7.1+cpu
torchvision==0.22.1+cpu
psycopg2-binary==2.9.10
gunicorn==23.0.0
werkzeug==3.1.3
sqlalchemy==2.0.36
email-validator==2.2.0
```

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/jingfdev/FaceTrackAttendance.git
cd face-detection-attendance
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Configuration
Set up your database connection by configuring environment variables:

```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/attendance_db"
export SESSION_SECRET="your-secret-key-here"
```

For development, you can also use SQLite:
```bash
export DATABASE_URL="sqlite:///attendance.db"
```

### 4. Initialize Database
The application automatically creates database tables on first run. Simply start the application and the schema will be initialized.

### 5. Run the Application

#### Development Mode
```bash
python main.py
```

#### Production Mode
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

The application will be available at `http://localhost:5000`

## Usage Guide

### Student Registration
1. Navigate to **Register Student** from the dashboard
2. Fill in student information (Name, Student ID, Email)
3. Upload a clear photo with the student's face visible
4. The system validates the photo contains a detectable face
5. Click **Register Student** to save

### Marking Attendance
1. Go to **Mark Attendance** from the navigation
2. Choose one of two methods:
   - **Upload Photo**: Select an image file containing the student's face
   - **Camera Capture**: Use the webcam to take a live photo
3. The system automatically detects faces and matches against registered students
4. Attendance is marked if a match is found with sufficient confidence

### Viewing Records
1. Access **Attendance Records** to view all attendance data
2. Use filters to search by:
   - Student name
   - Specific date
   - Detection method (automatic vs manual)
3. View detailed statistics and confidence scores

### Manual Attendance
1. Go to **Students** page to view all registered students
2. Use **Mark Present** button for manual attendance marking
3. Useful as backup when automatic detection fails

## Project Structure

```
face-detection-attendance/
├── app.py                 # Flask application setup and configuration
├── main.py               # Application entry point
├── models.py             # Database models (Student, Attendance)
├── routes.py             # Web routes and API endpoints
├── face_detection.py     # Computer vision and face detection logic
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── templates/           # HTML templates
│   ├── base.html        # Base template with navigation
│   ├── index.html       # Dashboard page
│   ├── register_student.html
│   ├── mark_attendance.html
│   ├── student_list.html
│   └── attendance_records.html
├── static/              # Static assets
│   ├── css/
│   │   └── custom.css   # Custom styling
│   └── js/
│       └── camera.js    # Camera and image handling
└── uploads/             # Student photos and temporary files
```

## Face Detection Algorithm

### Detection Pipeline
1. **Image Preprocessing**: Convert to grayscale, normalize lighting
2. **Multi-scale Detection**: Apply Haar Cascade at different scales
3. **Face Extraction**: Extract face regions from detected areas
4. **Feature Comparison**: Compare using histogram correlation and template matching
5. **Confidence Scoring**: Calculate similarity score (0.0 to 1.0)
6. **Threshold Matching**: Accept matches above 60% confidence

### Technical Details
- **Haar Cascade**: Uses pre-trained frontal face classifier
- **Histogram Comparison**: CV_COMP_CORREL method for color distribution
- **Template Matching**: CV_TM_CCOEFF_NORMED for structural similarity
- **Combined Scoring**: Weighted average (60% histogram + 40% template)

## Security Considerations

### Data Protection
- Student photos stored locally in uploads directory
- Database credentials managed through environment variables
- Session management with secure cookies
- Input validation for all file uploads

### File Upload Security
- Restricted file types (PNG, JPG, JPEG, GIF only)
- Maximum file size limit (16MB)
- Filename sanitization to prevent directory traversal
- Face validation to ensure only valid photos are stored

## Deployment

### Production Deployment
1. Set up PostgreSQL database
2. Configure environment variables:
   ```bash
   DATABASE_URL=postgresql://user:pass@host:port/dbname
   SESSION_SECRET=your-production-secret-key
   ```
3. Install dependencies and run with Gunicorn:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
   ```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
```

## Configuration Options

### Face Detection Settings
Modify `face_detection.py` to adjust:
- Detection confidence threshold (default: 0.6)
- Haar Cascade scale factors
- Minimum face size requirements
- Comparison algorithm weights

### Database Settings
Configure in `app.py`:
- Connection pooling options
- Session timeout settings
- Database engine parameters

## Performance Optimization

### Face Detection Performance
- Multi-scale detection for better accuracy
- Optimized image preprocessing
- Efficient histogram calculations
- Cached face cascade classifiers

### Database Performance
- Indexed queries on frequently accessed fields
- Connection pooling for concurrent users
- Optimized attendance record queries

## Troubleshooting

### Common Issues

**Face Detection Not Working**
- Ensure good lighting in photos
- Use clear, front-facing images
- Check OpenCV installation
- Verify Haar Cascade file path

**Database Connection Errors**
- Verify DATABASE_URL environment variable
- Check PostgreSQL service status
- Ensure database exists and user has permissions

**Camera Access Issues**
- Enable camera permissions in browser
- Check HTTPS requirement for camera API
- Verify camera hardware functionality

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings for functions
- Comment complex algorithms

## License

This project is open source and available under the MIT License.

## Acknowledgments

- OpenCV community for computer vision libraries
- Flask developers for the web framework
- Bootstrap team for the UI framework
- Contributors to the open source ecosystem

## Support

For questions, issues, or contributions:
1. Check the troubleshooting section
2. Search existing issues
3. Create a new issue with detailed description
4. Include system information and error logs

---

**Building under pressure by TAN JINGFONG, Using Flask, OpenCV, and modern web technologies**
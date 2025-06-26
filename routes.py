import os
import cv2
import numpy as np
from datetime import datetime, date, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app import app, db
from models import Student, Attendance
from face_detection import FaceDetector

# Initialize face detector
face_detector = FaceDetector()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Dashboard showing overview of students and recent attendance"""
    total_students = Student.query.count()
    today_attendance = Attendance.query.filter_by(date=date.today()).count()
    recent_attendance = Attendance.query.order_by(Attendance.timestamp.desc()).limit(5).all()
    
    return render_template('index.html', 
                         total_students=total_students,
                         today_attendance=today_attendance,
                         recent_attendance=recent_attendance)

@app.route('/students')
def student_list():
    """Display all registered students"""
    students = Student.query.all()
    return render_template('student_list.html', students=students)

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    """Register a new student with photo upload"""
    if request.method == 'POST':
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        
        if not name or not student_id:
            flash('Name and Student ID are required', 'error')
            return render_template('register_student.html')
        
        # Check if student ID already exists
        existing_student = Student.query.filter_by(student_id=student_id).first()
        if existing_student:
            flash('Student ID already exists', 'error')
            return render_template('register_student.html')
        
        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"{student_id}_{file.filename}")
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(photo_path)
                
                # Validate that the uploaded image contains a face
                try:
                    face_found = face_detector.detect_faces_in_image(photo_path)
                    if not face_found:
                        os.remove(photo_path)  # Remove the uploaded file
                        flash('No face detected in the uploaded image. Please upload a clear photo with a visible face.', 'error')
                        return render_template('register_student.html')
                except Exception as e:
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                    flash(f'Error processing image: {str(e)}', 'error')
                    return render_template('register_student.html')
        
        # Create new student record
        student = Student(
            name=name,
            student_id=student_id,
            email=email,
            photo_path=photo_path
        )
        
        try:
            db.session.add(student)
            db.session.commit()
            flash('Student registered successfully!', 'success')
            return redirect(url_for('student_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error registering student: {str(e)}', 'error')
    
    return render_template('register_student.html')

@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    """Mark attendance using face detection"""
    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No photo uploaded', 'error')
            return render_template('mark_attendance.html')
        
        file = request.files['photo']
        if file.filename == '':
            flash('No photo selected', 'error')
            return render_template('mark_attendance.html')
        
        if file and allowed_file(file.filename):
            # Save uploaded photo temporarily
            filename = secure_filename(f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            
            try:
                # Detect faces in uploaded image
                faces_detected = face_detector.detect_faces_in_image(temp_path)
                
                if not faces_detected:
                    flash('No faces detected in the uploaded image', 'error')
                    os.remove(temp_path)
                    return render_template('mark_attendance.html')
                
                # Get all registered students
                students = Student.query.filter(Student.photo_path.isnot(None)).all()
                matched_students = []
                
                for student in students:
                    if student.photo_path and os.path.exists(student.photo_path):
                        similarity = face_detector.compare_faces(student.photo_path, temp_path)
                        if similarity > 0.6:  # Threshold for face matching
                            matched_students.append({
                                'student': student,
                                'confidence': similarity
                            })
                
                # Clean up temporary file
                os.remove(temp_path)
                
                if matched_students:
                    # Sort by confidence and take the best match
                    matched_students.sort(key=lambda x: x['confidence'], reverse=True)
                    best_match = matched_students[0]
                    student = best_match['student']
                    confidence = best_match['confidence']
                    
                    # Check if attendance already marked today
                    existing_attendance = Attendance.query.filter_by(
                        student_id=student.id,
                        date=date.today()
                    ).first()
                    
                    if existing_attendance:
                        flash(f'Attendance already marked for {student.name} today', 'warning')
                    else:
                        # Mark attendance
                        attendance = Attendance(
                            student_id=student.id,
                            confidence_score=confidence,
                            detection_method='face_detection'
                        )
                        db.session.add(attendance)
                        db.session.commit()
                        flash(f'Attendance marked for {student.name} (Confidence: {confidence:.2%})', 'success')
                else:
                    flash('No matching student found. Please ensure the student is registered with a photo.', 'error')
                    
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                flash(f'Error processing image: {str(e)}', 'error')
        else:
            flash('Invalid file format. Please upload PNG, JPG, JPEG, or GIF files.', 'error')
    
    return render_template('mark_attendance.html')

@app.route('/attendance_records')
def attendance_records():
    """Display attendance records with filtering options"""
    # Get filter parameters
    student_filter = request.args.get('student', '')
    date_filter = request.args.get('date', '')
    
    # Build query
    query = Attendance.query
    
    if student_filter:
        query = query.join(Student).filter(Student.name.contains(student_filter))
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(Attendance.date == filter_date)
        except ValueError:
            flash('Invalid date format', 'error')
    
    # Order by most recent first
    attendance_records = query.order_by(Attendance.timestamp.desc()).all()
    
    # Get all students for filter dropdown
    students = Student.query.all()
    
    return render_template('attendance_records.html', 
                         attendance_records=attendance_records,
                         students=students,
                         student_filter=student_filter,
                         date_filter=date_filter)

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    """Delete a student and their associated records"""
    student = Student.query.get_or_404(student_id)
    
    try:
        # Delete photo file if it exists
        if student.photo_path and os.path.exists(student.photo_path):
            os.remove(student.photo_path)
        
        # Delete student (cascade will handle attendance records)
        db.session.delete(student)
        db.session.commit()
        flash(f'Student {student.name} deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    
    return redirect(url_for('student_list'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/live_recognition')
def live_recognition():
    """Live camera face recognition page"""
    return render_template('live_recognition.html')

@app.route('/api/detect_faces', methods=['POST'])
def api_detect_faces():
    """API endpoint for real-time face detection with bounding boxes"""
    try:
        # Get image data from request
        image_data = request.files.get('image')
        if not image_data:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        # Save temporary image
        temp_filename = f"temp_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        image_data.save(temp_path)
        
        try:
            # Use the enhanced face detection method
            detection_result = face_detector.detect_and_recognize_in_image(temp_path)
            
            # Clean up temporary file
            os.remove(temp_path)
            
            return jsonify(detection_result)
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'success': False, 'error': f'Detection error: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/recognize_face', methods=['POST'])
def api_recognize_face():
    """API endpoint for real-time face recognition"""
    try:
        # Get image data from request
        image_data = request.files.get('image')
        if not image_data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Save temporary image
        temp_filename = f"temp_recognition_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        image_data.save(temp_path)
        
        try:
            # Detect faces in the image
            faces_detected = face_detector.detect_faces_in_image(temp_path)
            
            if not faces_detected:
                os.remove(temp_path)
                return jsonify({'recognized': False, 'message': 'No faces detected'})
            
            # Get all registered students
            students = Student.query.filter(Student.photo_path.isnot(None)).all()
            best_match = None
            best_confidence = 0.0
            
            for student in students:
                if student.photo_path and os.path.exists(student.photo_path):
                    similarity = face_detector.compare_faces(student.photo_path, temp_path)
                    if similarity > best_confidence and similarity > 0.6:  # Minimum threshold
                        best_confidence = similarity
                        best_match = student
            
            # Clean up temporary file
            os.remove(temp_path)
            
            if best_match:
                # Determine check-in or check-out based on last attendance record
                today = date.today()
                last_attendance = Attendance.query.filter_by(
                    student_id=best_match.id,
                    date=today
                ).order_by(Attendance.timestamp.desc()).first()
                
                # Determine status: if last entry was 'in', then this should be 'out', otherwise 'in'
                new_status = 'out' if last_attendance and last_attendance.status == 'in' else 'in'
                
                # Check if already checked in/out in the last 5 minutes to avoid duplicates
                five_minutes_ago = datetime.now() - timedelta(minutes=5)
                recent_attendance = Attendance.query.filter(
                    Attendance.student_id == best_match.id,
                    Attendance.timestamp >= five_minutes_ago,
                    Attendance.status == new_status
                ).first()
                
                response_data = {
                    'recognized': True,
                    'student_name': best_match.name,
                    'student_id': best_match.student_id,
                    'confidence': round(best_confidence * 100, 2),
                    'status': new_status,
                    'already_marked': recent_attendance is not None
                }
                
                if not recent_attendance:
                    # Mark attendance with new status
                    attendance = Attendance(
                        student_id=best_match.id,
                        status=new_status,
                        confidence_score=best_confidence,
                        detection_method='live_recognition'
                    )
                    db.session.add(attendance)
                    db.session.commit()
                    response_data['message'] = f'{best_match.name} checked {new_status}'
                else:
                    response_data['message'] = f'{best_match.name} already checked {new_status} recently'
                
                return jsonify(response_data)
            else:
                return jsonify({
                    'recognized': False, 
                    'message': 'Face detected but no matching student found'
                })
                
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': f'Recognition error: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/manual_attendance/<int:student_id>', methods=['POST'])
def manual_attendance(student_id):
    """Manually mark attendance for a student"""
    student = Student.query.get_or_404(student_id)
    
    # Determine check-in or check-out based on last attendance record
    today = date.today()
    last_attendance = Attendance.query.filter_by(
        student_id=student.id,
        date=today
    ).order_by(Attendance.timestamp.desc()).first()
    
    # Determine status: if last entry was 'in', then this should be 'out', otherwise 'in'
    new_status = 'out' if last_attendance and last_attendance.status == 'in' else 'in'
    
    # Mark attendance manually
    attendance = Attendance(
        student_id=student.id,
        status=new_status,
        detection_method='manual'
    )
    db.session.add(attendance)
    db.session.commit()
    flash(f'{student.name} manually checked {new_status}', 'success')
    
    return redirect(url_for('student_list'))

from flask import Blueprint, render_template, request, redirect, url_for
from .models import Admin, Student
main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        loginType = request.form.get('type')
        email = request.form.get('email').lower()
        password = request.form.get('password')
        if loginType == 'admin':
            print(f"{loginType}, {email}, {password}")
            admin = Admin.query.filter_by(Email = email, Password = password).first()
            if not admin:
                return render_template('login.html', error = 'Invalid email or password')
            return redirect('/admin/dashboard')
        if loginType == 'student':
            student = Student.query.filter_by(Email = email, Password = password).first()
            if not student:
                return render_template('login.html', error = 'Invalid email or password')
            
            return redirect(url_for('student.dashboard',student_id = student.StudentID))
    return render_template('login.html')

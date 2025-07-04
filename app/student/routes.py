from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models import Student, Exam, Attempt, Subject, Chapter, SelectedAnswer, Question
from app import db  
from datetime import datetime,timedelta
from sqlalchemy import func , cast, Date

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        dob = request.form.get('dob')
        clgName = request.form.get('clgName')
        degree = request.form.get('degree')
        password = request.form.get('password')
        confirmPassword = request.form.get('confirmPassword')
        #print(f"{password} {confirmPassword}")
        if password != confirmPassword:
            return render_template('/student/registration.html',
                                   error="Password and Confirm Password should match",
                                   name=name, email=email, dob=dob, clgName=clgName,
                                   degree=degree)

        existing_user = Student.query.filter_by(Email=email).first()
        if existing_user:
            return render_template('/student/registration.html', error="Email already in use",
                                   name=name, dob=dob, clgName=clgName,
                                   degree=degree, password=password, confirmPassword=confirmPassword)
        '''
        last_student = db.session.query(Student).order_by(Student.StudentID.desc()).first()
        if last_student:
            last_student_id = last_student.StudentID
            print(last_student_id)
            lsdob = last_student.DOB
            #print(lsdob)
            lsdob =  lsdob.strftime('%Y-%m-%d')
            print(lsdob)    
            last_number = int(last_student_id[last_student_id.index(str(lsdob).replace('-','')) + 8:])
            student_id = f"{degree}{dob.replace('-',"")}{last_number + 1}"
        else:
            student_id = f"{degree}{dob.replace('-',"")}1"
        '''

        dob = datetime.strptime(dob, "%Y-%m-%d")
        new_student = Student(
            Name=name,
            DOB=dob,
            CollegeName=clgName,
            Degree=degree,
            Email=email.lower(),
            Password=password
        )

        db.session.add(new_student)
        db.session.commit()

        return redirect(url_for('main.login'))

    return render_template('/student/registration.html')


@student_bp.route('/<student_id>/dashboard',methods = ['POST','GET'])
def dashboard(student_id):

    search_query = request.form.get('search_query', '').strip()
    selected_subject = request.form.get('subject')
    selected_chapter = request.form.get('chapter')
    view_past_exam = request.form.get('past')
    filters = []
    filtered_chapter = ""
    filtered_subject = ""
    if Subject.query.get(selected_subject):
        filtered_subject = str(Subject.query.get(selected_subject).SubjectName)
    if Chapter.query.get(selected_chapter):
        filtered_chapter = str(Chapter.query.get(selected_chapter).ChapterName)
    filters = [str(search_query),filtered_subject,filtered_chapter]
    print(filters)

    subjects = Subject.query.all()
    chapters = Chapter.query.all()

    query = Exam.query

    if search_query:
        query = query.filter(Exam.ExamName.ilike(f"%{search_query}%"))
    if selected_subject and selected_subject != "All":
        chapter_ids = [chap.ChapterID for chap in Chapter.query.filter_by(SubjectID=selected_subject).all()]
        query = query.filter(Exam.ChapterID.in_(chapter_ids))
    if selected_chapter and selected_chapter != "All":
        query = query.filter(Exam.ChapterID == selected_chapter)
    if not view_past_exam:
        exams = query.filter(func.date(Exam.ExamDate) >= datetime.now().date()) \
             .order_by(Exam.ExamDate.asc()) \
             .all()
    else:
        exams = query.order_by(Exam.ExamDate.asc()).all()

    return render_template('/student/dashboard.html', exams=exams, subjects=subjects, chapters=chapters, student_id = student_id , filters = filters)

@student_bp.route('/<student_id>/<exam_id>/start', methods=['GET'])
def exam_start(student_id, exam_id):
    student = Student.query.get(student_id)
    exam = Exam.query.get(exam_id)
    if exam.ExamDate.date() < datetime.now().date():
        return render_template('student/exam_details.html', student =  student, exam = exam, student_id=student_id, exam_id=exam_id, passed = True)
    else:
        #attempt_id = f"{student_id}_{exam_id}_{int(datetime.now().timestamp())}"
        session_key = f"exam_{exam_id}_start_time"
        session[session_key] = datetime.now().isoformat()
        
        '''
        last_attempt = Attempt.query.order_by(func.length(Attempt.AttemptID).desc(), Attempt.AttemptID.desc()).first()
        if last_attempt:
            last_attempt_id = last_attempt.AttemptID
            print(str(last_attempt_id))
            new_number = int(last_attempt_id[last_attempt_id.index('AT')+2:]) + 1
            print(new_number)
        else:
            new_number = 1
        attempt_id = str(student_id)+str(exam_id)+"AT" + str(new_number)
        '''
        new_attempt = Attempt(
            StudentID=student_id,
            ExamID=exam_id,
            AttemptDate=datetime.now(),
            Marks=0,
            TotalMarks=exam.TotalMarks
        )
        db.session.add(new_attempt)
        db.session.commit()
        attempt_id = new_attempt.AttemptID 
        all_questions = sorted(
            Question.query.filter_by(ExamID=exam_id).all(),
            key=lambda q: int(q.QuestionID) 
        )

        first_question_id = all_questions[0].QuestionID
        return render_template('student/exam_details.html', student =  student, exam = exam, student_id=student_id, exam_id=exam_id, question_id=first_question_id, attempt_id = attempt_id)
    
@student_bp.route('/<student_id>/<exam_id>/<attempt_id>/<question_id>', methods=['GET', 'POST'])
def exam_question(student_id, exam_id, question_id, attempt_id):
    student = Student.query.get(student_id)
    exam = Exam.query.get(exam_id)
    
    all_questions = sorted(
        Question.query.filter_by(ExamID=exam_id).all(),
        key=lambda q: int(q.QuestionID)  
    )
    current_question = Question.query.get(question_id)  
    
    exam_start_time = session.get(f"exam_{exam_id}_start_time")
    if not exam_start_time:
        return redirect(url_for('student.exam_start', student_id=student_id, exam_id=exam_id))

    exam_start_time = datetime.fromisoformat(exam_start_time)
    total_duration = timedelta(seconds=(exam.TotalDuration * 60))
    time_remaining = total_duration - (datetime.now() - exam_start_time)

    if time_remaining.total_seconds() <= 0:
        return redirect(url_for('student.exam_end', student_id=student_id, exam_id=exam_id, attempt_id=attempt_id))

    if request.method == 'POST':
        selected_option = request.form.get('selected_option')
        selected_answer = SelectedAnswer.query.filter_by(AttemptID=attempt_id, QuestionID=question_id).first()
        if selected_answer:
            selected_answer.SelectedOption = selected_option
        else:
            new_selected = SelectedAnswer(AttemptID=attempt_id, QuestionID=question_id, SelectedOption=selected_option)
            db.session.add(new_selected)
        db.session.commit()

        next_question = None
        for i, q in enumerate(all_questions):
            if str(q.QuestionID) == str(question_id):
                next_question = all_questions[(i + 1) % len(all_questions)].QuestionID
                break

        if 'save_next' in request.form:
            return redirect(url_for('student.exam_question', attempt_id=attempt_id, student_id=student_id, exam_id=exam_id, question_id=next_question))

    selected_answer = SelectedAnswer.query.filter_by(AttemptID=attempt_id, QuestionID=question_id).first()
    selected_option = selected_answer.SelectedOption if selected_answer else None

    return render_template('student/exam_question.html',
                           student=student,
                           exam=exam,
                           question=current_question,
                           all_questions=all_questions,
                           selected_option=selected_option,
                           student_id=student_id,
                           attempt_id=attempt_id,
                           time_left=int(time_remaining.total_seconds()))

@student_bp.route('/<student_id>/<exam_id>/result/<attempt_id>', methods=['GET', 'POST'])
def exam_end(student_id, exam_id, attempt_id):
    student = Student.query.get(student_id)
    exam = Exam.query.get(exam_id)
    questions = Question.query.filter_by(ExamID = exam_id)
    attempt = Attempt.query.get(attempt_id)
    selected_answers = SelectedAnswer.query.filter_by(AttemptID=attempt_id).all()
    selected_questions = [ i.QuestionID for i in selected_answers]
    for question in questions:
        if question.QuestionID not in selected_questions:
            new_selected = SelectedAnswer(AttemptID=attempt_id, 
                                          QuestionID=question.QuestionID, 
                                          SelectedOption=-1)
            db.session.add(new_selected)
            db.session.commit()
    results = []
    selected_answers = SelectedAnswer.query.filter_by(AttemptID=attempt_id).all()
    total_obtained_marks = 0
    for selected in selected_answers:
        question = Question.query.get(selected.QuestionID)
        #obtained_marks = question.Marks if selected.SelectedOption == question.CorrectOption else -question.NegMarks
        if selected.SelectedOption == question.CorrectOption:
            obtained_marks = int(question.Marks)
        elif selected.SelectedOption == -1:
            obtained_marks = 0
        else:
            print("negative")
            obtained_marks = int(question.NegMarks)
        print(obtained_marks)
        total_obtained_marks += obtained_marks
        results.append({
            "question": question.QuestionStatement,
            "correct_option": question.CorrectOption,
            "student_option": selected.SelectedOption if selected.SelectedOption is not -1 else "Not Attempted",
            "obtained_marks": obtained_marks
        })
    
    attempt.Marks = total_obtained_marks
    db.session.commit()
    #print(selected_answers)
    #print("************************\n****************************")
    #print(results)
    return render_template('student/exam_result.html', 
                           exam_name=exam.ExamName, 
                           chapter_name=exam.chapter.ChapterName, 
                           total_marks=exam.TotalMarks, 
                           total_duration=exam.TotalDuration, 
                           student_name=student.Name, 
                           student_id=student.StudentID, 
                           results=results,
                           total_obtained_marks =total_obtained_marks,
                           attempt_id = attempt_id)

@student_bp.route('/<student_id>/scores',methods = ['GET'])
def scores (student_id):
    attempts = Attempt.query.filter_by(StudentID=student_id).all()
    return render_template('student/scores.html',attempts= attempts, student_id = student_id)

@student_bp.route('/<student_id>/summary', methods=['GET'])
def summary(student_id):
    student = Student.query.get(student_id)
    total_attempts = Attempt.query.filter_by(StudentID=student_id).count()

    # Fetch scores over time (Quiz Performance)
    performance_over_time = (
        db.session.query(Attempt.AttemptDate, func.avg(Attempt.Marks))
        .filter(Attempt.StudentID == student_id)
        .group_by(Attempt.AttemptDate)
        .order_by(Attempt.AttemptDate)
        .all()
    )

    dates = [row[0].strftime('%Y-%m-%d') for row in performance_over_time]  # X-axis (Dates)
    scores = [round(row[1], 2) for row in performance_over_time]  # Y-axis (Scores)

    # Fetch average scores per subject (Score Distribution)
    score_distribution = (
        db.session.query(Subject.SubjectName, func.avg(Attempt.Marks))
        .join(Chapter, Chapter.SubjectID == Subject.SubjectID)
        .join(Exam, Exam.ChapterID == Chapter.ChapterID)
        .join(Attempt, Attempt.ExamID == Exam.ExamID)
        .filter(Attempt.StudentID == student_id)
        .group_by(Subject.SubjectID)
        .all()
    )

    subject_labels = [row[0] for row in score_distribution]  # X-axis (Subjects)
    subject_scores = [round(row[1], 2) for row in score_distribution]  # Y-axis (Average Scores)

    return render_template(
        'student/summary.html',
        student=student,
        total_attempts=total_attempts,
        student_id=student_id,
        dates=dates,
        scores=scores,
        subject_labels=subject_labels,
        subject_scores=subject_scores
    )


@student_bp.route('/<student_id>/delete', methods = ['GET','POST'])
def student_delete(student_id):
    student = Student.query.get(student_id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('main.login'))

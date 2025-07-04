from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Subject, Chapter, Exam, Question, Student, Attempt
from datetime import datetime
from sqlalchemy.sql import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard', methods = ['POST','GET'])
def dashboard():
    
    search_query = request.form.get('search_query', '').strip()
    filters = [str(search_query)]
    if search_query:
        query = Subject.query
        query = query.filter(Subject.SubjectName.ilike(f"%{search_query}%"))
        subjects = query.all()
    else:
        subjects = Subject.query.all()
    return render_template('admin/dashboard.html', subjects=subjects, filters=filters)

@admin_bp.route('/subject/new', methods=['POST'])
def subject_add():
    name = request.form.get('name')
    subjectDesc = request.form.get('subjectDesc')
    '''
    last_subject = db.session.query(Subject).order_by(Subject.SubjectID.desc()).first()
    if last_subject:
        last_subject_id = last_subject.SubjectID
        new_number = int(last_subject_id[last_subject_id.index('SUB')+3:]) + 1
    else:
        new_number = 1
    subjectID = "SUB" + str(new_number)
    '''
    

    new_subject = Subject(
        SubjectName=name,
        Description=subjectDesc
    )
    db.session.add(new_subject)
    db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/<subject_id>/edit', methods=['GET', 'POST'])
def subject_edit(subject_id):
    subject = Subject.query.get(subject_id)
    if request.method == 'POST':
        subject.SubjectName = request.form.get('name')
        subject.Description = request.form.get('subjectDesc')
        db.session.commit()
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/subject_edit.html', subject=subject)

@admin_bp.route('/<subject_id>/delete', methods=['POST'])
def subject_delete(subject_id):
    subject = Subject.query.get(subject_id)
    if subject:
        chapters = Chapter.query.filter_by(SubjectID=subject_id).all()
        for chapter in chapters:
            exams = Exam.query.filter_by(ChapterID=chapter.ChapterID).all()
            for exam in exams:
                Attempt.query.filter_by(ExamID=exam.ExamID).delete()
                Question.query.filter_by(ExamID=exam.ExamID).delete()
                db.session.delete(exam)
            db.session.delete(chapter)
        db.session.delete(subject)
        db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/<subject_id>',methods = ['GET','POST'])
def subject_view(subject_id):
    search_query = request.form.get('search_query', '').strip()
    filters = [str(search_query)]
    subject = Subject.query.get(subject_id)
    SubjectName = subject.SubjectName  
    Description = subject.Description  
    
    query = Chapter.query.filter_by(SubjectID=subject_id)
    if search_query:
        query = query.filter(Chapter.ChapterName.ilike(f"%{search_query}%"))
        chapters = query.all()
    else:
        chapters = Chapter.query.filter_by(SubjectID = subject_id)
    return render_template('admin/chapters.html', chapters = chapters, 
                           subject_id = subject_id, 
                           SubjectName = SubjectName, 
                           Description = Description, 
                           filters = filters)

@admin_bp.route('/<subject_id>/chapter/new', methods=['POST'])
def chapter_add(subject_id):
    name = request.form.get('name')
    chapterDesc = request.form.get('chapterDesc')
    '''
    last_chapter = db.session.query(Chapter).filter_by(SubjectID=subject_id).order_by(Chapter.ChapterID.desc()).first()

    if last_chapter:
        last_chapter_id = last_chapter.ChapterID
        new_number = int(last_chapter_id[last_chapter_id.index('CH')+2:]) + 1
    else:
        new_number = 1

    chapterID = subject_id + "CH" + str(new_number)
    '''
    new_chapter = Chapter(
        ChapterName=name,
        Description=chapterDesc,
        SubjectID=subject_id
    )
    db.session.add(new_chapter)
    db.session.commit()
    return redirect(url_for('admin.subject_view', subject_id = subject_id))


@admin_bp.route('/<subject_id>/<chapter_id>/view', methods=['GET'])
def chapter_view(subject_id, chapter_id):
    chapter = Chapter.query.get(chapter_id)
    return render_template('admin/chapter_view.html', chapter=chapter, subject_id = subject_id)

@admin_bp.route('/<subject_id>/<chapter_id>/edit', methods=['GET', 'POST'])
def chapter_edit(subject_id, chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        chapter.ChapterName = request.form.get('name')
        chapter.Description = request.form.get('chapterDesc')
        db.session.commit()
        return redirect(url_for('admin.subject_view',  chapter=chapter, subject_id = subject_id))
    return render_template('admin/chapter_edit.html', chapter=chapter, subject_id = subject_id)

@admin_bp.route('/<subject_id>/<chapter_id>/delete', methods=['POST'])
def chapter_delete(subject_id, chapter_id):
    chapter = Chapter.query.get(chapter_id)
    exams = Exam.query.filter_by(ChapterID = chapter_id).all()
    for exam in exams:
        db.session.delete(exam)
    db.session.delete(chapter)
    db.session.commit()
    return redirect(url_for('admin.subject_view', subject_id = subject_id))


#####QUIZZ

@admin_bp.route('/exam/create', methods=['GET', 'POST'])
def exam_add():
    confirmed = False
    subjects = Subject.query.all()
    selected_subject = None
    chapters = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'confirm':
            confirmed = True
            selected_subject = request.form.get('subject')
            chapters = Chapter.query.filter_by(SubjectID=selected_subject).all()
            return render_template('admin/exam_new.html', subjects=subjects, chapters=chapters, confirmed=confirmed, selected_subject=selected_subject)

        elif action == 'change':
            confirmed = False
            selected_subject = None
            subjects = Subject.query.all()
            return render_template('admin/exam_new.html', subjects=subjects, chapters=[], confirmed=confirmed, selected_subject=selected_subject)

        elif action == 'save':
            if not selected_subject:
                selected_subject = request.form.get('selected_subject')

            exam_name = request.form.get('examName')
            total_duration = request.form.get('totalDuration')
            exam_date = request.form.get('examDate')
            chapter_id = request.form.get('chapter')
            
            if not (chapter_id and exam_name and total_duration and exam_date):
                flash("Please fill in all mandatory fields.")
                if selected_subject:
                    chapters = Chapter.query.filter_by(SubjectID=selected_subject).all() or []
                    confirmed = True
                else:
                    chapters = []
                return render_template('admin/exam_new.html',
                                       subjects=subjects,
                                       chapters=chapters,
                                       confirmed=confirmed,
                                       selected_subject=selected_subject)
            
            
            #last_exam = db.session.query(Exam).order_by(Exam.ExamID.desc()).first()
            #if last_exam:
            #    last_exam_id = last_exam.ExamID
            #    new_number = int(last_exam_id[last_exam_id.index('EX') + 12:]) + 1
            #else:
            #    new_number = 1
            #exam_id = "EX" + str(exam_date) + str(new_number)

            new_exam = Exam(
                ExamName=exam_name,
                TotalDuration=total_duration,
                ExamDate=datetime.strptime(exam_date, '%Y-%m-%d'),
                ChapterID=chapter_id,
                TotalMarks = 0,
                TotalQuestions = 0,
            )
            db.session.add(new_exam)
            db.session.commit()
            exam_id = new_exam.ExamID 
            return redirect(url_for('admin.question_add',exam_id = exam_id))
            
    return render_template('admin/exam_new.html', subjects=subjects, chapters=[], confirmed=confirmed)        


@admin_bp.route('exam/dashboard', methods=['GET','POST'])
def exam_dashboard():
    search_query = request.form.get('search_query', '').strip()
    selected_subject = request.form.get('subject')
    selected_chapter = request.form.get('chapter')
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

    exams = query.order_by(Exam.ExamDate.asc()).all()

    return render_template('admin/exam_dashboard.html', exams=exams, subjects=subjects, chapters=chapters , filters = filters)


@admin_bp.route('/exam/<exam_id>/delete', methods=['POST'])
def exam_delete(exam_id):
    exam = Exam.query.get(exam_id)
    db.session.delete(exam)
    db.session.commit()
    return redirect(url_for('admin.exam_dashboard'))


@admin_bp.route('/exam/<exam_id>/edit', methods=['GET', 'POST'])
def exam_edit(exam_id):
    if request.method=='POST':
        exam = Exam.query.get(exam_id)
        exam_name = request.form.get('examName')
        total_duration = request.form.get('totalDuration')
        exam_date = request.form.get('examDate')
        #chapter_id = request.form.get('chapter')
        exam.ExamName = exam_name
        exam.TotalDuration = total_duration
        exam.ExamDate = datetime.strptime(exam_date, '%Y-%m-%d')
        db.session.commit()

        return redirect(url_for('admin.exam_dashboard'))

    exam = Exam.query.get(exam_id)
    ChapterID = exam.ChapterID
    chapter = Chapter.query.get(ChapterID)
    subject = Subject.query.get(chapter.SubjectID)
    return render_template('admin/exam_new.html',
                                   subjects=[],
                                   chapters=[],
                                   confirmed=True,
                                   selected_subject=subject.SubjectName,
                                   examName = exam.ExamName,
                                   totalDuration = exam.TotalDuration,
                                   examDate = exam.ExamDate.strftime('%Y-%m-%d'),
                                   edit= True,
                                   exam_id = exam_id)


### Questions

@admin_bp.route('/exam/<exam_id>', methods=['GET'])
def exam_view(exam_id):
    exam = Exam.query.get(exam_id)
    questions = Question.query.filter_by(ExamID=exam_id).all()
    return render_template('admin/exam_questions.html', exam=exam, questions=questions)

@admin_bp.route('/exam/<exam_id>/questions', methods = ['GET','POST'])
def question_add(exam_id):
    exam = Exam.query.get(exam_id)
    if request.method == 'POST':
        '''
        lastQuestion = db.session.query(Question).order_by(Question.QuestionID.desc()).first()
        if lastQuestion:
            lastQuestion = lastQuestion.QuestionID
            QuestionID = exam.ExamID + "Q" + str(int(lastQuestion[lastQuestion.index('Q')+1:])+1)
        else:
            QuestionID = exam.ExamID + "Q1"
        ExamID = exam_id'
        '''
        QuestionStatement = request.form.get('questionStatement')
        Option1 = request.form.get('option1')
        Option2 = request.form.get('option2')
        Option3 = request.form.get('option3')
        Option4 = request.form.get('option4')
        CorrectOption = request.form.get('correctOption')
        Marks = int(request.form.get('marks', 0)) if request.form.get('marks') else 0
        NegMarks = int(request.form.get('negMarks', 0)) if request.form.get('negMarks') else 0
        new_question = Question(
            ExamID = exam_id,
            QuestionStatement = QuestionStatement,
            Option1 = Option1,
            Option2 = Option2,
            Option3 = Option3,
            Option4 = Option4,
            CorrectOption =CorrectOption ,
            Marks = Marks,
            NegMarks =NegMarks,
        )
        #print(type(exam.TotalMarks ))
        #print(type(exam.TotalQuestions))
        exam.TotalMarks += Marks
        exam.TotalQuestions += 1
        db.session.add(new_question)
        db.session.commit()
        
        return redirect(url_for('admin.exam_view', exam_id = exam_id))
    subjects = Subject.query.all()
    return redirect(url_for('admin.exam_view',exam_id = exam_id))

@admin_bp.route('/exam/<exam_id>/<question_id>/edit', methods=['POST'])
def question_edit(exam_id, question_id):
    exam = Exam.query.get(exam_id)

    question = Question.query.get(question_id)

    old_marks = question.Marks or 0

    question_statement = request.form.get('questionStatement')
    option1 = request.form.get('option1')
    option2 = request.form.get('option2')
    option3 = request.form.get('option3')
    option4 = request.form.get('option4')
    correct_option = request.form.get('correctOption')
    marks = int(request.form.get('marks', 0)) if request.form.get('marks') else 0
    neg_marks = int(request.form.get('negMarks', 0)) if request.form.get('negMarks') else 0

    question.QuestionStatement = question_statement
    question.Option1 = option1
    question.Option2 = option2
    question.Option3 = option3
    question.Option4 = option4
    question.CorrectOption = correct_option
    question.Marks = marks
    question.NegMarks = neg_marks

    exam.TotalMarks = (exam.TotalMarks or 0) - old_marks + marks

    db.session.commit()

    return redirect(url_for('admin.exam_view', exam_id=exam_id))


@admin_bp.route('/exam/<exam_id>/<question_id>/delete', methods=['POST'])
def question_delete(exam_id, question_id):
    exam = Exam.query.get(exam_id)
    question = Question.query.get(question_id)
    db.session.delete(question)
    exam.TotalQuestions -= 1
    db.session.commit()

    return redirect(url_for('admin.exam_view', exam_id=exam_id))

#Summary
@admin_bp.route('/summary',methods = ['GET'])
def summary():

    quiz_participation = db.session.query(Exam.ExamName, func.count(Attempt.AttemptID)) \
                                   .join(Attempt, Attempt.ExamID == Exam.ExamID) \
                                   .group_by(Exam.ExamID).all()
    
    quiz_labels = [row[0] for row in quiz_participation]  # Exam Names
    quiz_values = [row[1] for row in quiz_participation]  # Attempt Counts

    # Fetch Average Scores Per Subject
    avg_scores = db.session.query(Subject.SubjectName, func.avg(Attempt.Marks)) \
                           .join(Chapter, Chapter.SubjectID == Subject.SubjectID) \
                           .join(Exam, Exam.ChapterID == Chapter.ChapterID) \
                           .join(Attempt, Attempt.ExamID == Exam.ExamID) \
                           .group_by(Subject.SubjectID).all()
    
    subject_labels = [row[0] for row in avg_scores]  # Subject Names
    subject_values = [round(row[1], 2) for row in avg_scores]  # Average Scores

    return render_template('admin/summary.html', 
                           quiz_labels=quiz_labels, 
                           quiz_values=quiz_values, 
                           subject_labels=subject_labels, 
                           subject_values=subject_values)

@admin_bp.route('/user_list', methods=['POST', 'GET'])
def user_list():
    students = Student.query
    degrees = [degree[0] for degree in db.session.query(Student.Degree).distinct().all()]

    search_query_name = request.form.get('search_query_name', '').strip()
    search_query_email = request.form.get('search_query_email', '').strip()
    search_query_college = request.form.get('search_query_college', '').strip()
    selected_degree = request.form.get('degree', '').strip()
    selected_degree = '' if selected_degree == 'All' else selected_degree
    filters = [search_query_name, search_query_email, search_query_college, selected_degree]
    if search_query_name:
        students = students.filter(Student.Name.ilike(f"%{search_query_name}%"))
    if search_query_email:
        students = students.filter(Student.Email.ilike(f"%{search_query_email}%"))
    if search_query_college:
        students = students.filter(Student.CollegeName.ilike(f"%{search_query_college}%"))
    if selected_degree and selected_degree != "All":
        students = students.filter(Student.Degree == selected_degree)
    students = students.all()
    student_attempts = {student.StudentID: Attempt.query.filter_by(StudentID=student.StudentID).count() for student in students}
    

    return render_template('admin/user_list.html', students=students, student_attempts=student_attempts, degrees=degrees, filters=filters)


@admin_bp.route('/summary/student/<student_id>/delete', methods = ['GET','POST'])
def student_delete(student_id):
    #print(attempt_id)
    student = Student.query.get(student_id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/summary/attempt', methods = ['GET'])
def exam_attempts():
    attempts = Attempt.query.all()
    return render_template('admin/attempt_list.html',attempts=attempts)

@admin_bp.route('/summary/attempt/<attempt_id>/delete', methods = ['GET','POST'])
def attempt_delete(attempt_id):
    #print(attempt_id)
    attempt = Attempt.query.get(attempt_id)
    db.session.delete(attempt)
    db.session.commit()
    return redirect(url_for('admin.exam_attempts'))

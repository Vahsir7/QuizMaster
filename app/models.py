from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Question(db.Model):
    QuestionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ExamID = db.Column(db.Integer, db.ForeignKey('exam.ExamID', ondelete="CASCADE"), nullable=False)
    QuestionStatement = db.Column(db.String(255), nullable=False)
    Option1 = db.Column(db.String(255), nullable=False)
    Option2 = db.Column(db.String(255), nullable=False)
    Option3 = db.Column(db.String(255), nullable=True)
    Option4 = db.Column(db.String(255), nullable=True)
    CorrectOption = db.Column(db.Integer, nullable=False)
    Marks = db.Column(db.Integer, nullable=False)
    NegMarks = db.Column(db.Integer, nullable=True, default=0) 

class Exam(db.Model):
    ExamID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ExamName = db.Column(db.String(100), nullable=False)
    TotalMarks = db.Column(db.Integer, nullable=False)
    TotalQuestions = db.Column(db.Integer, nullable=False)
    TotalDuration = db.Column(db.Integer, nullable=False)
    ExamDate = db.Column(db.DateTime, nullable=False)
    ChapterID = db.Column(db.Integer, db.ForeignKey('chapter.ChapterID', ondelete="CASCADE"), nullable=False)
    
    questions = db.relationship('Question', backref='exam', lazy=True, cascade="all, delete-orphan")
    attempts = db.relationship('Attempt', backref='exam', lazy=True, cascade="all, delete-orphan")
    chapter = db.relationship('Chapter', backref='exams', lazy=True) 

class Attempt(db.Model):
    AttemptID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    StudentID = db.Column(db.Integer, db.ForeignKey('student.StudentID', ondelete="CASCADE"), nullable=False)
    ExamID = db.Column(db.Integer, db.ForeignKey('exam.ExamID', ondelete="CASCADE"), nullable=False)
    AttemptDate = db.Column(db.DateTime, nullable=False)
    Marks = db.Column(db.Integer, nullable=False)
    TotalMarks = db.Column(db.Integer, nullable=False)
    SelectedAnswers = db.relationship('SelectedAnswer', backref='attempt', lazy=True, cascade="all, delete-orphan")

class SelectedAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    AttemptID = db.Column(db.Integer, db.ForeignKey('attempt.AttemptID', ondelete="CASCADE"), nullable=False)
    QuestionID = db.Column(db.Integer, db.ForeignKey('question.QuestionID', ondelete="CASCADE"), nullable=False)
    SelectedOption = db.Column(db.Integer, nullable=True, default=-1) 

class Student(db.Model):
    StudentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    DOB = db.Column(db.DateTime, nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Password = db.Column(db.String(100), nullable=False)
    CollegeName = db.Column(db.String(255), nullable=True)
    Degree = db.Column(db.String(10), nullable=False)
    attempts = db.relationship('Attempt', backref='student', lazy=True, cascade="all, delete-orphan")

class Admin(db.Model):
    AdminID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Password = db.Column(db.String(100), nullable=False)

class Subject(db.Model):
    SubjectID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SubjectName = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.String(255), nullable=True, default="Null")
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade="all, delete-orphan")

class Chapter(db.Model):
    ChapterID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SubjectID = db.Column(db.Integer, db.ForeignKey('subject.SubjectID', ondelete="CASCADE"), nullable=False)
    ChapterName = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.String(255), nullable=True, default="Null")

from django.db import models
from django.contrib.auth.models import User
import random
import string


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('lecturer', 'Lecturer'),
        ('student', 'Student'),
    ]
    FONT_SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('xlarge', 'Extra Large'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    university = models.CharField(max_length=200, blank=True, default='')
    department = models.CharField(max_length=200, blank=True, default='')
    preferred_mode = models.CharField(max_length=20, blank=True, default='caption', choices=[
        ('caption', 'Smart Captions'),
        ('audio', 'Audio Description'),
        ('sign', 'Sign Language'),
    ])
    font_size = models.CharField(max_length=10, choices=FONT_SIZE_CHOICES, default='medium')
    high_contrast = models.BooleanField(default=False)
    dyslexia_font = models.BooleanField(default=False)
    caption_language = models.CharField(max_length=10, default='en-US', blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class LectureSession(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('live', 'Live'),
        ('ended', 'Ended'),
    ]
    SESSION_TYPE_CHOICES = [
        ('lecture', 'Lecture'),
        ('personal', 'Personal'),
    ]
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=200)
    course_code = models.CharField(max_length=50, blank=True)
    session_code = models.CharField(max_length=6, unique=True, editable=False)
    session_type = models.CharField(max_length=10, choices=SESSION_TYPE_CHOICES, default='lecture')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_active(self):
        return self.status in ('waiting', 'live')

    def save(self, *args, **kwargs):
        if not self.session_code:
            self.session_code = self._generate_code()
        super().save(*args, **kwargs)

    def _generate_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not LectureSession.objects.filter(session_code=code).exists():
                return code

    def __str__(self):
        return f"{self.title} ({self.session_code})"


class TranscriptSegment(models.Model):
    session = models.ForeignKey(LectureSession, on_delete=models.CASCADE, related_name='segments')
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    seconds_from_start = models.FloatField(default=0)
    has_technical_terms = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.text[:50]}..."


class SessionSlide(models.Model):
    session = models.ForeignKey(LectureSession, on_delete=models.CASCADE, related_name='slides')
    slide_number = models.PositiveIntegerField()
    image = models.ImageField(upload_to='slides/')
    ai_description = models.TextField(blank=True, default='')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['slide_number']
        unique_together = ['session', 'slide_number']

    def __str__(self):
        return f"Slide {self.slide_number} — {self.session.title}"


class GlossaryTerm(models.Model):
    term = models.CharField(max_length=100, unique=True)
    definition = models.TextField()
    subject_area = models.CharField(max_length=100, blank=True, default='General')
    sign_description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['term']

    def __str__(self):
        return self.term


class SessionAttendance(models.Model):
    session = models.ForeignKey(LectureSession, on_delete=models.CASCADE, related_name='attendees')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    mode = models.CharField(max_length=20, choices=[
        ('caption', 'Smart Captions'),
        ('audio', 'Audio Description'),
        ('sign', 'Sign Language'),
    ])
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['session', 'student']


class LectureSummary(models.Model):
    """AI-generated lecture summary and key points."""
    session = models.OneToOneField(LectureSession, on_delete=models.CASCADE, related_name='summary')
    summary_text = models.TextField()
    key_points = models.JSONField(default=list)
    keywords = models.JSONField(default=list)
    detected_terms = models.JSONField(default=list)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Summary — {self.session.title}"


class QuizQuestion(models.Model):
    """Auto-generated quiz question from lecture content."""
    QUESTION_TYPES = [
        ('fill_blank', 'Fill in the Blank'),
        ('definition', 'Definition Match'),
        ('true_false', 'True or False'),
    ]
    session = models.ForeignKey(LectureSession, on_delete=models.CASCADE, related_name='quiz_questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    correct_answer = models.TextField()
    hint = models.TextField(blank=True, default='')
    explanation = models.TextField(blank=True, default='')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:60]}..."


class StudentNote(models.Model):
    """Student personal notes taken during a live session."""
    session = models.ForeignKey(LectureSession, on_delete=models.CASCADE, related_name='notes')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_notes')
    text = models.TextField()
    timestamp_seconds = models.FloatField(default=0, help_text='Seconds from session start when note was taken')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp_seconds']

    def __str__(self):
        return f"Note by {self.student.username} at {self.timestamp_seconds:.0f}s"


class LectureAnalytics(models.Model):
    """AI-computed analytics for a lecture session."""
    session = models.OneToOneField(LectureSession, on_delete=models.CASCADE, related_name='analytics')
    total_words = models.IntegerField(default=0)
    total_sentences = models.IntegerField(default=0)
    unique_words = models.IntegerField(default=0)
    avg_wpm = models.FloatField(default=0)
    complexity_score = models.FloatField(default=0)
    complexity_label = models.CharField(max_length=20, default='')
    reading_ease = models.FloatField(default=0)
    grade_level = models.FloatField(default=0)
    topic_segments = models.JSONField(default=list)
    wpm_timeline = models.JSONField(default=list)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics — {self.session.title}"

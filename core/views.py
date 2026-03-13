from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from .models import (
    UserProfile, LectureSession, SessionAttendance,
    TranscriptSegment, GlossaryTerm, SessionSlide,
    LectureSummary, QuizQuestion, LectureAnalytics, StudentNote,
)
from .forms import RegisterForm, LectureSessionForm, JoinSessionForm, AccessibilityForm
from . import ai_services


def home(request):
    return render(request, 'core/home.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role=form.cleaned_data['role'])
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


@login_required
def dashboard(request):
    profile = request.user.profile
    if profile.role == 'lecturer':
        sessions = LectureSession.objects.filter(lecturer=request.user).order_by('-created_at')
        for s in sessions:
            s.attendee_count = s.attendees.count()
            s.segment_count = s.segments.count()
            if s.started_at and s.ended_at:
                delta = s.ended_at - s.started_at
                s.duration_minutes = int(delta.total_seconds() // 60)
            else:
                s.duration_minutes = None
        return render(request, 'core/lecturer_dashboard.html', {'sessions': sessions})
    else:
        attendances = SessionAttendance.objects.filter(student=request.user).select_related('session').order_by('-joined_at')
        hosted_sessions = LectureSession.objects.filter(
            lecturer=request.user, session_type='personal'
        ).order_by('-created_at')
        for s in hosted_sessions:
            s.attendee_count = s.attendees.count()
            s.segment_count = s.segments.count()
            if s.started_at and s.ended_at:
                delta = s.ended_at - s.started_at
                s.duration_minutes = int(delta.total_seconds() // 60)
            else:
                s.duration_minutes = None
        return render(request, 'core/student_dashboard.html', {
            'attendances': attendances,
            'hosted_sessions': hosted_sessions,
        })


@login_required
def create_session(request):
    if request.method == 'POST':
        form = LectureSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.lecturer = request.user
            session.save()
            return redirect('lecturer_session', session_code=session.session_code)
    else:
        form = LectureSessionForm()
    return render(request, 'core/create_session.html', {'form': form})


@login_required
def start_personal_session(request):
    if request.method == 'POST':
        now = timezone.now()
        session = LectureSession.objects.create(
            lecturer=request.user,
            title=f"Personal Session — {now.strftime('%b %d, %H:%M')}",
            session_type='personal',
        )
        return redirect('lecturer_session', session_code=session.session_code)
    return redirect('dashboard')


@login_required
def lecturer_session(request, session_code):
    session = get_object_or_404(LectureSession, session_code=session_code, lecturer=request.user)
    if session.session_type == 'personal':
        return render(request, 'core/personal_session.html', {'session': session})
    attendees = SessionAttendance.objects.filter(session=session)
    slides = SessionSlide.objects.filter(session=session).order_by('slide_number')
    return render(request, 'core/lecturer_session.html', {
        'session': session,
        'attendees': attendees,
        'slides': slides,
    })


@login_required
def end_session(request, session_code):
    session = get_object_or_404(LectureSession, session_code=session_code, lecturer=request.user)
    session.status = 'ended'
    session.ended_at = timezone.now()
    session.save()
    return redirect('dashboard')


@login_required
def join_session(request):
    if request.method == 'POST':
        form = JoinSessionForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['session_code'].upper()
            mode = form.cleaned_data['mode']
            try:
                session = LectureSession.objects.get(session_code=code, status__in=['waiting', 'live'])
            except LectureSession.DoesNotExist:
                messages.error(request, 'Session not found or has ended.')
                return render(request, 'core/join_session.html', {'form': form})

            SessionAttendance.objects.update_or_create(
                session=session, student=request.user,
                defaults={'mode': mode, 'left_at': None},
            )
            return redirect('student_session', session_code=code, mode=mode)
    else:
        # Pre-select user's saved preferred mode
        initial = {}
        if hasattr(request.user, 'profile') and request.user.profile.preferred_mode:
            initial['mode'] = request.user.profile.preferred_mode
        form = JoinSessionForm(initial=initial)
    return render(request, 'core/join_session.html', {'form': form})


@login_required
def student_session(request, session_code, mode):
    session = get_object_or_404(LectureSession, session_code=session_code)
    if session.status == 'ended':
        return redirect('session_transcript', session_code=session_code)
    slides = SessionSlide.objects.filter(session=session).order_by('slide_number')
    return render(request, 'core/student_session.html', {
        'session': session,
        'mode': mode,
        'slides': slides,
    })


@login_required
def session_transcript(request, session_code):
    session = get_object_or_404(LectureSession, session_code=session_code)
    segments = session.segments.all()
    attendees = session.attendees.all()
    mode_counts = attendees.values('mode').annotate(count=Count('id'))
    mode_dict = {m['mode']: m['count'] for m in mode_counts}

    duration = None
    if session.started_at and session.ended_at:
        delta = session.ended_at - session.started_at
        duration = int(delta.total_seconds() // 60)

    return render(request, 'core/session_transcript.html', {
        'session': session,
        'segments': segments,
        'attendees': attendees,
        'mode_counts': mode_dict,
        'duration': duration,
    })


@login_required
def download_transcript(request, session_code):
    session = get_object_or_404(LectureSession, session_code=session_code)
    segments = session.segments.all()

    lines = [
        f"SIKIKA — Transcript",
        f"Session: {session.title}",
        f"Course: {session.course_code}",
        f"Code: {session.session_code}",
        f"Date: {session.created_at.strftime('%B %d, %Y %H:%M')}",
        "",
        "=" * 60,
        "",
    ]

    for seg in segments:
        mins = int(seg.seconds_from_start // 60)
        secs = int(seg.seconds_from_start % 60)
        lines.append(f"[{mins:02d}:{secs:02d}]  {seg.text}")

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"Total segments: {segments.count()}")

    content = "\n".join(lines)
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="transcript_{session_code}.txt"'
    return response


@login_required
def upload_slides(request, session_code):
    session = get_object_or_404(LectureSession, session_code=session_code, lecturer=request.user)

    if request.method == 'POST':
        files = request.FILES.getlist('slides')
        existing_count = SessionSlide.objects.filter(session=session).count()

        for i, f in enumerate(files):
            if not f.content_type.startswith('image/'):
                continue
            slide = SessionSlide.objects.create(
                session=session,
                slide_number=existing_count + i + 1,
                image=f,
            )
            # Auto-generate AI description for blind students
            if slide.image:
                slide.ai_description = ai_services.generate_slide_description(slide.image.path)
                slide.save()
        messages.success(request, f'{len(files)} slide(s) uploaded with AI descriptions.')
        return redirect('lecturer_session', session_code=session_code)

    return redirect('lecturer_session', session_code=session_code)


@login_required
def glossary_api(request):
    terms = GlossaryTerm.objects.all().values('term', 'definition', 'subject_area', 'sign_description')
    return JsonResponse(list(terms), safe=False)


@login_required
def accessibility_settings(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = AccessibilityForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Accessibility settings saved.')
            return redirect('dashboard')
    else:
        form = AccessibilityForm(instance=profile)
    return render(request, 'core/accessibility_settings.html', {'form': form})


# ─── AI-POWERED VIEWS ────────────────────────────────────────────

def _get_glossary_dict():
    """Helper: get glossary as {term_lower: definition} dict."""
    return {
        t.term.lower(): t.definition
        for t in GlossaryTerm.objects.all()
    }


def _run_analysis(session):
    """
    Run full AI analysis on a session and save results to DB.
    Returns the analysis dict.
    """
    segments = session.segments.all()
    glossary_dict = _get_glossary_dict()
    result = ai_services.analyze_session(segments, glossary_dict)

    # Save/update LectureSummary
    LectureSummary.objects.update_or_create(
        session=session,
        defaults={
            'summary_text': result['summary'],
            'key_points': result['key_points'],
            'keywords': result['keywords'],
            'detected_terms': result['detected_terms'],
        }
    )

    # Save/update LectureAnalytics
    stats = result['stats']
    LectureAnalytics.objects.update_or_create(
        session=session,
        defaults={
            'total_words': stats.get('total_words', 0),
            'total_sentences': stats.get('total_sentences', 0),
            'unique_words': stats.get('unique_words', 0),
            'avg_wpm': stats.get('avg_wpm', 0),
            'complexity_score': stats.get('complexity', 0),
            'complexity_label': stats.get('complexity_label', ''),
            'reading_ease': stats.get('reading_ease', 0),
            'grade_level': stats.get('grade_level', 0),
            'topic_segments': result['topics'],
            'wpm_timeline': result['wpm_timeline'],
        }
    )

    # Save quiz questions (replace old ones)
    QuizQuestion.objects.filter(session=session).delete()
    for q in result['quiz']:
        QuizQuestion.objects.create(
            session=session,
            question_type=q['type'],
            question_text=q.get('question', ''),
            correct_answer=str(q.get('answer', '')),
            hint=q.get('hint', ''),
            explanation=q.get('explanation', ''),
            order=q.get('id', 0),
        )

    return result


@login_required
def analyze_session_view(request, session_code):
    """Trigger AI analysis and redirect to summary page."""
    session = get_object_or_404(LectureSession, session_code=session_code)
    _run_analysis(session)
    messages.success(request, 'AI analysis complete!')
    return redirect('session_summary', session_code=session_code)


@login_required
def session_summary(request, session_code):
    """AI-generated summary with key points and keywords."""
    session = get_object_or_404(LectureSession, session_code=session_code)

    # Auto-generate if not exists
    try:
        summary = session.summary
    except LectureSummary.DoesNotExist:
        _run_analysis(session)
        summary = getattr(session, 'summary', None)

    try:
        analytics = session.analytics
    except LectureAnalytics.DoesNotExist:
        analytics = None

    segments = session.segments.all()

    return render(request, 'core/session_summary.html', {
        'session': session,
        'summary': summary,
        'analytics': analytics,
        'segment_count': segments.count(),
    })


@login_required
def session_quiz(request, session_code):
    """Auto-generated quiz from lecture content."""
    session = get_object_or_404(LectureSession, session_code=session_code)
    questions = QuizQuestion.objects.filter(session=session).order_by('order')

    # Auto-generate if no questions exist
    if not questions.exists():
        _run_analysis(session)
        questions = QuizQuestion.objects.filter(session=session).order_by('order')

    return render(request, 'core/session_quiz.html', {
        'session': session,
        'questions': questions,
    })


@login_required
def session_analytics(request, session_code):
    """Detailed AI analytics with charts."""
    session = get_object_or_404(LectureSession, session_code=session_code)

    try:
        analytics = session.analytics
    except LectureAnalytics.DoesNotExist:
        _run_analysis(session)
        analytics = getattr(session, 'analytics', None)

    try:
        summary = session.summary
    except LectureSummary.DoesNotExist:
        summary = None

    attendees = session.attendees.all()
    mode_counts = attendees.values('mode').annotate(count=Count('id'))
    mode_dict = {m['mode']: m['count'] for m in mode_counts}

    duration = None
    if session.started_at and session.ended_at:
        delta = session.ended_at - session.started_at
        duration = int(delta.total_seconds() // 60)

    return render(request, 'core/session_analytics.html', {
        'session': session,
        'analytics': analytics,
        'summary': summary,
        'mode_counts': mode_dict,
        'duration': duration,
        'attendee_count': attendees.count(),
    })


@login_required
def quiz_api(request, session_code):
    """JSON API for quiz data (used by interactive quiz JS)."""
    session = get_object_or_404(LectureSession, session_code=session_code)
    questions = QuizQuestion.objects.filter(session=session).order_by('order')

    data = []
    for q in questions:
        data.append({
            'id': q.order,
            'type': q.question_type,
            'question': q.question_text,
            'answer': q.correct_answer,
            'hint': q.hint,
            'explanation': q.explanation,
        })
    return JsonResponse(data, safe=False)


# ─── SESSION REPLAY VIEW ─────────────────────────────────────────

@login_required
def session_replay(request, session_code):
    """Post-session replay with timed transcript playback."""
    session = get_object_or_404(LectureSession, session_code=session_code)
    segments = session.segments.all()
    slides = SessionSlide.objects.filter(session=session).order_by('slide_number')

    # Get user's notes if student
    notes = []
    if hasattr(request.user, 'profile') and request.user.profile.role == 'student':
        notes = StudentNote.objects.filter(session=session, student=request.user)

    # Try to get summary
    try:
        summary = session.summary
    except LectureSummary.DoesNotExist:
        summary = None

    duration = 0
    if session.started_at and session.ended_at:
        duration = int((session.ended_at - session.started_at).total_seconds())

    # Fallback: compute duration from last segment if session wasn't properly ended
    if duration == 0 and segments.exists():
        last_seg = segments.order_by('-seconds_from_start').first()
        if last_seg:
            duration = int(last_seg.seconds_from_start) + 10

    # Build timeline data as JSON for JS playback
    import json
    timeline = []
    for seg in segments:
        timeline.append({
            'time': round(seg.seconds_from_start, 1),
            'text': seg.text,
            'has_terms': seg.has_technical_terms,
        })

    return render(request, 'core/session_replay.html', {
        'session': session,
        'segments': segments,
        'slides': slides,
        'notes': notes,
        'summary': summary,
        'duration': duration,
        'timeline_json': json.dumps(timeline),
    })


# ─── STUDENT NOTES API ───────────────────────────────────────────

@login_required
def notes_api(request, session_code):
    """Create and list student notes for a session."""
    session = get_object_or_404(LectureSession, session_code=session_code)

    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        text = data.get('text', '').strip()
        if not text:
            return JsonResponse({'error': 'Empty note'}, status=400)
        timestamp = data.get('timestamp_seconds', 0)
        note = StudentNote.objects.create(
            session=session,
            student=request.user,
            text=text,
            timestamp_seconds=timestamp,
        )
        return JsonResponse({
            'id': note.id,
            'text': note.text,
            'timestamp_seconds': note.timestamp_seconds,
            'created_at': note.created_at.strftime('%H:%M'),
        })
    else:
        notes = StudentNote.objects.filter(session=session, student=request.user)
        data = [{
            'id': n.id,
            'text': n.text,
            'timestamp_seconds': n.timestamp_seconds,
            'created_at': n.created_at.strftime('%H:%M'),
        } for n in notes]
        return JsonResponse(data, safe=False)


@login_required
def delete_note_api(request, note_id):
    """Delete a student note."""
    if request.method == 'POST':
        note = get_object_or_404(StudentNote, id=note_id, student=request.user)
        note.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'POST required'}, status=405)

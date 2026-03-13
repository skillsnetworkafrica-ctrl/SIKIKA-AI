import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import LectureSession, TranscriptSegment, SessionAttendance, GlossaryTerm
from .ai_services import detect_technical_terms, complexity_score, complexity_label, tokenize_words, detect_emphasis, generate_live_summary, detect_complex_phrases
from django.utils import timezone


class LectureConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_code = self.scope['url_route']['kwargs']['session_code']
        self.room_group_name = f'lecture_{self.session_code}'
        self.user = self.scope.get('user')
        self.cumulative_words = 0
        self.session_start_time = None
        self.all_segments_text = []  # Store for mid-session summary

        session_exists = await self.check_session_exists()
        if not session_exists:
            await self.close()
            return

        # Load glossary terms once for real-time detection
        self.glossary_terms = await self.load_glossary_terms()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Reset left_at for reconnecting students
        if self.user and self.user.is_authenticated:
            await self.mark_student_rejoined()

        # Broadcast updated attendee count
        counts = await self.get_attendee_counts()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'attendee_update',
                'total': counts['total'],
                'caption': counts['caption'],
                'audio': counts['audio'],
                'sign': counts['sign'],
            }
        )

    async def disconnect(self, close_code):
        # Mark left_at for the student
        if self.user and self.user.is_authenticated:
            await self.mark_student_left()

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Broadcast updated attendee count after disconnect
        try:
            counts = await self.get_attendee_counts()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'attendee_update',
                    'total': counts['total'],
                    'caption': counts['caption'],
                    'audio': counts['audio'],
                    'sign': counts['sign'],
                }
            )
        except Exception:
            pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid JSON'}))
            return
        msg_type = data.get('type', '')

        if msg_type == 'transcript':
            text = data.get('text', '')
            is_final = data.get('is_final', False)

            if is_final and text.strip():
                # AI: Detect technical terms in this segment
                detected = detect_technical_terms(text, self.glossary_terms)
                has_terms = len(detected) > 0

                # AI: Detect emphasis/importance markers
                emphasis = detect_emphasis(text)

                # AI: Detect complex academic phrases
                complex_phrases = detect_complex_phrases(text)

                # AI: Track cumulative WPM
                words = tokenize_words(text)
                self.cumulative_words += len(words)
                wpm = 0
                if self.session_start_time:
                    elapsed = (timezone.now() - self.session_start_time).total_seconds()
                    if elapsed > 0:
                        wpm = round((self.cumulative_words / elapsed) * 60, 1)

                # AI: Compute segment complexity
                seg_complexity = complexity_score(text)
                seg_label = complexity_label(seg_complexity)

                # Store for mid-session summaries
                self.all_segments_text.append(text)

                await self.save_segment(text, has_terms)

                # Send enriched transcript with AI data
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_transcript',
                        'text': text,
                        'is_final': True,
                        'detected_terms': detected,
                        'complexity': seg_complexity,
                        'complexity_label': seg_label,
                        'wpm': wpm,
                        'emphasis': emphasis,
                        'complex_phrases': complex_phrases,
                    }
                )
            else:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_transcript',
                        'text': text,
                        'is_final': False,
                        'detected_terms': [],
                        'complexity': 0,
                        'complexity_label': '',
                        'wpm': 0,
                    }
                )

        elif msg_type == 'slide_change':
            slide_number = data.get('slide_number', 0)
            description = data.get('description', '')
            total_slides = data.get('total_slides', 0)
            image_url = data.get('image_url', '')
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_slide',
                    'slide_number': slide_number,
                    'description': description,
                    'total_slides': total_slides,
                    'image_url': image_url,
                }
            )

        elif msg_type == 'session_start':
            await self.start_session()
            self.session_start_time = timezone.now()
            self.cumulative_words = 0
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'broadcast_session_start'}
            )

        elif msg_type == 'heartbeat':
            await self.send(text_data=json.dumps({'type': 'heartbeat_ack'}))

        # ─── STUDENT QUESTION CHANNEL ─────────────────────────
        elif msg_type == 'student_question':
            question_text = data.get('text', '').strip()
            if question_text and self.user and self.user.is_authenticated:
                username = self.user.username
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_question',
                        'text': question_text,
                        'student': username,
                        'timestamp': timezone.now().strftime('%H:%M'),
                    }
                )

        # ─── SESSION END (Lecturer ends session) ──────────────
        elif msg_type == 'session_end':
            await self.end_session_db()
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'broadcast_session_end'}
            )

        # ─── LECTURER ALERT / TAG A STUDENT ───────────────────
        elif msg_type == 'lecturer_alert':
            alert_text = data.get('text', '').strip()
            target_student = data.get('target', '')  # username or empty for all
            if alert_text:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_lecturer_alert',
                        'text': alert_text,
                        'target': target_student,
                        'timestamp': timezone.now().strftime('%H:%M'),
                    }
                )

        # ─── MID-SESSION SUMMARY REQUEST (Blind students) ─────
        elif msg_type == 'request_summary':
            summary = generate_live_summary(self.all_segments_text, max_sentences=3)
            await self.send(text_data=json.dumps({
                'type': 'live_summary',
                'summary': summary,
                'segment_count': len(self.all_segments_text),
            }))

    async def broadcast_transcript(self, event):
        await self.send(text_data=json.dumps({
            'type': 'transcript',
            'text': event['text'],
            'is_final': event['is_final'],
            'detected_terms': event.get('detected_terms', []),
            'complexity': event.get('complexity', 0),
            'complexity_label': event.get('complexity_label', ''),
            'wpm': event.get('wpm', 0),
            'emphasis': event.get('emphasis', []),
            'complex_phrases': event.get('complex_phrases', []),
        }))

    async def broadcast_slide(self, event):
        await self.send(text_data=json.dumps({
            'type': 'slide_change',
            'slide_number': event['slide_number'],
            'description': event['description'],
            'total_slides': event['total_slides'],
            'image_url': event.get('image_url', ''),
        }))

    async def attendee_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'attendee_update',
            'total': event['total'],
            'caption': event['caption'],
            'audio': event['audio'],
            'sign': event['sign'],
        }))

    async def broadcast_session_start(self, event):
        await self.send(text_data=json.dumps({'type': 'session_start'}))

    async def broadcast_question(self, event):
        await self.send(text_data=json.dumps({
            'type': 'student_question',
            'text': event['text'],
            'student': event['student'],
            'timestamp': event['timestamp'],
        }))

    async def broadcast_session_end(self, event):
        await self.send(text_data=json.dumps({
            'type': 'session_end',
            'message': 'The lecturer has ended this session.',
        }))

    async def broadcast_lecturer_alert(self, event):
        await self.send(text_data=json.dumps({
            'type': 'lecturer_alert',
            'text': event['text'],
            'target': event['target'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def check_session_exists(self):
        return LectureSession.objects.filter(
            session_code=self.session_code, status__in=['waiting', 'live']
        ).exists()

    @database_sync_to_async
    def save_segment(self, text, has_terms=False):
        session = LectureSession.objects.get(session_code=self.session_code)
        seconds = 0
        if session.started_at:
            seconds = (timezone.now() - session.started_at).total_seconds()
        TranscriptSegment.objects.create(
            session=session, text=text,
            seconds_from_start=seconds,
            has_technical_terms=has_terms,
        )

    @database_sync_to_async
    def start_session(self):
        session = LectureSession.objects.get(session_code=self.session_code)
        session.status = 'live'
        session.started_at = timezone.now()
        session.save()

    @database_sync_to_async
    def get_attendee_counts(self):
        attendees = SessionAttendance.objects.filter(
            session__session_code=self.session_code,
            left_at__isnull=True,
        )
        return {
            'total': attendees.count(),
            'caption': attendees.filter(mode='caption').count(),
            'audio': attendees.filter(mode='audio').count(),
            'sign': attendees.filter(mode='sign').count(),
        }

    @database_sync_to_async
    def mark_student_left(self):
        try:
            attendance = SessionAttendance.objects.get(
                session__session_code=self.session_code,
                student=self.user,
                left_at__isnull=True,
            )
            attendance.left_at = timezone.now()
            attendance.save()
        except (SessionAttendance.DoesNotExist, Exception):
            pass

    @database_sync_to_async
    def mark_student_rejoined(self):
        """Reset left_at when a student's WebSocket reconnects."""
        try:
            SessionAttendance.objects.filter(
                session__session_code=self.session_code,
                student=self.user,
            ).update(left_at=None)
        except Exception:
            pass

    @database_sync_to_async
    def load_glossary_terms(self):
        return list(GlossaryTerm.objects.values_list('term', flat=True))

    @database_sync_to_async
    def end_session_db(self):
        try:
            session = LectureSession.objects.get(session_code=self.session_code)
            session.status = 'ended'
            session.ended_at = timezone.now()
            session.save()
        except LectureSession.DoesNotExist:
            pass

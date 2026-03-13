from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile


TEST_USERS = [
    # ─── LECTURERS ─────────────────────────────────────
    {
        'username': 'prof_james',
        'password': 'sikika2026',
        'role': 'lecturer',
        'university': 'USIU-Africa',
        'department': 'Computer Science',
        'preferred_mode': 'caption',
        'font_size': 'medium',
    },
    {
        'username': 'dr_wanjiku',
        'password': 'sikika2026',
        'role': 'lecturer',
        'university': 'USIU-Africa',
        'department': 'Biology',
        'preferred_mode': 'caption',
        'font_size': 'large',
    },

    # ─── DEAF STUDENT (Caption Mode) ───────────────────
    {
        'username': 'amina_deaf',
        'password': 'sikika2026',
        'role': 'student',
        'university': 'USIU-Africa',
        'department': 'Information Technology',
        'preferred_mode': 'caption',
        'font_size': 'xlarge',
        'high_contrast': True,
    },

    # ─── DEAF STUDENT (Sign Language Mode) ─────────────
    {
        'username': 'brian_sign',
        'password': 'sikika2026',
        'role': 'student',
        'university': 'USIU-Africa',
        'department': 'Business Administration',
        'preferred_mode': 'sign',
        'font_size': 'large',
    },

    # ─── BLIND STUDENT (Audio Mode) ────────────────────
    {
        'username': 'grace_blind',
        'password': 'sikika2026',
        'role': 'student',
        'university': 'USIU-Africa',
        'department': 'Computer Science',
        'preferred_mode': 'audio',
        'font_size': 'medium',
        'high_contrast': True,
    },

    # ─── LOW-VISION STUDENT (Audio + Large Font) ───────
    {
        'username': 'kevin_lowvision',
        'password': 'sikika2026',
        'role': 'student',
        'university': 'USIU-Africa',
        'department': 'Mathematics',
        'preferred_mode': 'audio',
        'font_size': 'xlarge',
        'high_contrast': True,
    },

    # ─── DYSLEXIC STUDENT ─────────────────────────────
    {
        'username': 'faith_dyslexia',
        'password': 'sikika2026',
        'role': 'student',
        'university': 'USIU-Africa',
        'department': 'Psychology',
        'preferred_mode': 'caption',
        'font_size': 'large',
        'dyslexia_font': True,
    },

    # ─── REGULAR STUDENT (no disability) ───────────────
    {
        'username': 'david_student',
        'password': 'sikika2026',
        'role': 'student',
        'university': 'USIU-Africa',
        'department': 'Computer Science',
        'preferred_mode': 'caption',
        'font_size': 'medium',
    },
]


class Command(BaseCommand):
    help = 'Create test users for all accessibility scenarios'

    def handle(self, *args, **options):
        created = 0
        for data in TEST_USERS:
            username = data['username']
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  Exists: {username}')
                continue

            user = User.objects.create_user(
                username=username,
                password=data['password'],
            )
            UserProfile.objects.create(
                user=user,
                role=data['role'],
                university=data.get('university', ''),
                department=data.get('department', ''),
                preferred_mode=data.get('preferred_mode', 'caption'),
                font_size=data.get('font_size', 'medium'),
                high_contrast=data.get('high_contrast', False),
                dyslexia_font=data.get('dyslexia_font', False),
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f'  Created: {username} ({data["role"]})'))

        self.stdout.write(self.style.SUCCESS(f'\nDone. {created} new users created.'))

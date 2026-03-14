from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/accessibility/', views.accessibility_settings, name='accessibility_settings'),
    path('session/create/', views.create_session, name='create_session'),
    path('personal/start/', views.start_personal_session, name='start_personal_session'),
    path('session/<str:session_code>/', views.lecturer_session, name='lecturer_session'),
    path('session/<str:session_code>/end/', views.end_session, name='end_session'),
    path('session/<str:session_code>/transcript/', views.session_transcript, name='session_transcript'),
    path('session/<str:session_code>/download/', views.download_transcript, name='download_transcript'),
    path('session/<str:session_code>/slides/upload/', views.upload_slides, name='upload_slides'),
    # AI-powered routes
    path('session/<str:session_code>/analyze/', views.analyze_session_view, name='analyze_session'),
    path('session/<str:session_code>/summary/', views.session_summary, name='session_summary'),
    path('session/<str:session_code>/quiz/', views.session_quiz, name='session_quiz'),
    path('session/<str:session_code>/analytics/', views.session_analytics, name='session_analytics'),
    path('api/session/<str:session_code>/quiz/', views.quiz_api, name='quiz_api'),
    path('session/<str:session_code>/replay/', views.session_replay, name='session_replay'),
    path('api/session/<str:session_code>/notes/', views.notes_api, name='notes_api'),
    path('api/notes/<int:note_id>/delete/', views.delete_note_api, name='delete_note_api'),
    path('join/', views.join_session, name='join_session'),
    path('live/<str:session_code>/<str:mode>/', views.student_session, name='student_session'),
    path('api/glossary/', views.glossary_api, name='glossary_api'),
    # Presentations
    path('pitch/room/', views.presentation_room, name='presentation_room'),
    path('pitch/final/', views.presentation_final, name='presentation_final'),
    path('pitch/v3/', views.presentation_v3, name='presentation_v3'),
]

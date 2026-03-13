"""
SIKIKA AI Services — Pure Python NLP Engine
No external API dependencies. Uses frequency-based NLP, regex patterns,
and statistical text analysis for lecture intelligence.
"""

import re
import math
from collections import Counter, defaultdict


# ─── TEXT UTILITIES ────────────────────────────────────────────────

def tokenize_sentences(text):
    """Split text into sentences using punctuation boundaries."""
    text = text.strip()
    if not text:
        return []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def tokenize_words(text):
    """Extract clean lowercase words from text."""
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())


def count_syllables(word):
    """Estimate syllable count using vowel groups."""
    word = word.lower().strip()
    if not word:
        return 0
    count = len(re.findall(r'[aeiouy]+', word))
    if word.endswith('e') and count > 1:
        count -= 1
    return max(1, count)


# ─── READABILITY & COMPLEXITY ─────────────────────────────────────

def flesch_kincaid_grade(text):
    """
    Flesch-Kincaid Grade Level.
    Returns approximate US school grade level needed to understand the text.
    Higher = more complex. Range: ~1-18+
    """
    sentences = tokenize_sentences(text)
    words = tokenize_words(text)
    if not sentences or not words:
        return 0.0

    num_sentences = len(sentences)
    num_words = len(words)
    num_syllables = sum(count_syllables(w) for w in words)

    grade = (0.39 * (num_words / num_sentences)
             + 11.8 * (num_syllables / num_words)
             - 15.59)
    return round(max(0, grade), 1)


def flesch_reading_ease(text):
    """
    Flesch Reading Ease score. Higher = easier to read.
    90-100: Very Easy | 60-70: Standard | 0-30: Very Difficult
    """
    sentences = tokenize_sentences(text)
    words = tokenize_words(text)
    if not sentences or not words:
        return 100.0

    num_sentences = len(sentences)
    num_words = len(words)
    num_syllables = sum(count_syllables(w) for w in words)

    score = (206.835
             - 1.015 * (num_words / num_sentences)
             - 84.6 * (num_syllables / num_words))
    return round(max(0, min(100, score)), 1)


def complexity_score(text):
    """
    Compute a 0-100 complexity score combining multiple factors:
    - Flesch-Kincaid grade level
    - Average word length
    - Long word ratio (6+ chars)
    - Sentence length
    """
    words = tokenize_words(text)
    sentences = tokenize_sentences(text)
    if not words or not sentences:
        return 0

    fk_grade = flesch_kincaid_grade(text)
    avg_word_len = sum(len(w) for w in words) / len(words)
    long_word_ratio = sum(1 for w in words if len(w) >= 6) / len(words)
    avg_sentence_len = len(words) / len(sentences)

    # Normalize each factor to 0-25 range and sum
    grade_score = min(25, fk_grade * 1.5)
    word_len_score = min(25, (avg_word_len - 3) * 8)
    long_ratio_score = min(25, long_word_ratio * 70)
    sentence_score = min(25, avg_sentence_len * 0.8)

    total = grade_score + word_len_score + long_ratio_score + sentence_score
    return round(max(0, min(100, total)), 1)


def complexity_label(score):
    """Human-readable label for complexity score."""
    if score < 20:
        return 'Simple'
    elif score < 40:
        return 'Easy'
    elif score < 60:
        return 'Moderate'
    elif score < 80:
        return 'Complex'
    else:
        return 'Advanced'


# ─── WORD FREQUENCY & KEY TERMS ───────────────────────────────────

STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'need', 'dare',
    'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
    'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his',
    'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs', 'what',
    'which', 'who', 'whom', 'where', 'when', 'why', 'how', 'all', 'each',
    'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    'just', 'because', 'as', 'until', 'while', 'about', 'between', 'through',
    'during', 'before', 'after', 'above', 'below', 'up', 'down', 'out',
    'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
    'there', 'also', 'if', 'into', 'like', 'right', 'well', 'back',
    'still', 'way', 'even', 'new', 'want', 'look', 'first', 'now', 'get',
    'make', 'go', 'going', 'know', 'take', 'see', 'come', 'think', 'say',
    'said', 'one', 'two', 'three', 'much', 'many', 'thing', 'things',
    'really', 'actually', 'basically', 'okay', 'um', 'uh', 'yeah',
    'something', 'anything', 'everything', 'nothing',
}


def extract_keywords(text, top_n=20):
    """
    Extract top keywords by frequency, excluding stop words.
    Returns list of (word, count) tuples.
    """
    words = tokenize_words(text)
    meaningful = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    return Counter(meaningful).most_common(top_n)


def tf_idf_keywords(segments_text_list, top_n=15):
    """
    Simple TF-IDF across transcript segments.
    Each segment is treated as a 'document'.
    Returns top terms ranked by TF-IDF score.
    """
    if not segments_text_list:
        return []

    # Document frequency
    df = Counter()
    tf_per_doc = []
    for text in segments_text_list:
        words = [w for w in tokenize_words(text) if w not in STOP_WORDS and len(w) > 2]
        tf = Counter(words)
        tf_per_doc.append(tf)
        df.update(set(words))

    n_docs = len(segments_text_list)
    if n_docs == 0:
        return []

    # Compute TF-IDF scores
    scores = defaultdict(float)
    for tf in tf_per_doc:
        for word, count in tf.items():
            idf = math.log((n_docs + 1) / (df[word] + 1)) + 1
            scores[word] += count * idf

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]


# ─── TECHNICAL TERM DETECTION ─────────────────────────────────────

def detect_technical_terms(text, glossary_terms):
    """
    Detect glossary terms present in text.
    Returns list of matched term strings (lowercase).
    """
    text_lower = text.lower()
    found = []
    for term in glossary_terms:
        pattern = r'\b' + re.escape(term.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(term)
    return found


def detect_complex_phrases(text):
    """
    Detect academic/complex phrases using pattern matching.
    Returns list of detected patterns.
    """
    patterns = [
        (r'\b(?:in\s+(?:terms\s+of|relation\s+to|contrast\s+to|addition\s+to))\b', 'academic phrase'),
        (r'\b(?:furthermore|moreover|consequently|nevertheless|notwithstanding)\b', 'formal connector'),
        (r'\b(?:hypothesis|theorem|algorithm|paradigm|methodology)\b', 'academic term'),
        (r'\b(?:essentially|fundamentally|theoretically|conceptually)\b', 'abstract qualifier'),
        (r'\b\w+tion\b', None),  # -tion words (nominalization)
        (r'\b\w+ment\b', None),  # -ment words
        (r'\b\w+ness\b', None),  # -ness words
        (r'\b\w+ity\b', None),   # -ity words
    ]
    found = []
    text_lower = text.lower()
    for pattern, label in patterns[:4]:  # Only labeled patterns
        matches = re.findall(pattern, text_lower)
        for m in matches:
            found.append({'text': m, 'type': label})
    return found


# ─── EXTRACTIVE SUMMARIZATION ─────────────────────────────────────

def extractive_summary(full_text, num_sentences=5):
    """
    Extractive summarization using sentence scoring based on:
    1. Word frequency (TF)
    2. Position bonus (earlier sentences score higher)
    3. Length preference (not too short, not too long)
    4. Presence of key signal words
    """
    sentences = tokenize_sentences(full_text)
    if len(sentences) <= num_sentences:
        return full_text

    # Word frequencies
    words = [w for w in tokenize_words(full_text) if w not in STOP_WORDS and len(w) > 2]
    word_freq = Counter(words)
    max_freq = max(word_freq.values()) if word_freq else 1

    # Normalize frequencies
    for word in word_freq:
        word_freq[word] /= max_freq

    # Signal words that indicate important sentences
    signal_words = {
        'important', 'key', 'significant', 'crucial', 'essential', 'main',
        'primary', 'fundamental', 'critical', 'note', 'remember', 'define',
        'definition', 'means', 'called', 'known', 'example', 'therefore',
        'conclusion', 'summary', 'result', 'because', 'concept', 'principle',
    }

    # Score each sentence
    scored = []
    for i, sentence in enumerate(sentences):
        sent_words = tokenize_words(sentence)
        if not sent_words:
            continue

        # TF score
        tf_score = sum(word_freq.get(w, 0) for w in sent_words) / len(sent_words)

        # Position score (earlier = better, with slight boost for conclusions)
        position = i / len(sentences)
        position_score = 1.0 - (position * 0.5)  # 1.0 → 0.5
        if position > 0.9:  # Conclusion boost
            position_score += 0.3

        # Length score (prefer 8-25 word sentences)
        length_score = 1.0
        if len(sent_words) < 5:
            length_score = 0.3
        elif len(sent_words) > 30:
            length_score = 0.6

        # Signal word bonus
        signal_score = sum(0.15 for w in sent_words if w in signal_words)

        total = tf_score + position_score * 0.3 + length_score * 0.2 + signal_score
        scored.append((i, sentence, total))

    # Select top sentences, maintain original order
    scored.sort(key=lambda x: x[2], reverse=True)
    selected = sorted(scored[:num_sentences], key=lambda x: x[0])

    return ' '.join(s[1] for s in selected)


def extract_key_points(full_text, max_points=8):
    """
    Extract key points from lecture text.
    Identifies sentences that:
    - Contain definitions ("X is...", "X means...", "X refers to...")
    - Contain enumerations ("first...", "second...", "three types...")
    - Contain signal phrases ("important", "key concept", "remember")
    """
    sentences = tokenize_sentences(full_text)
    if not sentences:
        return []

    key_patterns = [
        (r'\b(?:is defined as|means that|refers to|is called|known as)\b', 'definition', 1.0),
        (r'\b(?:important|crucial|essential|key|significant|critical)\b', 'emphasis', 0.8),
        (r'\b(?:for example|such as|for instance|e\.g\.)\b', 'example', 0.7),
        (r'\b(?:first|second|third|finally|lastly|step)\b', 'enumeration', 0.6),
        (r'\b(?:therefore|thus|hence|consequently|as a result)\b', 'conclusion', 0.9),
        (r'\b(?:remember|note that|keep in mind|don\'t forget)\b', 'instruction', 0.95),
        (r'\b(?:difference between|compared to|unlike|whereas)\b', 'comparison', 0.75),
        (r'\b(?:advantage|disadvantage|benefit|drawback|pro|con)\b', 'evaluation', 0.7),
    ]

    scored = []
    for sentence in sentences:
        s_lower = sentence.lower()
        best_score = 0
        best_type = 'general'
        for pattern, ptype, weight in key_patterns:
            if re.search(pattern, s_lower):
                if weight > best_score:
                    best_score = weight
                    best_type = ptype
        if best_score > 0:
            scored.append((sentence, best_score, best_type))

    scored.sort(key=lambda x: x[1], reverse=True)

    points = []
    for sentence, score, ptype in scored[:max_points]:
        # Clean up the sentence
        clean = sentence.strip()
        if len(clean) > 200:
            clean = clean[:197] + '...'
        points.append({
            'text': clean,
            'type': ptype,
            'importance': round(score, 2),
        })

    return points


# ─── TOPIC SEGMENTATION ──────────────────────────────────────────

def detect_topic_segments(segments_data):
    """
    Detect topic shifts by analyzing vocabulary changes between
    groups of consecutive transcript segments.

    segments_data: list of dicts with 'text' and 'seconds_from_start' keys
    Returns: list of topic segments with start time, keywords, and label
    """
    if len(segments_data) < 3:
        return [{'start_seconds': 0, 'label': 'Full Lecture', 'keywords': []}]

    # Group segments into windows
    window_size = max(3, len(segments_data) // 8)
    windows = []
    for i in range(0, len(segments_data), window_size):
        chunk = segments_data[i:i + window_size]
        combined_text = ' '.join(s['text'] for s in chunk)
        words = [w for w in tokenize_words(combined_text) if w not in STOP_WORDS and len(w) > 2]
        windows.append({
            'start_seconds': chunk[0]['seconds_from_start'],
            'words': Counter(words),
            'text': combined_text,
        })

    # Detect shifts using Jaccard distance between consecutive windows
    topics = []
    for i, window in enumerate(windows):
        if i == 0:
            top_words = window['words'].most_common(5)
            topics.append({
                'start_seconds': window['start_seconds'],
                'keywords': [w for w, _ in top_words],
                'label': _generate_topic_label([w for w, _ in top_words]),
            })
        else:
            prev_words = set(windows[i - 1]['words'].keys())
            curr_words = set(window['words'].keys())
            if not prev_words and not curr_words:
                continue
            intersection = prev_words & curr_words
            union = prev_words | curr_words
            jaccard = len(intersection) / len(union) if union else 1.0

            # If similarity drops below threshold, it's a new topic
            if jaccard < 0.35:
                top_words = window['words'].most_common(5)
                topics.append({
                    'start_seconds': window['start_seconds'],
                    'keywords': [w for w, _ in top_words],
                    'label': _generate_topic_label([w for w, _ in top_words]),
                })

    return topics if topics else [{'start_seconds': 0, 'label': 'Full Lecture', 'keywords': []}]


def _generate_topic_label(keywords):
    """Generate a human-readable topic label from keywords."""
    if not keywords:
        return 'General Discussion'
    return ', '.join(kw.title() for kw in keywords[:3])


# ─── QUIZ GENERATION ──────────────────────────────────────────────

def generate_fill_blank_questions(full_text, glossary_terms_dict, max_q=5):
    """
    Generate fill-in-the-blank questions by finding sentences
    that contain glossary terms and blanking out the term.

    glossary_terms_dict: {term_lower: definition}
    """
    sentences = tokenize_sentences(full_text)
    questions = []

    for sentence in sentences:
        if len(questions) >= max_q:
            break
        s_lower = sentence.lower()
        for term, definition in glossary_terms_dict.items():
            pattern = r'\b(' + re.escape(term) + r')\b'
            match = re.search(pattern, s_lower)
            if match:
                # Create blank version
                blanked = re.sub(pattern, '________', sentence, count=1, flags=re.IGNORECASE)
                questions.append({
                    'type': 'fill_blank',
                    'question': blanked,
                    'answer': term.title(),
                    'hint': definition[:80] + ('...' if len(definition) > 80 else ''),
                    'source_sentence': sentence,
                })
                break  # One question per sentence

    return questions


def generate_definition_questions(glossary_terms_dict, detected_terms, max_q=5):
    """
    Generate 'What is X?' definition-matching questions
    from terms that appeared in the lecture.
    """
    questions = []
    for term in detected_terms[:max_q * 2]:
        term_lower = term.lower()
        if term_lower in glossary_terms_dict:
            definition = glossary_terms_dict[term_lower]
            questions.append({
                'type': 'definition',
                'question': f'What is {term.title()}?',
                'answer': definition,
                'term': term.title(),
            })
            if len(questions) >= max_q:
                break
    return questions


def generate_true_false_questions(full_text, max_q=5):
    """
    Generate true/false questions from factual statements in the text.
    Uses sentences with 'is', 'are', 'means', 'defined as' patterns.
    """
    sentences = tokenize_sentences(full_text)
    questions = []
    factual_patterns = [
        r'\b\w+\s+(?:is|are|was|were)\s+(?:a|an|the)\s+',
        r'\b\w+\s+(?:means|refers to|is defined as)\s+',
        r'\b(?:the|a)\s+\w+\s+(?:of|in)\s+\w+\s+(?:is|are)\s+',
    ]

    for sentence in sentences:
        if len(questions) >= max_q:
            break
        for pattern in factual_patterns:
            if re.search(pattern, sentence.lower()):
                questions.append({
                    'type': 'true_false',
                    'question': sentence.strip(),
                    'answer': True,
                    'explanation': 'This statement appeared in the lecture transcript.',
                })
                break

    return questions


def generate_quiz(full_text, glossary_terms_dict, detected_terms, max_total=10):
    """
    Generate a mixed quiz combining all question types.
    Returns a shuffled list of questions.
    """
    fill = generate_fill_blank_questions(full_text, glossary_terms_dict, max_q=4)
    defs = generate_definition_questions(glossary_terms_dict, detected_terms, max_q=3)
    tf = generate_true_false_questions(full_text, max_q=3)

    all_questions = fill + defs + tf
    # Assign sequential IDs
    for i, q in enumerate(all_questions):
        q['id'] = i + 1

    return all_questions[:max_total]


# ─── ANALYTICS ────────────────────────────────────────────────────

def compute_wpm_timeline(segments_data):
    """
    Compute words-per-minute at each segment.
    Returns list of {seconds, wpm} dicts for charting.
    """
    if not segments_data:
        return []

    timeline = []
    cumulative_words = 0
    for seg in segments_data:
        words = len(tokenize_words(seg['text']))
        cumulative_words += words
        seconds = seg['seconds_from_start']
        if seconds > 0:
            wpm = (cumulative_words / seconds) * 60
        else:
            wpm = 0
        timeline.append({
            'seconds': round(seconds),
            'wpm': round(wpm, 1),
            'words': words,
        })
    return timeline


def compute_session_stats(full_text, segments_data):
    """
    Comprehensive session statistics.
    """
    words = tokenize_words(full_text)
    sentences = tokenize_sentences(full_text)

    total_seconds = 0
    if segments_data:
        total_seconds = max(s['seconds_from_start'] for s in segments_data)

    avg_wpm = (len(words) / total_seconds * 60) if total_seconds > 0 else 0

    return {
        'total_words': len(words),
        'total_sentences': len(sentences),
        'unique_words': len(set(words)),
        'avg_wpm': round(avg_wpm, 1),
        'total_duration_seconds': round(total_seconds),
        'complexity': complexity_score(full_text),
        'complexity_label': complexity_label(complexity_score(full_text)),
        'reading_ease': flesch_reading_ease(full_text),
        'grade_level': flesch_kincaid_grade(full_text),
        'avg_sentence_length': round(len(words) / max(len(sentences), 1), 1),
    }


# ─── MASTER ANALYSIS FUNCTION ────────────────────────────────────

def analyze_session(segments_queryset, glossary_terms_dict):
    """
    Run full AI analysis on a session's transcript segments.

    segments_queryset: queryset of TranscriptSegment objects
    glossary_terms_dict: {term_lower: definition}

    Returns dict with all analysis results.
    """
    segments_data = [
        {'text': seg.text, 'seconds_from_start': seg.seconds_from_start}
        for seg in segments_queryset
    ]

    if not segments_data:
        return {
            'summary': 'No transcript data available for analysis.',
            'key_points': [],
            'keywords': [],
            'quiz': [],
            'topics': [],
            'stats': {},
            'wpm_timeline': [],
            'detected_terms': [],
        }

    full_text = ' '.join(s['text'] for s in segments_data)
    glossary_term_list = list(glossary_terms_dict.keys())

    # Run all analyses
    summary = extractive_summary(full_text, num_sentences=5)
    key_points = extract_key_points(full_text, max_points=8)
    keywords = extract_keywords(full_text, top_n=20)
    detected = detect_technical_terms(full_text, glossary_term_list)
    topics = detect_topic_segments(segments_data)
    stats = compute_session_stats(full_text, segments_data)
    wpm_timeline = compute_wpm_timeline(segments_data)
    quiz = generate_quiz(full_text, glossary_terms_dict, detected, max_total=10)

    return {
        'summary': summary,
        'key_points': key_points,
        'keywords': [(w, c) for w, c in keywords],
        'quiz': quiz,
        'topics': topics,
        'stats': stats,
        'wpm_timeline': wpm_timeline,
        'detected_terms': detected,
    }


# ─── REAL-TIME EMPHASIS DETECTION ─────────────────────────────────

def detect_emphasis(text):
    """
    Detect emphasis/importance markers in real-time text.
    Returns list of {type, label, icon} for UI markers.
    Used by WebSocket consumer for live annotation.
    """
    markers = []
    t = text.lower()

    # Key definitions
    if re.search(r'\b(?:is defined as|means that|refers to|is called|known as|definition of)\b', t):
        markers.append({'type': 'definition', 'label': 'Definition', 'icon': '📖'})

    # Important emphasis
    if re.search(r'\b(?:important|crucial|essential|critical|key point|remember|note that|keep in mind|pay attention)\b', t):
        markers.append({'type': 'important', 'label': 'Important', 'icon': '❗'})

    # Examples
    if re.search(r'\b(?:for example|for instance|such as|e\.g\.|let me illustrate|consider this)\b', t):
        markers.append({'type': 'example', 'label': 'Example', 'icon': '📌'})

    # Conclusions / summaries
    if re.search(r'\b(?:therefore|in conclusion|to summarize|in summary|the result is|hence|thus|so basically)\b', t):
        markers.append({'type': 'conclusion', 'label': 'Conclusion', 'icon': '🎯'})

    # Questions / prompts
    if re.search(r'\b(?:what do you think|any questions|does that make sense|do you understand|is that clear)\b', t):
        markers.append({'type': 'question', 'label': 'Check-in', 'icon': '❓'})

    # Warnings / caveats
    if re.search(r'\b(?:be careful|common mistake|don\'t confuse|watch out|avoid|trap|pitfall)\b', t):
        markers.append({'type': 'warning', 'label': 'Warning', 'icon': '⚠️'})

    # Transitions
    if re.search(r'\b(?:moving on|next topic|let\'s now|now let\'s|turning to|switching to)\b', t):
        markers.append({'type': 'transition', 'label': 'New Topic', 'icon': '➡️'})

    return markers


def generate_live_summary(segments_texts, max_sentences=3):
    """
    Generate a quick mid-session summary from accumulated segments.
    Used for blind students pressing 'M' for on-demand summary.
    """
    if not segments_texts:
        return "No content to summarize yet."
    full_text = ' '.join(segments_texts)
    return extractive_summary(full_text, num_sentences=max_sentences)


# ─── AI SLIDE DESCRIPTION (Pure Python, no external APIs) ─────────

def generate_slide_description(image_path):
    """
    Generate an accessibility description for a slide image.
    Uses PIL to extract visual properties (colors, dimensions, text regions).
    Returns a descriptive string for blind students.
    """
    try:
        from PIL import Image, ImageStat
        img = Image.open(image_path)
        width, height = img.size
        mode = img.mode

        # Convert to RGB for analysis
        if mode != 'RGB':
            img_rgb = img.convert('RGB')
        else:
            img_rgb = img

        stat = ImageStat.Stat(img_rgb)
        avg_r, avg_g, avg_b = [int(v) for v in stat.mean]
        brightness = (avg_r * 299 + avg_g * 587 + avg_b * 114) / 1000

        # Determine dominant color tone
        if brightness > 200:
            bg_desc = "light background"
        elif brightness < 80:
            bg_desc = "dark background"
        else:
            bg_desc = "medium-toned background"

        # Determine color dominance
        if avg_r > avg_g + 30 and avg_r > avg_b + 30:
            color_desc = "with warm red/orange tones"
        elif avg_b > avg_r + 30 and avg_b > avg_g + 30:
            color_desc = "with cool blue tones"
        elif avg_g > avg_r + 30 and avg_g > avg_b + 30:
            color_desc = "with green tones"
        else:
            color_desc = "with neutral tones"

        # Check image variance (indicates content complexity)
        variance = sum(stat.var) / 3
        if variance > 5000:
            complexity_desc = "This appears to be a complex slide with many visual elements, possibly charts, diagrams, or photos."
        elif variance > 2000:
            complexity_desc = "This slide contains moderate visual content, likely text with some graphics."
        else:
            complexity_desc = "This appears to be a simple slide, possibly mostly text or a title slide."

        # Orientation
        orientation = "landscape" if width > height else "portrait" if height > width else "square"

        description = (
            f"Slide image ({orientation}, {width}x{height}px). "
            f"{bg_desc.capitalize()} {color_desc}. "
            f"{complexity_desc}"
        )
        return description

    except Exception:
        return "Slide image uploaded. Visual description could not be generated."

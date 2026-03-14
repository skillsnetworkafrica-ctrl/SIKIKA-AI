# SIKIKA — Q&A Preparation Guide

> Anticipated judge questions with suggested answers.
> Speaker: primarily Iranzi (technical), with Deogracia (business) and Daisy (impact/UX) stepping in where noted.

---

## Category 1: Technical Accuracy & Reliability

### Q: "How accurate is the speech recognition, especially with African accents?"

**Answer (Iranzi):**
> "Great question. We use the Web Speech API, which leverages Google's speech models trained on millions of hours of diverse speech. Accuracy for clear English is 92 to 97 percent in real time. For African accents, we've tested with Kenyan, Rwandan, and Nigerian speakers and see around 85 to 92 percent accuracy — which is already better than what most students get through a human interpreter, where studies show 20 to 30 percent content loss. As an additional layer, we highlight technical terms separately, so even if a word is slightly mistranscribed, the key vocabulary is captured correctly through our term detection engine."

**If pressed:** "We're also building a feedback loop — lecturers can correct terms post-session, and those corrections will improve future recognition for that specific lecturer's speech patterns."

---

### Q: "What happens when the internet goes down mid-lecture?"

**Answer (Iranzi):**
> "SIKIKA is WebSocket-based, so it maintains a persistent connection. If there's a brief drop, the connection auto-reconnects and resumes within seconds — students don't lose their existing transcript, only the gap during the outage. If the internet is completely unavailable, the lecturer can still record locally and upload the session afterward for asynchronous transcription. But in a university setting with campus WiFi, sustained outages are rare — and when they happen, even human interpreters can't help if they aren't physically present."

---

### Q: "How does the whiteboard diagram analysis actually work technically?"

**Answer (Iranzi):**
> "The whiteboard is an HTML5 canvas. As the lecturer draws, every stroke is captured as vector data — coordinates, shapes, connections, and text labels. Our diagram analysis engine doesn't use image recognition — it understands the actual drawing objects. It identifies shapes like rectangles and circles, detects arrows and their connections between shapes, reads text labels, and then generates a natural-language description of the spatial relationships: 'A Client node connects to a Server node via a data flow arrow.' That description is sent to blind students via WebSocket and read aloud. It's deterministic, not probabilistic — so it's reliable and fast."

---

### Q: "Why not just use existing tools like Google Live Transcribe or Otter.ai?"

**Answer (Iranzi):**
> "Three reasons. First, those tools are individual consumer apps — one person, one device. They don't broadcast to an entire classroom of 200 students simultaneously. SIKIKA is a one-to-many platform. Second, none of them have diagram analysis. When a professor draws on a whiteboard, Google Live Transcribe captures nothing. SIKIKA describes the diagram in real time. Third, neither offers sign language output. SIKIKA provides three modes — captions, audio, and sign — from one input. We're not competing with transcription apps. We're building a classroom accessibility platform. Different category entirely."

---

### Q: "What about data privacy? You're processing students' lecture content through external APIs?"

**Answer (Iranzi):**
> "Speech recognition runs in the browser using the Web Speech API — audio data is processed by the browser engine, not stored on our servers. The transcript text flows through our Django Channels WebSocket server, which can be deployed on the university's own infrastructure if required. We don't store audio. We store only text transcripts, and those are tied to the session — universities control retention policies. For GDPR and Kenya's Data Protection Act compliance, we process only what's needed, store only text, and can offer on-premise deployment."

---

## Category 2: Business & Market

### Q: "Who's paying for this? Universities in Africa don't have big tech budgets."

**Answer (Deogracia):**
> "That's exactly why our pricing starts at 2,000 dollars per year for a small institution — less than what they'd pay for a single semester of interpreter services. But more importantly, universities aren't our only revenue path. National disability councils, international development organizations like USAID and DFID, and NGOs like the WHO actively fund accessibility initiatives. In Kenya, the Persons with Disabilities Act requires reasonable accommodation — SIKIKA helps universities comply at a fraction of current costs. We're not asking universities to add budget. We're offering them a way to meet legal obligations they're already failing to meet."

---

### Q: "2.9 million ARR by year three seems ambitious. How do you get there?"

**Answer (Deogracia):**
> "Here's the math. Our target is 80 university subscriptions by year three. Africa has over 1,500 universities. That's roughly 5% penetration. At an average contract of 36,000 dollars per year for a mid-size tier — which is still 85% cheaper than interpreter costs — that's 2.9 million. We start with Kenya and Rwanda in year one — markets we know — expand to East Africa in year two, then pan-African in year three. The critical lever is that once one university in a country adopts SIKIKA, peer pressure and regulatory pressure drive others. Disability compliance is a rising tide across the continent."

---

### Q: "What's your competitive moat? What stops Google from building this?"

**Answer (Iranzi):**
> "Google could build a transcription tool. They already have one. What they can't easily build is a purpose-built classroom accessibility platform that integrates real-time transcription, diagram analysis, sign language output, session management, and student-specific customization — all designed for the constraints of African universities: low bandwidth, varied accents, limited IT infrastructure. Our moat is domain specificity. We're not a general transcription API. We're a full vertical solution for lecture accessibility. And our early mover advantage in African universities — with local language support, local deployment options, and local partnerships — creates switching costs that matter in institutional sales."

---

### Q: "How do you make money before universities start paying? What about the seed stage?"

**Answer (Deogracia):**
> "We're seeking 250,000 dollars in seed funding, which covers 18 months of runway — product development, pilot deployments at 3 to 5 universities, and initial go-to-market hires. During the pilot phase, the product is free to universities in exchange for data, feedback, and case studies. Those case studies become our primary sales tool. By month 12, we convert pilots to paid contracts. We're also eligible for grants from organizations like the Mastercard Foundation, Skoll Foundation, and the African Development Bank's disability inclusion funding, which de-risks the seed stage."

---

## Category 3: Impact & Inclusion

### Q: "How do you measure actual impact on student outcomes?"

**Answer (Daisy):**
> "Three metrics. First, content access rate — what percentage of lecture content reaches the student. Research shows deaf students with interpreters get 70 to 80 percent. With SIKIKA captions, they get 95 to 100 percent of the spoken content. Second, for blind students, the metric is visual content access — previously zero for diagrams, now described in real time. Third, session replay usage — students can revisit lectures, which studies show improves retention by 20 to 30 percent. We'll track these through built-in analytics: transcript completeness, session duration, replay frequency, and student satisfaction surveys."

---

### Q: "Isn't this just a band-aid? Shouldn't we be training more interpreters?"

**Answer (Daisy):**
> "Absolutely, we should train more interpreters. SIKIKA doesn't replace that effort — it covers the gap while that effort scales. Kenya needs about 15,000 interpreters to reach adequate coverage. At current training rates, that's decades away. Students with disabilities can't wait decades. SIKIKA provides immediate, scalable access today while the long-term human capacity is built. Think of it like solar power — you build solar panels now while also investing in the grid. They're complementary, not competing."

---

### Q: "What about students who prefer human interaction over AI tools?"

**Answer (Daisy):**
> "That preference is completely valid, and SIKIKA doesn't force anyone to switch. It's additive — a student who has a human interpreter can still use SIKIKA captions as a backup. A student who prefers audio can use SIKIKA alongside their existing support. The real question is: what about the 99% of disabled students who have NO support at all? They don't have the luxury of preference. SIKIKA serves the gap, not the replacement."

---

## Category 4: Technical Roadmap

### Q: "The sign language avatar — is it real or is it a future plan?"

**Answer (Iranzi):**
> "Today, our sign mode converts text to a visual sign representation. The full 3D avatar with fluid Kenyan Sign Language is on our 12-month roadmap. The infrastructure is already built — the text pipeline, the WebSocket delivery, the student interface. What we're adding is the animation layer on top. We're evaluating partnerships with SignAll and MotionSavvy who have existing avatar technology. The key point: the hardest part — real-time text generation and delivery — is done. The avatar is an interface upgrade, not an architectural change."

---

### Q: "How does this scale to multiple languages?"

**Answer (Iranzi):**
> "The Web Speech API already supports over 100 languages including Swahili, Amharic, Yoruba, and Zulu. Our architecture is language-agnostic — the AI engine processes whatever language the browser recognizes. Adding a new language is a configuration change, not a code change. For the sign language component, each sign language — KSL, ASL, BSL — requires its own avatar model, which is the costlier part. That's why we're starting with Kenyan Sign Language and expanding based on demand and partnership availability."

---

### Q: "What about STEM-specific content — equations, chemical formulas, code?"

**Answer (Iranzi):**
> "Our term highlighting already handles STEM vocabulary. For equations, the whiteboard diagram engine captures what's drawn — so if a lecturer writes an equation on the whiteboard, the vector data includes the symbols and their spatial relationships. We describe it as 'the equation shows x squared plus 2x minus 5 equals 0.' For code, since it's typically typed and displayed on screen rather than spoken, our next integration target is screen-sharing analysis — reading code displayed on the lecturer's screen. That's on the 18-month roadmap."

---

## Category 5: Team & Execution

### Q: "Why should we believe a student team can execute this?"

**Answer (Iranzi):**
> "Because we already did. SIKIKA isn't a concept — it's deployed. Right now. On Railway. With real-time transcription, whiteboard analysis, personal accessibility sessions, session replay, and WebSocket-based multi-user delivery. All built in weeks. The technology works. What we need is funding to take it from a working product to a scaled platform. And frankly, university accessibility is a problem best solved by people who live in universities — we understand the lecture experience because we sit in those classrooms every day."

---

### Q: "What's the team's technical background?"

**Answer (Iranzi):**
> "I'm a full-stack developer with experience in Django, JavaScript, and real-time systems — I built the entire SIKIKA backend and WebSocket infrastructure. Deogracia handles business strategy and go-to-market. Daisy drives user research and accessibility design. We're a small team that ships fast. For scaling, our seed funding includes hiring two additional engineers and a growth lead."

---

## Quick-Fire Response Templates

For unexpected questions, use these frameworks:

**"I don't know" response:**
> "That's a question we haven't fully explored yet, and I'd rather be honest than guess. What I can tell you is [related thing we DO know]. We'd love to dig into that with you after the session."

**"That's outside our current scope" response:**
> "Great question. Right now we're laser-focused on [core feature]. We've thought about [their suggestion] and it's on our roadmap for [timeframe], but our priority is nailing the core experience first."

**"Redirect to strength" response:**
> "That's an important consideration. Let me connect it back to what SIKIKA does differently — [strongest point]. That's what makes this approach viable even given the challenge you're raising."

---

## Final Prep Checklist

- [ ] Each speaker rehearses their slides 5x out loud with timer
- [ ] Practice transitions between speakers (smooth handoffs, no gaps)
- [ ] Iranzi rehearses the opening question + silence 3x (the pause is everything)
- [ ] Test demo on venue WiFi or have mobile hotspot backup
- [ ] Have backup demo script memorized (Slide 7 backup version)
- [ ] Print 2 copies of judge handout per judge
- [ ] Ensure laptop is charged, browser is open to SIKIKA before presenting
- [ ] Close all other tabs and notifications on demo laptop
- [ ] Know the 5-minute and 3-minute contingency cuts by heart

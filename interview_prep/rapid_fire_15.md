# Rapid Fire: Top 15 Interview Questions (30-60s Answers)

Use this file in the final 10 minutes before interview.

## 1) Explain your project in one minute.
"I built VaradGPT-Bot, a Python Telegram AI assistant using aiogram and OpenAI APIs. It supports text chat through GPT and voice chat through Whisper transcription plus GPT response. It also includes portfolio commands like resume, projects, and contact. I built the architecture, handlers, model integration, and deployment-ready setup."

## 2) What problem does your bot solve?
"It combines assistant + portfolio in one interface. Users can ask normal questions and also access my resume, projects, and contact quickly."

## 3) Why Telegram?
"Low-friction distribution, built-in voice support, and quick iteration without frontend overhead."

## 4) Why aiogram?
"Async architecture and clean router-based handlers make it practical for concurrent bot interactions."

## 5) Why GPT + Whisper together?
"GPT provides text intelligence, Whisper handles speech-to-text, and together they enable natural multimodal chat."

## 6) Walk me through voice pipeline.
"Voice file comes from Telegram, bot downloads `.ogg`, transcribes with Whisper, sends transcript to GPT, replies to user, and deletes temp file."

## 7) How do you handle failures?
"Guard checks for missing user/file context and try/except around API calls with user-safe fallback messages."

## 8) What is one limitation today?
"Conversation memory is global and in-memory, so per-user isolation is a planned improvement."

## 9) Why are there doc/code mismatches in features?
"Some roadmap features were documented early; stable code focuses on chat and voice. I should align docs with current implementation."

## 10) What would you improve first?
"Per-user session state, remove risky debug prints, and align runtime/dependency consistency."

## 11) Tell me about yourself.
"I am an AI/ML undergraduate focused on practical Python AI applications. I build usable projects that combine model APIs with real user workflows."

## 12) Which project are you most proud of?
"VaradGPT-Bot, because it combines async bot engineering, AI integration, and user-focused product design."

## 13) Tell me one analytics project from your resume.
"In Diwali Sales Analysis, I cleaned data with Pandas, performed EDA with Matplotlib/Seaborn, and extracted customer behavior insights for decision support."

## 14) Biggest challenge you solved?
"Making voice workflow reliable across multiple APIs. I solved it using step-by-step validation and fallback handling."

## 15) Why this intern/fresher role?
"I can contribute quickly with Python and AI integration experience, and I want to grow under production engineering standards."

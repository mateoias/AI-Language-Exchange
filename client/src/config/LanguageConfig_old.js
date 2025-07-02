// Language configuration for the frontend
export const languageConfig = {
  Spanish: {
    greeting: (username) => `¡Hola ${username}! ¿De qué te gustaría hablar hoy?`,
    placeholder: "Escribe en español o inglés...",
    voices: {
      male: 'es-ES-AlvaroNeural',
      female: 'es-ES-ElviraNeural'
    }
  },
  English: {
    greeting: (username) => `Hello ${username}! What would you like to talk about today?`,
    placeholder: "Type in English or your native language...",
    voices: {
      male: 'en-US-GuyNeural',
      female: 'en-US-AriaNeural'
    }
  },
  French: {
    greeting: (username) => `Bonjour ${username}! De quoi aimeriez-vous parler aujourd'hui?`,
    placeholder: "Écrivez en français ou anglais...",
    voices: {
      male: 'fr-FR-HenriNeural',
      female: 'fr-FR-DeniseNeural'
    }
  },
  German: {
    greeting: (username) => `Hallo ${username}! Worüber möchtest du heute sprechen?`,
    placeholder: "Schreibe auf Deutsch oder Englisch...",
    voices: {
      male: 'de-DE-ConradNeural',
      female: 'de-DE-KatjaNeural'
    }
  },
  Italian: {
    greeting: (username) => `Ciao ${username}! Di cosa ti piacerebbe parlare oggi?`,
    placeholder: "Scrivi in italiano o inglese...",
    voices: {
      male: 'it-IT-DiegoNeural',
      female: 'it-IT-ElsaNeural'
    }
  },
  Portuguese: {
    greeting: (username) => `Olá ${username}! Sobre o que você gostaria de falar hoje?`,
    placeholder: "Digite em português ou inglês...",
    voices: {
      male: 'pt-BR-AntonioNeural',
      female: 'pt-BR-FranciscaNeural'
    }
  },
  Russian: {
    greeting: (username) => `Привет ${username}! О чем бы ты хотел поговорить сегодня?`,
    placeholder: "Пишите на русском или английском...",
    voices: {
      male: 'ru-RU-DmitryNeural',
      female: 'ru-RU-SvetlanaNeural'
    }
  },
  Chinese: {
    greeting: (username) => `你好 ${username}! 今天想聊什么?`,
    placeholder: "用中文或英文输入...",
    voices: {
      male: 'zh-CN-YunxiNeural',
      female: 'zh-CN-XiaoxiaoNeural'
    }
  },
  Japanese: {
    greeting: (username) => `こんにちは ${username}さん! 今日は何について話したいですか?`,
    placeholder: "日本語または英語で入力してください...",
    voices: {
      male: 'ja-JP-KeitaNeural',
      female: 'ja-JP-NanamiNeural'
    }
  },
  Korean: {
    greeting: (username) => `안녕하세요 ${username}님! 오늘은 무엇에 대해 이야기하고 싶으신가요?`,
    placeholder: "한국어 또는 영어로 입력하세요...",
    voices: {
      male: 'ko-KR-InJoonNeural',
      female: 'ko-KR-SunHiNeural'
    }
  },
  Arabic: {
    greeting: (username) => `مرحبا ${username}! ما الذي تود التحدث عنه اليوم؟`,
    placeholder: "اكتب بالعربية أو الإنجليزية...",
    voices: {
      male: 'ar-SA-HamedNeural',
      female: 'ar-SA-ZariyahNeural'
    }
  },
  Hindi: {
    greeting: (username) => `नमस्ते ${username}! आज आप किस बारे में बात करना चाहेंगे?`,
    placeholder: "हिंदी या अंग्रेजी में टाइप करें...",
    voices: {
      male: 'hi-IN-MadhurNeural',
      female: 'hi-IN-SwaraNeural'
    }
  }
}

// Helper functions
export const getGreeting = (language, username) => {
  const config = languageConfig[language] || languageConfig.English
  return config.greeting(username)
}

export const getPlaceholder = (learningLanguage, nativeLanguage) => {
  const config = languageConfig[learningLanguage] || languageConfig.English
  return config.placeholder
}

export const getVoices = (language) => {
  const config = languageConfig[language] || languageConfig.English
  return config.voices
}

// Error messages in each language
export const errorMessages = {
  Spanish: "Lo siento, estoy teniendo problemas en este momento. Por favor, inténtalo de nuevo.",
  English: "I'm sorry, I'm having trouble right now. Please try again in a moment.",
  French: "Désolé, j'ai des difficultés en ce moment. Veuillez réessayer.",
  German: "Entschuldigung, ich habe gerade Probleme. Bitte versuchen Sie es noch einmal.",
  Italian: "Mi dispiace, sto avendo problemi in questo momento. Per favore riprova.",
  Portuguese: "Desculpe, estou tendo problemas no momento. Por favor, tente novamente.",
  Russian: "Извините, у меня сейчас проблемы. Пожалуйста, попробуйте еще раз.",
  Chinese: "对不起，我现在遇到了问题。请稍后再试。",
  Japanese: "申し訳ありません、現在問題が発生しています。もう一度お試しください。",
  Korean: "죄송합니다, 지금 문제가 있습니다. 다시 시도해 주세요.",
  Arabic: "آسف، أواجه مشكلة الآن. يرجى المحاولة مرة أخرى.",
  Hindi: "क्षमा करें, मुझे अभी समस्या हो रही है। कृपया फिर से प्रयास करें।"
}

export const getErrorMessage = (language) => {
  return errorMessages[language] || errorMessages.English
}
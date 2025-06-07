# Language configuration for the backend
LANGUAGE_CONFIG = {
    'Spanish': {
        'voices': {
            'male': 'es-ES-AlvaroNeural',
            'female': 'es-ES-ElviraNeural'
        },
        'default_voice': 'male',
        'error_message': 'Lo siento, estoy teniendo problemas en este momento. Por favor, inténtalo de nuevo.'
    },
    'English': {
        'voices': {
            'male': 'en-US-GuyNeural',
            'female': 'en-US-AriaNeural'
        },
        'default_voice': 'male',
        'error_message': "I'm sorry, I'm having trouble right now. Please try again in a moment."
    },
    'French': {
        'voices': {
            'male': 'fr-FR-HenriNeural',
            'female': 'fr-FR-DeniseNeural'
        },
        'default_voice': 'male',
        'error_message': "Désolé, j'ai des difficultés en ce moment. Veuillez réessayer."
    },
    'German': {
        'voices': {
            'male': 'de-DE-ConradNeural',
            'female': 'de-DE-KatjaNeural'
        },
        'default_voice': 'male',
        'error_message': 'Entschuldigung, ich habe gerade Probleme. Bitte versuchen Sie es noch einmal.'
    },
    'Italian': {
        'voices': {
            'male': 'it-IT-DiegoNeural',
            'female': 'it-IT-ElsaNeural'
        },
        'default_voice': 'male',
        'error_message': 'Mi dispiace, sto avendo problemi in questo momento. Per favore riprova.'
    },
    'Portuguese': {
        'voices': {
            'male': 'pt-BR-AntonioNeural',
            'female': 'pt-BR-FranciscaNeural'
        },
        'default_voice': 'male',
        'error_message': 'Desculpe, estou tendo problemas no momento. Por favor, tente novamente.'
    },
    'Russian': {
        'voices': {
            'male': 'ru-RU-DmitryNeural',
            'female': 'ru-RU-SvetlanaNeural'
        },
        'default_voice': 'male',
        'error_message': 'Извините, у меня сейчас проблемы. Пожалуйста, попробуйте еще раз.'
    },
    'Chinese': {
        'voices': {
            'male': 'zh-CN-YunxiNeural',
            'female': 'zh-CN-XiaoxiaoNeural'
        },
        'default_voice': 'male',
        'error_message': '对不起，我现在遇到了问题。请稍后再试。'
    },
    'Japanese': {
        'voices': {
            'male': 'ja-JP-KeitaNeural',
            'female': 'ja-JP-NanamiNeural'
        },
        'default_voice': 'male',
        'error_message': '申し訳ありません、現在問題が発生しています。もう一度お試しください。'
    },
    'Korean': {
        'voices': {
            'male': 'ko-KR-InJoonNeural',
            'female': 'ko-KR-SunHiNeural'
        },
        'default_voice': 'male',
        'error_message': '죄송합니다, 지금 문제가 있습니다. 다시 시도해 주세요.'
    },
    'Arabic': {
        'voices': {
            'male': 'ar-SA-HamedNeural',
            'female': 'ar-SA-ZariyahNeural'
        },
        'default_voice': 'male',
        'error_message': 'آسف، أواجه مشكلة الآن. يرجى المحاولة مرة أخرى.'
    },
    'Hindi': {
        'voices': {
            'male': 'hi-IN-MadhurNeural',
            'female': 'hi-IN-SwaraNeural'
        },
        'default_voice': 'male',
        'error_message': 'क्षमा करें, मुझे अभी समस्या हो रही है। कृपया फिर से प्रयास करें।'
    }
}

# Single pause pattern for all languages (can be customized later)
PAUSE_PATTERN = {
    'sentence': 300,     # After . ! ?
    'comma': 150,        # After ,
    'semicolon': 200     # After ;
}

def get_voice_name(language, voice_type='default'):
    """
    Get Azure voice name for a language and type.
    
    Args:
        language (str): The language name (e.g., 'Spanish', 'English')
        voice_type (str): Either 'male', 'female', or 'default'
    
    Returns:
        str: Azure voice name
    """
    lang_config = LANGUAGE_CONFIG.get(language, LANGUAGE_CONFIG['English'])
    
    if voice_type == 'default':
        voice_type = lang_config['default_voice']
    
    voices = lang_config['voices']
    return voices.get(voice_type, voices[lang_config['default_voice']])

def get_pause_durations():
    """
    Get pause durations in milliseconds.
    
    Returns:
        dict: Pause durations for different punctuation
    """
    return PAUSE_PATTERN.copy()

def get_error_message(language):
    """
    Get localized error message for a language.
    
    Args:
        language (str): The language name
    
    Returns:
        str: Error message in the specified language
    """
    lang_config = LANGUAGE_CONFIG.get(language, LANGUAGE_CONFIG['English'])
    return lang_config['error_message']

def get_supported_languages():
    """
    Get list of all supported languages.
    
    Returns:
        list: List of language names
    """
    return list(LANGUAGE_CONFIG.keys())

def get_voices_for_language(language):
    """
    Get all available voices for a language.
    
    Args:
        language (str): The language name
    
    Returns:
        dict: Dictionary of voice types and their Azure voice names
    """
    lang_config = LANGUAGE_CONFIG.get(language, LANGUAGE_CONFIG['English'])
    return lang_config['voices'].copy()
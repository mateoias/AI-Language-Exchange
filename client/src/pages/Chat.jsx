import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { getGreeting, getPlaceholder, getErrorMessage } from '../config/LanguageConfig'
import '../styles/AudioRecorder.css'

function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [audioSpeed, setAudioSpeed] = useState(0.8)
  const [playingAudioId, setPlayingAudioId] = useState(null)
  const [isTranscribing, setIsTranscribing] = useState(false)
  
  // New audio recording states
  const [isRecording, setIsRecording] = useState(false)
  const [recordingDuration, setRecordingDuration] = useState(0)
  const [transcriptionComplete, setTranscriptionComplete] = useState(false)
  const [inputMode, setInputMode] = useState('text');

  const { user } = useAuth()
  const audioRefs = useRef({})
  const currentAudioRef = useRef(null)
  const currentQueueIndexRef = useRef(-1)
  const isProcessingQueueRef = useRef(false)

  // Audio recording refs
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const recordingIntervalRef = useRef(null)

  const [audioQueue, setAudioQueue] = useState([])
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(-1)
  const [isProcessingQueue, setIsProcessingQueue] = useState(false)
  const audioQueueRef = useRef([])

  const [isStartingNewSession, setIsStartingNewSession] = useState(false)
  const [isSavingConversation, setIsSavingConversation] = useState(false)
  // Load chat history when component mounts
  useEffect(() => {
    loadChatHistory()
  }, [])

  // Send initial greeting only after history is loaded and if no messages exist
  useEffect(() => {
    if (user && historyLoaded && messages.length === 0 && !loading) {
      const timer = setTimeout(() => {
        sendInitialGreeting()
      }, 100)
      
      return () => clearTimeout(timer)
    }
  }, [user, historyLoaded, messages.length, loading])
useEffect(() => {
  // Focus input after any message changes
  const input = document.querySelector('.chat-input input');
  if (input && !isRecording && !loading) {
    input.focus();
  }
}, [messages, isRecording, loading]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    const messagesContainer = document.querySelector('.chat-messages')
    if (messagesContainer) {
      setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight
      }, 50)
    }
  }, [messages])

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause()
        currentAudioRef.current = null
      }
      // Cleanup recording
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop()
      }
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current)
      }
    }
  }, [])

  useEffect(() => {
    // Auto-focus input when component mounts
    const input = document.querySelector('.chat-input input');
    if (input) {
      input.focus();
    }
  }, []);

  // Audio Recording Functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      mediaRecorderRef.current = new MediaRecorder(stream)
      audioChunksRef.current = []
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        stream.getTracks().forEach(track => track.stop())
        
        // Handle the recorded audio
        await handleAudioRecording(audioBlob)
      }
      
      mediaRecorderRef.current.start()
      setIsRecording(true)
      setRecordingDuration(0)
      
      // Start duration counter
      recordingIntervalRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1)
      }, 1000)
      
    } catch (err) {
      console.error('Failed to start recording:', err)
      setError('Failed to access microphone. Please check permissions.')
      setTimeout(() => setError(''), 3000)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current)
        recordingIntervalRef.current = null
      }
    }
  }

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  const formatRecordingDuration = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const loadChatHistory = async () => {
    try {
      const history = await api.getChatHistory()
      if (history.messages && history.messages.length > 0) {
        setMessages(history.messages)
      }
      setHistoryLoaded(true)
    } catch (err) {
      console.error('Failed to load chat history:', err)
      setHistoryLoaded(true)
    }
  }

  const sendInitialGreeting = async () => {
    if (!user) return
    const greetingMessage = getGreeting(user.learningLanguage, user.username)
    
    // Generate audio for greeting
    try {
      const audioResponse = await api.regenerateAudio(
        greetingMessage,
        user.learningLanguage,
        audioSpeed
      )
      
      const botMessage = {
        id: `greeting-${Date.now()}`,
        content: greetingMessage,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        intent: 'chat',
        audio_language: user.learningLanguage,
        audio_data: audioResponse.audio_data
      }
      
      setMessages([botMessage])
      
      // Play the greeting audio automatically
      setTimeout(() => playAudio(botMessage.id, audioResponse.audio_data), 100)
      
    } catch (err) {
      console.error('Failed to generate greeting audio:', err)
      // If audio fails, still show the message
      const botMessage = {
        id: `greeting-${Date.now()}`,
        content: greetingMessage,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        intent: 'chat',
        audio_language: user.learningLanguage
      }
      setMessages([botMessage])
    }
  }


const handleFinishAndSave = async () => {
  if (isSavingConversation) return; // Prevent double-clicks
  
  setIsSavingConversation(true);
  setError('Saving conversation, please wait...');
  
  try {
    const response = await api.finalizeConversation();
    
    if (response.success) {
      // Clear messages and reset state
      setMessages([]);
      setHistoryLoaded(false);
      
      // Show success message with summary info
      const messageCount = response.message_count || 0;
      setError(`Conversation saved successfully! ${messageCount} messages saved.`);
      setTimeout(() => setError(''), 4000);
    } else {
      setError(response.message || 'No active conversation to save');
      setTimeout(() => setError(''), 3000);
    }
  } catch (error) {
    console.error('Error saving conversation:', error);
    setError('Failed to save conversation. Please try again.');
    setTimeout(() => setError(''), 3000);
  } finally {
    setIsSavingConversation(false);
  }
};

    const handleLogout = async () => {
      try {
        setError('Logging out...');
        
        // Stop any playing audio
        stopAudio();
        
        // Clear local state
        setMessages([]);
        audioRefs.current = {};
        
        // Call logout API (this would also clear the conversation on server)
        await api.logout();
        
        // Clear local storage
        localStorage.removeItem('token');
        
        // Redirect to login or trigger app state change
        window.location.reload(); // Simple approach, or use your app's navigation
        
      } catch (error) {
        console.error('Logout error:', error);
        // Even if API fails, still clear local data
        localStorage.removeItem('token');
        window.location.reload();
      }
    };


  const playAudio = (messageId, audioData) => {
    // Stop any currently playing audio
    if (currentAudioRef.current) {
      currentAudioRef.current.pause()
      setPlayingAudioId(null)
    }

    if (!audioData) return

    try {
      // Create audio element if it doesn't exist
      if (!audioRefs.current[messageId]) {
        const audio = new Audio(`data:audio/mp3;base64,${audioData}`)
        audioRefs.current[messageId] = audio
        
        // Set up event listeners
        audio.addEventListener('ended', () => {
          setPlayingAudioId(null)
          currentAudioRef.current = null
        })
        
        audio.addEventListener('error', (e) => {
          console.error('Audio playback error:', e)
          setPlayingAudioId(null)
          currentAudioRef.current = null
          
          // Show user-friendly error
          setError('Audio playback failed. Please try again.')
          setTimeout(() => setError(''), 3000)
        })
      }

      // Play the audio
      const audio = audioRefs.current[messageId]
      currentAudioRef.current = audio
      setPlayingAudioId(messageId)
      audio.play().catch(err => {
        console.error('Failed to play audio:', err)
        setPlayingAudioId(null)
      })
      
    } catch (err) {
      console.error('Audio setup error:', err)
    }
  }

  // Audio Queue Management functions (keeping existing functionality)
  const processAudioQueue = () => {
    console.log('[DEBUG] processAudioQueue called, currentIndex:', currentQueueIndexRef.current, 'queueLength:', audioQueueRef.current.length, 'isProcessing:', isProcessingQueueRef.current)
    
    if (audioQueueRef.current.length === 0) {
      console.log('[DEBUG] Queue is empty, stopping')
      isProcessingQueueRef.current = false
      setIsProcessingQueue(false)
      currentQueueIndexRef.current = -1
      setCurrentSegmentIndex(-1)
      return
    }
    
    if (!isProcessingQueueRef.current) {
      console.log('[DEBUG] Queue processing stopped, aborting')
      return
    }
    
    if (currentQueueIndexRef.current >= audioQueueRef.current.length - 1) {
      console.log('[DEBUG] Reached end of queue, stopping')
      isProcessingQueueRef.current = false
      setIsProcessingQueue(false)
      currentQueueIndexRef.current = -1
      setCurrentSegmentIndex(-1)
      return
    }

    currentQueueIndexRef.current += 1
    const nextIndex = currentQueueIndexRef.current
    setCurrentSegmentIndex(nextIndex)
    
    console.log('[DEBUG] Moving to segment:', nextIndex, 'of', audioQueueRef.current.length)
    
    const segment = audioQueueRef.current[nextIndex]
    console.log('[DEBUG] Processing segment:', segment.type, 'hasAudio:', !!segment.audio_data)
    
    if (segment.audio_data) {
      const delay = nextIndex === 0 ? 0 : 800
      
      console.log('[DEBUG] Scheduling segment playback with delay:', delay)
      setTimeout(() => {
        playSegmentAudio(segment, nextIndex)
      }, delay)
    } else {
      console.log('[DEBUG] No audio for segment, moving to next')
      processAudioQueue()
    }
  }

  const playSegmentAudio = (segment, segmentIndex) => {
    console.log('[DEBUG] playSegmentAudio called for segment:', segment.type, 'index:', segmentIndex, 'isProcessing:', isProcessingQueueRef.current, 'currentIndex:', currentQueueIndexRef.current)
    
    if (!isProcessingQueueRef.current) {
      console.log('[DEBUG] Queue processing stopped, aborting playback')
      return
    }
    
    if (currentQueueIndexRef.current !== segmentIndex) {
      console.log('[DEBUG] Index mismatch, aborting playback. Expected:', currentQueueIndexRef.current, 'Got:', segmentIndex)
      return
    }
    
    if (currentAudioRef.current) {
      console.log('[DEBUG] Stopping previous audio')
      currentAudioRef.current.pause()
      currentAudioRef.current = null
      setPlayingAudioId(null)
    }

    if (!segment.audio_data) {
      console.log('[DEBUG] No audio data for segment:', segment.type)
      processAudioQueue()
      return
    }

    try {
      const segmentId = `segment-${segment.type}-${segmentIndex}-${Date.now()}`
      console.log('[DEBUG] Creating audio element with ID:', segmentId)
      
      const audio = new Audio(`data:audio/mp3;base64,${segment.audio_data}`)
      currentAudioRef.current = audio
      setPlayingAudioId(segmentId)
      
      const onEnded = () => {
        console.log('[DEBUG] Audio ended for segment:', segment.type, 'index:', segmentIndex)
        
        if (currentAudioRef.current === audio) {
          setPlayingAudioId(null)
          currentAudioRef.current = null
          
          if (isProcessingQueueRef.current) {
            console.log('[DEBUG] Moving to next segment after audio ended')
            setTimeout(() => {
              processAudioQueue()
            }, 100)
          } else {
            console.log('[DEBUG] Queue processing stopped, not continuing')
          }
        }
      }
      
      const onError = (e) => {
        console.error('[DEBUG] Audio error for segment:', segment.type, 'error:', e)
        
        if (currentAudioRef.current === audio) {
          setPlayingAudioId(null)
          currentAudioRef.current = null
          
          if (isProcessingQueueRef.current) {
            setTimeout(() => {
              processAudioQueue()
            }, 100)
          }
        }
      }
      
      audio.addEventListener('ended', onEnded, { once: true })
      audio.addEventListener('error', onError, { once: true })
      
      console.log('[DEBUG] Starting audio playback for:', segment.type)
      audio.play().catch(err => {
        console.error('[DEBUG] Failed to play segment audio:', err)
        onError(err)
      })
      
    } catch (err) {
      console.error('[DEBUG] Audio setup error:', err)
      setTimeout(() => {
        processAudioQueue()
      }, 100)
    }
  }

  const startAudioQueue = (segments) => {
    console.log('[DEBUG] startAudioQueue called with segments:', segments.length)
    console.log('[DEBUG] Segments details:', segments.map(s => ({ type: s.type, hasAudio: !!s.audio_data })))
    
    stopAudio()
    
    audioQueueRef.current = segments
    currentQueueIndexRef.current = -1
    isProcessingQueueRef.current = true
    
    setCurrentSegmentIndex(-1)
    setIsProcessingQueue(true)
    
    console.log('[DEBUG] Queue initialized, starting processing...')
    
    setTimeout(() => {
      console.log('[DEBUG] Starting queue processing...')
      processAudioQueue()
    }, 50)
  }

  const stopAudio = () => {
    console.log('[DEBUG] stopAudio called')
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause()
      currentAudioRef.current.currentTime = 0
      currentAudioRef.current = null
    }
    
    isProcessingQueueRef.current = false
    currentQueueIndexRef.current = -1
    audioQueueRef.current = []
    
    setIsProcessingQueue(false)
    setPlayingAudioId(null)
    setCurrentSegmentIndex(-1)
    
    console.log('[DEBUG] All audio stopped and queue cleared')
  }

  const regenerateAudioWithNewSpeed = async (message) => {
    try {
      stopAudio()
      
      const response = await api.regenerateAudio(
        message.content,
        message.audio_language,
        audioSpeed
      )

      if (response.audio_data) {
        setMessages(prev => prev.map(msg => 
          msg.id === message.id 
            ? { ...msg, audio_data: response.audio_data }
            : msg
        ))
        
        if (audioRefs.current[message.id]) {
          delete audioRefs.current[message.id]
        }
        
        playAudio(message.id, response.audio_data)
      }
    } catch (err) {
      console.error('Failed to regenerate audio:', err)
    }
  }

const isProcessingRef = useRef(false);
const handleAudioRecording = async (audioBlob) => {
  if (isProcessingRef.current) return;
  isProcessingRef.current = true;

  setIsTranscribing(true);

  try {
    const languageMap = {
      Spanish: 'es', French: 'fr', German: 'de', Italian: 'it',
      Portuguese: 'pt', Russian: 'ru', Chinese: 'zh',
      Japanese: 'ja', Korean: 'ko', Arabic: 'ar', Hindi: 'hi',
    };
    const languageCode = languageMap[user.learningLanguage] || null;

    const transcription = await api.transcribeAudio(audioBlob, languageCode);

    if (!transcription?.text) {
      throw new Error('Empty transcription'); // defensive catch
    }

    setInput(prev => prev ? prev + ' ' + transcription.text : transcription.text);
    setInputMode('text');
    setError(''); // ✅ Clear only after success

  } catch (err) {
    console.error('Transcription error:', err);
    setError('Failed to transcribe audio. Please try again.');
  } finally {
    setIsTranscribing(false);
    isProcessingRef.current = false;
  }
};



  const handleSpeedChange = async (e) => {
    const newSpeed = parseFloat(e.target.value)
    console.log('[DEBUG] Speed dropdown changed to', newSpeed)
    setAudioSpeed(newSpeed)
    
    const lastBotMessage = messages
      .filter(msg => msg.sender === 'bot' && msg.audio_data)
      .pop()
    
    if (lastBotMessage) {
      console.log('[DEBUG] Found message to regenerate:', lastBotMessage.id)
      
      try {
        const response = await api.regenerateAudio(
          lastBotMessage.content,
          lastBotMessage.audio_language,
          newSpeed
        )
        
        console.log('[DEBUG] Got new audio response')
        
        if (response.audio_data) {
          setMessages(prev => prev.map(msg => 
            msg.id === lastBotMessage.id 
              ? { ...msg, audio_data: response.audio_data }
              : msg
          ))
          
          if (audioRefs.current[lastBotMessage.id]) {
            delete audioRefs.current[lastBotMessage.id]
          }
          
          stopAudio()
          setTimeout(() => {
            playAudio(lastBotMessage.id, response.audio_data)
          }, 100)
        }
      } catch (err) {
        console.error('[DEBUG] Failed to regenerate audio:', err)
      }
    }
  }

const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setError('')
    setLoading(true)

    const userMessageId = Date.now()
    const newUserMessage = {
      id: userMessageId,
      content: userMessage,
      sender: 'user',
      timestamp: new Date().toISOString(),
      audio_language: user.learningLanguage
    }
    setMessages(prev => [...prev, newUserMessage])

    try {
      const response = await api.sendChatMessage(userMessage, audioSpeed)
      
      console.log('[DEBUG] Full response received:', response)
      
      if (response.segments) {
        console.log('[DEBUG] Processing segments:', response.segments.length)
        
        const segments = response.segments
        
        // Log all segments for debugging
        segments.forEach((seg, idx) => {
          console.log(`[DEBUG] Segment ${idx}:`, {
            type: seg.type,
            text: seg.text,
            hasAudio: !!seg.audio_data,
            persona: seg.persona
          })
        })
        
        if (response.user_audio_data) {
          setMessages(prev => prev.map(msg => 
            msg.id === userMessageId 
              ? { ...msg, audio_data: response.user_audio_data }
              : msg
          ))
        }
        
        const botMessages = []
        
        // Process ALL segment types in order
        segments.forEach((segment, index) => {
          if (segment && segment.text) {
            console.log(`[DEBUG] Adding ${segment.type} segment with persona ${segment.persona}`)
            
            const messageId = `${segment.type}-${Date.now()}-${index}`
            const message = {
              id: messageId,
              content: segment.text,
              sender: 'bot',
              timestamp: new Date().toISOString(),
              message_type: segment.type,
              audio_data: segment.audio_data,
              audio_language: segment.persona === 'teacher' ? user.nativeLanguage : response.audio_language,
              persona: segment.persona || 'partner'
            }
            
            botMessages.push(message)
          }
        })
        
        console.log('[DEBUG] Total bot messages to add:', botMessages.length)
        
        setMessages(prev => {
          const newMessages = [...prev, ...botMessages]
          console.log('[DEBUG] Messages state updated, total messages:', newMessages.length)
          return newMessages
        })
        
        // Play audio for segments that have it
        const audioSegments = segments.filter(s => s.audio_data)
        console.log('[DEBUG] Audio segments found:', audioSegments.length)
        
        audioSegments.forEach((seg, idx) => {
          console.log(`[DEBUG] Audio segment ${idx}:`, {
            type: seg.type,
            hasAudio: !!seg.audio_data,
            audioLength: seg.audio_data ? seg.audio_data.length : 0
          })
        })
        
        if (audioSegments.length > 0) {
          console.log('[DEBUG] Starting audio queue with delay...')
          setTimeout(() => {
            console.log('[DEBUG] Actually starting audio queue now')
            startAudioQueue(audioSegments)
          }, 100)
        } else {
          console.log('[DEBUG] No audio segments to play')
        }
        
      } else {
        console.log('[DEBUG] Using fallback for old response format')
        const botMessage = {
          id: Date.now() + 1,
          content: response.response,
          sender: 'bot',
          timestamp: new Date().toISOString(),
          intent: response.intent,
          audio_language: response.audio_language,
          audio_data: response.audio_data
        }
        
        setMessages(prev => [...prev, botMessage])
        
        if (response.audio_data) {
          setTimeout(() => playAudio(botMessage.id, response.audio_data), 100)
        }
      }
      
    } catch (err) {
      console.error('[DEBUG] Chat error:', err)
      setError('Failed to send message. Please try again.')
      
      setMessages(prev => prev.filter(msg => msg.id !== userMessageId))
    } finally {
      setLoading(false)
    }
  }

  const startNewSession = async () => {
  if (isStartingNewSession) return; // Prevent double-clicks
  
  setIsStartingNewSession(true);
  setError('Clearing conversation, please wait...');
  
  try {
    stopAudio();
    
    // Clear audio refs
    audioRefs.current = {};
    
    // Call API to start new session
    await api.startNewChatSession();
    
    // Clear local state
    setMessages([]);
    setError('');
    setHistoryLoaded(false);
    
    // Show brief success message
    setError('New conversation started');
    setTimeout(() => setError(''), 2000);
    
    // Load new greeting after a short delay
    setTimeout(() => {
      if (user) {
        sendInitialGreeting();
      }
    }, 500);
    
  } catch (err) {
    console.error('Failed to start new session:', err);
    setError('Failed to start new conversation. Please try again.');
    setTimeout(() => setError(''), 3000);
  } finally {
    setIsStartingNewSession(false);
  }
};


  if (!user) {
    return <div className="page-content">Loading...</div>
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div>
          <h2>Practice {user.learningLanguage}</h2>
          <p>Your AI language partner is ready to help!</p>
        </div>
        <div className="chat-controls">
          <div className="speed-control">
            <label>Speed:</label>
            <select 
              value={audioSpeed} 
              onChange={handleSpeedChange}
              className="speed-selector"
            >
              <option value={0.5}>50%</option>
              <option value={0.6}>60%</option>
              <option value={0.7}>70%</option>
              <option value={0.8}>80%</option>
              <option value={0.9}>90%</option>
              <option value={1.0}>100%</option>
              <option value={1.2}>120%</option>
            </select>
          </div>
          <div className="session-controls">
            {messages.length > 0 ? (
              <>
                <button 
                  className="start-new-btn"
                  onClick={startNewSession}
                  disabled={loading || isStartingNewSession || isSavingConversation}
                  title="Start new conversation without saving"
                >
                  {isStartingNewSession ? 'Clearing...' : 'Start New'}
                </button>
                <button 
                  className="finish-save-btn"
                  onClick={handleFinishAndSave}
                  disabled={loading || isStartingNewSession || isSavingConversation}
                  title="Save conversation and start new"
                >
                  {isSavingConversation ? 'Saving...' : 'Finish & Save'}
                </button>
              </>
            ) : (
              <button 
                className="new-session-btn"
                onClick={startNewSession}
                disabled={loading || isStartingNewSession}
              >
                {isStartingNewSession ? 'Starting...' : 'New Conversation'}
              </button>
            )}
          </div>
         </div>
      </div>

      {error && (
        <div className="chat-error">
          {error}
        </div>
      )}
      
      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.sender} ${message.message_type || ''} ${message.persona || ''}`}>
            <div className="message-bubble">
              {message.message_type === 'rephrase' && (
                <span className="message-type-indicator">👩‍🏫 </span>
              )}
              {message.message_type === 'help' && (
                <span className="message-type-indicator">👩‍🏫 </span>
              )}
              {message.content}
              {message.audio_data && (
                <button
                  className={`audio-btn ${playingAudioId === message.id ? 'playing' : ''}`}
                  onClick={() => {
                    if (playingAudioId === message.id) {
                      stopAudio()
                    } else {
                      setIsProcessingQueue(false)
                      playAudio(message.id, message.audio_data)
                    }
                  }}
                  title={playingAudioId === message.id ? 'Stop' : 'Play audio'}
                  disabled={isProcessingQueue && !playingAudioId?.includes(message.id)}
                >
                  {playingAudioId === message.id ? '⏸️' : '🔊'}
                </button>
              )}
              {!message.audio_data && message.audio_language && (
                <button
                  className="audio-btn regenerate"
                  onClick={() => regenerateAudioWithNewSpeed(message)}
                  title="Generate audio"
                >
                  🔄
                </button>
              )}
            </div>
          </div>
        ))}

        {isProcessingQueue && (
          <div className="audio-queue-indicator">
            <span className="queue-dot"></span>
            Playing audio sequence...
          </div>
        )}
        
        {loading && (
          <div className="message bot">
            <div className="message-bubble typing">
              Thinking...
            </div>
          </div>
        )}
      </div>
      
      <form className="chat-input" onSubmit={sendMessage}>
        <div className={`input-wrapper ${isRecording ? 'recording' : ''} ${transcriptionComplete ? 'transcription-complete' : ''}`}>
          <button
            type="button"
            className={`microphone-btn ${isRecording ? 'recording' : ''}`}
            onClick={toggleRecording}
            disabled={loading || isTranscribing}
            title={isRecording ? 'Stop recording' : 'Start recording'}
          >
            {isRecording ? '⏹️' : '🎤'}
          </button>
          
          <input
            type="text"
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              // Clear transcription success state when user types
              if (transcriptionComplete) {
                setTranscriptionComplete(false)
              }
            }}
            placeholder={
              isTranscribing 
                ? 'Transcribing...' 
                : isRecording 
                  ? `Recording... ${formatRecordingDuration(recordingDuration)}`
                  : getPlaceholder(user.learningLanguage, user.nativeLanguage)
            }
            disabled={loading || isTranscribing}
            className={isRecording ? 'recording' : ''}
          />
          
          {(isTranscribing || isRecording || transcriptionComplete) && (
            <div className="recording-indicator">
              {isTranscribing && <span className="transcribing-text">🔄</span>}
              {isRecording && <span className="recording-pulse">🔴</span>}
              {transcriptionComplete && <span className="transcription-success">✅</span>}
            </div>
          )}
        </div>
        
        <button type="submit" disabled={loading || !input.trim() || isRecording}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  )
}

export default Chat
import { useState, useRef, useEffect } from 'react'

function AudioRecorder({ onRecordingComplete, disabled }) {
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioLevel, setAudioLevel] = useState(0)
  const [error, setError] = useState('')
  
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const timerRef = useRef(null)
  const streamRef = useRef(null)
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const animationFrameRef = useRef(null)

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      stopRecording()
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  const startRecording = async () => {
    try {
      setError('')
      
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,  // Mono
          sampleRate: 16000,  // 16kHz
          echoCancellation: true,
          noiseSuppression: true
        } 
      })
      
      streamRef.current = stream

      // Set up audio level monitoring
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
      analyserRef.current = audioContextRef.current.createAnalyser()
      const source = audioContextRef.current.createMediaStreamSource(stream)
      source.connect(analyserRef.current)
      analyserRef.current.fftSize = 256
      
      // Start monitoring audio levels
      monitorAudioLevel()

      // Create MediaRecorder with WebM/Opus
      const options = {
        mimeType: 'audio/webm;codecs=opus'
      }
      
      // Fallback for browsers that don't support WebM/Opus
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'audio/webm'
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
          options.mimeType = 'audio/mp4'
        }
      }

      mediaRecorderRef.current = new MediaRecorder(stream, options)
      audioChunksRef.current = []

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: options.mimeType })
        onRecordingComplete(audioBlob)
        cleanupRecording()
      }

      // Start recording
      mediaRecorderRef.current.start()
      setIsRecording(true)
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          // Stop at 60 seconds
          if (prev >= 59) {
            stopRecording()
            return 60
          }
          return prev + 1
        })
      }, 1000)

    } catch (err) {
      console.error('Error starting recording:', err)
      if (err.name === 'NotAllowedError') {
        setError('Microphone permission denied')
      } else if (err.name === 'NotFoundError') {
        setError('No microphone found')
      } else {
        setError('Failed to start recording')
      }
      cleanupRecording()
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const cleanupRecording = () => {
    // Stop all tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }

    // Clear timer
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    // Cancel animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }

    // Reset states
    setRecordingTime(0)
    setAudioLevel(0)
  }

  const monitorAudioLevel = () => {
    if (!analyserRef.current) return

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    analyserRef.current.getByteFrequencyData(dataArray)
    
    // Calculate average volume
    const average = dataArray.reduce((a, b) => a + b) / dataArray.length
    setAudioLevel(Math.min(100, (average / 128) * 100))

    if (isRecording) {
      animationFrameRef.current = requestAnimationFrame(monitorAudioLevel)
    }
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="audio-recorder">
      <button
        type="button"
        className={`record-button ${isRecording ? 'recording' : ''}`}
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled}
        title={isRecording ? 'Stop recording' : 'Start recording'}
      >
        {isRecording ? (
          <span className="stop-icon">⏹️</span>
        ) : (
          <span className="mic-icon">🎤</span>
        )}
      </button>

      {isRecording && (
        <div className="recording-indicator">
          <span className="recording-dot"></span>
          <span className="recording-time">{formatTime(recordingTime)}</span>
          <div className="audio-level" style={{ width: `${audioLevel}%` }}></div>
        </div>
      )}

      {error && (
        <div className="recording-error">
          {error}
        </div>
      )}
    </div>
  )
}

export default AudioRecorder
import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

function Personalization() {
  const [formData, setFormData] = useState({
    name: '',
    nationality: '',
    currentLocation: '',
    workStudy: '',
    freeTime: '',
    travelDestinations: '',
    favoriteActivities: '',
    familyFriends: '',
    pets: '',
    hobbies: ''
  })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  
  const { user, updatePersonalization, deletePersonalization } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (user?.personalization) {
      setFormData({
        name: user.personalization.name || '',
        nationality: user.personalization.nationality || '',
        currentLocation: user.personalization.currentLocation || '',
        workStudy: user.personalization.workStudy || '',
        freeTime: user.personalization.freeTime || '',
        travelDestinations: user.personalization.travelDestinations || '',
        favoriteActivities: user.personalization.favoriteActivities || '',
        familyFriends: user.personalization.familyFriends || '',
        pets: user.personalization.pets || '',
        hobbies: user.personalization.hobbies || ''
      })
    }
  }, [user])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      await updatePersonalization(formData)
      setMessage('Settings saved successfully!')
      setTimeout(() => navigate('/'), 2000)
    } catch (err) {
      setMessage('Error saving settings: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete all personalization data?')) {
      setLoading(true)
      try {
        await deletePersonalization()
        setMessage('Personalization data deleted')
        setFormData({
          name: '',
          nationality: '',
          currentLocation: '',
          workStudy: '',
          freeTime: '',
          travelDestinations: '',
          favoriteActivities: '',
          familyFriends: '',
          pets: '',
          hobbies: ''
        })
      } catch (err) {
        setMessage('Error deleting data: ' + err.message)
      } finally {
        setLoading(false)
      }
    }
  }

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <div className="page-content">
      <div className="personalization-container">
        <h1>Personalize Your Experience</h1>
        
        <div className="personalization-intro">
          <p>
            If we have some basic information about you we will be able to personalize 
            our conversation more quickly and our conversations will be more interesting 
            and easier to remember. Please answer some or all of the following questions 
            briefly. We will add more information as the chat progresses.
          </p>
          <p className="reminder">
            <strong>Just a reminder:</strong> You can change or delete your personal 
            information at any time. Also, it doesn't have to be true! It's just 
            something we can talk about, so if you want a pet alligator.......
          </p>
        </div>
        
        {message && <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>{message}</div>}
        
        <form onSubmit={handleSubmit} className="personalization-form">
          <div className="form-group">
            <label>What should I call you?</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Your preferred name"
            />
          </div>

          <div className="form-group">
            <label>What's your nationality?</label>
            <input
              type="text"
              name="nationality"
              value={formData.nationality}
              onChange={handleChange}
              placeholder="e.g., American, Brazilian, Japanese"
            />
          </div>

          <div className="form-group">
            <label>Where do you currently live?</label>
            <input
              type="text"
              name="currentLocation"
              value={formData.currentLocation}
              onChange={handleChange}
              placeholder="City, country or region"
            />
          </div>

          <div className="form-group">
            <label>What do you do for work or study?</label>
            <input
              type="text"
              name="workStudy"
              value={formData.workStudy}
              onChange={handleChange}
              placeholder="Job, studies, or main activity"
            />
          </div>

          <div className="form-group">
            <label>How do you like to spend your free time?</label>
            <textarea
              name="freeTime"
              value={formData.freeTime}
              onChange={handleChange}
              placeholder="Activities you enjoy in your spare time"
              rows="2"
            />
          </div>

          <div className="form-group">
            <label>Any places you'd like to travel to or have visited?</label>
            <input
              type="text"
              name="travelDestinations"
              value={formData.travelDestinations}
              onChange={handleChange}
              placeholder="Dream destinations or favorite places"
            />
          </div>

          <div className="form-group">
            <label>What are some of your favorite activities?</label>
            <input
              type="text"
              name="favoriteActivities"
              value={formData.favoriteActivities}
              onChange={handleChange}
              placeholder="Sports, hobbies, entertainment you enjoy"
            />
          </div>

          <div className="form-group">
            <label>Tell me about your family or friends</label>
            <textarea
              name="familyFriends"
              value={formData.familyFriends}
              onChange={handleChange}
              placeholder="Family members, close friends, or people important to you"
              rows="2"
            />
          </div>

          <div className="form-group">
            <label>Do you have any pets?</label>
            <input
              type="text"
              name="pets"
              value={formData.pets}
              onChange={handleChange}
              placeholder="Real or imaginary pets (alligators welcome!)"
            />
          </div>

          <div className="form-group">
            <label>Any other hobbies or interests?</label>
            <textarea
              name="hobbies"
              value={formData.hobbies}
              onChange={handleChange}
              placeholder="Anything else you're passionate about"
              rows="2"
            />
          </div>

          <div className="form-actions">
            <button type="submit" disabled={loading} className="save-btn">
              {loading ? 'Saving...' : 'Save Information'}
            </button>
            
            <button type="button" onClick={() => navigate('/')} className="skip-btn">
              Skip for Now
            </button>
            
            {user?.personalization && (
              <button type="button" onClick={handleDelete} className="delete-btn">
                Delete All Information
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}

export default Personalization
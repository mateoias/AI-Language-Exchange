import { Link } from 'react-router-dom'

function About() {
  return (
    <div className="page-content">
      <div className="about-page">
        {/* Hero Section */}
        <div className="about-hero">
          <h1>About Language Exchange AI</h1>
          <p className="hero-subtitle">Revolutionizing language learning through personalized AI conversation practice</p>
        </div>

        <div className="about-content">
          {/* About the Author */}
          <section className="about-section">
            <h2>About the Author</h2>
            <p>
              Welcome to the computer assisted language learning website. My name is <strong>Matthew Werth</strong> 
              and I have been a language teacher for many years. Currently I am working on 
              a number of automated tools to make life easier for language teachers and language learners.
            </p>
            <p>
              This tool is an automated language exchange chatbot for students who want to practice their 
              language skills, it is divided into three levels with fine tuned prompts to make language 
              learning easier. The guiding philosophy is <strong>CI with TPRS</strong>, especially at the lower levels.
            </p>
          </section>

          {/* Learning Levels */}
          <section className="about-section">
            <h2>Learning Levels</h2>
            <div className="levels-grid">
              <div className="level-card">
                <div className="level-header">
                  <span className="level-badge beginner">Beginner</span>
                  <h3>Starting Out</h3>
                </div>
                <p>
                  This section is designed for users who are just starting out. This is the hardest part for an AI 
                  powered chatbot and it is still under construction.
                </p>
                <Link to="/beginner" className="level-link">Learn More →</Link>
              </div>

              <div className="level-card">
                <div className="level-header">
                  <span className="level-badge intermediate">Intermediate</span>
                  <h3>Building Skills</h3>
                </div>
                <p>
                  For learners who can hold a basic conversation. This section is fine tuned to help your listening ability 
                  and grammar knowledge. It limits vocabulary and focuses on letting you achieve 90% comprehension so that 
                  you can internalize grammatical structures.
                </p>
                <Link to="/intermediate" className="level-link">Learn More →</Link>
              </div>

              <div className="level-card">
                <div className="level-header">
                  <span className="level-badge advanced">Advanced</span>
                  <h3>Mastering Fluency</h3>
                </div>
                <p>
                  Aimed at users with solid speaking skills, this is the easiest type of language learning to automate.
                  It is a sampling of prompts to make sure that you focus on language learning with minimal friction.
                </p>
                <Link to="/advanced" className="level-link">Learn More →</Link>
              </div>
            </div>
          </section>

          {/* Technology Section */}
          <section className="about-section">
            <h2>About the Language Exchange Chatbot</h2>
            <p>
              The chatbot is powered by <a href="https://openai.com/api/" target="_blank" rel="noreferrer" className="external-link">OpenAI</a>, 
              this is a wrapper for the GPT 4.0 model that has been optimized for conversation 
              based on the level that you choose.
            </p>

            <div className="info-box">
              <h3>Important Notes</h3>
              <ul>
                <li>The model responses are usually factually accurate, but there is no guarantee and that isn't important for language learning</li>
                <li>GPT hallucinates sometimes, so if the conversation gets too weird, just change the topic and carry on</li>
                <li>You, the human, are ultimately responsible for what happens in these conversations, chatGPT is generally
                eager to please, so it's easy to get it to say weird and/or unsavory things, but that's usually because
                the computer thinks that what you wanted based on your side of the text.</li>
              </ul>
            </div>
          </section>

          {/* Contact Section */}
          <section className="about-section contact-section">
            <h2>Get in Touch</h2>
            <p>
              Feel free to contact me with any comments or suggestions:
            </p>
            <a 
              href="mailto:mateoias@hotmail.com" 
              target="_blank" 
              rel="noopener noreferrer"
              className="contact-btn"
            >
              📧 Send Email
            </a>
          </section>
        </div>
      </div>
    </div>
  )
}

export default About
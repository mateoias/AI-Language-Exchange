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
              Welcome to the computer assisted language learning website. My name is <strong>Matthew Werth </strong> 
               and I have been a language teacher for many years. I have lived and taught English in America, 
               Mexico and Taiwan and I enjoy learning new languages. Currently I am working on 
              automated tools to make life easier for language teachers and language learners, mostly for my own benefit,
              but I hope that they will also be useful to others. Feel free to try them out and let me know if you have any suggestions!
            </p>
            <p>
              This tool is an automated language exchange chatbot for students who want to practice their 
              language skills, it is divided into three levels with fine tuned prompts to make language 
              learning easier. The guiding philosophy is <strong>CI, </strong> Comprehensible Input, with <strong>TPRS, </strong> 
              Total Proficiency through Reading and Storytelling, especially at the lower levels.
            </p>
          </section>
                  <br />      
          {/* Learning Levels */}
          <section className="about-section">
            <h2>Learning Levels</h2>
            <div className="levels-grid">
              <div className="level-card">
                <div className="level-header">
                  <span className="level-badge beginner">Beginner</span>
                </div>
                <p>
                  This section is designed for users who are just starting out in a language. The beinning level requires 
                  the most direct teacher guidance so it is the hardest for a chatbot to do. The focus is on TPRS, maintaining 
                  a very limited vocabulary of high frequency words so that the learner can understand from keywords and context. This allows the grammar of the
                  language to slowly sink in and be acquired. I recommend using a lower speed setting and replaying the audio multiple times.
                </p>
                <Link to="/beginner" className="level-link">Learn More →</Link>
              </div>
                  <br />
              <div className="level-card">
                <div className="level-header">
                  <span className="level-badge intermediate">Intermediate</span>
                </div>
                <p>
                  This section is for learners who can hold a basic conversation.  It is fine tuned to help your listening ability 
                  and help you acquire grammar knowledge. It limits vocabulary and focuses on letting you achieve maximum comprehension, so
                  that you can internalize grammatical structures.It does however also start to introduce new vocabulary relevant to your interests.
                  This is the section I have done the most work on as it is relevant for my current interests and it is relatively easy for the
                  chatbot to do.
                </p>
                <Link to="/intermediate" className="level-link">Learn More →</Link>
              </div>            
                  <br />
              <div className="level-card">
                <div className="level-header">
                  <span className="level-badge advanced">Advanced</span>
                </div>
                <p>
                  This section is aimed at users with solid speaking skills, and it is the easiest type of language learning to automate.
                  For the most part you can directly cgat with the bot and I have simply added some prompts to help the conversatoin stay on track.
                  It will also allow you to take your conversation and turn it into a story with relevant vocabukary notes for extra practice --under construction--.
                </p>
                <Link to="/advanced" className="level-link">Learn More →</Link>
              </div> 
            </div>
          </section>               
                  <br />
          {/* Technology Section */}
          <section className="about-section">
            <h2>About the Language Exchange Chatbot</h2>
            <p>
              The chatbot is powered by <a href="https://openai.com/api/" target="_blank" rel="noreferrer" className="external-link">OpenAI, </a> 
              Basically the app is a wrapper for the GPT 4.0 model that has been optimized for conversation based on the level that you choose. 
              Audio is currently provided by Microsoft Azure text to speech. The database is maintained on a Neo4j instance as I have been experimenting
              with different ways to model the learner's current understanding of a language -- For more information, check out our <Link to="/faqs">FAQs - Interlanguage</Link>             
            </p>
                  <br />      
            <div className="info-box">
              <h2>Important Notes</h2>
              <ul>
                <li>The model responses are usually factually accurate, but there is no guarantee of that, and it isn't important for language learning. 
                  The language you see will be correct and that's what you need to learn.</li>
                <li>chatGPT hallucinates sometimes, so if the conversation gets too weird, just change the topic and carry on.</li>
                <li>You, the human, are ultimately responsible for what happens in these conversations, chatGPT is generally
                eager to please, so it's easy to get it to say weird and/or unsavory things; it's also easy to get it to talk about your personal intersts.</li>
                <li>The system is designed to remember your personal information, which helps to personalize the conversation and make it more interesting.
                   If you are not comfortable with that, you can delete or change the model's knowledge base in settings, or just lie.
                   Language class is where you get to claim to be a prince from an exotic country and to have a pet alligator, what happens with chatGPT stays with chatGPT!</li>
                <li>Finally, I'm a language teacher who likes technology, not a cybersecuity expert. I personally won't use your data in any way,
                  but I can't promise that foreign hackers, internet trolls or your cousin Ned won't try to crash the system and steal your profile.
                </li>

              </ul>
            </div>
          </section>
                  <br />      
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
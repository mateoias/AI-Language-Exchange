import { Link } from 'react-router-dom'

function Beginner() {
  return (
    <div className="methodology-page">
      <div className="methodology-hero">
        <h1>Beginner Level</h1>
        <p className="hero-subtitle">Building foundations through comprehensible input and storytelling</p>
      </div>

      <div className="methodology-content">
        <section className="methodology-section">
          <h2>How We Teach Beginners</h2>
          <p>
            At the beginner level, we use <strong>Comprehensible Input (CI)</strong> and <strong>Teaching Proficiency through Reading and Storytelling (TPRS)</strong> to create a natural, stress-free learning environment. Instead of memorizing grammar rules, you'll acquire language the same way children do - through meaningful stories and conversations.
          </p>
          
          <div className="methodology-principles">
            <div className="principle">
              <h3>🎭 Story-Based Learning</h3>
              <p>Every conversation revolves around interesting, personalized stories that keep you engaged while naturally repeating high-frequency vocabulary.</p>
            </div>
            <div className="principle">
              <h3>🎯 Comprehensible Input</h3>
              <p>Our AI tutor carefully adjusts language complexity to stay just within your understanding - challenging but never overwhelming.</p>
            </div>
            <div className="principle">
              <h3>🔄 Natural Repetition</h3>
              <p>Key words and structures are repeated naturally through the story, helping them stick without boring drill exercises.</p>
            </div>
          </div>
        </section>

        <section className="methodology-section">
          <h2>What a Conversation Looks Like</h2>
          <div className="conversation-example">
            <div className="conversation-intro">
              <p><em>Here's how our AI tutor might introduce the concept of "family" in Spanish:</em></p>
            </div>
            
            <div className="conversation-flow">
              <div className="message tutor">
                <strong>AI Tutor:</strong> ¡Hola María! Hay una familia muy interesante. La familia tiene un papá, una mamá y dos hijos. ¿Tu familia tiene dos hijos también?
              </div>
              <div className="message-note">
                <em>Notice: Simple present tense, high-frequency words (family, father, mother, children), and a personal question to keep you engaged.</em>
              </div>
              
              <div className="message student">
                <strong>You:</strong> No, mi familia tiene tres hijos.
              </div>
              
              <div className="message tutor">
                <strong>AI Tutor:</strong> ¡Qué interesante! Tres hijos. En esta familia hay dos hijos: un hijo se llama Carlos y una hija se llama Ana. Carlos tiene 15 años. ¿Cuántos años tienes tú?
              </div>
              <div className="message-note">
                <em>Natural repetition of "hijos" (children) and introduction of ages - still comprehensible and personally relevant.</em>
              </div>
            </div>
          </div>
        </section>

        <section className="methodology-section">
          <h2>Why This Works</h2>
          <p>
            Research shows that language acquisition happens best when learners receive comprehensible input in low-stress environments (Krashen, 1982). TPRS methodology has been proven effective in numerous studies, showing faster vocabulary acquisition and better retention compared to traditional grammar-based methods (Ray & Seely, 2015).
          </p>
          
          <div className="benefits-grid">
            <div className="benefit">
              <h4>🧠 Natural Acquisition</h4>
              <p>Your brain processes language naturally, like learning your first language</p>
            </div>
            <div className="benefit">
              <h4>😌 Low Stress</h4>
              <p>No pressure to produce perfect grammar - focus on communication</p>
            </div>
            <div className="benefit">
              <h4>🎯 Personalized</h4>
              <p>Stories adapt to your interests and life, making learning relevant</p>
            </div>
            <div className="benefit">
              <h4>⚡ Faster Progress</h4>
              <p>Acquire vocabulary 3x faster than traditional methods</p>
            </div>
          </div>
        </section>

        <section className="methodology-section">
          <h2>Ready to Start?</h2>
          <p>
            Experience beginner-level TPRS for yourself. Our AI tutor will adapt to your pace and interests, creating engaging stories that help you naturally acquire your target language.
          </p>
          
          <div className="cta-section">
            <Link to="/signup" className="cta-button primary">Try Beginner Level</Link>
            <Link to="/intermediate" className="cta-button secondary">Explore Intermediate</Link>
          </div>
        </section>

        <section className="references">
          <h3>References</h3>
          <ul>
            <li>Krashen, S. (1982). <em>Principles and Practice in Second Language Acquisition</em>. Oxford: Pergamon Press.</li>
            <li>Ray, B. & Seely, C. (2015). <em>Fluency Through TPR Storytelling</em>. Command Performance Language Institute.</li>
          </ul>
        </section>
      </div>
    </div>
  )
}

export default Beginner
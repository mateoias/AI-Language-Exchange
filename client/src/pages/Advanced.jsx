import { Link } from 'react-router-dom'

function Advanced() {
  return (
    <div className="methodology-page">
      <div className="methodology-hero">
        <h1>Advanced Level</h1>
        <p className="hero-subtitle">Mastering nuance through sophisticated discourse and cultural immersion</p>
      </div>

      <div className="methodology-content">
        <section className="methodology-section">
          <h2>How We Teach Advanced Learners</h2>
          <p>
            At the advanced level, TPRS evolves into sophisticated discourse analysis and cultural immersion. While maintaining comprehensible input principles, we explore abstract concepts, nuanced expressions, and professional communication through rich, multi-layered narratives that challenge your analytical and creative thinking.
          </p>
          
          <div className="methodology-principles">
            <div className="principle">
              <h3>🎓 Abstract Concepts</h3>
              <p>Explore complex ideas like philosophy, ethics, and theoretical concepts through engaging storytelling frameworks.</p>
            </div>
            <div className="principle">
              <h3>💼 Professional Discourse</h3>
              <p>Master workplace communication, academic writing, and formal presentations through realistic scenarios.</p>
            </div>
            <div className="principle">
              <h3>🎨 Cultural Nuance</h3>
              <p>Navigate subtle cultural differences, humor, and idiomatic expressions with native-like precision.</p>
            </div>
          </div>
        </section>

        <section className="methodology-section">
          <h2>What a Conversation Looks Like</h2>
          <div className="conversation-example">
            <div className="conversation-intro">
              <p><em>Here's how our AI tutor might facilitate a philosophical discussion in Spanish:</em></p>
            </div>
            
            <div className="conversation-flow">
              <div className="message tutor">
                <strong>AI Tutor:</strong> Imagínate que Roberto, un filósofo contemporáneo, se encontró con un dilema ético fascinante. Durante una conferencia sobre inteligencia artificial, alguien le preguntó: "¿Puede una máquina realmente comprender el sufrimiento humano, o simplemente simula comprensión?" ¿Qué crees que contestó Roberto? Y más importante, ¿cuál sería tu respuesta?
              </div>
              <div className="message-note">
                <em>Notice: Complex subjunctive mood, philosophical vocabulary, and open-ended critical thinking prompts.</em>
              </div>
              
              <div className="message student">
                <strong>You:</strong> Creo que Roberto habría dicho que la comprensión requiere experiencia subjetiva, algo que las máquinas no pueden tener.
              </div>
              
              <div className="message tutor">
                <strong>AI Tutor:</strong> ¡Qué perspectiva tan profunda! Roberto efectivamente argumentó algo similar, pero añadió una paradoja interesante: "Si una máquina pudiera convencernos completamente de que comprende nuestro dolor, ¿importaría realmente si esa comprensión es 'auténtica'?" ¿Cómo reconciliarías esta paradoja con tu punto de vista anterior?
              </div>
              <div className="message-note">
                <em>Building complex argumentation skills while maintaining natural conversation flow and personal engagement.</em>
              </div>
            </div>
          </div>
        </section>

        <section className="methodology-section">
          <h2>Advanced CI Theory and Application</h2>
          <p>
            Advanced comprehensible input focuses on the acquisition of sophisticated discourse markers, pragmatic competence, and register variation (Swain & Lapkin, 2013). Our approach integrates cognitive academic language proficiency (CALP) development with continued emphasis on meaningful communication, ensuring learners can navigate both social and academic contexts with native-like competence.
          </p>
          
          <div className="benefits-grid">
            <div className="benefit">
              <h4>🧠 Critical Thinking</h4>
              <p>Analyze complex topics and form sophisticated arguments</p>
            </div>
            <div className="benefit">
              <h4>🎯 Pragmatic Competence</h4>
              <p>Master subtle social cues and contextually appropriate language</p>
            </div>
            <div className="benefit">
              <h4>📝 Academic Proficiency</h4>
              <p>Produce native-like academic and professional writing</p>
            </div>
            <div className="benefit">
              <h4>🌐 Cultural Insider</h4>
              <p>Understand humor, irony, and cultural references naturally</p>
            </div>
          </div>
        </section>

        <section className="methodology-section">
          <h2>Achieve Native-Like Proficiency</h2>
          <p>
            Experience the pinnacle of TPRS methodology with advanced-level conversations that challenge your intellect while honoring comprehensible input principles. Our AI tutor will guide you through sophisticated discussions that prepare you for any academic, professional, or social situation.
          </p>
          
          <div className="cta-section">
            <Link to="/signup" className="cta-button primary">Try Advanced Level</Link>
            <div className="level-nav">
              <Link to="/intermediate" className="cta-button secondary">← Intermediate</Link>
              <Link to="/about" className="cta-button secondary">Learn More</Link>
            </div>
          </div>
        </section>

        <section className="references">
          <h3>References</h3>
          <ul>
            <li>Swain, M. & Lapkin, S. (2013). A Vygotskian sociocultural perspective on immersion education. <em>Journal of Immersion and Content-Based Language Education</em>, 1(1), 101-129.</li>
            <li>Cummins, J. (2008). BICS and CALP: Empirical and theoretical status of the distinction. <em>Encyclopedia of Language and Education</em>, 2, 71-83.</li>
            <li>Mason, B. & Krashen, S. (2017). Self-selected reading and TPRS/CI: How they can work together. <em>International Journal of Foreign Language Teaching</em>, 12(1), 2-8.</li>
          </ul>
        </section>
      </div>
    </div>
  )
}

export default Advanced
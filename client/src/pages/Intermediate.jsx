import { Link } from 'react-router-dom'

function Intermediate() {
  return (
    <div className="methodology-page">
      <div className="methodology-hero">
        <h1>Intermediate Level</h1>
        <p className="hero-subtitle">Expanding fluency through complex narratives and authentic scenarios</p>
      </div>

      <div className="methodology-content">
        <section className="methodology-section">
          <h2>How We Teach Intermediate Learners</h2>
          <p>
            At the intermediate level, we build on your foundation with more sophisticated stories and real-world scenarios. Our approach continues to emphasize <strong>comprehensible input</strong> while gradually increasing complexity. You'll engage with longer narratives, multiple timeframes, and authentic cultural situations.
          </p>
          
          <div className="methodology-principles">
            <div className="principle">
              <h3>📚 Complex Narratives</h3>
              <p>Stories become multi-layered with subplots, character development, and cultural contexts that deepen your understanding.</p>
            </div>
            <div className="principle">
              <h3>🌍 Authentic Scenarios</h3>
              <p>Practice real-world situations like job interviews, travel planning, and social interactions through guided storytelling.</p>
            </div>
            <div className="principle">
              <h3>⏰ Multiple Time Frames</h3>
              <p>Naturally acquire past and future tenses through stories that move between different time periods.</p>
            </div>
          </div>
        </section>

        <section className="methodology-section">
          <h2>What a Conversation Looks Like</h2>
          <div className="conversation-example">
            <div className="conversation-intro">
              <p><em>Here's how our AI tutor might guide you through a travel scenario in French:</em></p>
            </div>
            
            <div className="conversation-flow">
              <div className="message tutor">
                <strong>AI Tutor:</strong> Sophie avait planifié son voyage à Paris depuis des mois. Hier, elle a finalement acheté son billet d'avion. Demain, elle fera ses valises. Dis-moi, quand tu voyages, qu'est-ce que tu mets toujours dans ta valise?
              </div>
              <div className="message-note">
                <em>Notice: Past perfect, simple past, and future tenses woven naturally into the story, plus a personal connection.</em>
              </div>
              
              <div className="message student">
                <strong>You:</strong> Je mets toujours mon téléphone et mes médicaments.
              </div>
              
              <div className="message tutor">
                <strong>AI Tutor:</strong> C'est très pratique! Sophie aussi a mis son téléphone dans sa valise, mais elle a oublié quelque chose d'important à l'aéroport. Devine ce qu'elle a oublié? Et raconte-moi une fois où tu as oublié quelque chose en voyageant.
              </div>
              <div className="message-note">
                <em>Past tense reinforcement through narrative suspense, encouraging both prediction and personal sharing.</em>
              </div>
            </div>
          </div>
        </section>

        <section className="methodology-section">
          <h2>The Science Behind Intermediate CI</h2>
          <p>
            At the intermediate level, your brain is ready for more complex input while still benefiting from the scaffolding that CI provides. Research by VanPatten (2003) shows that learners at this stage process meaning and form simultaneously when input is carefully calibrated. Our AI tutor uses this principle to introduce advanced structures naturally within compelling contexts.
          </p>
          
          <div className="benefits-grid">
            <div className="benefit">
              <h4>🎭 Contextual Grammar</h4>
              <p>Complex structures emerge naturally from meaningful stories</p>
            </div>
            <div className="benefit">
              <h4>🗣️ Fluency Development</h4>
              <p>Practice connected discourse and longer conversations</p>
            </div>
            <div className="benefit">
              <h4>🎨 Cultural Competence</h4>
              <p>Navigate authentic cultural situations with confidence</p>
            </div>
            <div className="benefit">
              <h4>🔄 Automatic Processing</h4>
              <p>Language becomes more intuitive and less effortful</p>
            </div>
          </div>
        </section>

        <section className="methodology-section">
          <h2>Ready to Advance?</h2>
          <p>
            Take your language skills to the next level with intermediate TPRS. Our AI tutor will challenge you with richer stories and authentic scenarios while maintaining the comprehensible input that makes learning natural and enjoyable.
          </p>
          
          <div className="cta-section">
            <Link to="/signup" className="cta-button primary">Try Intermediate Level</Link>
            <div className="level-nav">
              <Link to="/beginner" className="cta-button secondary">← Beginner</Link>
              <Link to="/advanced" className="cta-button secondary">Advanced →</Link>
            </div>
          </div>
        </section>

        <section className="references">
          <h3>References</h3>
          <ul>
            <li>VanPatten, B. (2003). <em>From Input to Output: A Teacher's Guide to Second Language Acquisition</em>. McGraw-Hill.</li>
            <li>Krashen, S. & Mason, B. (2020). The optimal input hypothesis: Not all comprehensible input is of equal value. <em>TESOL Journal</em>, 11(4).</li>
          </ul>
        </section>
      </div>
    </div>
  )
}

export default Intermediate
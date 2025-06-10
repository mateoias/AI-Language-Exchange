import { useState } from 'react'

function FAQs() {
  const [openIndex, setOpenIndex] = useState(null)

  const faqs = [
    {
      question: "How does the AI language chatbot work?",
      answer: "Our AI chatbot uses GPT-4 technology to provide conversational practice in your target language. It adapts to your level and provides natural, contextual responses to help you improve your speaking skills."
    },
    {
      question: "What languages are currently supported?",
      answer: "We currently support Chinese, English, French, German, Italian, and Spanish. We're continuously working to add more languages based on user demand."
    },
    {
      question: "What's the difference between the three levels?",
      answer: "Beginner level uses simple vocabulary and basic grammar structures. Intermediate level introduces more complex sentences and everyday topics. Advanced level provides near-native conversations with sophisticated vocabulary and cultural nuances."
    },
    {
      question: "Is this suitable for complete beginners?",
      answer: "While our beginner level is designed to be as accessible as possible, having some basic knowledge of the language (alphabet, basic greetings) will help you get the most out of the experience."
    },
    {
      question: "Why does the conversation sometimes get creepy or strange?",
      answer: "ChatGPT is designed to follow your lead, so if the conversation takes an unexpected turn, it's usually because you've steered it that way, either unintentionally or intentionally. ChatGPT doesn't have its own agenda. It just does what you ask. And remember, you can always reset the conversation with the reset button and start over fresh!"
    },
    {
      question: "What can I do if I don't like the way the conversation is going?",
      answer: "The app is pretty good at understanding what you're trying to do, and it's designed to guess what you need. You can control the direction of the conversation more by clearly setting your intentions or asking for specific conversation types. If you want to switch things up, just let it know—like, 'I want to practice the past tense,' or 'I'm talking about my sister, not my brother.' If you're clear, the app will adjust and help keep the conversation going the way you want."
    },
    {
      question: "Is my conversation data saved?",
      answer: "Conversations are saved only for the duration of your session. When you log out or reset the chat, your conversation history is cleared to protect your privacy."
    },
    {
      question: "Can I use this on mobile devices?",
      answer: "Yes! Our website is fully responsive and works on smartphones and tablets. Simply access it through your mobile browser."
    },
    {
      question: "What teaching methodology do you use?",
      answer: "We follow the Comprehensible Input (CI) approach with TPRS (Teaching Proficiency through Reading and Storytelling), especially at lower levels. This ensures you understand 90% of the content while learning new structures naturally."
    },
    {
      question: "How do I report issues or suggest improvements?",
      answer: "You can email us at mateoias@hotmail.com with any feedback, bug reports, or feature suggestions. We value user input and use it to improve the platform."
    }
  ]

  const toggleFAQ = (index) => {
    setOpenIndex(openIndex === index ? null : index)
  }

  return (
    <div className="page-content">
      <div className="faqs-page">
        <div className="faqs-hero">
          <h1>Frequently Asked Questions</h1>
          <p className="faqs-intro">
            Find answers to common questions about our AI-powered language learning platform.
          </p>
        </div>

        <div className="faqs-container">
          {faqs.map((faq, index) => (
            <div key={index} className="faq-item">
              <button
                className={`faq-question ${openIndex === index ? 'active' : ''}`}
                onClick={() => toggleFAQ(index)}
              >
                <span>{faq.question}</span>
                <span className="faq-icon">{openIndex === index ? '−' : '+'}</span>
              </button>
              {openIndex === index && (
                <div className="faq-answer">
                  <p>{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="faqs-footer">
          <h2>Still have questions?</h2>
          <p>
            Feel free to reach out to us at{' '}
            <a href="mailto:mateoias@hotmail.com">mateoias@hotmail.com</a>
          </p>
        </div>
      </div>
    </div>
  )
}

export default FAQs
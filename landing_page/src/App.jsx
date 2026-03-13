import React from 'react'
import Header from './components/Header'
import Hero from './components/Hero'
import Services from './components/Services'
import Footer from './components/Footer'
import Medibot from './components/Medibot'

function App() {
  return (
    <div className="min-h-screen bg-white">
      <Header />
      <main>
        <Hero />
        <Services />
        {/* Additional sections can be added here */}
      </main>
      <Footer />
      <Medibot />
    </div>
  )
}

export default App

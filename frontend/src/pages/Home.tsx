import Nav from '../components/Nav'
import ScrollHero from '../components/ScrollHero'
import Showcase from '../components/Showcase'
import Services from '../components/Services'
import Footer from '../components/Footer'

export default function Home() {
  return (
    <>
      <Nav />
      <main>
        <ScrollHero />
        <Showcase />
        <Services />
      </main>
      <Footer />
    </>
  )
}

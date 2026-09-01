import { useEffect, useState } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { getReviews } from '../api/reviews'
import StarIcon from './StarIcon'
import type { Review } from '../types/api'
import './Testimonials.css'

const MAX_QUOTES = 3

export default function Testimonials() {
  const [reviews, setReviews] = useState<Review[] | null>(null)
  const reducedMotion = useReducedMotion()

  useEffect(() => {
    getReviews()
      .then((data) => setReviews(data.filter((review) => review.comment.trim().length > 0)))
      .catch(() => setReviews([]))
  }, [])

  if (!reviews || reviews.length === 0) {
    return null
  }

  const quotes = reviews.slice(0, MAX_QUOTES)

  return (
    <section className="testimonials">
      <motion.div
        className="testimonials__header"
        initial={reducedMotion ? {} : { opacity: 0, y: 24 }}
        whileInView={reducedMotion ? {} : { opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.4 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      >
        <span className="testimonials__eyebrow">Lo que dicen</span>
        <h2 className="testimonials__headline">Voces de quienes ya vivieron Lirios.</h2>
      </motion.div>

      <div className="testimonials__grid">
        {quotes.map((review, i) => (
          <motion.figure
            key={review.id}
            className="testimonials__quote"
            initial={reducedMotion ? {} : { opacity: 0, y: 32 }}
            whileInView={reducedMotion ? {} : { opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: i * 0.1 }}
          >
            <div className="testimonials__stars" aria-label={`${review.rating} de 5 estrellas`}>
              {[1, 2, 3, 4, 5].map((star) => (
                <StarIcon key={star} filled={star <= review.rating} />
              ))}
            </div>
            <blockquote className="testimonials__quote-text">"{review.comment}"</blockquote>
            <figcaption className="testimonials__attribution">— {review.reviewer_name}</figcaption>
          </motion.figure>
        ))}
      </div>
    </section>
  )
}

import { useState } from 'react'
import type { FormEvent } from 'react'
import { submitReview } from '../api/appointments'
import { getErrorMessage } from '../api/errors'
import Button from './Button'
import StarIcon from './StarIcon'
import type { Appointment, ReviewStatus } from '../types/api'
import '../components/booking/BookingSteps.css'
import './ReviewForm.css'

interface ReviewFormProps {
  accessToken: string
  appointment: Appointment
  onSubmitted: (appointment: Appointment) => void
}

const STATUS_LABELS: Record<ReviewStatus, string> = {
  pending: 'Pendiente de aprobación',
  approved: 'Publicada',
  rejected: 'No publicada',
}

export default function ReviewForm({ accessToken, appointment, onSubmitted }: ReviewFormProps) {
  const [rating, setRating] = useState(5)
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (appointment.review) {
    const { rating: savedRating, comment: savedComment, status } = appointment.review
    return (
      <div className="review-form review-form--submitted">
        <span className="review-form__label">Tu reseña</span>
        <div className="review-form__stars" aria-label={`${savedRating} de 5 estrellas`}>
          {[1, 2, 3, 4, 5].map((star) => (
            <StarIcon key={star} filled={star <= savedRating} size={18} />
          ))}
        </div>
        {savedComment && <p className="review-form__comment">{savedComment}</p>}
        <span className="review-form__status">{STATUS_LABELS[status]}</span>
      </div>
    )
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const updated = await submitReview(accessToken, { rating, comment })
      onSubmitted(updated)
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="review-form" onSubmit={handleSubmit}>
      <span className="review-form__label">Deja tu reseña</span>
      <div className="review-form__star-picker" role="radiogroup" aria-label="Calificación">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            role="radio"
            aria-checked={star === rating}
            aria-label={`${star} de 5 estrellas`}
            className="review-form__star-button"
            onClick={() => setRating(star)}
          >
            <StarIcon filled={star <= rating} size={22} />
          </button>
        ))}
      </div>

      <div className="booking-step__field">
        <label htmlFor="review_comment">Comentario (opcional)</label>
        <textarea
          id="review_comment"
          rows={3}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
      </div>

      {error && <p className="booking-step__status booking-step__status--error">{error}</p>}

      <Button variant="solid" type="submit" disabled={submitting}>
        {submitting ? 'Enviando…' : 'Enviar reseña'}
      </Button>
    </form>
  )
}

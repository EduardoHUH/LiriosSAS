# Lirios

Booking website and admin panel for a beauty salon in Honduras (makeup, nails and lashes).

Customers can browse services, pick an open time slot and book without creating an account. They get an email with a private link where they can check, reschedule or cancel their appointment, and leave a review once it's done. The salon manages everything else from an admin panel: services and prices, opening hours, days off, the photo gallery, reviews, and a dashboard with income and service stats.

The site is in Spanish and prices are in Honduran lempiras.

## Stack

- **Backend:** Python 3.13, Django 5.2, Django REST Framework, MySQL
- **Frontend:** React 19, TypeScript, Vite, React Router
- **Auth:** JWT for staff (SimpleJWT). Customers don't have accounts; each booking has its own access link.
- **Email:** SendGrid through django-anymail. Without an API key, emails are printed to the console.

## What it does

**Customers**
- Browse services by category, with price and duration
- Book in four steps: service, date and time, contact info, review
- Only free slots are shown, based on opening hours, special dates, blocked time and existing bookings
- Manage the booking from the emailed link: view, reschedule once, or cancel before the deadline
- Leave a review after the appointment is completed
- Gallery of the salon's work, filterable by category

**Salon staff**
- Dashboard with today's appointments, the next 7 days, monthly income, completed and cancelled appointments
- Income over time (by day, week or month) and the most booked services
- Confirm, complete, reschedule or cancel appointments, and mark no-shows
- Approve or reject reviews before they go public
- Edit services, categories, hours, closed days and booking rules (notice time, cancellation window, etc.)

The React staff panel covers the dashboard and analytics. The rest is done through Django's admin for now, and all of it is also available in the API.

There's no online payment. Customers pay at the salon and staff confirm the booking.

## A few things worth knowing

- **Double booking can't happen.** Every booking or reschedule locks a single row in the database first, so two people trying to grab the same slot at the same time can't both succeed. There's a test that fires 8 requests at once to check this.
- **The backend decides what's available.** The frontend only shows what the API returns, and the slot is checked again right before the booking is saved.
- **Business rules live in the database**, not in the code. Cancellation deadline, minimum notice, how far ahead people can book and the gap between appointments can all be changed from the admin without a deploy.
- Public endpoints are rate limited, and private notes on customers and appointments never show up in the public API.

## Running it locally

You'll need Python 3.13, Node 20 or newer, and MySQL 8.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # on Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create an empty MySQL database (utf8mb4), then copy `.env.example` to `.env` and fill in your database user and password. Generate a secret key with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API runs at `http://localhost:8000/api/v1/` and the Django admin at `http://localhost:8000/admin/`.

Heads up: on a fresh database there are no opening hours, so no slots will show up. Log into `/admin/`, add the business hours and at least one service, and the booking page will start working.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:5173`. The staff panel is at `/admin` and uses the account you created with `createsuperuser`.

### Appointment reminders

Reminder emails are sent by a management command. Nothing runs it automatically, so in production it needs a cron job:

```bash
python manage.py send_appointment_reminders
```

## Tests

```bash
# backend
cd backend
pytest
pytest --cov=. --cov-report=term-missing   # with coverage

# frontend
cd frontend
npm test
npm run test:coverage
```

## Project layout

```
backend/
  config/          settings and main urls
  accounts/        staff login and password reset
  catalog/         services and categories
  scheduling/      opening hours, special dates, blocked time, availability
  appointments/    bookings and their status flow
  customers/       customer records
  reviews/         reviews and moderation
  gallery/         photo gallery
  notifications/   emails and the reminder command
  core/            business settings, dashboard and analytics

frontend/src/
  pages/           public pages (home, services, booking, gallery, manage booking)
  components/      shared UI and the booking steps
  admin/           staff panel (login, overview, analytics)
  api/             API calls
```

## Deploying

Not deployed yet. The plan is Railway for the backend and MySQL, and Vercel for the frontend. Production settings (HTTPS redirect, secure cookies, HSTS) turn on automatically when `DJANGO_DEBUG=False`. Static files are served with WhiteNoise. Uploaded photos are saved to `backend/media/`, so the host needs a persistent volume there or they'll be lost on every redeploy.

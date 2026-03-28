# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Persistent SQLite storage for activities, users, and requests

## Getting Started

1. Install the dependencies:

   ```
   pip install -r ../requirements.txt
   ```

2. Run the application:

   ```
   uvicorn app:app --reload
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Data is stored in SQLite at `src/data/school.db`, so it survives server restarts.

The schema includes:

1. **users**
   - `email` (PK)
   - `role` (`student` or `admin`)

2. **activities**
   - `id` (PK)
   - `name` (unique)
   - `description`
   - `schedule`
   - `max_participants`

3. **activity_participants**
   - `(activity_id, user_email)` as composite PK
   - Tracks signups

4. **membership_requests** and **event_requests**
   - Request tables for upcoming workflow features

## Migration and Seed Strategy

- On app startup, schema migrations run with `CREATE TABLE IF NOT EXISTS`.
- If there are no activities yet, the app seeds default activities and participants.
- To reset local DB state, delete `src/data/school.db` and restart the app.

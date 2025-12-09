# Medication Reminder Schedule Guide

## Overview

The MediGenius system allows patients to set medication reminders that will send email notifications at scheduled times.

## How to Create a Medication Reminder Schedule

### Step 1: Access Your Prescriptions

1. Log in to the system as a **patient**
2. Navigate to **"Prescriptions"** from the header menu
3. You'll see all prescriptions assigned to you by doctors

### Step 2: Set a Reminder

1. Find the prescription you want to set a reminder for
2. Click the **"Set Reminder"** button (bell icon) on the prescription card
3. A modal window will open

### Step 3: Fill in Reminder Details

In the reminder modal, provide:

- **Medication Name** (required)
  - Pre-filled from your prescription
  - You can edit if needed
- **Reminder Time** (required)

  - Select the time you want to be reminded
  - Format: HH:MM (24-hour format)
  - Example: 09:00, 14:30, 20:00

- **Frequency** (optional, defaults to Daily)
  - **Daily**: Reminder every day at the specified time
  - **Twice Daily**: Reminder twice per day (morning and evening)
  - **Three Times Daily**: Reminder three times per day
  - **Weekly**: Reminder once per week

### Step 4: Submit

Click **"Set Reminder"** to save your schedule.

## How It Works

### Email Notifications

- The system checks for due reminders **every minute**
- When it's time for your medication, you'll receive an email with:
  - Medication name
  - Dosage information
  - Instructions from your prescription
  - Reminder to take your medicine

### Reminder Schedule

- Reminders are sent at the exact time you specified
- Each reminder is sent only once per day (prevents duplicates)
- The system tracks when reminders were last sent

## Managing Your Reminders

### View All Reminders

- Navigate to **"Medication Reminders"** from the patient menu
- View all your active reminders
- See medication names, times, and frequencies

### Delete a Reminder

1. Go to **"Medication Reminders"** page
2. Find the reminder you want to delete
3. Click the delete button
4. Confirm deletion

## API Usage (For Developers)

### Create a Reminder

```http
POST /api/reminders
Content-Type: application/json
Authorization: Required (patient role)

{
  "prescription_id": 1,
  "medication_name": "Paracetamol 500mg",
  "reminder_time": "09:00",
  "frequency": "daily"
}
```

### Get All Reminders

```http
GET /api/reminders
Authorization: Required (patient role)
```

### Delete a Reminder

```http
DELETE /api/reminders/<reminder_id>
Authorization: Required (patient role)
```

## Email Configuration

To receive email reminders, configure your email settings in `.env`:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
```

**Note for Gmail users:**

- You need to use an **App Password**, not your regular password
- Enable 2-factor authentication
- Generate an app password from: https://myaccount.google.com/apppasswords

## Example Scenarios

### Scenario 1: Daily Morning Medication

- **Medication**: Vitamin D 1000 IU
- **Time**: 08:00
- **Frequency**: Daily
- **Result**: Email sent every day at 8:00 AM

### Scenario 2: Twice Daily Antibiotic

- **Medication**: Amoxicillin 500mg
- **Time**: 08:00
- **Frequency**: Twice Daily
- **Result**: Email sent at 8:00 AM and 8:00 PM daily

### Scenario 3: Weekly Medication

- **Medication**: Weekly Vitamin B12 injection
- **Time**: 10:00
- **Frequency**: Weekly
- **Result**: Email sent every week on the same day at 10:00 AM

## Troubleshooting

### Reminders Not Being Sent

1. Check your email configuration in `.env`
2. Verify your email address is correct in your user profile
3. Check the application logs for errors
4. Ensure the scheduler is running (it starts automatically)

### Can't Set Reminder

- Make sure you're logged in as a **patient** (not doctor)
- Ensure you have a valid prescription
- Check that all required fields are filled

### Email Not Received

- Check your spam/junk folder
- Verify email settings are correct
- Test email sending manually
- Check SMTP server credentials

## Technical Details

### Scheduler

- Uses **APScheduler** (Advanced Python Scheduler)
- Runs in the background
- Checks for due reminders every minute
- Automatically starts when the application starts

### Database

Reminders are stored in the `medication_reminders` table with:

- `prescription_id`: Links to prescription
- `patient_id`: Links to patient user
- `medication_name`: Name of medication
- `reminder_time`: Time to send reminder (HH:MM)
- `frequency`: How often to remind
- `is_active`: Whether reminder is active
- `last_sent`: Timestamp of last email sent

### Email Service

- Uses Python's `smtplib` for sending emails
- Supports SMTP servers (Gmail, Outlook, etc.)
- Sends HTML-formatted reminder emails
- Includes prescription details in email

## Support

If you encounter issues:

1. Check the application logs
2. Verify your email configuration
3. Ensure you have an active prescription
4. Contact support if problems persist

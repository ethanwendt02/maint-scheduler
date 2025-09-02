# 🛠️ Maintenance Scheduler (Field AI Client & Admin Portal)

A Django-based web application for managing maintenance scheduling.  
It provides **two sides**:
- **Admin Portal**: for Field AI admins to manage clients, tickets, policies, and checklists.
- **Client Portal**: for organizations working with Field AI to log in, view policies, and create support tickets.

---

## 🚀 Features
- **Authentication**
  - Admin users (superusers) access Django Admin.
  - Client users log in via a custom portal.
- **Client Portal**
  - Dashboard with policies, tickets, and contact info.
  - Create and track support tickets.
- **Admin Portal**
  - Manage organizations, policies, and tickets.
  - View and update client tickets from admin side.
- **Custom Styling**
  - Branded UI with Field AI color scheme (orange, black, white).
  - Customized Django Admin theme.

---

## 📂 Project Structure
maint-scheduler/
│
├── apps/
│ ├── accounts/ # Authentication and user accounts
│ ├── portal/ # Client-facing portal (tickets, policies)
│ ├── fleet/ # Fleet management (future extension)
│ ├── policies/ # Policies management
│ ├── workorders/ # Work orders
│ ├── checklists/ # Checklists
│ └── notifications/ # Notifications system
│
├── maint_app/ # Main project configuration
│
├── static/ # CSS, JS, images (branding and admin overrides)
├── templates/ # Shared templates (base.html, etc.)
│
├── manage.py
├── requirements.txt
└── README.md


---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/your-username/maint-scheduler.git
cd maint-scheduler

```
### 2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate

```
### 3. Install Dependencies
```bash
pip install -r requirements.txt

```
### 4. Configure Environment Variables
```bash
create a .env file in the project root:

DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-here
DATABASE_NAME=maintdb
DATABASE_USER=maintuser
DATABASE_PASSWORD=maintpass
DATABASE_HOST=127.0.0.1
DATABASE_PORT=5432

```
### 5. Run Migrations
```bash
python manage.py migrate

```
### 6. Create a Superuser (admin account)
```bash
python manage.py createsuperuser

```
### 7. Start the Development Server
```bash
python manage.py runserver

```
### 8. Running the Servers
Admin Portal: http://127.0.0.1:8000/admin/
Client Portal: http://127.0.0.1:8000/portal/


**DEPLOYMENT (UBUNTU + GUNICORN + Nginx)**

### 1. Install System Packages
```bash
sudo apt update
sudo apt install python3-pip python3-venv postgresql postgresql-contrib nginx

```
### 2. Create and Configure PostgreSQL Database
```sql
CREATE DATABASE maintdb;
CREATE USER maintuser WITH PASSWORD 'maintpass';
ALTER ROLE maintuser SET client_encoding TO 'utf8';
ALTER ROLE maintuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE maintuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE maintdb TO maintuser;

```
### 3. Run Migrations and Collect Static Files
```bash
python manage.py migrate
python manage.py collectstatic

```
### 4. Configfure Gunicorn + Nginx
```
Gunicorn runs the app (gunicorn maint_app.wsgi).

Nginx proxies requests to Gunicorn.

```
### 5. Setup a systemd service (e.g., /etc/systemd/system/maint-scheduler.service)

### 6. Enable HTTPS with Let's Encrypt if deploying publicly

**FUTURE FEATURES**

Client notifications via email.

SLA tracking inside tickets.

File attachments on tickets (implemented, but can be expanded).

Client-specific dashboards with analytics.

**DEVELOPMENT NOTES**
Built with Django 5.x

Uses PostgreSQL as the database.

UI styled with Bootstrap 5 + custom branding.

Admin customized via fieldai_admin.css.

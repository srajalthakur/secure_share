# Secure Share

A Django-based secure file sharing app with role-based access, secure email login, and modern UI.

## Features

- **Two user roles:** Ops (upload) and Client (download)
- **Secure file upload/download** (Ops uploads, Clients download via secure links)
- **Email-based login links** (no password required)
- **Role-based access control**
- **Modern, user-friendly UI**
- **Tested and production-ready**

## Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/srajalthakur/secure_share.git
   cd secure_share
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start the server:**
   ```bash
   python manage.py runserver
   ```

## Usage

- **Register as Ops or Client**
- **Ops:** Upload files (`.docx`, `.pptx`, `.xlsx`)
- **Client:** Download files via secure email links
- **Email login:** Enter your email/username, receive a secure link, and log in

## API & Testing

- API endpoints documented in the included Postman collection (`postman_collection.json`)
- Run tests:
  ```bash
  python manage.py test
  ```

## Deployment

- Use environment variables for secrets in production
- Set up a production server (e.g., Gunicorn + Nginx)
- Configure allowed hosts and email backend

## License

MIT
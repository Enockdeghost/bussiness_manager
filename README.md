# AMP ENVIRONMENTAL CLEANING AND WASTE MANAGEMENT SYSTEM  
## Technical Proposal  

**Prepared by:** Anna Mkurambe  
**Date:** February 19, 2026  
**Version:** 1.0  

---

## Table of Contents  

1. [Introduction](#1-introduction)  
   1.1 [Purpose](#11-purpose)  
   1.2 [Scope](#12-scope)  
   1.3 [Target Audience](#13-target-audience)  

2. [System Overview](#2-system-overview)  
   2.1 [Objectives](#21-objectives)  
   2.2 [Key Features](#22-key-features)  
   2.3 [User Roles](#23-user-roles)  

3. [Technical Architecture](#3-technical-architecture)  
   3.1 [Framework and Libraries](#31-framework-and-libraries)  
   3.2 [Application Structure](#32-application-structure)  
   3.3 [Database Design](#33-database-design)  
   3.4 [API Design](#34-api-design)  

4. [Module Deep Dive](#4-module-deep-dive)  
   4.1 [User Authentication & Management](#41-user-authentication--management)  
   4.2 [Project & Service Management](#42-project--service-management)  
   4.3 [Payment & Invoice Processing](#43-payment--invoice-processing)  
   4.4 [Service Request & Waste Collection Reporting](#44-service-request--waste-collection-reporting)  
   4.5 [Messaging System](#45-messaging-system)  
   4.6 [Statistics Dashboard](#46-statistics-dashboard)  
   4.7 [Invoice & Receipt Generation](#47-invoice--receipt-generation)  

5. [Security Considerations](#5-security-considerations)  
   5.1 [Authentication & Authorization](#51-authentication--authorization)  
   5.2 [Data Protection](#52-data-protection)  
   5.3 [Input Validation & Sanitization](#53-input-validation--sanitization)  
   5.4 [Error Handling & Logging](#54-error-handling--logging)  

6. [Deployment and Operations](#6-deployment-and-operations)  
   6.1 [Environment Configuration](#61-environment-configuration)  
   6.2 [Database Initialization](#62-database-initialization)  
   6.3 [Running the Application](#63-running-the-application)  

7. [Future Enhancements](#7-future-enhancements)  
   7.1 [Payment Gateway Integration](#71-payment-gateway-integration)  
   7.2 [Real-time Notifications](#72-real-time-notifications)  
   7.3 [Mobile App Integration](#73-mobile-app-integration)  
   7.4 [Advanced Analytics & Reporting](#74-advanced-analytics--reporting)  

8. [Conclusion](#8-conclusion)  

9. [Appendices](#9-appendices)  
   9.1 [Complete API Endpoint List](#91-complete-api-endpoint-list)  
   9.2 [Database Schema Diagram](#92-database-schema-diagram)  
   9.3 [Sample .env Configuration](#93-sample-env-configuration)  

---

## 1. Introduction  

### 1.1 Purpose  
This document provides a comprehensive technical proposal for the **AMP Environmental Cleaning and Waste Management System**, a web‑based application designed to manage environmental cleaning services and waste collection operations. The platform supports multiple user roles (admin, field staff, customer), handles project creation, service invoicing, waste collection requests, and internal communication.  

### 1.2 Scope  
The proposal covers the entire architecture, implementation details, security measures, and deployment guidelines for the Flask‑based application. It explains every component of the system, including models, routes, decorators, helper functions, and database initialization.  

### 1.3 Target Audience  
- **Stakeholders** seeking an overview of the system’s capabilities.  
- **Developers** who need to understand the codebase for maintenance or extension.  
- **System Administrators** responsible for deployment and operations.  

---

## 2. System Overview  

### 2.1 Objectives  
- Enable environmental service companies to create and manage cleaning projects and waste collection contracts.  
- Allow customers to request services easily via web forms or QR‑code redirection.  
- Provide a platform for citizens to report illegal dumping or request waste collection (with geolocation) and track resolution.  
- Assign tasks to field staff and monitor progress.  
- Offer administrative dashboards for real‑time statistics and user management.  

### 2.2 Key Features  
- **User Registration & Authentication** (with password hashing)  
- **Role‑Based Access Control** (admin, field staff, customer)  
- **Project & Service Management** (CRUD operations, QR code generation for site identification)  
- **Payment & Invoice Processing** (including anonymous payments and invoice generation)  
- **Service Request & Waste Collection Reporting** (geolocation, waste type, status updates)  
- **Internal Messaging System** (between users)  
- **Administrative Dashboards** (with aggregated statistics)  
- **RESTful API** for integration with external services or front‑end clients  

### 2.3 User Roles  

| Role        | Permissions                                                                                         |
|-------------|-----------------------------------------------------------------------------------------------------|
| Admin       | Full access: manage users, projects, invoices, service requests; view all data; assign field staff. |
| Field Staff | View assigned service requests, update their status, log completed work.                           |
| Customer    | Request services (logged‑in or guest), view own service history and invoices.                      |

---

## 3. Technical Architecture  

### 3.1 Framework and Libraries  
The application is built with **Python Flask**, a lightweight WSGI web framework. Key libraries include:  

- **Flask-SQLAlchemy** – ORM for database interactions.  
- **Flask-Login** – User session management.  
- **Werkzeug** – Password hashing and security utilities.  
- **PyQRCode / qrcode** – Generate QR codes for projects or sites.  
- **Python’s `secrets` module** – Cryptographically strong random tokens.  
- **Datetime & functools** – For time‑based operations and decorators.  

### 3.2 Application Structure  
The code is organized in a single file (monolithic) for simplicity, but follows a logical separation:  

1. **Configuration** – App settings, secret key, database URI.  
2. **Models** – SQLAlchemy ORM classes (`User`, `Project`, `Invoice`, `ServiceRequest`, `Message`, `PaymentRequest`).  
3. **Login Manager & Decorators** – User loader and role‑based access decorator.  
4. **Helper Functions** – `get_request_data()` to unify JSON/form data handling.  
5. **HTML Page Routes** – Render templates for user interfaces.  
6. **API Routes** – JSON endpoints for programmatic access.  
7. **Error Handlers** – Custom 404, 500, etc.  
8. **Database Initialization** – `init_db()` seeds default users and sample data.  

### 3.3 Database Design  
The database schema is relational (SQLite in development, easily switchable to PostgreSQL/MySQL).  

**Main Tables & Relationships:**  

- **users** – Stores user credentials, profile info, role, and active status.  
- **projects** – Environmental cleaning projects or service contracts with target budget, dates, and QR token.  
- **invoices** – Each invoice references a project and optionally a user. Includes status, payment method, and unique invoice ID.  
- **service_requests** – Reported waste collection or cleaning requests with geocoordinates, waste type, status, and optional assignment to field staff.  
- **messages** – Internal messaging between users.  
- **payment_requests** – (Placeholder) for future payment gateway integration.  

Relationships are defined via foreign keys and SQLAlchemy relationships (e.g., `User.invoices`).  

### 3.4 API Design  
The API follows REST conventions and responds to both JSON and traditional form submissions. The helper `get_request_data()` ensures compatibility.  

**Key Endpoint Categories:**  
- Authentication (`/api/register`, `/api/login`, `/api/logout`)  
- User management (`/api/users/<id>`)  
- Projects (`/api/projects`, `/api/projects/<id>/qr`)  
- Invoices (`/api/invoices`, `/api/invoices/<id>/pay`)  
- Service requests (`/api/service-requests`, assignment, status update)  
- Messaging (`/api/messages`, `/api/messages/<id>/read`)  
- Statistics (`/api/statistics`)  
- Invoices/Receipts (`/api/invoices/<invoice_id>`)  

All endpoints that modify data are protected by authentication and role checks where appropriate.  

---

## 4. Module Deep Dive  

### 4.1 User Authentication & Management  

**Models:**  
- `User` extends `UserMixin` for Flask‑Login compatibility.  
- Passwords are hashed using `werkzeug.security.generate_password_hash` (default: pbkdf2:sha256).  
- Fields: `username`, `email`, `full_name`, `phone`, `role`, `is_active`, password hash, password reset token/expiry.  

**Authentication Flow:**  
- `/api/register` – Accepts username, email, password, optional fields. Checks uniqueness, hashes password, stores user.  
- `/api/login` – Validates credentials, checks `is_active`, logs in user via `login_user()`. Returns JSON or redirects.  
- `/api/logout` – Logs out current user.  
- **Session Management:** Flask‑Login manages user sessions with a secure cookie.  

**Role‑Based Access Control:**  
- Custom decorator `@role_required(*roles)` checks authentication and user role.  
- Used on admin‑only routes (e.g., `/admin/dashboard`, user management endpoints).  

**Password Reset (Skeleton):**  
- Fields `reset_token` and `reset_token_expiry` exist but no routes are implemented – a placeholder for future feature.  

### 4.2 Project & Service Management  

**Model:**  
- `Project`: `name`, `description`, `budget`, `invoiced_amount`, dates, `is_active`, `qr_token`.  

**Key Features:**  
- **CRUD Operations:**  
  - `GET /api/projects` – List all projects.  
  - `POST /api/projects` (admin) – Create project; auto‑generates QR token.  
  - `PUT /api/projects/<id>` (admin) – Update project details.  
- **QR Code Generation:**  
  - `GET /api/projects/<id>/qr` – Generates QR code pointing to the service request page with token validation.  
  - QR code contains a URL like `https://.../request/<id>?qr=<token>`.  
  - Uses `qrcode` library to create PNG image, returned as file download.  
- **Invoice Integration:**  
  - Project’s `invoiced_amount` updates automatically when an invoice is paid.  

### 4.3 Payment & Invoice Processing  

**Model:**  
- `Invoice`: `reference_id` (unique), `user_id` (nullable for guests), `project_id`, `amount`, `payment_method`, `status` (pending/paid/rejected), `transaction_id`, `invoice_id` (unique).  

**Invoice Flow:**  
1. Customer (logged‑in or guest) receives an invoice via `/api/invoices` (POST).  
2. Required fields: `project_id`, `amount`. Optional: `payment_method`.  
3. Server validates project active, amount > 0.  
4. Creates invoice record with `pending` status and a unique `reference_id`.  
5. **Demo Auto‑approval:** Currently invoices are automatically set to `paid` for simplicity. In production, a payment gateway would be called.  
6. On payment, project’s `invoiced_amount` increases and a receipt ID is generated.  

**Admin Actions:**  
- `POST /api/invoices/<id>/approve` – Manually approve a pending invoice.  
- `POST /api/invoices/<id>/reject` – Reject an invoice.  

**Receipts:**  
- Each paid invoice gets a unique `receipt_id`.  
- `GET /receipts/<receipt_id>` – Renders an HTML receipt.  
- `GET /api/receipts/<receipt_id>` – Returns receipt data as JSON.  

### 4.4 Service Request & Waste Collection Reporting  

**Model:**  
- `ServiceRequest`: `latitude`, `longitude`, `address`, `description`, `waste_type` (general, recyclable, hazardous), `status` (reported/assigned/in_progress/completed/cancelled), `reported_by` (user ID), `assigned_to` (staff ID), `image_url` (placeholder), timestamps.  

**Features:**  
- **Report Request:**  
  - `POST /api/service-requests` (authenticated) – Creates a new request. Extracts geocoordinates, address, waste type.  
- **List Requests:**  
  - `GET /api/service-requests` – Returns all requests (admin) or filtered for staff/customers; permission checks on individual GET.  
- **Assignment:**  
  - `POST /api/service-requests/<id>/assign` (admin) – Assigns a field staff (must have role 'staff') to the request. Updates status to 'assigned'.  
- **Status Update:**  
  - `POST /api/service-requests/<id>/update-status` (admin or assigned staff) – Changes status, sets `completed_at` if status becomes 'completed'.  

**Access Control:**  
- `GET /api/service-requests/<id>` checks if the requester is admin, reporter, or assigned staff.  

### 4.5 Messaging System  

**Model:**  
- `Message`: `sender_id`, `receiver_id`, `subject`, `content`, `is_read`, `created_at`.  

**Endpoints:**  
- `GET /api/messages` – Returns messages received by current user.  
- `POST /api/messages` – Sends a message to another user (validates receiver exists).  
- `POST /api/messages/<id>/read` – Marks a message as read (only receiver can do this).  

**User Search:**  
- `GET /api/users/search?q=<query>` – Searches users by username, full name, or email; used for finding recipients.  

### 4.6 Statistics Dashboard  

**Endpoint:**  
- `GET /api/statistics` (admin only) – Aggregates key metrics:  
  - Total invoiced amount, total projects, active projects, total users.  
  - Service request counts (total, completed).  
  - Recent invoices (last 5).  
  - Project progress percentages.  

This powers the admin dashboard template (`admin_dashboard.html`).  

### 4.7 Invoice & Receipt Generation  

**HTML Template:**  
- `receipt.html` – Displays invoice details in a printable format.  
- Accessed via `/receipts/<receipt_id>` – Publicly viewable? Currently no permission check; anyone with the receipt ID can view.  

**API:**  
- `GET /api/receipts/<receipt_id>` – Returns JSON with invoice info, including customer name unless anonymous.  

---

## 5. Security Considerations  

### 5.1 Authentication & Authorization  
- **Password Hashing:** `werkzeug.security` uses strong, salted hashes (default 600,000 iterations of pbkdf2:sha256).  
- **Session Security:** Flask‑Login uses secure cookies; `SECRET_KEY` is read from environment variable or generated randomly.  
- **Role Enforcement:** The `@role_required` decorator ensures only users with specific roles access privileged endpoints.  
- **Object‑Level Permissions:** Some endpoints (e.g., `GET /api/service-requests/<id>`) manually check ownership/assignment.  

### 5.2 Data Protection  
- **Sensitive Data:** Passwords are never stored in plain text. Email addresses are considered personal data and should be handled according to privacy regulations (GDPR, etc.).  
- **CSRF Protection:** Not explicitly implemented; forms rely on same‑origin policy and Flask‑Login’s session protection. For production, CSRF tokens (e.g., Flask‑WTF) should be added.  
- **Environment Variables:** `SECRET_KEY` and `WEBHOOK_SECRET` are loaded from environment to avoid hardcoding.  

### 5.3 Input Validation & Sanitization  
- **Helper Function `get_request_data()`:** Parses JSON, form data, or raw JSON from request body, but does not perform schema validation.  
- **Manual Checks:** Routes check required fields and data types (e.g., amount must be float > 0).  
- **SQL Injection:** SQLAlchemy ORM uses parameterized queries, protecting against injection.  
- **XSS:** Templates (if using Jinja) auto‑escape content. However, the current code only returns JSON or redirects; any HTML templates must be reviewed for safe rendering.  

### 5.4 Error Handling & Logging  
- **Custom Error Handlers:** Return appropriate JSON or HTML for 400/401/403/404/500 errors.  
- **Database Rollback:** On 500 error, `db.session.rollback()` prevents corrupt transactions.  
- **No Verbose Errors in Production:** Error handlers return generic messages; detailed errors are not exposed to clients.  

---

## 6. Deployment and Operations  

### 6.1 Environment Configuration  
The application uses the following environment variables:  

| Variable          | Purpose                                         | Default                             |
|-------------------|-------------------------------------------------|-------------------------------------|
| `SECRET_KEY`      | Flask session signing key                       | Auto‑generated random hex (32)      |
| `WEBHOOK_SECRET`  | Future webhook authentication                   | Auto‑generated random hex (32)      |

For production, set these to strong, persistent values.  

### 6.2 Database Initialization  
- Database URI is configured as `sqlite:///envclean.db` by default.  
- The `init_db()` function runs inside `app.app_context()` to create tables and seed initial data:  
  - Admin user: `admin` / `admin123`  
  - Field staff: `staff1` / `staff123`  
  - Customer: `customer1` / `customer123`  
  - Two sample projects and two service requests.  

To reset the database, delete the `.db` file and restart the app.  

### 6.3 Running the Application  

**Development:**  
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```
or directly:
```bash
python app.py
```
This starts a development server on `0.0.0.0:5000`.  

**Production:**  
Use a production WSGI server like Gunicorn:  
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
Set environment variables appropriately and use a reverse proxy (nginx) for SSL termination.  

---

## 7. Future Enhancements  

### 7.1 Payment Gateway Integration  
- Replace the auto‑approval logic with actual payment processing (e.g., Stripe, PayPal, M‑Pesa).  
- Use the `PaymentRequest` model to track gateway requests and responses.  
- Implement webhooks to update invoice status asynchronously.  

### 7.2 Real-time Notifications  
- Integrate WebSockets (Flask‑SocketIO) to notify admins of new service requests or field staff of assignments.  
- Email/SMS notifications for invoice receipts or status changes.  

### 7.3 Mobile App Integration  
- Expose the API for a mobile front‑end (React Native / Flutter).  
- Add OAuth2 or JWT authentication for mobile clients.  

### 7.4 Advanced Analytics & Reporting  
- Generate PDF reports for projects, invoices, and service completion.  
- Visualize data with charts (using Chart.js or similar).  

---

## 8. Conclusion  

The **AMP Environmental Cleaning and Waste Management System** provides a solid foundation for managing environmental services and waste collection operations. Its modular design, role‑based access, and RESTful API make it extensible and suitable for both web and mobile clients. With proper security measures and planned enhancements, it can evolve into a full‑fledged solution for environmental service companies.  

This proposal outlines the current implementation and future directions, ensuring all stakeholders have a clear understanding of the system’s capabilities and technical underpinnings.  

---

## 9. Appendices  

### 9.1 Complete API Endpoint List  

| Method | Endpoint                                | Access              | Description                               |
|--------|-----------------------------------------|---------------------|-------------------------------------------|
| POST   | /api/register                           | Public              | Register new user                         |
| POST   | /api/login                              | Public              | Log in user                               |
| POST   | /api/logout                             | Authenticated       | Log out current user                      |
| GET    | /api/users/<id>                         | Admin               | Get user details                          |
| PUT    | /api/users/<id>                         | Admin               | Update user                               |
| DELETE | /api/users/<id>                         | Admin               | Delete user                               |
| GET    | /api/projects                           | Public              | List all projects                         |
| POST   | /api/projects                           | Admin               | Create project                            |
| GET    | /api/projects/<id>                      | Public              | Get project details                       |
| PUT    | /api/projects/<id>                      | Admin               | Update project                            |
| GET    | /api/projects/<id>/qr                   | Public              | Get QR code for project                    |
| GET    | /api/projects/<id>/invoices             | Public              | List paid invoices for project            |
| GET    | /api/invoices                           | Admin               | List all invoices                         |
| POST   | /api/invoices                           | Public/Logged-in    | Create invoice (auto‑paid)                |
| GET    | /api/invoices/<id>                      | Admin/Customer owner| Get invoice details                       |
| POST   | /api/invoices/<id>/approve              | Admin               | Approve pending invoice                   |
| POST   | /api/invoices/<id>/reject               | Admin               | Reject pending invoice                    |
| GET    | /api/service-requests                    | Authenticated       | List all service requests                 |
| POST   | /api/service-requests                    | Authenticated       | Report a service request                  |
| GET    | /api/service-requests/<id>               | Admin/Reporter/Assigned | Get request details                |
| POST   | /api/service-requests/<id>/assign        | Admin               | Assign field staff to request             |
| POST   | /api/service-requests/<id>/update-status | Admin/Assigned staff| Update request status                     |
| GET    | /api/messages                            | Authenticated       | Get received messages                     |
| POST   | /api/messages                            | Authenticated       | Send a message                            |
| POST   | /api/messages/<id>/read                  | Authenticated (receiver) | Mark message as read                |
| GET    | /api/users/search                        | Authenticated       | Search users                              |
| GET    | /api/statistics                          | Admin               | Get system statistics                     |
| GET    | /api/receipts/<receipt_id>                | Public              | Get receipt data (JSON)                   |
| GET    | /receipts/<receipt_id>                    | Public              | View receipt HTML                         |

### 9.2 Database Schema Diagram  

*(A visual diagram would be inserted here – for brevity, refer to the model relationships described in section 3.3.)*  

### 9.3 Sample .env Configuration  

```
SECRET_KEY=your-very-strong-secret-key-here
WEBHOOK_SECRET=another-strong-secret-for-webhooks
DATABASE_URL=postgresql://user:pass@localhost/envdb   # optional, defaults to sqlite
```


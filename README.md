# E-Commerce Backend MVP (Perfume Brand)

A production-ready robust backend API for an e-commerce platform, built with FastAPI and PostgreSQL. This MVP focuses on strict data integrity, secure payment processing, and architectural cleanliness, designed to handle real-world scenarios such as concurrent inventory modifications and secure webhook processing.

## Core Architecture & Engineering Highlights

* **Clean Architecture:** The codebase strictly separates business logic, data access, and API routing, ensuring high maintainability and scalability.
* **Secure Payment Integration (Paymob):** Fully integrated End-to-End payment lifecycle for both Credit Cards and Mobile Wallets.
* **HMAC Signature Validation:** Webhook endpoints are heavily secured using SHA-512 HMAC validation to prevent payload tampering and unauthorized state mutations.
* **ACID Compliant Transactions:** Implemented database-level transactions with Row-Level Locking (`with_for_update`) via SQLAlchemy to prevent race conditions during inventory deduction, ensuring accurate stock levels even under concurrent checkouts.

## Tech Stack

* **Framework:** FastAPI
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy
* **Migrations:** Alembic
* **Payment Gateway:** Paymob (Card & Wallet integration)
* **Language:** Python 3.10+

## Getting Started

### Prerequisites

Ensure you have Python 3.10+ and PostgreSQL installed on your local machine.

### Installation

1. Clone the repository:
```bash
git clone [https://github.com/yourusername/perfume-store-backend.git](https://github.com/yourusername/perfume-store-backend.git)
cd perfume-store-backend

```

2. Create and activate a virtual environment:

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate

```

3. Install the dependencies:

```bash
pip install -r requirements.txt

```

4. Environment Variables:
Create a `.env` file in the root directory and configure the following variables (refer to `.env.example` for details):

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY= ####

# Paymob Configuration
PAYMOB_API_KEY=your_api_key
PAYMOB_CARD_INTEGRATION_ID=your_card_id
PAYMOB_WALLET_INTEGRATION_ID=your_wallet_id
PAYMOB_HMAC_SECRET=your_hmac_secret

```

5. Run Database Migrations:

```bash
alembic upgrade head

```

6. Start the Development Server:

```bash
uvicorn app.main:app --reload

```

## API Documentation

Once the server is running, FastAPI automatically generates interactive API documentation. You can access it at:

* **Swagger UI:** `http://127.0.0.1:8000/docs`
* **ReDoc:** `http://127.0.0.1:8000/redoc`

## Project Structure

```text
backend/
├── app/
│   ├── api/          # API Routers and Endpoints
│   ├── core/         # Configuration and Security setup
│   ├── models/       # SQLAlchemy Database Models
│   ├── schemas/      # Pydantic Models for Validation
│   └── services/     # Business Logic and External Integrations (e.g., Paymob)
├── alembic/          # Database Migration Scripts
├── main.py           # Application Entry Point
└── requirements.txt  # Project Dependencies

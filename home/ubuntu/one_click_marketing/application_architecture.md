# Application Architecture: ONE CLICK MARKETING

## 1. Introduction

This document outlines the application architecture for **ONE CLICK MARKETING**, a WhatsApp API-based marketing application. It details the overall system design, frontend and backend components, their interactions, API endpoints, and data models. The application will allow clients to manage their WhatsApp marketing campaigns, integrate with Meta (WhatsApp Business API), create message templates, send messages, and view detailed financial and campaign reports.

## 2. System Overview

The application will follow a client-server architecture:

*   **Frontend (Client-Side):** A Next.js single-page application (SPA) providing the user interface for clients and administrators. It will be responsible for rendering views, handling user interactions, and communicating with the backend API.
*   **Backend (Server-Side):** A Flask (Python) application serving as the API backend. It will handle business logic, data processing, database interactions (MySQL), user authentication, and integration with the WhatsApp Business API.
*   **Database:** A MySQL database will be used to store all persistent data, including user accounts, client information, campaign details, message templates, financial records, and campaign reports.
*   **WhatsApp Business API:** The application will integrate with the official WhatsApp Business API for sending and receiving messages, managing templates, and handling webhooks.

## 3. Frontend Architecture (Next.js)

The frontend will be built using Next.js and will consist of the following main modules/pages:

*   **Authentication Pages:**
    *   Client Registration
    *   Client Login
    *   Password Reset (Future Enhancement)
*   **Client Dashboard:**
    *   Overview of account status, recent activity, and key metrics.
*   **Meta Account Management:**
    *   Interface for clients to connect/disconnect their WhatsApp Business API account (guidance and steps, potentially manual input of API keys initially).
*   **Template Management:**
    *   Create, view, edit, and delete WhatsApp message templates (following Meta's guidelines).
    *   Template status tracking (pending, approved, rejected).
*   **Campaign Management:**
    *   Create new campaigns (selecting templates, target audience/contacts).
    *   Schedule campaigns.
    *   View ongoing and completed campaigns.
*   **Messaging Interface:**
    *   Interface for sending messages (potentially for individual messages or small batches, primarily through campaigns).
*   **Reporting Pages:**
    *   **Financial Reports:** Displaying cost per message, daily profit, wallet top-ups, and daily deductions.
    *   **Campaign Reports:** Displaying sent rate, open rate (if feasible), click-through rate, and failure rates with reasons.
*   **Admin Section (Separate or Role-Based Access):**
    *   User management (view clients, manage accounts).
    *   System-wide settings.
    *   Global financial overview.

## 4. Backend Architecture (Flask)

The Flask backend will expose a RESTful API for the frontend and handle all server-side operations. Key modules will include:

*   **Authentication Module (`/auth`):
    *   Handles user registration, login, session management (e.g., JWT tokens).
*   **User/Client Management Module (`/users`, `/clients`):
    *   CRUD operations for client accounts.
    *   Profile management.
*   **Meta Integration Module (`/meta`):
    *   Endpoints for storing Meta API credentials (securely).
    *   Webhook endpoint to receive updates from WhatsApp (message status, incoming messages).
    *   Service layer to interact with the WhatsApp Business API.
*   **Template Management Module (`/templates`):
    *   CRUD operations for message templates.
    *   Logic for template submission to Meta (potentially manual guidance initially).
*   **Campaign Management Module (`/campaigns`):
    *   CRUD operations for campaigns.
    *   Scheduling logic (e.g., using a task queue like Celery - for future enhancement, initially direct execution or simple cron).
*   **Messaging Module (`/messages`):
    *   Endpoints for sending messages via the WhatsApp API.
    *   Tracking message status.
*   **Reporting Module (`/reports`):
    *   Endpoints to fetch data for financial and campaign reports.
    *   Aggregation and calculation logic for report metrics.
*   **Database Models (SQLAlchemy):
    *   Define schema for all entities (Users, Clients, Templates, Campaigns, Messages, FinancialData, etc.).

## 5. API Endpoints (Initial Draft)

All endpoints will be prefixed with `/api/v1`.

*   **Authentication:**
    *   `POST /auth/register` - Client registration
    *   `POST /auth/login` - Client login
    *   `POST /auth/logout` - Client logout
    *   `GET /auth/me` - Get current user details
*   **Client Management (Admin may have more extensive endpoints):**
    *   `GET /clients/me` - Get current client's details
    *   `PUT /clients/me` - Update current client's details
    *   `POST /clients/me/meta-connect` - Store Meta API credentials
*   **Template Management:**
    *   `POST /templates` - Create a new template
    *   `GET /templates` - List all templates for the client
    *   `GET /templates/{template_id}` - Get a specific template
    *   `PUT /templates/{template_id}` - Update a template
    *   `DELETE /templates/{template_id}` - Delete a template
*   **Campaign Management:**
    *   `POST /campaigns` - Create a new campaign
    *   `GET /campaigns` - List all campaigns for the client
    *   `GET /campaigns/{campaign_id}` - Get a specific campaign
    *   `PUT /campaigns/{campaign_id}` - Update a campaign (e.g., schedule)
    *   `POST /campaigns/{campaign_id}/send` - Initiate sending for a campaign
*   **Messaging & Webhooks:**
    *   `POST /webhook/whatsapp` - Receives incoming events from WhatsApp API
*   **Reporting:**
    *   `GET /reports/financial` - Get financial report data (with query params for date ranges)
    *   `GET /reports/campaigns/{campaign_id}` - Get report for a specific campaign
    *   `GET /reports/campaigns` - Get summary of all campaign reports

## 6. Data Models (Initial Draft - SQLAlchemy)

*   **User:**
    *   `id` (PK)
    *   `username` (unique)
    *   `email` (unique)
    *   `password_hash`
    *   `role` (e.g., 'client', 'admin')
    *   `created_at`, `updated_at`
*   **ClientProfile (extends User or one-to-one with User):**
    *   `user_id` (FK)
    *   `company_name`
    *   `meta_api_key` (encrypted)
    *   `meta_phone_number_id`
    *   `wallet_balance`
*   **MessageTemplate:**
    *   `id` (PK)
    *   `client_id` (FK to User/ClientProfile)
    *   `name`
    *   `category` (e.g., MARKETING, UTILITY)
    *   `content` (structure as per WhatsApp: header, body, footer, buttons)
    *   `variables` (list of placeholder variables)
    *   `status` (e.g., DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)
    *   `meta_template_id` (once approved by Meta)
    *   `created_at`, `updated_at`
*   **Campaign:**
    *   `id` (PK)
    *   `client_id` (FK)
    *   `name`
    *   `template_id` (FK)
    *   `contact_list_id` (FK - or store contacts directly, TBD)
    *   `scheduled_at` (nullable)
    *   `status` (e.g., DRAFT, SCHEDULED, SENDING, COMPLETED, FAILED)
    *   `created_at`, `updated_at`
*   **MessageLog:**
    *   `id` (PK)
    *   `campaign_id` (FK, nullable if single message)
    *   `client_id` (FK)
    *   `recipient_phone_number`
    *   `template_id` (FK, if applicable)
    *   `message_content` (rendered message)
    *   `status` (e.g., SENT, DELIVERED, READ, FAILED)
    *   `failure_reason` (if FAILED)
    *   `cost`
    *   `sent_at`, `delivered_at`, `read_at`
*   **FinancialTransaction:**
    *   `id` (PK)
    *   `client_id` (FK)
    *   `type` (e.g., TOP_UP, MESSAGE_COST, REFUND)
    *   `amount`
    *   `description`
    *   `transaction_date`
*   **Contact/ContactList (TBD based on complexity):**
    *   How contacts are managed and imported.

## 7. Technology Stack Summary

*   **Frontend:** Next.js (React, TypeScript/JavaScript)
*   **Backend:** Flask (Python)
*   **Database:** MySQL
*   **Deployment:** To be determined (options like Vercel for Next.js, Docker + Cloud VM/PaaS for Flask & MySQL)
*   **Version Control:** Git

## 8. Next Steps

1.  Refine data models and API endpoints.
2.  Begin implementation of User Authentication module.
3.  Research and document the WhatsApp Business API integration process in detail.

This document will be updated as the project progresses.

# WhatsApp Business API (Cloud API) Onboarding Guide

This document outlines the key steps and information gathered from the official Meta Developer documentation for onboarding to the WhatsApp Business Cloud API. This will serve as a reference for integrating the "ONE CLICK MARKETING" application.

## 1. Overview

The WhatsApp Business Platform allows businesses to connect with customers at scale. It consists of several APIs, with the **Cloud API** (hosted by Meta) being the preferred solution for sending and receiving messages due to its ease of implementation and low maintenance. The **Business Management API** is also essential for managing WhatsApp Business Account (WABA) assets and message templates.

**Source:** [WhatsApp Business Platform Overview](https://developers.facebook.com/docs/whatsapp/)

## 2. Getting Started with Cloud API

The Cloud API allows developers to implement WhatsApp Business APIs without hosting their own servers.

**Source:** [Cloud API Overview](https://developers.facebook.com/docs/whatsapp/cloud-api)

### Prerequisites:

*   **Meta Developer Account:** Required to create and manage apps. ([Learn more about registering](https://developers.facebook.com/docs/development/register))
*   **Meta Business App:** A specific type of app for business integrations. If not directly available, create an app by selecting "Other" > "Next" > "Business". ([Learn more about creating apps](https://developers.facebook.com/docs/development/create-an-app))

**Source:** [Get Started - Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)

### Step-by-Step Process:

1.  **Add WhatsApp Product to Your App:**
    *   In the Meta App Dashboard, select your app (or create a new one).
    *   Add the "WhatsApp" product. This action will:
        *   Prompt for a Meta Business Account (MBA) or guide you through creating one if it doesn't exist.
        *   Automatically create a **test WhatsApp Business Account (WABA)** for development and testing (messages are free).
        *   Create a **test business phone number** associated with the test WABA (can send free messages to up to 5 verified recipient numbers).
        *   Provide a set of pre-approved message templates (e.g., `hello_world`).

2.  **Add Recipient Phone Number(s) for Testing:**
    *   In the App Dashboard, navigate to **WhatsApp > API Setup**.
    *   Under "Send and receive messages", select the "To" field and choose "Manage phone number list".
    *   Add up to 5 valid WhatsApp numbers. Each number will receive a confirmation code via WhatsApp for verification.

3.  **Send a Test Message:**
    *   Using the **WhatsApp > API Setup** panel in the App Dashboard:
        *   Ensure the test business phone number is selected in the "From" field.
        *   Select a verified recipient number in the "To" field.
        *   Use the "Send messages with the API" panel (or the provided cURL command) to send a pre-approved template message (e.g., `hello_world`).
    *   The API call will specify `"type":"template"` and `"name":"hello_world"`.

4.  **Configure Webhooks:**
    *   Webhooks are crucial for receiving real-time notifications (message status, incoming messages, account changes).
    *   A callback URL needs to be configured to receive these webhook payloads.
    *   Meta provides a [Sample Callback URL for Webhooks Testing guide](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks) to help set up a sample app for viewing webhook JSON payloads.
    *   After setup, sending a message and replying should trigger multiple webhook notifications (sent, delivered, read, incoming message).

5.  **(Optional) Add a Real Business Phone Number:**
    *   Once development with test assets is complete and you are ready to message actual customers, you can add a real business phone number.
    *   This involves creating a **real WhatsApp Business Account** through the **API Setup** panel.
    *   This step will involve costs associated with sending messages.

### Key Components & Concepts:

*   **Access Tokens:** Needed to authenticate API requests. ([Learn About Access Tokens and System Users](https://developers.facebook.com/docs/whatsapp/cloud-api/access-tokens))
*   **System Users:** Programmatic users for managing assets and permissions.
*   **Message Templates:** Pre-approved message formats required for business-initiated conversations outside the 24-hour customer service window. ([Learn About Message Templates](https://developers.facebook.com/docs/whatsapp/message-templates))
*   **Phone Numbers:** Managing and connecting phone numbers to your WABA. ([Phone Numbers Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api/phone-numbers))
*   **Pricing:** Understand the pricing model for messages. (Refer to official Meta documentation for current pricing, as it can change - e.g., changes effective July 1, 2025, mentioned on the platform pages).
*   **Quality Rating and Messaging Limits:** Important for maintaining a healthy account. ([Quality Rating and Messaging Limits](https://developers.facebook.com/docs/whatsapp/ τότε/quality-rating))

## 3. Next Steps for "ONE CLICK MARKETING" Integration

1.  **User Guidance:** Prepare a clear guide for our application's users (your clients) on how to:
    *   Create a Meta Developer Account and a Meta Business App.
    *   Add the WhatsApp product to their app.
    *   Connect/create their Meta Business Account.
    *   Obtain their WhatsApp Business Account ID (WABA ID), Phone Number ID, and a permanent System User Access Token.
    *   Verify their business (Meta may require business verification for full access).
2.  **Backend Development (Flask):**
    *   Create secure storage for client's Meta API credentials (WABA ID, Phone Number ID, Access Token).
    *   Implement API client logic to send messages using the Cloud API.
    *   Develop a webhook endpoint in our Flask app to receive and process notifications from WhatsApp (message status, incoming messages).
3.  **Frontend Development (Next.js):**
    *   Create an interface for clients to input and save their Meta API credentials.
    *   Display connection status.

This document will be updated as more specific details are uncovered or if Meta's documentation changes.

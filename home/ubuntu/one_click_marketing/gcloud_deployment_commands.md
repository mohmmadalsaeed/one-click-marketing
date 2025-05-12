## Google Cloud Run Deployment Commands for ONE CLICK MARKETING

**Prerequisites:**

1.  **Google Cloud SDK (`gcloud`)**: Ensure you have the `gcloud` command-line tool installed and authenticated on your local machine, OR plan to use the Google Cloud Shell (which has `gcloud` pre-installed and authenticated).
2.  **Google Cloud Project**: You need an active Google Cloud Project with billing enabled.
3.  **Enable APIs**: Make sure the following APIs are enabled in your Google Cloud Project:
    *   Cloud Build API
    *   Artifact Registry API (or Container Registry API - Artifact Registry is recommended)
    *   Cloud Run API

**Instructions:**

*   Replace placeholders like `[YOUR_PROJECT_ID]`, `[YOUR_REGION]`, `[YOUR_SERVICE_NAME_BACKEND]`, `[YOUR_SERVICE_NAME_FRONTEND]`, and all `YOUR_..._HERE` values with your actual information.
*   It's recommended to use Artifact Registry for storing your Docker images. If you are using the older Container Registry, you might need to adjust image paths (e.g., `gcr.io/[YOUR_PROJECT_ID]/[IMAGE_NAME]` instead of `[YOUR_REGION]-docker.pkg.dev/[YOUR_PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME]`).

--- 

### Part 1: Deploy Backend (Flask Application)

**1. Set your Project ID and Region:**
```bash
gcloud config set project [YOUR_PROJECT_ID]
# Example region: us-central1, europe-west1, etc.
export REGION="[YOUR_REGION]"
```

**2. (Optional, Recommended) Create an Artifact Registry Docker repository (if you don't have one):**
```bash
# Replace [REPOSITORY_NAME] with a name like 'oneclick-marketing-repo'
gcloud artifacts repositories create [REPOSITORY_NAME] \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for ONE CLICK MARKETING application"
```

**3. Build the Backend Docker image using Cloud Build and push to Artifact Registry:**
```bash
# Replace [REPOSITORY_NAME] with the name you chose above or your existing repository
# Replace [IMAGE_NAME_BACKEND] with a name like 'oneclick-backend'
gcloud builds submit ./backend --tag $REGION-docker.pkg.dev/[YOUR_PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME_BACKEND]:latest
```

**4. Deploy the Backend to Cloud Run:**
```bash
# Replace [SERVICE_NAME_BACKEND] with a name like 'oneclick-backend-service'
# Replace [REPOSITORY_NAME] and [IMAGE_NAME_BACKEND] as used above.
# Set environment variables directly. For sensitive values, consider Secret Manager integration (more advanced).

gcloud run deploy [SERVICE_NAME_BACKEND] \
    --image $REGION-docker.pkg.dev/[YOUR_PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME_BACKEND]:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars "SECRET_KEY=YOUR_FLASK_SECRET_KEY_HERE" \
    --set-env-vars "JWT_SECRET_KEY=YOUR_JWT_SECRET_KEY_HERE" \
    --set-env-vars "DB_USERNAME=YOUR_DB_USERNAME" \
    --set-env-vars "DB_PASSWORD=YOUR_DB_PASSWORD" \
    --set-env-vars "DB_HOST=YOUR_DB_HOST_IP_OR_CLOUDSQL_CONNECTION_NAME" \
    --set-env-vars "DB_PORT=3306" \
    --set-env-vars "DB_NAME=YOUR_DB_NAME" \
    --set-env-vars "META_APP_ID=YOUR_META_APP_ID" \
    --set-env-vars "META_APP_SECRET=YOUR_META_APP_SECRET" \
    --set-env-vars "META_VERIFY_TOKEN=YOUR_META_VERIFY_TOKEN_FOR_WEBHOOKS" \
    --set-env-vars "WHATSAPP_BUSINESS_ACCOUNT_ID=YOUR_WHATSAPP_BUSINESS_ACCOUNT_ID" \
    --set-env-vars "WHATSAPP_PHONE_NUMBER_ID=YOUR_WHATSAPP_PHONE_NUMBER_ID" \
    --set-env-vars "FRONTEND_URL=TEMPORARY_PLACEHOLDER_WILL_UPDATE_LATER" 
    # Add other necessary environment variables from your .env.example
```
**Note:** After deployment, Cloud Run will provide a URL for your backend service. You will need this URL for the frontend configuration.

--- 

### Part 2: Deploy Frontend (Next.js Application)

**1. Build the Frontend Docker image using Cloud Build and push to Artifact Registry:**
```bash
# Ensure your REGION and [YOUR_PROJECT_ID] are still set from Part 1
# Replace [REPOSITORY_NAME] with the name you chose or your existing repository
# Replace [IMAGE_NAME_FRONTEND] with a name like 'oneclick-frontend'
gcloud builds submit ./frontend --tag $REGION-docker.pkg.dev/[YOUR_PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME_FRONTEND]:latest
```

**2. Deploy the Frontend to Cloud Run:**
```bash
# Replace [SERVICE_NAME_FRONTEND] with a name like 'oneclick-frontend-service'
# Replace [REPOSITORY_NAME] and [IMAGE_NAME_FRONTEND] as used above.
# IMPORTANT: Replace [URL_OF_YOUR_DEPLOYED_BACKEND_SERVICE] with the actual URL you got after deploying the backend.

gcloud run deploy [SERVICE_NAME_FRONTEND] \
    --image $REGION-docker.pkg.dev/[YOUR_PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME_FRONTEND]:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars "NEXT_PUBLIC_API_BASE_URL=[URL_OF_YOUR_DEPLOYED_BACKEND_SERVICE]" 
    # Add any other NEXT_PUBLIC_ environment variables if needed
```
**Note:** After deployment, Cloud Run will provide a URL for your frontend service. This is the main URL for accessing your application.

--- 

### Part 3: Update Backend with Frontend URL (if necessary)

If your backend needs to know the final URL of the frontend (e.g., for CORS or redirects), you might need to update the `FRONTEND_URL` environment variable for the backend service:

**1. Get the URL of your deployed frontend service:**
   You can find this in the Google Cloud Console or from the output of the frontend deployment command.

**2. Update the backend Cloud Run service:**
```bash
# Replace [SERVICE_NAME_BACKEND] with your backend service name
# Replace [URL_OF_YOUR_DEPLOYED_FRONTEND_SERVICE] with the actual frontend URL

gcloud run services update [SERVICE_NAME_BACKEND] \
    --platform managed \
    --region $REGION \
    --update-env-vars "FRONTEND_URL=[URL_OF_YOUR_DEPLOYED_FRONTEND_SERVICE]"
```

--- 

**Important Considerations for Temporary Deployment:**

*   **Database**: These instructions assume your database is already accessible from Google Cloud Run (e.g., Cloud SQL configured for public/private IP or a publicly accessible DB). If you need to set up a temporary database on Google Cloud, that would be an additional set of steps (e.g., creating a Cloud SQL instance).
*   **Stopping/Deleting Services**: To stop incurring charges, you can either:
    *   **Delete the Cloud Run services**: `gcloud run services delete [SERVICE_NAME_BACKEND] --region $REGION` and `gcloud run services delete [SERVICE_NAME_FRONTEND] --region $REGION`.
    *   **Delete the entire project** if it was created solely for this temporary deployment.
*   **Security**: The `--allow-unauthenticated` flag makes your services publicly accessible. For production, you would implement authentication.
*   **Environment Variables**: For a real production setup, especially for sensitive data like database passwords or API keys, you should use Google Cloud Secret Manager and integrate it with Cloud Run instead of setting environment variables directly in the deploy command.

This guide provides the basic commands. You may need to adjust them based on your specific Google Cloud project setup and requirements.

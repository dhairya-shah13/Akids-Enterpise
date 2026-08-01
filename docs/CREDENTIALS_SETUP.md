# 🔑 Third-Party Credentials Setup Guide (Google OAuth & Firebase Auth)

This guide provides step-by-step instructions for the site owner to generate and configure live credentials for **Google Sign-In / Sign-Up** and **Firebase Email-Link (Passwordless) Sign-In**.

---

## 1. Google OAuth 2.0 Client Credentials (Google Sign-In)

Follow these steps to enable Google authentication on your site:

1. **Go to Google Cloud Console**:
   Visit [https://console.cloud.google.com/](https://console.cloud.google.com/) and sign in with your Google account.
2. **Create or Select a Project**:
   - Click the project dropdown at the top of the page.
   - Click **New Project**, name it (e.g. `Akids Enterprise`), and click **Create**.
3. **Configure OAuth Consent Screen**:
   - In the left sidebar, navigate to **APIs & Services** > **OAuth consent screen**.
   - Select **User Type**: **External** and click **Create**.
   - Fill in:
     - **App name**: `A kids India / Little Fingers`
     - **User support email**: `info@akidsenterprise.com`
     - **Developer contact information**: `info@akidsenterprise.com`
   - Click **Save and Continue** through Scopes and Test users.
4. **Create OAuth 2.0 Client ID**:
   - Go to **APIs & Services** > **Credentials**.
   - Click **+ CREATE CREDENTIALS** > **OAuth client ID**.
   - Select **Application type**: **Web application**.
   - **Name**: `Akids Web Client`
   - **Authorized JavaScript origins**:
     - `http://127.0.0.1:8000`
     - `http://localhost:8000`
     - `https://akidsenterprise.com` (or your Vercel deployment domain)
   - **Authorized redirect URIs**:
     - `http://127.0.0.1:8000/auth/google/callback/`
     - `https://akidsenterprise.com/auth/google/callback/`
   - Click **Create**.
5. **Copy Credentials into `.env`**:
   - Copy the generated **Client ID** and **Client Secret**.
   - Paste them into your `.env` file at `backend/.env` (the single canonical `.env` for this repo):
     ```env
     GOOGLE_OAUTH_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
     GOOGLE_OAUTH_CLIENT_SECRET="YOUR_GOOGLE_CLIENT_SECRET"
     ```

---

## 2. Firebase Web Authentication Setup (Passwordless Sign-In)

Follow these steps to configure Firebase Email Link (magic link) sign-in:

1. **Go to Firebase Console**:
   Visit [https://console.firebase.google.com/](https://console.firebase.google.com/) and click **Add project**.
2. **Create Firebase Project**:
   - Project Name: `Akids-Enterprise`
   - Disable or enable Google Analytics (optional), then click **Create project**.
3. **Enable Email Link Authentication**:
   - In the left navigation, go to **Build** > **Authentication**.
   - Click **Get started**.
   - Select **Email/Password** under Sign-in providers.
   - Toggle **Enable** for Email/Password.
   - Toggle **Enable** for **Email link (passwordless sign-in)**.
   - Click **Save**.
4. **Add Authorized Domain**:
   - Under **Authentication** > **Settings** > **Authorized domains**, click **Add domain**.
   - Add your localhost domain `127.0.0.1` and production domain `akidsenterprise.com`.
5. **Register Web App & Get Web Config**:
   - Go to **Project Settings** (gear icon top left).
   - Scroll down to **Your apps** and click the Web icon (`</>`).
   - App nickname: `Akids Web App`.
   - Leave **"Also set up Firebase Hosting for this app" unchecked** (your Django web app is hosted separately on Vercel / server).
   - Click **Register app**.
   - Copy the values inside `firebaseConfig`:
     ```javascript
     const firebaseConfig = {
       apiKey: "AIzaSy...",
       authDomain: "akids-enterprise.firebaseapp.com",
       projectId: "akids-enterprise",
       storageBucket: "akids-enterprise.appspot.com",
       messagingSenderId: "1234567890",
       appId: "1:1234567890:web:abc123def456"
     };
     ```
6. **Copy Credentials into `.env`**:
   - Paste these values into your `.env` file at `backend/.env` (the single canonical `.env` for this repo):
     ```env
     FIREBASE_API_KEY="AIzaSy..."
     FIREBASE_AUTH_DOMAIN="akids-enterprise.firebaseapp.com"
     FIREBASE_PROJECT_ID="akids-enterprise"
     FIREBASE_STORAGE_BUCKET="akids-enterprise.appspot.com"
     FIREBASE_MESSAGING_SENDER_ID="1234567890"
     FIREBASE_APP_ID="1:1234567890:web:abc123def456"
     ```

---

## 3. Database Connectivity (IMPORTANT)

There is now a **single canonical `.env` file**: `backend/.env`. On 2026-08-01 the stale root `.env` (which pointed at the decommissioned Supabase host `db.raonllwzgumhalpjdmqe.supabase.co` whose credentials fail auth) was consolidated into it and removed. The active host is:

| Source | Host | Status |
|---|---|---|
| `backend/.env` (canonical) | `aws-0-ap-southeast-2.pooler.supabase.com` | ✅ ACTIVE (used by `runserver`) |

**Trap:** `settings.py` loads `backend/.env` with `load_dotenv(..., override=False)`, so if your shell or machine already exports a `DATABASE_URL` env var, it **silently wins over the `.env` file** and `manage.py` commands can target the *wrong* database without any error.

**To be safe:**
1. Treat `backend/.env` as the single source of truth — do not create a new root `.env`.
2. Do **not** export `DATABASE_URL` in your shell; if you already have one set to the old host, remove it (e.g. `unset DATABASE_URL`).
3. Before any `manage.py migrate` against production, verify the target with `python manage.py showmigrations products` — it must connect (not error) and show `[ ]` on pending items.

---

## 4. Verify Live Status

Once the environment variables are added to `.env` and the server is restarted:
- The "Continue with Google" button will automatically become active.
- Passwordless sign-in with Firebase email link will function end-to-end.

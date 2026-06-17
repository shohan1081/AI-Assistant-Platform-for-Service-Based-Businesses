# NexFlow AI: AWS EC2 Deployment Guide

This guide covers everything you need to know to deploy the NexFlow AI backend onto an AWS EC2 instance using Docker and GitLab.

---

## Phase 1: Set Up the AWS EC2 Instance

1. **Log into AWS Console:** Go to the [EC2 Dashboard](https://console.aws.amazon.com/ec2/v2/home).
2. **Launch Instance:** Click **"Launch Instance"**.
   - **Name:** `nexflow-ai-server`
   - **OS Image (AMI):** Select **Ubuntu Server 22.04 LTS** (or 24.04).
   - **Instance Type:** `t3.small` or `t2.micro` (t3.small is recommended as the AI agent and Django process can consume decent memory).
   - **Key Pair:** Create a new key pair (e.g., `nexflow-key.pem`). **Download this file and keep it safe!**
3. **Network Settings:**
   - Allow **SSH traffic** (Port 22) from "Anywhere" (or your specific IP).
   - Allow **HTTP traffic** (Port 80) from the Internet.
   - Allow **HTTPS traffic** (Port 443) from the Internet.
4. **Storage:** Set the root volume to at least **20 GB** (gp3).
5. **Launch:** Click "Launch instance".

---

## Phase 2: Set Up an Elastic IP
EC2 public IPs change when the server restarts. An Elastic IP is permanent.

1. In the EC2 Dashboard (left menu), go to **Network & Security -> Elastic IPs**.
2. Click **"Allocate Elastic IP address"** -> "Allocate".
3. Select the newly created IP, click **"Actions" -> "Associate Elastic IP address"**.
4. Choose the `nexflow-ai-server` instance you just created and click "Associate".
*Take note of this IP address. This is your permanent server IP.*

---

## Phase 3: Connect to Your Server (SSH)

Open your terminal (PowerShell, Command Prompt, or Mac/Linux Terminal) where your `nexflow-key.pem` is located.

1. **Secure your key file (Mac/Linux only):**
   ```bash
   chmod 400 nexflow-key.pem
   ```
2. **SSH into the server:**
   ```bash
   ssh -i "nexflow-key.pem" ubuntu@<YOUR_ELASTIC_IP>
   ```
   *(Type `yes` if it asks to continue connecting).*

---

## Phase 4: Install Docker & Git on the Server

Once you are logged into the Ubuntu terminal, run these commands:

1. **Update packages & install Git:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install git -y
   ```
2. **Install Docker:**
   ```bash
   sudo apt install docker.io -y
   sudo systemctl start docker
   sudo systemctl enable docker
   ```
3. **Install Docker Compose:**
   ```bash
   sudo apt install docker-compose-v2 -y
   ```
4. **Add your user to the Docker group (so you don't have to type `sudo docker` every time):**
   ```bash
   sudo usermod -aG docker ubuntu
   ```
   *(You must type `exit` to log out, and then SSH back into the server for this to take effect).*

---

## Phase 5: Add Code from GitLab

You need to securely pull your code from GitLab to your server. We will use an SSH key for this.

1. **Generate an SSH key on the EC2 server:**
   ```bash
   ssh-keygen -t ed25519 -C "aws-ec2-nexflow"
   ```
   *(Press Enter through all the prompts to use default settings and no password).*
2. **View and copy the public key:**
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
   *(Copy the entire output).*
3. **Add the key to GitLab:**
   - Go to your GitLab account in your web browser.
   - Go to **Edit Profile -> SSH Keys** (or go to your specific Project -> Settings -> Repository -> Deploy Keys).
   - Paste the key, give it a title (e.g., "AWS EC2"), and click **Add key**.
4. **Clone the repository on the server:**
   ```bash
   git clone git@gitlab.com:your-username/nexflow-ai.git
   cd nexflow-ai
   ```

---

## Phase 6: Configure Environment Variables

1. Inside your `nexflow-ai` folder on the server, create the `.env` file:
   ```bash
   nano .env
   ```
2. Paste your production environment variables. Make sure to update the ALLOWED_HOSTS and Database URL:
   ```env
   DEBUG=False
   SECRET_KEY=your-super-secret-key-change-this
   ALLOWED_HOSTS=<YOUR_ELASTIC_IP>,yourdomain.com
   CORS_ALLOWED_ORIGINS=http://<YOUR_ELASTIC_IP>,https://yourdomain.com

   DATABASE_URL=postgres://postgres:postgres_secure_password@db:5432/nexflow_db
   POSTGRES_DB=nexflow_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres_secure_password

   OPENAI_API_KEY=your_openai_key
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your_livekit_key
   LIVEKIT_API_SECRET=your_livekit_secret
   ```
3. Save and exit nano: Press `Ctrl+O`, `Enter`, then `Ctrl+X`.

---

## Phase 7: Build and Run with Docker Compose

I have created a `docker-compose.prod.yml` file designed specifically for production. It automatically collects static files, runs database migrations, and uses Gunicorn for high performance.

1. **Start the containers in the background:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```
2. **Check the logs to ensure everything is running:**
   ```bash
   docker compose -f docker-compose.prod.yml logs -f web
   ```
   *(You should see "Starting gunicorn" and no errors. Press `Ctrl+C` to exit logs).*

3. **Create a superuser for your Admin Panel:**
   ```bash
   docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
   ```

---

## Phase 8: Updating Code in the Future

When you make changes locally and push them to GitLab, here is how you update your live server:

1. SSH into the server.
2. Go to the project directory: `cd nexflow-ai`
3. Pull the latest code:
   ```bash
   git pull origin main
   ```
4. Rebuild and restart the containers:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

**Your NexFlow AI backend is now live!** You can access the API and Admin panel by going to `http://<YOUR_ELASTIC_IP>/admin/` in your web browser.
# Heroku Deployment Guide - Options Scanner v2

**Complete step-by-step guide to deploy your Options Scanner to Heroku**

---

## 📋 Prerequisites

Before starting, make sure you have:

1. **Heroku Account** - Sign up at https://signup.heroku.com/ (free tier available)
2. **Heroku CLI** - Install from https://devcenter.heroku.com/articles/heroku-cli
3. **Git** - Already have (repository initialized)
4. **PostgreSQL Database** - You already have NeonDB running
5. **Alpha Vantage API Key** - You already have: `ZSDQA0G3YL73HLCC`

---

## 🚀 Step 1: Install Heroku CLI (if not installed)

### macOS:
```bash
brew tap heroku/brew && brew install heroku
```

### Verify installation:
```bash
heroku --version
# Should show: heroku/8.x.x
```

---

## 🔐 Step 2: Login to Heroku

```bash
heroku login
```

This will open your browser for authentication. Complete the login process.

---

## 📦 Step 3: Create Heroku App

```bash
cd /Users/herambhathavale/jupyterDir2/Oct-12-2025-Options-Scanner-v2/options-scanner-v2

# Create a new Heroku app (choose a unique name)
heroku create options-scanner-v2

# Or use auto-generated name:
# heroku create
```

**Note:** Heroku will give you a URL like: `https://options-scanner-v2-xxxxx.herokuapp.com`

---

## 🔧 Step 4: Set Environment Variables on Heroku

### Method 1: Using Heroku CLI (Recommended)

```bash
# Set DATABASE_URL
heroku config:set DATABASE_URL="postgresql://neondb_owner:npg_frKG6w0xePSB@ep-super-king-ad9z2xxi-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Set Alpha Vantage API Key
heroku config:set ALPHAVANTAGE_API_KEY="ZSDQA0G3YL73HLCC"
```

### Method 2: Using Heroku Dashboard (Alternative)

1. Go to https://dashboard.heroku.com/apps
2. Click on your app: `options-scanner-v2`
3. Click on **"Settings"** tab
4. Click **"Reveal Config Vars"**
5. Add two config vars:

| KEY | VALUE |
|-----|-------|
| `DATABASE_URL` | `postgresql://neondb_owner:npg_frKG6w0xePSB@ep-super-king-ad9z2xxi-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require` |
| `ALPHAVANTAGE_API_KEY` | `ZSDQA0G3YL73HLCC` |

### Verify environment variables:
```bash
heroku config
```

**Expected output:**
```
=== options-scanner-v2 Config Vars
ALPHAVANTAGE_API_KEY: ZSDQA0G3YL73HLCC
DATABASE_URL:         postgresql://neondb_owner:...
```

---

## 📝 Step 5: Verify Deployment Files

Make sure these files exist in your project root:

### ✅ Procfile
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### ✅ runtime.txt
```
python-3.11.5
```

### ✅ requirements.txt
Should include:
```
Flask==3.0.0
psycopg2-binary==2.9.9
requests==2.31.0
python-dotenv==1.0.0
scipy==1.11.4
gunicorn==21.2.0
```

### ✅ .gitignore
Should include:
```
.env
.venv/
__pycache__/
*.pyc
```

---

## 🚢 Step 6: Deploy to Heroku

### Commit your latest changes:
```bash
git add .
git commit -m "Prepare for Heroku deployment - add Procfile, runtime.txt, gunicorn"
```

### Push to GitHub (optional but recommended):
```bash
git push origin main
```

### Deploy to Heroku:
```bash
# Add Heroku remote (if not already added)
heroku git:remote -a options-scanner-v2

# Push to Heroku
git push heroku main
```

**You'll see:**
```
remote: -----> Building on the Heroku-22 stack
remote: -----> Using buildpack: heroku/python
remote: -----> Python app detected
remote: -----> Installing python-3.11.5
remote: -----> Installing requirements with pip
remote: -----> Discovering process types
remote:        Procfile declares types -> web
remote: -----> Compressing...
remote: -----> Launching...
remote:        Released v1
remote:        https://options-scanner-v2-xxxxx.herokuapp.com/ deployed to Heroku
```

---

## ✅ Step 7: Verify Deployment

### Check app status:
```bash
heroku ps
```

**Expected:**
```
=== web (Free): gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
web.1: up 2024/10/12 15:30:00 (~ 1m ago)
```

### View logs:
```bash
heroku logs --tail
```

### Open app in browser:
```bash
heroku open
```

Or visit: `https://options-scanner-v2-xxxxx.herokuapp.com`

---

## 🗄️ Step 8: Initialize Database (if needed)

If this is a fresh database deployment:

```bash
# Connect to Heroku app's database
heroku pg:psql

# Or connect to your NeonDB directly
psql "postgresql://neondb_owner:npg_frKG6w0xePSB@ep-super-king-ad9z2xxi-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
```

Since you're using NeonDB (external PostgreSQL), your database is already set up!

---

## 🔍 Step 9: Test Your App

1. **Open the app:**
   ```bash
   heroku open
   ```

2. **Test PMCC:**
   - Select "Poor Man's Covered Call"
   - Enter: AAPL
   - Click "Scan Opportunities"
   - Should see call options

3. **Test PMCP:**
   - Select "Poor Man's Covered Put"
   - Enter: AAPL
   - Click "Scan Opportunities"
   - Should see put options (different from PMCC)

4. **Check logs for errors:**
   ```bash
   heroku logs --tail
   ```

---

## 📊 Step 10: Monitor Your App

### View real-time logs:
```bash
heroku logs --tail
```

### Check dyno usage:
```bash
heroku ps
```

### View metrics:
Go to: https://dashboard.heroku.com/apps/options-scanner-v2/metrics

---

## 🛠️ Troubleshooting

### App won't start:
```bash
heroku logs --tail
heroku ps
heroku restart
```

### Environment variables not working:
```bash
heroku config
heroku config:set KEY="VALUE"
```

### Database connection errors:
```bash
# Test database connection
heroku run python -c "import psycopg2; import os; conn = psycopg2.connect(os.environ['DATABASE_URL']); print('Connected!')"
```

### Check app configuration:
```bash
heroku config
heroku ps:scale web=1
```

---

## 🔄 Updating Your App

When you make changes:

```bash
# Commit changes
git add .
git commit -m "Your update message"

# Push to GitHub
git push origin main

# Deploy to Heroku
git push heroku main
```

Heroku will automatically:
1. Detect changes
2. Rebuild the app
3. Restart the dynos
4. Deploy new version

---

## 💰 Heroku Free Tier Limits

**Free Dyno Hours:**
- 550 hours/month (without credit card)
- 1000 hours/month (with credit card verified)

**App Behavior:**
- Sleeps after 30 minutes of inactivity
- Takes 10-30 seconds to wake up
- First request after sleep is slower

**To keep app awake (optional):**
- Upgrade to Hobby dyno ($7/month)
- Use external monitoring service (like UptimeRobot)

---

## 🔐 Security Best Practices

### ✅ What we're doing right:
- Environment variables stored on Heroku (not in code)
- `.env` file in `.gitignore`
- PostgreSQL connection uses SSL
- API keys not committed to repository

### ⚠️ Additional recommendations:
1. **Enable 2FA on Heroku account**
2. **Rotate API keys periodically**
3. **Monitor API usage**
4. **Set up alerts for errors**

---

## 📱 Custom Domain (Optional)

To use your own domain:

```bash
# Add domain
heroku domains:add www.yourdomain.com

# Configure DNS with your domain provider
# Point CNAME to: your-app-name.herokudns.com
```

---

## 🎯 Quick Reference Commands

```bash
# View logs
heroku logs --tail

# Restart app
heroku restart

# Run one-off commands
heroku run python

# Scale dynos
heroku ps:scale web=1

# Open app
heroku open

# View config
heroku config

# Access database
heroku pg:psql

# Check app status
heroku ps
```

---

## 📞 Support & Resources

- **Heroku Documentation:** https://devcenter.heroku.com/
- **Heroku Status:** https://status.heroku.com/
- **GitHub Repo:** https://github.com/hathavale/options-scanner-v2
- **Alpha Vantage Docs:** https://www.alphavantage.co/documentation/

---

## ✅ Deployment Checklist

Before going live:

- [ ] Heroku CLI installed
- [ ] Logged into Heroku
- [ ] App created on Heroku
- [ ] Environment variables set
- [ ] Procfile created
- [ ] runtime.txt created
- [ ] gunicorn added to requirements.txt
- [ ] Code committed to git
- [ ] Pushed to Heroku
- [ ] App opens in browser
- [ ] Database connection works
- [ ] PMCC scan works
- [ ] PMCP scan works
- [ ] Logs show no errors

---

## 🎉 Success!

Your Options Scanner v2 is now live on Heroku!

**App URL:** `https://options-scanner-v2-xxxxx.herokuapp.com`

Share this URL with anyone to access your scanner!

---

**Next Steps:**
1. Test thoroughly with different symbols
2. Monitor logs for any errors
3. Set up custom domain (optional)
4. Consider upgrading to Hobby dyno for better performance
5. Share with friends!

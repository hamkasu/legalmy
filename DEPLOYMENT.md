# LegalMY Deployment Guide

## Railway.app Deployment

### Prerequisites

- Railway.app account
- GitHub repository linked to Railway
- PostgreSQL and Redis services on Railway

### Environment Setup

1. **Create Railway project** and connect to the GitHub repository

2. **Add PostgreSQL plugin**
   - Add PostgreSQL database plugin from Railway marketplace
   - Enable pgvector extension:
     ```sql
     CREATE EXTENSION vector;
     ```

3. **Add Redis plugin**
   - Add Redis cache plugin from Railway marketplace

4. **Set environment variables** in Railway Variables:

   ```
   FLASK_ENV=production
   SECRET_KEY=<generate-random-64-byte-hex>
   ANTHROPIC_API_KEY=<your-anthropic-api-key>
   STRIPE_SECRET_KEY=<your-stripe-secret-key>
   STRIPE_WEBHOOK_SECRET=<your-stripe-webhook-secret>
   MAIL_SERVER=smtp.brevo.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=<your-brevo-smtp-username>
   MAIL_PASSWORD=<your-brevo-smtp-password>
   MAIL_DEFAULT_SENDER=noreply@legalmy.com.my
   SENTRY_DSN=<your-sentry-dsn>
   RAILWAY_ENV=production
   ```

5. **Database URL** is automatically injected by Railway as `DATABASE_URL`

6. **Redis URL** is automatically injected by Railway as `REDIS_URL`

### Deployment Checklist

- [ ] Flask environment set to production
- [ ] SECRET_KEY configured (random, secure)
- [ ] DATABASE_URL connected to PostgreSQL
- [ ] REDIS_URL connected to Redis
- [ ] pgvector extension enabled in PostgreSQL
- [ ] ANTHROPIC_API_KEY set
- [ ] STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET set
- [ ] Email configuration (MAIL_*) set
- [ ] SENTRY_DSN for error tracking set
- [ ] Custom domain configured (legalmy.com.my)
- [ ] SSL/TLS certificates enabled
- [ ] Railway volume mounted at `/data/raw/` for raw scraper data

### Running Migrations

Migrations run automatically on deploy via `flask db upgrade` in the `railway.toml` startCommand.

If manual migration is needed:

```bash
railway run flask db upgrade
```

### Worker Service

The Celery worker runs as a separate service in `railway.toml`:

```toml
[[services]]
name = "worker"
startCommand = "celery -A celery_worker worker --loglevel=info -Q default,ingest,alerts"
```

This runs automatically after deployment. Monitor worker status in Railway dashboard.

### Database Backups

Configure Railway automated backups:
1. Go to PostgreSQL plugin settings
2. Enable automated backups (daily recommended)
3. Retention period: 30 days minimum

### Monitoring

- **Health Check**: Railway will probe `/health` endpoint every 30 seconds
- **Sentry**: Error tracking via SENTRY_DSN
- **Logs**: Stream application logs via `railway logs`

### SSL/TLS

Railway provides free SSL certificates. Enable via:
1. Railway Dashboard → Project → Domains
2. Add custom domain (legalmy.com.my)
3. SSL certificate auto-provisioned

### Custom Domain Configuration

1. Point your domain DNS records to Railway:
   - CNAME: `<railway-domain>` (provided by Railway)
2. Update Railway domain settings
3. SSL certificate auto-provisioned

### Post-Deployment

1. Verify application health:
   ```bash
   curl https://legalmy.com.my/health
   ```

2. Create admin user:
   ```bash
   railway run flask shell
   >>> from app import db
   >>> from app.models.user import User
   >>> admin = User(email='admin@legalmy.com.my', full_name='Admin', role='admin')
   >>> admin.set_password('secure-password')
   >>> db.session.add(admin)
   >>> db.session.commit()
   ```

3. Monitor first 24 hours of logs for errors

### Rollback Procedure

If a deployment fails:

1. Railway automatically keeps previous deployments
2. In Railway Dashboard → Deployments → select previous version → Redeploy
3. Database migrations can be rolled back with:
   ```bash
   railway run flask db downgrade
   ```

### Scaling

- **Web service**: CPU/RAM automatically scales. Configure in Railway dashboard.
- **Worker service**: Independent scaling. Add more workers in `railway.toml` if needed.
- **Database**: PostgreSQL auto-scaling available via Railway.
- **Redis**: Pre-configured cache instance (upgrade if needed for high traffic).

### Troubleshooting

**502 Bad Gateway**
- Check `railway logs web`
- Verify database connection: `railway run flask shell`
- Check worker status: `railway logs worker`

**Celery tasks not processing**
- Check worker logs: `railway logs worker`
- Restart worker: Railway Dashboard → Services → Worker → Restart
- Verify Redis connection

**Database migration failed**
- Manual rollback: `railway run flask db downgrade`
- Check migration files in `migrations/versions/`
- Review Alembic log for errors

---

For local development testing before production deployment, follow [README.md](README.md#quick-start) instructions.

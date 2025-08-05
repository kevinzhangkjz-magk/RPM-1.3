# Fix Netlify Environment Variables

The frontend is still trying to connect to localhost:8000 instead of your Railway backend!

## Steps to Fix:

1. Go to Netlify Dashboard: https://app.netlify.com
2. Click on your site "frabjous-cuchufli-daaafb"
3. Go to "Site configuration" → "Environment variables"
4. Add this variable:
   ```
   Key: NEXT_PUBLIC_API_URL
   Value: https://rpm-13-production-ca68.up.railway.app
   ```
5. Click "Save"
6. Go to "Deploys" tab
7. Click "Trigger deploy" → "Clear cache and deploy site"

## Alternative: Update .env.production

Create a file `/apps/frontend/.env.production`:
```
NEXT_PUBLIC_API_URL=https://rpm-13-production-ca68.up.railway.app
```

Then commit and push to trigger a new Netlify build.

## Why This Happens

- Next.js apps use `NEXT_PUBLIC_` prefixed variables for client-side code
- These are baked in at build time, not runtime
- Netlify builds your app with the environment variables you set
- Without setting it, it defaults to localhost:8000
# Migration Status & Debugging

## Recent Changes
All enum values have been updated to lowercase in the codebase and migrations:
- UserRole: free, subscriber, admin, api
- SubscriptionStatus: active, cancelled, trial
- OutcomeType: allowed, dismissed, partly_allowed, struck_out
- CitationRelationship: followed, distinguished, overruled, considered, referred, approved
- HeadcountTier: solo, small, medium, large
- CaseStatus: active, decided, struck_out, settled
- PartyRole: plaintiff, defendant, intervener, appellant, respondent, claimant
- DocumentType: statement_of_claim, defence, affidavit, written_submission, order, judgment
- AlertFrequency: daily, weekly

## If Dashboard Shows "Failed to load dashboard"

**Step 1: Check if migrations are applied**
```
# On Railway terminal or local:
flask db current
flask db upgrade
```

**Step 2: Check subscription record exists**
```sql
-- In production database:
SELECT * FROM subscriptions WHERE user_id = (SELECT id FROM users WHERE email = 'your-email@example.com');
```

**Step 3: Check enum values in database**
```sql
-- Verify enum types have lowercase values:
SELECT enum_range(NULL::userrole);
SELECT enum_range(NULL::subscriptionstatus);
```

**Step 4: Check server logs**
Dashboard error logging includes traceback - look for "Dashboard error:" in logs

## Key Fixes Applied
1. ✅ Flask-Login properties (@property decorators)
2. ✅ Password verification (bcrypt)
3. ✅ Subscription relationship (all references fixed)
4. ✅ Enum values (migration updated)
5. ✅ Dashboard error logging (traceback)
6. ✅ Alert query (explicit join)

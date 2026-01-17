# LexArena Security Checklist

## 1. Firebase Security Rules ✅

**Status:** Rules file created at `firestore.rules`

**Action Required:** Deploy these rules to Firebase:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project `lexarena-99c05`
3. Navigate to **Firestore Database** → **Rules** tab
4. Copy the contents of `firestore.rules` and paste
5. Click **Publish**

**What the rules do:**
- Allow creating predictions with required fields (caseId, timestamp)
- Block updates and deletes (predictions are immutable)
- Allow reading predictions (for community stats)
- Block all other collections

---

## 2. reCAPTCHA Domain Whitelist

**Status:** Needs verification

**Action Required:**

1. Go to [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)
2. Find site key: `6LedAUwsAAAAANi0RBfXLM074heqcW6wK57g6wBP`
3. Verify the **Domains** list contains ONLY:
   - `localhost`
   - `127.0.0.1`
   - Your production domain(s)

**Remove** any test domains, wildcards, or domains you don't control.

---

## 3. Spam Prevention

**Decision:** Accept risk for now (Option C)

**Rationale:**
- Low-traffic open-source project
- reCAPTCHA v3 provides bot protection
- userId tracking prevents duplicate submissions from same browser
- Firebase security rules validate data structure

**If abuse detected later:**
- Implement Firebase Cloud Function for server-side validation
- Add rate limiting via security rules
- Consider requiring authentication

---

## 4. Ground Truth Data Verification

Spot-check these 10 cases against SEC source documents:

| # | Case ID | Defendant | Disgorgement | Injunction | Officer Bar | SEC Link | Verified? |
|---|---------|-----------|--------------|------------|-------------|----------|-----------|
| 1 | LR-26445 | Artur Khachatryan | $373,885 | No | No | [Link](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26445) | ☐ |
| 2 | LR-26444 | James O Ward, Jr. | null | Yes | No | [Link](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26444) | ☐ |
| 3 | LR-26443 | Irfan Mohammed | $385,220 | Yes | No | [Link](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26443) | ☐ |
| 4 | LR-26442 | Charles D. Oliver et al. | null | No | No | [Link](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26442) | ☐ |
| 5 | LR-26441 | Tiffany Kelly / Curastory | null | Yes | Yes | [Link](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26441) | ☐ |
| 6 | LR-26440 | Kevin L. Jefferson et al. | $35,490 | Yes | No | [Link](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26440) | ☐ |
| 7 | LR-26438 | Marshall E. Melton | $916,341 | Yes | No | [Link](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26438) | ☐ |
| 8 | LR-26437 | Rapid Therapeutic Science | $686,090 | Yes | Yes | [Link](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26437) | ☐ |
| 9 | LR-26435 | Oppenheimer & Co. | null | Yes | No | [Link](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26435) | ☐ |
| 10 | LR-26436 | Thomas San Miguel | null | Yes | Yes | [Link](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26436) | ☐ |

**Verification Process:**
1. Click each SEC Link
2. Find the actual judgment/settlement amounts in the litigation release
3. Verify injunction and officer bar provisions match
4. Check the box if verified correct, or note discrepancy

---

## Post-Deployment Verification

After deploying Firebase rules:

```javascript
// Test in browser console on your site
// This should SUCCEED:
db.collection('predictions').add({
  caseId: 'test-123',
  timestamp: new Date().toISOString(),
  disgorgement: 50000,
  injunctionPct: 75,
  officerBarPct: 25
});

// This should FAIL (missing required fields):
db.collection('predictions').add({
  foo: 'bar'
});

// This should FAIL (wrong collection):
db.collection('users').add({
  name: 'test'
});
```

---

## Security Audit Log

| Date | Action | Status |
|------|--------|--------|
| 2026-01-16 | Created firestore.rules | ✅ |
| 2026-01-16 | reCAPTCHA domains | Pending verification |
| 2026-01-16 | Ground truth spot-check | Pending |

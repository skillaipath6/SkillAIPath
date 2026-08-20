# SKILLAIPATH LICENSE SYSTEM - IMPLEMENTATION GUIDE

**Version:** 1.0  
**Purpose:** Workspace-bound license activation with anti-piracy protection  
**Last Updated:** August 19, 2026  
**INTERNAL USE ONLY - Technical Implementation Reference**

---

## PROBLEM STATEMENT

**Scenario:** Customer receives README with embedded license key

```
README_LICENSE.md contains:
LICENSE_KEY = "SKILLAI-abc123-20270816-x8f9a2"
```

**Risk:** Customer can share README → Unlimited redistribution → Revenue loss

---

## SOLUTION: WORKSPACE BINDING

**Principle:** First activation locks the license to that workspace permanently

**Flow:**
```
Customer A activates → Binds to Workspace A → Works only in Workspace A
Customer B tries same key → Workspace B detected → ACTIVATION BLOCKED
```

**Result:** One license = One workspace = One paying customer

---

## TECHNICAL ARCHITECTURE

### Component 1: License Generator (Internal)

**File:** `scripts/generate_license.py`

Generates unforgeable license keys using HMAC-SHA256 signatures.

**Security:**
- Signature cannot be forged without SECRET_KEY
- Expiry embedded in key (tamper-proof)
- Customer ID derived from email (traceable)

### Component 2: Activation Registry (Cloud Database)

**Purpose:** Track which workspace each license is activated in

**Recommended:** Firebase/Supabase - simpler, faster, free tier sufficient

### Component 3: Setup Notebook (Customer Side - One Time)

**File:** `00_Setup_License.py`

**Flow:**
1. Customer runs notebook (license key pre-embedded)
2. Validates signature + expiry
3. Gets current workspace ID
4. Calls activation API
5. Store activation locally (Delta table)
6. Show success message

### Component 4: Validation Cell (Every Notebook - Daily Use)

**Location:** Cell 1 of every SkillAIPath notebook

Silent validation - customers never see it unless there's an error.

---

## DEPLOYMENT AUTOMATION

### GitHub Actions Workflow

**Trigger:** Webhook from purchase form

**Steps:**
1. Generate License Key
2. Embed License in Setup Notebook
3. Create README with Instructions
4. Deploy to Customer Workspace
5. Log License Issuance
6. Send Confirmation Email

---

## ACTIVATION SCENARIOS

### Scenario 1: Legitimate Customer (First Activation)
- Customer purchases → License generated → Deployed → Activated [SUCCESS]

### Scenario 2: Same Customer, Reinstall (Reactivation)
- Customer reinstalls → Reactivates in same workspace [SUCCESS]

### Scenario 3: Piracy Attempt (Different Workspace)
- Person B tries shared key in different workspace → BLOCKED [DENIED]
- Internal alert sent with details

### Scenario 4: Customer Switches Workspaces (Legitimate)
- Customer contacts support → Manual transfer → Continues [SUCCESS]

---

## SECURITY LAYERS

| Layer | Prevents | Detection |
|-------|----------|-----------|
| **HMAC Signature** | Key forgery | Invalid keys rejected |
| **Workspace Binding** | Cross-workspace sharing | API blocks second workspace |
| **Expiry Enforcement** | Expired usage | Daily validation fails |
| **Activation Registry** | Multiple activations | API tracks all attempts |
| **Watermarking** | Anonymous sharing | Customer email in comments |
| **Legal Terms** | Redistribution | License revocation grounds |
| **Telemetry (Optional)** | Silent piracy | Usage patterns tracked |

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Core System (Week 1)
- [ ] License generator script
- [ ] Activation API endpoint
- [ ] Setup notebook
- [ ] Validation cell template
- [ ] Test end-to-end

### Phase 2: Deployment Automation (Week 2)
- [ ] GitHub Actions workflow
- [ ] Form webhook integration
- [ ] Email notifications
- [ ] License logging

### Phase 3: Anti-Piracy (Week 3)
- [ ] Workspace binding enforcement
- [ ] Piracy detection alerts
- [ ] Support process
- [ ] Watermarking

### Phase 4: Monitoring (Week 4)
- [ ] Usage telemetry
- [ ] Admin dashboard
- [ ] Renewal reminders
- [ ] Support ticketing

---

## CONFIGURATION

### Environment Variables (GitHub Secrets)

```bash
LICENSE_SECRET_KEY="your-256-bit-secret"
DATABRICKS_DEPLOY_TOKEN="dapi..."
ACTIVATION_API_KEY="firebase-key"
EMAIL_API_KEY="sendgrid-key"
```

---

## CUSTOMER EXPERIENCE FLOW

### Purchase to Activation (5 Minutes Total)

1. **Purchase** (30 sec) - Customer fills form
2. **Auto-Deployment** (2-3 min) - GitHub Actions deploys
3. **Email Received** (30 sec) - Setup instructions sent
4. **One-Time Activation** (1 min) - Run setup notebook
5. **Daily Usage** (Zero friction) - Silent validation

---

## ERROR MESSAGES (Customer-Facing)

### Error 1: License Not Activated
```
[ERROR] LICENSE ERROR
License not found in workspace.
Did you run the 00_Setup_License notebook?
Contact: tech@skillaipath.com
```

### Error 2: License Expired
```
[ERROR] LICENSE EXPIRED
Your SkillAIPath license expired on 2027-08-16.
Renew at: https://skillaipath.com/renew
```

### Error 3: Already Activated (Different Workspace)
```
[ERROR] LICENSE ALREADY ACTIVATED IN ANOTHER WORKSPACE
This license is single-user and already active.
Contact: tech@skillaipath.com for workspace transfer.
```

### Error 4: Invalid License Key
```
[ERROR] INVALID LICENSE KEY
The license key is invalid or corrupted.
Contact: tech@skillaipath.com with this error message.
```

---

## MONITORING DASHBOARD (Internal Use)

### Key Metrics
- Active Licenses: 147
- Expiring (30 days): 23
- Expired (grace): 5
- Piracy Attempts: 3 [ALERT]
- Support Tickets: 2

---

## SUCCESS METRICS

### System Works When:
- Activation success rate > 95%
- Support tickets < 2% of activations
- Piracy attempts blocked 100%
- Average activation time < 2 minutes
- Zero false positives

### System Fails When:
- API downtime > 5 minutes
- False piracy blocks
- License keys leaked publicly
- Support backlog > 24 hours

---

## MAINTENANCE

**Daily:** Monitor activations, review piracy alerts, respond to tickets  
**Weekly:** Review expiring licenses, send renewal reminders  
**Monthly:** Rotate API keys, backup registry, review logs  
**Quarterly:** Update generator, review effectiveness, gather feedback

---

## NEXT STEPS

### Immediate (This Week)
1. Set up Firebase/Supabase activation registry
2. Create license generator script
3. Build setup notebook with API integration
4. Test end-to-end

### Short-Term (Next 2 Weeks)
1. GitHub Actions deployment automation
2. Form webhook integration
3. Email notification system
4. Piracy detection alerts

### Long-Term (Next Month)
1. Usage telemetry and analytics
2. Admin dashboard for monitoring
3. Automated renewal system
4. Multi-workspace enterprise licenses

---

## SUPPORT

**For Customers:**
- Email: tech@skillaipath.com
- Response time: < 24 hours

**For Internal Team:**
- This guide: Implementation reference
- API docs: activation-api-docs.md
- Troubleshooting: common-issues.md

---

**End of Implementation Guide**

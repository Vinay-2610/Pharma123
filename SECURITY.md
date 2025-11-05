# PharmaChain Security Documentation

## Current Security Implementation (MVP/Demo)

This document explains the security model of the PharmaChain system, its limitations, and how to make it production-ready.

### Authentication & Authorization

**Current Implementation:**
- ✅ Supabase Auth for email/password authentication
- ✅ User profiles stored in dedicated `user_profiles` table
- ✅ Row Level Security (RLS) policies prevent users from modifying their roles
- ✅ Role validation via CHECK constraint (Manufacturer, FDA, Distributor, Pharmacy)
- ⚠️ Users self-select roles during signup (see limitations below)

**Database Security:**
- Row Level Security enabled on `user_profiles` table
- Users can only read their own profile
- Users can insert their profile once during signup
- Users cannot update or delete their profile

### Known Limitations (Demo/Educational Use)

#### 1. Self-Selected Roles at Signup

**Issue:** Users can choose any role when creating an account, allowing potential privilege escalation.

**Why This Exists:** This is an MVP/demonstration system designed to be easy to test and explore. In a real pharmaceutical supply chain, users would be invited or registered by administrators.

**Impact:** Anyone can create an account with FDA or Manufacturer privileges.

**Acceptable For:**
- Development and testing
- Educational demonstrations
- Personal projects
- Prototypes and POCs

**NOT Acceptable For:**
- Production pharmaceutical systems
- Any system handling real patient data
- Regulatory compliance scenarios
- Multi-organization deployments

### Making PharmaChain Production-Ready

To deploy PharmaChain in a production environment, implement one of these approaches:

#### Option 1: Admin Approval Workflow (Recommended)

1. **Modify Signup:**
```sql
-- Add status column to user_profiles
ALTER TABLE user_profiles 
ADD COLUMN status TEXT DEFAULT 'pending' 
CHECK (status IN ('pending', 'active', 'suspended'));

-- Users start in 'pending' status
-- Update RLS policy to only allow active users to access dashboards
```

2. **Create Admin Dashboard:**
- Build an admin interface to approve/reject signups
- Only approved users can access role-specific dashboards
- Administrators can assign/modify user roles

3. **Update Login Logic:**
```python
# In app.py login function
if user_profile['status'] != 'active':
    st.error("Your account is pending approval. Please contact an administrator.")
    return
```

#### Option 2: Invitation-Based System

1. **Pre-create User Invitations:**
```sql
-- Create invitations table
CREATE TABLE user_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

2. **Validate Invitation on Signup:**
- Require invitation token during signup
- Verify token is valid and not expired
- Automatically assign the pre-approved role
- Mark invitation as used

#### Option 3: Backend Service Role Assignment

1. **Create Supabase Edge Function or FastAPI Endpoint:**
```python
# In backend/main.py
from supabase import create_client
import os

# Use service role key (server-side only)
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
admin_supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

@app.post("/admin/assign-role")
async def assign_role(user_id: str, role: str, admin_token: str):
    # Verify admin_token belongs to an admin user
    # Then assign role using service_role client
    admin_supabase.table("user_profiles").update({"role": role}).eq("id", user_id).execute()
```

2. **Update RLS Policies:**
```sql
-- Remove client INSERT policy
DROP POLICY "Users can insert own profile" ON user_profiles;

-- Only service role can insert/update
CREATE POLICY "Service role can manage profiles"
    ON user_profiles
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');
```

#### Option 4: External Identity Provider Integration

For enterprise deployments, integrate with existing identity systems:
- **Okta** - Enterprise SSO with role mapping
- **Auth0** - Custom role assignment via Actions
- **Azure AD** - Group-based role assignment
- **Google Workspace** - Organizational unit based roles

### Data Security Best Practices

#### 1. IoT Data Integrity
- ✅ SHA-256 blockchain hashing implemented
- ✅ Verify hash before trusting data
- Consider: Add digital signatures using private keys

#### 2. API Security
- ⚠️ Currently no rate limiting
- ⚠️ No API key authentication for IoT endpoints
- **Recommendation:** Add API keys for IoT simulator
- **Recommendation:** Implement rate limiting (FastAPI-limiter)

#### 3. Database Security
```sql
-- Enable RLS on IoT data tables
ALTER TABLE iot_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- Manufacturer can only see their batches
CREATE POLICY "Manufacturers see own batches"
    ON iot_data FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid()
            AND role = 'Manufacturer'
            -- Add: AND batch_id IN (SELECT batch_id FROM manufacturer_batches WHERE manufacturer_id = auth.uid())
        )
    );
```

#### 4. Audit Logging

Add audit trails for compliance:
```sql
-- Create audit log table
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    action TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id TEXT,
    old_values JSONB,
    new_values JSONB,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger function to log changes
CREATE OR REPLACE FUNCTION log_audit()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (user_id, action, table_name, record_id, old_values, new_values)
    VALUES (auth.uid(), TG_OP, TG_TABLE_NAME, NEW.id, row_to_json(OLD), row_to_json(NEW));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to sensitive tables
CREATE TRIGGER audit_user_profiles
    AFTER INSERT OR UPDATE OR DELETE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION log_audit();
```

### Compliance Considerations

For pharmaceutical and healthcare applications:

#### HIPAA Compliance (if handling patient data)
- Encrypt data at rest and in transit
- Implement access controls and audit logs
- Sign Business Associate Agreements (BAA) with vendors
- Regular security assessments

#### FDA 21 CFR Part 11 (Electronic Records)
- Implement digital signatures
- Secure audit trails with timestamps
- Version control for all data changes
- Validation of computer systems

#### GDPR Compliance (EU data)
- Data minimization
- Right to deletion
- Data portability
- Privacy by design

### Environment Security

**Development:**
```bash
# .env
SUPABASE_URL=your_dev_url
SUPABASE_KEY=your_dev_anon_key
```

**Production:**
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Rotate keys regularly
- Never commit secrets to version control
- Use environment-specific credentials

### Network Security

1. **CORS Configuration:**
```python
# In backend/main.py - restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Not ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict methods
    allow_headers=["Authorization", "Content-Type"],
)
```

2. **HTTPS Only:**
- Enforce HTTPS in production
- Use HSTS headers
- Configure TLS 1.3

3. **API Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/iot/data")
@limiter.limit("100/minute")  # Max 100 requests per minute
async def receive_iot_data(request: Request, data: IoTData):
    # ... existing code
```

### Monitoring & Incident Response

1. **Set up monitoring:**
   - Application performance monitoring (APM)
   - Error tracking (Sentry, Rollbar)
   - Uptime monitoring
   - Security scanning

2. **Incident response plan:**
   - Define security incident procedures
   - Establish escalation paths
   - Document breach notification requirements
   - Regular security drills

### Security Checklist for Production

- [ ] Implement admin approval or invitation-based signup
- [ ] Remove self-service role selection
- [ ] Enable RLS on all sensitive tables
- [ ] Add audit logging
- [ ] Implement API authentication for IoT endpoints
- [ ] Add rate limiting
- [ ] Configure CORS properly
- [ ] Use HTTPS only
- [ ] Set up monitoring and alerting
- [ ] Regular security audits
- [ ] Penetration testing
- [ ] Compliance validation (FDA, HIPAA, GDPR as needed)
- [ ] Disaster recovery plan
- [ ] Regular backups with encryption
- [ ] Incident response procedures

## Summary

**Current State:** PharmaChain is a functional demonstration system suitable for development, testing, and educational purposes.

**For Production:** Implement the recommended security enhancements based on your specific compliance requirements and organizational security policies.

**Questions?** Review the implementation guides in this document or consult with a security professional for regulatory environments.

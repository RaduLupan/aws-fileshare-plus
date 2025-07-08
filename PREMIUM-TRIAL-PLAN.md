# Premium Trial Implementation Plan v0.7.0

## 🎯 **Project Overview**
Implement a 30-day Premium trial system for Free tier users, allowing them to experience Premium features before upgrading. This includes trial countdown tracking, automatic downgrade, and UI updates to support the new trial flow.

**Target Version**: v0.7.0  
**Implementation Approach**: Backend trial tracking with frontend UI updates  
**Estimated Timeline**: 8-12 hours development time

---

## 📋 **Requirements Summary**

### **User Requirements**
1. **Trial Button**: "Try Premium - Free for 30 days" replaces current "Upgrade to Premium (Free for now)"
2. **Premium Button**: New "Upgrade to Premium" button (grayed out/disabled for now)
3. **Trial Tracking**: 30-day countdown with daily decrement
4. **Auto Downgrade**: Automatic return to Free tier after trial expires
5. **Trial Status Display**: Show remaining trial days to users
6. **One-time Trial**: Prevent multiple trial activations per user

### **Business Logic**
- **Free Users**: Can start 30-day trial (once per user)
- **Trial Users**: Full Premium features + countdown display
- **Expired Trial**: Automatic downgrade to Free tier
- **Premium Users**: No trial options (already Premium)

---

## 🚀 **Implementation Phases**

## **Phase 1: Backend Foundation**

### **1.1 Database Schema Enhancement**
- [ ] **Task**: Add trial tracking to users table
- [ ] **New Columns**:
  ```sql
  ALTER TABLE users ADD COLUMN trial_started_at TIMESTAMP NULL;
  ALTER TABLE users ADD COLUMN trial_expires_at TIMESTAMP NULL;
  ALTER TABLE users ADD COLUMN trial_used BOOLEAN DEFAULT FALSE;
  ```
- [ ] **Migration Strategy**: Runtime migration in database.py
- [ ] **Files**: `backend/database.py`
- [ ] **Status**: ❌ Not Started

### **1.2 User Management Logic**
- [ ] **Task**: Create trial management functions
- [ ] **Functions Needed**:
  ```python
  def start_premium_trial(user_email)
  def check_trial_status(user_email)
  def get_trial_days_remaining(user_email)
  def expire_trial_users()  # Daily cleanup job
  ```
- [ ] **Files**: `backend/user_management.py` (new file)
- [ ] **Status**: ❌ Not Started

### **1.3 Cognito Group Management**
- [ ] **Task**: Update group assignment logic
- [ ] **Groups**:
  - `free-tier` (default)
  - `premium-trial` (new)
  - `premium-tier` (paid)
- [ ] **Auto-assignment**: Add users to `premium-trial` group during trial
- [ ] **Files**: `backend/cognito_utils.py` (enhance existing)
- [ ] **Status**: ❌ Not Started

### **1.4 API Endpoints**
- [ ] **New Endpoint**: `POST /api/start-trial`
  ```json
  Request: {}
  Response: {
    "success": true,
    "trial_expires_at": "2025-08-06T12:00:00Z",
    "days_remaining": 30
  }
  ```
- [ ] **Enhanced Endpoint**: `GET /api/user-status`
  ```json
  Response: {
    "tier": "premium-trial",
    "trial_days_remaining": 25,
    "trial_expires_at": "2025-08-06T12:00:00Z",
    "can_start_trial": false
  }
  ```
- [ ] **Files**: `backend/app.py`
- [ ] **Status**: ❌ Not Started

---

## **Phase 2: Frontend UI Enhancement**

### **2.1 Button Updates for Free Tier**
- [ ] **Task**: Replace upgrade button with trial buttons
- [ ] **Current**: "Upgrade to Premium (Free for now)"
- [ ] **New Layout**:
  ```
  ┌─────────────────────────────────────┐
  │ [Try Premium - Free for 30 days]   │ ← Primary button
  │ [Upgrade to Premium] (grayed out)   │ ← Secondary, disabled
  └─────────────────────────────────────┘
  ```
- [ ] **Files**: `frontend/src/App.jsx`
- [ ] **Status**: ❌ Not Started

### **2.2 Trial Status Display**
- [ ] **Task**: Show trial countdown for trial users
- [ ] **UI Elements**:
  ```
  Premium File Manager (Trial)
  ⏰ 25 days remaining in your trial
  ```
- [ ] **Files**: `frontend/src/App.jsx`
- [ ] **Status**: ❌ Not Started

### **2.3 Trial Expiration Handling**
- [ ] **Task**: Handle trial expiration gracefully
- [ ] **Behavior**: 
  - Redirect to Free tier UI
  - Show "Trial expired" message
  - Offer upgrade to paid Premium
- [ ] **Files**: `frontend/src/App.jsx`
- [ ] **Status**: ❌ Not Started

---

## **Phase 3: Trial Management System**

### **3.1 Daily Cleanup Job**
- [ ] **Task**: Implement automated trial expiration
- [ ] **Options**:
  1. **Lambda Function**: Scheduled daily check
  2. **Backend Cron**: Application-level scheduler
  3. **Manual Check**: On user login (simpler)
- [ ] **Recommended**: Manual check on login (Phase 1)
- [ ] **Files**: `backend/app.py`, potentially AWS Lambda
- [ ] **Status**: ❌ Not Started

### **3.2 Trial Validation Logic**
- [ ] **Task**: Prevent trial abuse
- [ ] **Validations**:
  - One trial per user (check `trial_used` flag)
  - Valid email verification before trial
  - Check trial expiration on each request
- [ ] **Files**: `backend/user_management.py`
- [ ] **Status**: ❌ Not Started

### **3.3 Group Assignment Automation**
- [ ] **Task**: Automatic Cognito group management
- [ ] **Flow**:
  1. Start trial → Add to `premium-trial` group
  2. Trial expires → Remove from trial, add to `free-tier`
  3. Upgrade to paid → Move to `premium-tier` group
- [ ] **Files**: `backend/cognito_utils.py`
- [ ] **Status**: ❌ Not Started

---

## **Phase 4: Testing & Edge Cases**

### **4.1 Trial Flow Testing**
- [ ] **Test**: Start trial button functionality
- [ ] **Test**: Trial countdown accuracy
- [ ] **Test**: Automatic expiration after 30 days
- [ ] **Test**: Group assignment changes
- [ ] **Test**: Prevention of multiple trials
- [ ] **Status**: ❌ Not Started

### **4.2 UI/UX Testing**
- [ ] **Test**: Button layouts on different screen sizes
- [ ] **Test**: Trial status display clarity
- [ ] **Test**: Smooth transitions between tiers
- [ ] **Test**: Error handling for trial failures
- [ ] **Status**: ❌ Not Started

### **4.3 Edge Cases**
- [ ] **Test**: User manually added to premium-trial group
- [ ] **Test**: System clock changes
- [ ] **Test**: User deletion during trial
- [ ] **Test**: Concurrent trial start attempts
- [ ] **Status**: ❌ Not Started

---

## 🎨 **UI/UX Design Specifications**

### **Free Tier User Interface**
```
┌─────────────────────────────────────────────────────────────┐
│ Welcome! You have Free tier access.                        │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🎉 Try Premium Features - Free for 30 days!            │ │
│ │ • Advanced link expiration management                   │ │
│ │ • File organization and search                          │ │
│ │ • Priority support                                      │ │
│ │                                                         │ │
│ │ [Try Premium - Free for 30 days] [Upgrade to Premium]  │ │
│ │                                    (grayed out)        │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### **Trial User Interface**
```
┌─────────────────────────────────────────────────────────────┐
│ Premium File Manager (Trial)                                │
│ ⏰ 25 days remaining in your trial                          │
│                                                             │
│ [Upgrade to Premium] ← Convert to paid                     │
└─────────────────────────────────────────────────────────────┘
```

### **Trial Expired Interface**
```
┌─────────────────────────────────────────────────────────────┐
│ Your Premium trial has ended                                │
│ 🎯 Enjoyed the Premium features?                            │
│                                                             │
│ [Upgrade to Premium] [Continue with Free]                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 **Database Schema Changes**

### **Users Table Enhancement**
```sql
-- Add trial tracking columns
ALTER TABLE users ADD COLUMN trial_started_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN trial_expires_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN trial_used BOOLEAN DEFAULT FALSE;

-- Index for efficient trial queries
CREATE INDEX idx_users_trial_expires ON users(trial_expires_at);
```

### **Example User Records**
```sql
-- Free user (never tried trial)
INSERT INTO users (email, tier, trial_used) VALUES 
('user1@email.com', 'free', false);

-- Trial user (active)
INSERT INTO users (email, tier, trial_started_at, trial_expires_at, trial_used) VALUES 
('user2@email.com', 'premium-trial', '2025-07-07', '2025-08-06', true);

-- Expired trial user
INSERT INTO users (email, tier, trial_used) VALUES 
('user3@email.com', 'free', true);
```

---

## 🔧 **Technical Implementation Details**

### **Trial Status Enum**
```python
class TrialStatus(Enum):
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    EXPIRED = "expired"
    USED = "used"
```

### **Trial Management Functions**
```python
def get_user_trial_status(user_email):
    """Return comprehensive trial status for user"""
    return {
        'status': TrialStatus.ACTIVE,
        'days_remaining': 25,
        'can_start_trial': False,
        'expires_at': '2025-08-06T12:00:00Z'
    }

def start_premium_trial(user_email):
    """Start 30-day trial for eligible user"""
    # Validate eligibility
    # Update database
    # Assign Cognito group
    # Return trial info
```

### **Frontend State Management**
```javascript
const [userStatus, setUserStatus] = useState({
  tier: 'free',
  trialDaysRemaining: null,
  canStartTrial: true,
  trialExpiresAt: null
});
```

---

## 🎯 **Success Criteria**

### **Functional Requirements**
- [ ] Free users see "Try Premium - Free for 30 days" button
- [ ] "Upgrade to Premium" button is visible but disabled
- [ ] Trial users get full Premium features for 30 days
- [ ] Trial countdown displays accurately
- [ ] Automatic downgrade after trial expiration
- [ ] Prevention of multiple trials per user

### **Technical Requirements**
- [ ] Database schema supports trial tracking
- [ ] Cognito groups handle trial users correctly
- [ ] API endpoints provide trial management
- [ ] Frontend handles all trial states smoothly
- [ ] Automated cleanup of expired trials

### **Business Requirements**
- [ ] Clear trial value proposition in UI
- [ ] Smooth trial-to-paid conversion flow
- [ ] Trial abuse prevention mechanisms
- [ ] Analytics tracking for trial conversion

---

## 🚀 **Implementation Strategy**

### **Phase 1: Foundation (Days 1-2)**
1. Database schema updates
2. Basic trial management functions
3. API endpoint creation

### **Phase 2: UI Updates (Days 3-4)**
1. Button layout changes
2. Trial status display
3. Frontend state management

### **Phase 3: Integration (Days 5-6)**
1. Cognito group automation
2. Trial expiration handling
3. End-to-end testing

### **Phase 4: Polish & Launch (Days 7-8)**
1. Edge case handling
2. UI/UX refinements
3. Production deployment

---

## 📝 **Risk Considerations**

### **Technical Risks**
- **Cognito Group Limits**: AWS limits on group memberships
- **Trial Abuse**: Users creating multiple accounts
- **Data Consistency**: Trial status synchronization
- **Performance**: Daily cleanup job efficiency

### **Business Risks**
- **Trial Conversion**: Low trial-to-paid conversion rates
- **User Confusion**: Complex trial UI/flow
- **Support Load**: Increased trial user support requests

### **Mitigation Strategies**
- Start with simple manual cleanup (not automated)
- Clear trial terms and countdown display
- Monitor trial metrics closely
- Gradual rollout to subset of users first

---

## 🏁 **Completion Checklist**

### **Development Complete**
- [ ] All backend changes implemented and tested
- [ ] All frontend changes implemented and tested
- [ ] Integration testing completed
- [ ] Edge cases handled

### **Deployment Ready**
- [ ] Code committed to dev branch
- [ ] Backend deployed and verified
- [ ] Frontend deployed and verified
- [ ] End-to-end testing completed

### **Documentation & Milestone**
- [ ] README.md updated with v0.7.0 features
- [ ] Version tagged as v0.7.0
- [ ] Trial system features documented

---

## 🎉 **Future Enhancements**

### **v0.7.1 Potential Features**
- Trial extension for valuable users
- Trial analytics dashboard
- A/B testing for trial duration
- Referral trial bonuses

### **v0.8.0 Payment Integration**
- Stripe integration for Premium upgrades
- Subscription management
- Billing dashboard
- Payment failure handling

---

**Last Updated**: July 7, 2025  
**Status**: Ready for Implementation  
**Next Action**: Begin Phase 1 - Backend Foundation  
**Dependencies**: v0.6.4 Premium File Explorer (✅ Complete)

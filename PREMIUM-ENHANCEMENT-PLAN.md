# Premium File Explorer Enhancement Plan v0.6.4

## 🎯 **Project Overview**
Enhance the Premium File Explorer with advanced link expiration management, including visual expiration indicators, flexible link duration selection, and improved user experience.

**Target Version**: v0.6.4  
**Implementation Approach**: Option A - Minimal Backend Changes with Dropdown UI  
**Estimated Timeline**: 6-9 hours development time

---

## 📋 **Requirements Summary**

### **User Requirements**
1. ✅ **Expiration Visibility**: Show "Expires On" column with clear time indicators
   - Valid links: "3 days", "1 day", etc.
   - Expired links: "4 days ago", "1 day ago", etc.

2. ✅ **Flexible Link Generation**: Dropdown selection for new link durations
   - Options: 1, 3, 5, or 7 days
   - Default selection: 3 days

3. ✅ **Visual Indicators**: Color-coded expiration status
   - Green: Valid links
   - Red: Expired links

4. ✅ **Real-time Updates**: Immediate UI updates when new links are generated

---

## 🚀 **Implementation Phases**

## **Phase 1: Backend Foundation** ✅

### **1.1 Database Enhancement**
- [x] **Task**: Update SQLite schema for expiration tracking
- [x] **Details**: 
  ```sql
  ALTER TABLE url_mappings ADD COLUMN expires_in_days INTEGER DEFAULT 7;
  UPDATE url_mappings SET expires_in_days = 7 WHERE expires_in_days IS NULL;
  ```
- [x] **Files**: `backend/database.py`, `backend/url_shortener.py`
- [x] **Status**: ✅ Complete

### **1.2 URL Shortener Updates**
- [x] **Task**: Modify `create_short_url()` function
- [x] **Details**: Accept and store `expires_in_days` parameter
- [x] **Files**: `backend/url_shortener.py`
- [x] **Status**: ✅ Complete

### **1.3 API Endpoint: `/api/files/new-link`**
- [x] **Task**: Accept `expiration_days` parameter
- [x] **Request Format**:
  ```json
  {
    "file_key": "user@email.com/filename.pdf",
    "expiration_days": 3
  }
  ```
- [x] **Validation**: Ensure 1-7 day range, default to 3 days
- [x] **Files**: `backend/app.py`
- [x] **Status**: ✅ Complete

### **1.4 API Endpoint: `/api/files`**
- [x] **Task**: Include expiration data in response
- [x] **Response Format**:
  ```json
  {
    "files": [
      {
        "filename": "filename.pdf",
        "size_display": "3.8 MB", 
        "upload_date": "Jul 07, 2025",
        "expires_in_days": 3,
        "expires_at": "2025-07-10T12:00:00",
        "short_code": "aBc123"
      }
    ]
  }
  ```
- [x] **Files**: `backend/app.py`
- [x] **Status**: ✅ Complete

---

## **Phase 2: Frontend UI Enhancement** ⏳

### **2.1 File Table Structure Update**
- [ ] **Task**: Add "Expires On" column to Premium File Explorer
- [ ] **Layout Change**: 
  ```
  Before: File Name | Size | Upload Date | Actions
  After:  File Name | Size | Upload Date | Expires On | Actions
  ```
- [ ] **Files**: `frontend/src/App.jsx`
- [ ] **Status**: ❌ Not Started

### **2.2 New Link Dropdown Component**
- [ ] **Task**: Replace simple "New Link" button with dropdown
- [ ] **UI Options**:
  ```
  [New Link ▼] → Dropdown:
  ┌─────────────────┐
  │ ○ 1 day         │
  │ ● 3 days        │ ← Default
  │ ○ 5 days        │
  │ ○ 7 days        │
  └─────────────────┘
  ```
- [ ] **Files**: `frontend/src/App.jsx`
- [ ] **Status**: ❌ Not Started

### **2.3 Color Coding CSS**
- [ ] **Task**: Add CSS classes for expiration status
- [ ] **Classes**:
  ```css
  .expires-valid { color: green; }
  .expires-expired { color: red; }
  ```
- [ ] **Files**: `frontend/src/App.css` or inline styles
- [ ] **Status**: ❌ Not Started

---

## **Phase 3: Integration & Logic** ⏳

### **3.1 Expiration Calculation Logic**
- [ ] **Task**: Implement client-side expiration calculation
- [ ] **Function**: 
  ```javascript
  function calculateExpiresOn(shortUrl) {
    const createdDate = new Date(shortUrl.created_at);
    const expirationDate = new Date(createdDate.getTime() + (shortUrl.expires_in_days * 24 * 60 * 60 * 1000));
    const now = new Date();
    const diffDays = Math.ceil((expirationDate - now) / (24 * 60 * 60 * 1000));
    
    if (diffDays > 0) {
      return {
        text: `${diffDays} day${diffDays > 1 ? 's' : ''}`,
        isExpired: false
      };
    } else {
      const expiredDays = Math.abs(diffDays);
      return {
        text: `${expiredDays} day${expiredDays > 1 ? 's' : ''} ago`,
        isExpired: true
      };
    }
  }
  ```
- [ ] **Files**: `frontend/src/App.jsx`
- [ ] **Status**: ❌ Not Started

### **3.2 Real-time UI Updates**
- [ ] **Task**: Update "Expires On" immediately after new link generation
- [ ] **Behavior**: 
  - User selects expiration from dropdown
  - New link generated successfully
  - "Expires On" column updates instantly
  - Color coding applied correctly
- [ ] **Files**: `frontend/src/App.jsx`
- [ ] **Status**: ❌ Not Started

### **3.3 State Management**
- [ ] **Task**: Manage dropdown state and file list updates
- [ ] **Details**: 
  - Track selected expiration days
  - Update file list after successful link generation
  - Handle loading states during API calls
- [ ] **Files**: `frontend/src/App.jsx`
- [ ] **Status**: ❌ Not Started

---

## **Phase 4: Testing & Polish** ⏳

### **4.1 Functional Testing**
- [ ] **Test**: All expiration durations (1, 3, 5, 7 days)
- [ ] **Test**: Expired link display ("X days ago")
- [ ] **Test**: Color coding (green=valid, red=expired)
- [ ] **Test**: Default 3-day selection works
- [ ] **Test**: Real-time updates after link generation
- [ ] **Status**: ❌ Not Started

### **4.2 Edge Case Testing**
- [ ] **Test**: Links expiring today (boundary case)
- [ ] **Test**: Very old expired links
- [ ] **Test**: Invalid expiration days (should default to 3)
- [ ] **Test**: Network failures during link generation
- [ ] **Status**: ❌ Not Started

### **4.3 UI/UX Polish**
- [ ] **Task**: Ensure dropdown UX is smooth
- [ ] **Task**: Verify table layout doesn't break on different screen sizes
- [ ] **Task**: Test color contrast for accessibility
- [ ] **Task**: Add loading indicators if needed
- [ ] **Status**: ❌ Not Started

---

## 📱 **Expected User Experience**

### **Scenario 1: Viewing Files with Valid Links**
```
User sees table:
┌─────────────────────────────────────────────────────────────────────────┐
│ File Name               │ Size │Upload Date│ Expires On │ Actions        │
├─────────────────────────────────────────────────────────────────────────┤
│ Real Canadian Super...  │ 3.8MB│ Jul 07    │  3 days    │[New Link ▼]   │
│                         │      │   2025    │ (green)    │[Email] [Delete]│
└─────────────────────────────────────────────────────────────────────────┘
```
- ✅ Clear indication of time remaining
- ✅ Green color indicates valid link

### **Scenario 2: Viewing Files with Expired Links**
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Old Document.pdf        │ 1.2MB│ Jul 01    │4 days ago  │[New Link ▼]   │
│                         │      │   2025    │  (red)     │[Email] [Delete]│
└─────────────────────────────────────────────────────────────────────────┘
```
- ✅ Clear indication link is expired
- ✅ Red color warns user of expired status

### **Scenario 3: Generating New Link**
1. User clicks "New Link ▼"
2. Dropdown opens with 1, 3, 5, 7 day options (3 days pre-selected)
3. User selects "5 days"
4. New link generated
5. "Expires On" immediately updates to "5 days" (green)
6. User sees immediate feedback

---

## 🛠️ **File Modification Checklist**

### **Backend Files**
- [ ] `backend/database.py` - Database schema update
- [ ] `backend/url_shortener.py` - Enhanced short URL creation
- [ ] `backend/app.py` - API endpoint modifications

### **Frontend Files**  
- [ ] `frontend/src/App.jsx` - UI components and logic
- [ ] `frontend/src/App.css` - Color coding styles (if needed)

### **Testing Files**
- [ ] Manual testing checklist completion
- [ ] Edge case validation
- [ ] Cross-browser compatibility

---

## 📊 **Success Criteria**

### **Functional Requirements**
- [ ] ✅ "Expires On" column displays correctly for all files
- [ ] ✅ Valid links show "X days" in green
- [ ] ✅ Expired links show "X days ago" in red  
- [ ] ✅ Dropdown allows selection of 1, 3, 5, 7 days
- [ ] ✅ Default selection is 3 days
- [ ] ✅ Real-time updates work after link generation

### **Technical Requirements**
- [ ] ✅ Backend API accepts expiration_days parameter
- [ ] ✅ Database stores expiration information
- [ ] ✅ Frontend calculates expiration correctly
- [ ] ✅ No breaking changes to existing functionality
- [ ] ✅ Maintains existing JWT authentication

### **User Experience Requirements**
- [ ] ✅ Intuitive dropdown interaction
- [ ] ✅ Clear visual distinction between valid/expired
- [ ] ✅ Immediate feedback on link generation
- [ ] ✅ Consistent with existing UI patterns

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
- [ ] README.md updated with v0.6.4 features
- [ ] Version tagged as v0.6.4
- [ ] Premium File Explorer features updated in documentation

---

## 📝 **Notes & Considerations**

### **Technical Notes**
- Keep debug logging in place until v1.0 as agreed
- Maintain backward compatibility with existing short URLs
- Use existing JWT authentication patterns
- Follow established code patterns in both frontend and backend

### **Future Enhancements** 
- Consider adding bulk operations for multiple files
- Potential analytics dashboard for link usage
- Advanced search/filtering capabilities

---

**Last Updated**: July 7, 2025  
**Status**: Ready for Implementation  
**Next Action**: Begin Phase 1 - Backend Foundation

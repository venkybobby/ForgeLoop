# TRACE GUIDE: Login with Credentials

## State Machine Overview
The login process follows a linear progression through distinct states. Monitor page state, form state, and network state at each transition.

## State Cards

### STATE 1: Login Page Loaded
**Entry**: User navigates to or is redirected to login page  
**Check**:
- [ ] Current URL is login page (contains '/login', '/signin', '/auth', etc.)
- [ ] Page title contains 'Login', 'Sign In', 'Authentication', etc.
- [ ] No error messages or warnings visible
- [ ] SSL certificate is valid (HTTPS)

**Actions**:
- Identify login form container
- Locate username input field
- Locate password input field
- Locate submit button

**Next State**: Username Field Focused OR Field Not Found (FAIL)

---

### STATE 2: Username Field Focused
**Entry**: Username field is located and clicked  
**Check**:
- [ ] Field has focus (cursor visible, border highlighted)
- [ ] Field is empty or pre-populated (note if pre-filled)
- [ ] Field is interactive (not disabled)

**Actions**:
- Clear any existing text
- Type username value

**Next State**: Username Entered

---

### STATE 3: Username Entered
**Entry**: Username text has been typed into field  
**Check**:
- [ ] Username value is visible in the field
- [ ] Value matches expected username exactly
- [ ] No validation errors appeared for username field

**Actions**:
- Click password field to focus

**Next State**: Password Field Focused

---

### STATE 4: Password Field Focused
**Entry**: Password field is located and clicked  
**Check**:
- [ ] Field has focus (cursor visible)
- [ ] Field is empty or pre-populated
- [ ] Field is interactive (not disabled)
- [ ] Characters will be masked (verify field type='password')

**Actions**:
- Clear any existing text
- Type password value

**Next State**: Password Entered

---

### STATE 5: Password Entered
**Entry**: Password text has been typed into field  
**Check**:
- [ ] Password field shows masked characters (dots/asterisks)
- [ ] Field contains password value (do not expose in logs)
- [ ] No validation errors appeared for password field

**Actions**:
- Locate submit button
- Click submit button

**Next State**: Form Submitted (Waiting for Response)

---

### STATE 6: Form Submitted
**Entry**: Submit button has been clicked  
**Check**:
- [ ] Button shows loading state (spinner, disabled, text change)
- [ ] Network request is in progress (check Network tab)
- [ ] Form has not re-rendered with new form state
- [ ] No error message immediately appeared

**Wait**: Page response (10-30 seconds typical)  
**Monitor**: Network requests, page URL, page content

**Next State**: Navigation in Progress OR Login Error (FAIL)

---

### STATE 7: Navigation in Progress
**Entry**: Page is loading new content after form submission  
**Check**:
- [ ] URL is changing from login page
- [ ] Page shows loading indicator (spinner, blank page, content fading)
- [ ] Response status is 200 or 302 (redirect)
- [ ] No error messages in console

**Wait**: Page to fully load (10-30 seconds)

**Next State**: Authenticated Page Loaded OR Redirect Back to Login (FAIL)

---

### STATE 8: Authenticated Page Loaded ✓ SUCCESS
**Entry**: New page has loaded after successful authentication  
**Check**:
- [ ] URL has changed from login page (e.g., /login → /dashboard)
- [ ] URL does NOT contain login path again
- [ ] Page displays authenticated content (user profile, dashboard, protected resource)
- [ ] No login form is visible
- [ ] Page fully loaded (no loading spinners)
- [ ] Session cookie or auth token is present in browser storage
- [ ] Page title or heading indicates authenticated state

**Terminal State**: LOGIN SUCCESSFUL ✓

---

## Failure States

### FAIL STATE A: Field Not Found
**Entry**: Username or password field cannot be located  
**Check**:
- [ ] Attempted all standard selectors
- [ ] Page has fully loaded (not still loading)
- [ ] Field is not hidden or off-screen
- [ ] Field is not within a collapsed accordion/modal

**Recovery Actions**:
1. Refresh page and retry
2. Inspect page HTML for alternative field identifiers
3. Check if page requires JavaScript to render form
4. Escalate: Form structure is non-standard

**Terminal State**: SKILL CANNOT PROCEED

---

### FAIL STATE B: Login Error Message
**Entry**: Error message appears after form submission  
**Examples**:
- "Invalid username or password"
- "User account not found"
- "Account locked"
- "Email not verified"

**Check**:
- [ ] Error message text clearly indicates reason
- [ ] Form is still visible and can be resubmitted
- [ ] URL has NOT changed (still on login page)

**Recovery Actions**:
1. Verify credentials are correct (check case, whitespace, special characters)
2. Check for temporary account lock (wait and retry)
3. If account is locked, escalate to account recovery flow
4. If credentials are unknown, escalate to password reset

**Terminal State**: AUTHENTICATION FAILED (INVALID CREDENTIALS)

---

### FAIL STATE C: Redirect Back to Login
**Entry**: Page navigated but returned to login page  
**Check**:
- [ ] Current URL is login page again
- [ ] Form is empty or re-rendered
- [ ] Session cookie was not created or persisted

**Recovery Actions**:
1. Verify credentials were entered correctly
2. Check browser cookie settings (ensure 3rd-party cookies allowed if needed)
3. Clear browser cache/cookies and retry login
4. Check browser console for JavaScript errors
5. Verify server is functioning (check status page)

**Terminal State**: SESSION NOT PERSISTED

---

### FAIL STATE D: Page Loading Indefinitely
**Entry**: Loading spinner persists; page does not complete load  
**Check**:
- [ ] Network requests are pending (not completed)
- [ ] No timeout errors in console
- [ ] URL has changed from login page

**Recovery Actions**:
1. Wait up to 30 seconds for network response
2. Check browser console for JavaScript errors
3. Check Network tab for failed requests
4. Stop page load (press Escape) and check current state
5. If no progress, escalate: Server error or network issue

**Terminal State**: TIMEOUT / SERVER ERROR

---

### FAIL STATE E: CAPTCHA or MFA Required
**Entry**: CAPTCHA puzzle or MFA code input appears  
**Check**:
- [ ] Form is asking for additional verification
- [ ] This is not the primary login form

**Recovery Actions**:
1. This skill does not handle secondary verification
2. Escalate to appropriate secondary verification skill (if available)
3. If unavailable, authentication cannot proceed

**Terminal State**: SECONDARY VERIFICATION REQUIRED (OUT OF SCOPE)

---

## Trace Checklist

When reviewing a login trace, verify:

- [ ] **Entry State**: User was on login page with valid credentials available
- [ ] **Actions Sequence**: Username → Password → Submit button clicked (in order)
- [ ] **No Intermediate Errors**: No error messages between steps
- [ ] **Network Response**: Form submission received a successful response (200, 302)
- [ ] **Navigation Occurred**: Page URL changed from login page
- [ ] **Content Verification**: New page displays authenticated content
- [ ] **Session Established**: Browser storage shows auth token/cookie
- [ ] **Exit State**: Terminal success condition met

## Common Trace Patterns

### Pattern 1: Happy Path (Simple Login)
```
LOAD /login
CLICK username field
INPUT "user@example.com"
CLICK password field
INPUT "password"
CLICK Login button
WAIT for navigation
LOAD /dashboard
VERIFY authenticated content
✓ SUCCESS
```

### Pattern 2: Recovery from Invalid Credentials
```
LOAD /login
CLICK username field
INPUT "user@example.com"
CLICK password field
INPUT "wrongpassword"
CLICK Login button
ERROR: "Invalid credentials" message appears
CLICK username field
CLEAR and re-input "user@example.com"
CLICK password field
CLEAR and re-input "correctpassword"
CLICK Login button
WAIT for navigation
LOAD /dashboard
✓ SUCCESS on retry
```

### Pattern 3: Recovery from Field Not Found
```
LOAD /login
SEARCH for username field (standard selectors fail)
INSPECT page HTML
FIND username field with non-standard id
CLICK field using alternative selector
INPUT username
...(continue with alternative selectors)...
✓ SUCCESS with adapted approach
```

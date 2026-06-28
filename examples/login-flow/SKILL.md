# Skill: Login with Credentials

## Purpose
Authenticate a user by submitting valid username and password credentials through a login form.

## When to Use
Use this skill whenever you need to access a protected resource or authenticated user session. The skill should be invoked when a login page is detected or when credentials are required to proceed.

## Preconditions
- You are on a page that contains a login form
- Username and password input fields are visible and in an interactive state
- A submit button (labeled 'Login', 'Sign In', or similar) is present
- You have valid credentials available (username and password values)

## Step-by-Step Procedure

### 1. Verify Login Page
- Confirm the current page is a login page by checking the URL, page title, or form labels
- Verify no security warnings or certificate errors are present

### 2. Locate and Focus Username Field
- Search for username input field using common selectors:
  - `input[name='username']` or `input[id='username']`
  - `input[name='user']` or `input[name='email']`
  - `input[aria-label*='username']` or `input[placeholder*='username']`
- Click on the field to ensure focus

### 3. Enter Username
- Clear any pre-filled text in the username field
- Type the username value provided
- Verify the value appears correctly in the field

### 4. Locate and Focus Password Field
- Search for password input field using common selectors:
  - `input[type='password']`
  - `input[name='password']` or `input[id='password']`
  - `input[aria-label*='password']`
- Click on the field to ensure focus

### 5. Enter Password
- Clear any pre-filled text in the password field
- Type the password value provided (characters will be masked)
- Do NOT log or expose the password value in any trace

### 6. Locate Submit Button
- Search for the login submit button using common selectors:
  - `button:contains('Login')` or `button:contains('Sign In')`
  - `input[type='submit']`
  - `button[type='submit']`
  - `button[aria-label*='login']`

### 7. Click Submit Button
- Click the submit button
- Wait for the page to respond (do not click multiple times)
- Monitor for visual feedback (loading spinner, button disabled state)

### 8. Wait for Navigation
- Allow the page to navigate to the post-login destination
- Wait for the new page to fully load
- Monitor for any error messages or redirects back to login

### 9. Verify Authentication Success
- Confirm the URL has changed from the login page
- Verify the new page shows authenticated content (user profile, dashboard, etc.)
- Check that session/auth tokens are present in browser storage (if accessible)
- Confirm no login form is visible on the new page

## Milestones
1. ✓ Username field located and focused
2. ✓ Username entered into field
3. ✓ Password field located and focused
4. ✓ Password entered into field
5. ✓ Submit button located
6. ✓ Submit button clicked
7. ✓ Page navigation initiated
8. ✓ New page loaded (URL changed)
9. ✓ Authenticated content verified

## Success Criteria (Terminal Conditions)
- The page URL has changed from the login page to an authenticated resource
- The new page displays user-specific or authenticated content
- No login form is visible on the new page
- The page load completes without error
- Session/auth cookies or tokens are present in browser storage

## Failure Scenarios & Recovery

### Login Form Still Visible
- **Symptom**: Form reloads after submit button click
- **Cause**: Form submission may have failed silently
- **Recovery**: Verify credentials are correct, clear form fields, and retry submission

### Invalid Credentials Error
- **Symptom**: Error message appears (e.g., 'Invalid username or password')
- **Cause**: Credentials provided are incorrect or user account doesn't exist
- **Recovery**: Verify credentials are correct; check for case sensitivity or whitespace issues

### Redirected Back to Login
- **Symptom**: Page navigates to login page again immediately
- **Cause**: Session was not persisted or server rejected the authentication
- **Recovery**: Retry login; check browser cookie settings; verify server is functioning

### CAPTCHA or MFA Required
- **Symptom**: CAPTCHA challenge or multi-factor authentication code field appears
- **Cause**: Additional verification required before login completes
- **Recovery**: This skill does not handle CAPTCHA/MFA; escalate or use separate skill if available

### Page Loads Indefinitely
- **Symptom**: Loading spinner persists; page does not fully load
- **Cause**: Network timeout, server error, or unresponsive server
- **Recovery**: Wait longer; check browser console for errors; retry the entire login flow

### Field Not Found
- **Symptom**: Username or password field cannot be located
- **Cause**: Field uses non-standard selectors or is dynamically rendered
- **Recovery**: Inspect page HTML; try alternative selectors; check if page has fully loaded

## Rules & Constraints

### Things You MUST Do
- Verify the page is a legitimate login form before entering credentials
- Enter credentials exactly as provided (respect case and whitespace)
- Wait for each action to complete before proceeding to the next step
- Confirm authentication success before considering the task complete

### Things You MUST NOT Do
- Do NOT use browser password managers or autofill features; manually enter credentials
- Do NOT log, store, or expose passwords in any trace or debug output
- Do NOT click 'Forgot Password' or 'Sign Up' links unless explicitly required
- Do NOT submit the form multiple times if it appears unresponsive
- Do NOT attempt to bypass login with URL manipulation or direct session access

### Security Boundaries
- Only submit credentials to pages with valid SSL certificates (HTTPS)
- Verify the URL domain matches the expected service domain
- Do NOT submit credentials if the page shows phishing warnings
- Do NOT proceed if certificate validation fails

## Related Skills
- **Logout**: Terminate the authenticated session
- **Handle CAPTCHA**: Complete CAPTCHA challenges if required
- **Multi-Factor Authentication**: Complete MFA/2FA verification steps
- **Account Recovery**: Reset password or recover locked account

## Examples

### Example 1: Simple Username/Password Login
```
1. Navigate to https://example.com/login
2. Find username field (id='username')
3. Enter 'john.doe@example.com'
4. Find password field (type='password')
5. Enter 'SecurePassword123'
6. Click 'Login' button
7. Wait for redirect to https://example.com/dashboard
8. Confirm user profile or dashboard content is visible
```

### Example 2: Login with Non-Standard Fields
```
1. Navigate to https://service.com/auth/signin
2. Find username field (aria-label='Email Address')
3. Enter 'user@service.com'
4. Find password field (name='pass')
5. Enter provided password
6. Click submit button (data-testid='signin-button')
7. Wait for navigation to authenticated area
8. Verify session token in localStorage
```

## Troubleshooting Checklist
- [ ] Page is definitely a login page (check URL and page title)
- [ ] Fields are visible and interactive (not hidden or disabled)
- [ ] Credentials are correct (check for case sensitivity)
- [ ] Browser allows cookies and localStorage (check settings)
- [ ] Network connection is stable
- [ ] No certificate or HTTPS warnings present
- [ ] JavaScript is enabled (form submission may require JS)
- [ ] No pop-ups or overlays blocking the form

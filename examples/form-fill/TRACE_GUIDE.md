# TRACE GUIDE: Fill and Submit Form

## Navigation State Cards

Follow this sequence to trace successful form submission:

### STATE 1: Form Page Loaded
**Conditions**: 
- Current URL contains form path (e.g., /forms/post, /contact, /checkout)
- Form element is visible on page
- Input fields, dropdowns, and submit button are rendered

**Action**: Proceed to STATE 2 (Identify Fields)

**False Alarm**: If form does not load (404, timeout), navigate to form URL and retry

---

### STATE 2: Identify Form Fields
**Conditions**:
- Form structure is understood
- All required fields are catalogued
- Submit button is located and visible

**Action**: Proceed to STATE 3 (Populate Fields)

**False Alarm**: If fields are not visible, scroll down or wait for page to fully load

---

### STATE 3: Populate Required Fields
**Conditions**:
- At least one text field has been clicked and focused
- Data has been entered into text fields
- Dropdowns/selects have been clicked and options selected
- No validation errors are visible yet

**Action**: Continue populating; once all fields are filled, proceed to STATE 4

**False Alarm**: If a field shows a validation error (red border, error text), correct the data and re-populate

---

### STATE 4: Verify Form Completeness
**Conditions**:
- All required fields are populated
- All dropdown selections are made
- All radio/checkbox selections are made
- No validation error messages are visible
- Submit button is enabled (not greyed out)

**Action**: Proceed to STATE 5 (Click Submit)

**False Alarm**: If validation errors are present, do NOT proceed; correct fields and return to STATE 3

---

### STATE 5: Click Submit Button
**Conditions**:
- Submit button is visible and enabled
- Form is fully populated
- No validation errors are visible

**Action**:
1. Click submit button once
2. Wait 2–3 seconds for page response
3. Observe page (look for loading spinner, URL change, new content)

**Next State**: Proceed to STATE 6 (Monitor Page Response)

**False Alarm**: If page does not respond within 3 seconds, wait an additional 3–5 seconds before proceeding

---

### STATE 6: Monitor Page Response
**Conditions**:
- Submit button was clicked
- Page is responding (loading indicator visible, or URL is changing)

**Observations**:
- **Loading spinner visible**: Wait for page to load; proceed to STATE 7
- **URL changed**: Page is navigating; proceed to STATE 7
- **New page content appearing**: Proceed to STATE 7
- **Form reloaded with errors**: Treat as FAILURE; go to STATE 8 (Handle Validation Errors)
- **Modal or dialog appeared**: Treat as FALSE TERMINAL STATE; close modal if possible, investigate

**Next State**: STATE 7 or STATE 8 (depending on observation)

---

### STATE 7: Confirm Page Navigation & Load
**Conditions**:
- URL has changed from form URL
- New page content is loading or fully loaded
- Page shows confirmation, results, or success message

**Observations**:
- **Success message visible** ("Thank you", "Confirmation", order details, etc.): **→ SUCCESS TERMINAL STATE**
- **Results page displayed**: **→ SUCCESS TERMINAL STATE**
- **Redirected to different domain/path**: **→ SUCCESS TERMINAL STATE**
- **Page is still loading** (spinner visible): Wait up to 10 seconds, then proceed
- **Page reloaded to form with errors**: **→ FAILURE (go to STATE 8)**
- **Error message displayed** (not validation error, but server error): Investigate and retry

**Next State**: STATE 8 (if errors) or SUCCESS (if confirmation)

---

### STATE 8: Handle Validation or Submission Errors
**Conditions**:
- Form reloaded (or page shows error message)
- Error message(s) indicate missing or invalid field(s)
- Submit did not navigate to new page

**Actions**:
1. Read each error message carefully
2. Identify the flagged field(s)
3. Correct the field data:
   - For missing fields: Enter required data
   - For invalid fields: Clear and re-enter in correct format
4. Verify all other fields still contain correct data
5. **Return to STATE 4** (Verify Completeness) and revalidate
6. **Return to STATE 5** (Click Submit) and resubmit

**Recovery Loop**: If errors persist, repeat this state up to 3 times. If errors continue, escalate (check data format, inspect form HTML, etc.)

---

## Terminal States

### ✓ SUCCESS TERMINAL STATE
**Indicators**:
- URL has changed from form URL to results/confirmation page
- Page displays:
  - "Thank you" or "Success" message
  - Order confirmation or receipt
  - Results or summary data
  - Redirect landing page
- No error messages are visible
- No loading spinner is visible

**Action**: Task complete. Skill execution successful.

---

### ✗ FAILURE TERMINAL STATE
**Indicators**:
- Form reloaded multiple times with same or different validation errors
- Submit button does not trigger any page response after multiple attempts
- Server error (500, 503) displayed
- Form is broken or inaccessible

**Action**: Log failure reason. Potential recovery:
1. Clear browser cache
2. Refresh page and retry form
3. If issue persists, escalate to manual investigation

---

### ⚠ FALSE TERMINAL STATES (Do NOT Stop)

| State | Why It's False | Recovery |
|---|---|---|
| Form filled, submit not clicked | Task incomplete; submit is required | Click submit button |
| Loading spinner visible | Page may still be processing | Wait 5–10 seconds for page load |
| Modal dialog appeared | Not actual submission | Close modal, investigate error, retry submit |
| Form reloaded to same URL | Validation failed | Go to STATE 8 (Handle Errors) |
| Page refreshed without navigation | Possible client-side error | Wait 2–3 seconds, observe for late navigation; if none, retry |

---

## Quick Reference: State Flowchart

```
START
  ↓
STATE 1: Form Page Loaded?
  ├─ YES → STATE 2
  └─ NO → Reload form URL

STATE 2: Identify Fields
  ↓
STATE 3: Populate Fields
  ↓
STATE 4: Verify Completeness
  ├─ Validation errors → Correct → STATE 3
  ├─ All fields OK → STATE 5
  └─ NO → Go back to STATE 3

STATE 5: Click Submit
  ↓
STATE 6: Monitor Response
  ├─ Loading/URL changing → STATE 7
  ├─ Form reloaded with errors → STATE 8
  └─ Modal appeared → Investigate, close, retry

STATE 7: Confirm Navigation & Load
  ├─ Success message / Results → ✓ SUCCESS
  ├─ Error message / Form reloaded → STATE 8
  └─ Still loading → Wait, then re-observe

STATE 8: Handle Errors
  ├─ Correct field(s)
  ├─ Return to STATE 4
  └─ Retry STATE 5

✓ SUCCESS: Task Complete
```

---

## Debugging Checklist

If stuck in any state:
1. **Verify form is loaded**: Check URL, look for form elements
2. **Verify field data**: Confirm all required fields are populated with valid data
3. **Check for validation errors**: Look for red borders, error messages, tooltips
4. **Verify submit button**: Confirm it's not disabled (greyed out) and is clickable
5. **Check browser console**: Look for JavaScript errors (F12 → Console tab)
6. **Inspect network tab**: Check for failed requests after submit (F12 → Network tab)
7. **Wait for async operations**: Some forms have client-side validation; wait 2–3 seconds before retrying
8. **Clear cache**: Ctrl+Shift+Delete → Clear cache and cookies, retry form

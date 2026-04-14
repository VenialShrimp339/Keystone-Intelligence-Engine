# Browser Use Cloud / OSS Split, Auth, and Anti-Bot Reality

Audit scope:
- Browser Use repo at commit `5970007d86b99c073307ac78150eaff6631de807`
- Focused on cloud wrappers, sandbox, profiles, auth/storage state, captcha/proxy handling, Gmail/2FA, and embedded docs

Bottom line:
- The open-source package is real and useful, but the strongest difficult-site capabilities are concentrated in Browser Use Cloud, not in the bare OSS runtime.
- The OSS package gives Keystone browser control, state persistence, proxy auth wiring, HAR/video/download hooks, and generic CDP connectivity.
- Browser Use Cloud adds the things that matter most for hard acquisition at scale: managed stealth/residential proxying, cloud profiles, cloud browser sessions, hosted sandbox execution, live takeover/share links, search/task APIs, and skillized website automation.
- Strategically, the most important surprise is not "the OSS package secretly solves anti-bot." It does not.
- The real surprise is that the repo embeds a fairly large cloud product surface that could matter as a fallback acquisition vendor/control arm, while the OSS runtime remains a thinner browser-agent framework with some useful low-level primitives.

## 1. Open-Source vs Cloud Capability Table

| Capability | OSS package | Cloud-only or cloud-dependent | Evidence |
|---|---|---|---|
| Local browser automation | Yes. Local Chromium/Chrome sessions, direct CDP control, CLI/MCP direct control. | No. | `browser_use/browser/session.py`, `browser_use/skill_cli/sessions.py`, `skills/open-source/references/integrations.md` |
| Connect to any remote browser via CDP | Yes. `Browser(cdp_url=...)` works with any CDP provider. | No. | `skills/open-source/references/browser.md:219-237` |
| Browser Use Cloud browser provisioning | Thin OSS wrapper only. The package can request a cloud browser and receive `cdpUrl`/`liveUrl`. | Yes. Actual browser infra is remote. | `browser_use/browser/cloud/cloud.py:27-105`, `browser_use/browser/cloud/views.py:28-84` |
| Local proxy config | Yes. Custom proxy URL plus optional username/password. | No. | `browser_use/browser/profile.py:521-532`, `browser_use/browser/profile.py:879-886` |
| Proxy auth challenge handling | Yes. Handles HTTP proxy auth via CDP Fetch. | No. | `browser_use/browser/session.py:1901-2030` |
| Managed residential proxy country routing | No in OSS package itself. | Yes. Cloud docs expose residential proxy countries and make them default/recommended. | `browser_use/browser/cloud/views.py:46-60`, `skills/cloud/references/api-v2.md:170-183`, `skills/cloud/references/features.md:11-27` |
| Stealth / anti-fingerprinting stack | Partial, light-touch only. Some launch arg tweaks and masking claims exist, but not a full shipped stealth system. | Yes for the real productized story. | `browser_use/browser/profile.py:390-398`, `README.md:272-287`, `skills/cloud/references/features.md:11-27` |
| CAPTCHA solving | No standalone local solver shipped. Watchdog only listens for proxy-emitted events. | Yes in practice. Cloud docs/README tie solving to cloud browsers + proxies. | `browser_use/browser/watchdogs/captcha_watchdog.py:1-207`, `browser_use/browser/profile.py:605-608`, `README.md:272-275` |
| Real Chrome profile reuse | Yes. Can attach to real Chrome profile and copy it into temp user-data for safe reuse. | No. | `skills/open-source/references/browser.md:173-189`, `browser_use/browser/profile.py:797-842` |
| Storage state export/load/merge | Yes. Cookies, localStorage, sessionStorage are loaded, merged, and auto-saved. | No. | `browser_use/browser/watchdogs/storage_state_watchdog.py:49-345`, `browser_use/browser/session.py:1603-1623` |
| Cloud profile persistence across sessions | No, except through cloud service. | Yes. | `skills/cloud/references/sessions.md:56-88`, `skills/cloud/references/api-v2.md:219-238` |
| Local-to-cloud profile sync | Not built into Python runtime itself; delegated to external script/binary. | Yes, because the target is a cloud profile. | `README.md:263-268`, `browser_use/skill_cli/profile_use.py:25-104`, `browser_use/skill_cli/README.md:261-275` |
| Hosted production sandbox | No local equivalent in this decorator. | Yes. `@sandbox` uploads pickled code to Browser Use infra. | `browser_use/sandbox/sandbox.py:215-380`, `skills/open-source/references/quickstart.md:115-189` |
| Live browser URL / public share URL | Not for local OSS runtime by default. | Yes. | `browser_use/browser/cloud/cloud.py:90-95`, `browser_use/sandbox/views.py:26-32`, `skills/cloud/references/sessions.md:43-52` |
| Search API that browses/extracts content | No OSS implementation in package. | Yes. | `examples/cloud/05_search_api.py:1-123`, `examples/cloud/README.md:88-125` |
| Cloud task/session API | No. Local MCP/CLI exists, but not the hosted task/session product. | Yes. | `skills/cloud/references/api-v2.md:21-218`, `skills/open-source/references/integrations.md:61-72` |
| Skills / marketplace / "website into API endpoint" | Not as an OSS runtime feature. Local agents can call cloud skills, but the skill system is cloud. | Yes. | `skills/cloud/references/api-v2.md:239-271`, `skills/cloud/references/features.md:143-178`, `skills/open-source/references/integrations.md:147-167` |
| Persistent cloud filesystem / workspaces | No. Local filesystem exists only where you run it. | Yes. | `README.md:110-116`, `skills/cloud/references/features.md:68-106` |
| Hosted MCP server | No. OSS offers a local stdio MCP server. | Yes. | `skills/open-source/references/integrations.md:11-72`, `skills/open-source/references/integrations.md:76-143` |
| Recommended LLM path | No fully local default. The recommended `ChatBrowserUse` is itself a cloud API client. | Yes. | `browser_use/llm/browser_use/chat.py:1-95`, `README.md:204-217` |

## 2. Auth / Browser-State Findings

### What the OSS package can really do

1. Reuse a real logged-in Chrome profile.
   - The docs explicitly support `Browser.from_system_chrome()` and manual `user_data_dir` + `profile_directory` usage for existing saved logins.
   - The implementation copies the Chrome profile into a temp directory before use, which is useful operationally because it reduces direct corruption risk to the user's main profile.
   - Evidence:
     - `skills/open-source/references/browser.md:173-189`
     - `browser_use/browser/profile.py:797-842`

2. Persist browser auth state with a file-based storage state.
   - `StorageStateWatchdog` auto-loads on browser connect, auto-saves on interval/shutdown, merges with existing state, restores cookies, and injects localStorage/sessionStorage via init scripts.
   - This is real OSS functionality and probably the strongest open-source auth/session primitive in the package.
   - Evidence:
     - `browser_use/browser/watchdogs/storage_state_watchdog.py:49-86`
     - `browser_use/browser/watchdogs/storage_state_watchdog.py:167-345`
     - `browser_use/browser/session.py:1603-1623`

3. Export storage state from a live session.
   - The docs and example support exporting auth state to JSON for later reuse.
   - Evidence:
     - `skills/open-source/references/browser.md:128-138`
     - `examples/browser/save_cookies.py:38-45`

4. Inject secrets and generate TOTP codes.
   - `sensitive_data` supports domain-scoped secrets.
   - Keys ending in `bu_2fa_code` are converted into current TOTP codes at replacement time.
   - The agent also warns when secrets are used without `allowed_domains`, which matters for prompt-injection risk.
   - Evidence:
     - `skills/open-source/references/browser.md:140-169`
     - `browser_use/tools/registry/service.py:442-485`
     - `browser_use/agent/service.py:526-573`

5. Read Gmail for email-based OTP/verification codes.
   - Gmail integration is real OSS code, but it is not magic. It uses Gmail API OAuth, local token files, and a read-only inbox scope.
   - It is useful for 2FA retrieval, but it is separate from browser-session auth.
   - Evidence:
     - `browser_use/integrations/gmail/service.py:25-137`
     - `browser_use/integrations/gmail/actions.py:29-113`

### What the cloud product adds on top

1. Persistent cloud profiles across sessions.
   - Browser Use Cloud profiles are first-class objects with CRUD and reuse patterns.
   - Docs explicitly recommend per-user/per-site patterns and refreshing old profiles.
   - Evidence:
     - `skills/cloud/references/sessions.md:56-88`
     - `skills/cloud/references/api-v2.md:219-238`

2. Profile sync from local browser into cloud profile.
   - This is an important auth bridge for hard sites.
   - But it is not a pure Python open-source feature. It relies on `profile.sh` or the external `profile-use` Go binary downloaded from Browser Use infrastructure.
   - Evidence:
     - `README.md:261-268`
     - `browser_use/skill_cli/profile_use.py:25-104`
     - `browser_use/skill_cli/README.md:261-275`

3. Manual live takeover on remote sessions.
   - Cloud sessions and sandbox/browser sessions surface `liveUrl`, which makes human login bootstrap and recovery much more practical for difficult/authenticated sites.
   - Evidence:
     - `browser_use/browser/cloud/cloud.py:90-95`
     - `browser_use/sandbox/views.py:26-32`
     - `skills/cloud/references/sessions.md:30-52`
     - `skills/cloud/references/features.md:199-226`

## 3. Stealth / Proxy / CAPTCHA Reality

### What is genuinely present in OSS

1. Proxy support is real.
   - You can set `ProxySettings(server, bypass, username, password)`.
   - The session layer implements proxy auth challenge handling with CDP Fetch.
   - This means Browser Use OSS can work with bring-your-own proxy infrastructure.
   - Evidence:
     - `browser_use/browser/profile.py:521-532`
     - `browser_use/browser/profile.py:879-886`
     - `browser_use/browser/session.py:1901-2030`

2. Some anti-fingerprint tuning exists, but it is modest.
   - The code opts out of Playwright's default `--enable-automation` flag and comments that the automation fingerprint is masked via JS and other flags.
   - There are some defaults around permissions/extensions intended to improve automation and page cleanliness.
   - This is directionally helpful, but it is not a complete stealth browser product.
   - Evidence:
     - `browser_use/browser/profile.py:319-324`
     - `browser_use/browser/profile.py:390-398`
     - `browser_use/browser/profile.py:601-616`
     - `browser_use/browser/profile.py:924-1053`

3. Default extensions help with page usability, not serious bot evasion.
   - Shipped defaults are uBlock Origin Lite, a cookie-banner helper, and a background-tab extension.
   - The commented-out captcha extension is not active.
   - Evidence:
     - `browser_use/browser/profile.py:965-999`

4. Generic CDP connectivity is strategically important.
   - Because `Browser(cdp_url=...)` is supported, the OSS package can sit on top of a third-party browser provider with stronger stealth if Keystone wants to BYO vendor instead of Browser Use Cloud.
   - Evidence:
     - `skills/open-source/references/browser.md:219-237`

### What is not truly solved in OSS

1. CAPTCHA solving is not implemented locally in any serious sense.
   - `CaptchaWatchdog` only listens for `BrowserUse.captchaSolverStarted` and `BrowserUse.captchaSolverFinished` CDP events.
   - The profile field description explicitly says this is only active when the browser emits Browser Use CDP events, e.g. Browser Use cloud browsers.
   - The README flatly says to use Browser Use Cloud for CAPTCHA handling because you need better fingerprinting and proxies.
   - Evidence:
     - `browser_use/browser/watchdogs/captcha_watchdog.py:1-207`
     - `browser_use/browser/profile.py:605-608`
     - `README.md:272-275`

2. The repo's own docs tie real stealth to cloud infrastructure.
   - The README recommends cloud browsers for stealth, proxy rotation, and scaling.
   - Cloud docs say stealth is on by default and cite anti-fingerprinting, CAPTCHA solving, Cloudflare bypass, and residential proxies.
   - Evidence:
     - `README.md:105-115`
     - `README.md:280-287`
     - `skills/cloud/references/features.md:11-27`

3. The strongest proxy story is cloud, not OSS.
   - Cloud API docs expose residential proxies, 195+ countries, and pricing/proxy usage accounting.
   - OSS gives only a hook for custom proxies or any-CDP-provider connectivity.
   - Evidence:
     - `skills/cloud/references/api-v2.md:170-183`
     - `skills/cloud/references/api-v3.md:69-97`
     - `skills/cloud/references/features.md:11-43`

### Practical interpretation for Keystone

If Keystone wants difficult-site acquisition, there are two different plays here:

1. Use Browser Use OSS as a browser-control framework.
   - Valuable for local profile reuse, storage-state persistence, downloads/PDF acquisition, HAR/video capture, proxy auth, and generic CDP integration.
   - Not enough by itself to claim "we now have a robust stealth/anti-bot acquisition layer."

2. Use Browser Use Cloud as a managed acquisition vendor.
   - Valuable because the hard parts are concentrated there: residential proxying, profile sync, live takeover, cloud sessions/browsers, hosted search/task APIs, and the productized stealth story.
   - This is the version that could materially help Keystone on difficult sites, but it comes with vendor dependency and governance tradeoffs.

## 4. Vendor / Ops Risk

1. The recommended path is vendor-backed, not self-contained.
   - `ChatBrowserUse` is a cloud API client, not a local model wrapper.
   - The repo repeatedly recommends cloud browsers and cloud production paths.
   - Evidence:
     - `browser_use/llm/browser_use/chat.py:1-95`
     - `README.md:105-115`
     - `skills/open-source/references/quickstart.md:115-189`

2. The `@sandbox` production path uploads executable code to Browser Use infrastructure.
   - The decorator cloudpickles function inputs/closures, base64-encodes code, and POSTs it to `https://sandbox.api.browser-use.com/sandbox-stream`.
   - For Keystone, that is a serious boundary: it is not just "remote browser," it is remote code execution on vendor infra.
   - Evidence:
     - `browser_use/sandbox/sandbox.py:286-380`

3. Some important auth/profile pieces are outside the main Python package.
   - Profile sync depends on `profile.sh` and an external `profile-use` binary fetched at runtime from Browser Use-controlled URLs.
   - That raises supply-chain, reproducibility, and reviewability concerns.
   - Evidence:
     - `README.md:263-268`
     - `browser_use/skill_cli/profile_use.py:25-104`

4. Billing and capability gating are real.
   - Cloud browsers have free/paid timeout limits.
   - Profiles can require subscription.
   - Proxies, skills, sessions, and cloud search/task APIs are part of the commercial surface.
   - Evidence:
     - `browser_use/browser/cloud/views.py:22-24`
     - `browser_use/browser/cloud/views.py:53-60`
     - `skills/cloud/references/api-v2.md:170-183`
     - `skills/cloud/references/api-v2.md:219-238`
     - `skills/cloud/references/features.md:143-178`

5. Data governance surface expands quickly in the cloud product.
   - Live URLs, share URLs, cloud profiles, uploaded files, hosted skills, and remote logs all widen the operational attack surface.
   - Evidence:
     - `browser_use/browser/cloud/cloud.py:90-95`
     - `browser_use/sandbox/views.py:26-32`
     - `skills/cloud/references/api-v2.md:82-95`
     - `skills/cloud/references/sessions.md:43-52`

## 5. Strategic Take for Keystone

What looks strategically important for difficult-site acquisition:

1. Generic CDP support in OSS.
   - This is the cleanest "keep ownership" angle.
   - Keystone could use Browser Use's browser/session/watchdog stack against a browser provider of its own choosing rather than buying into the full Browser Use Cloud platform.

2. Storage state + real profile reuse in OSS.
   - These are genuinely useful primitives for authenticated and JS-heavy acquisition.

3. Browser Use Cloud profiles + residential proxies + live takeover.
   - This is the strongest part of the Browser Use product for hard sites.
   - If Keystone ever wants a vendor-backed acquisition fallback, this is the actual value center.

4. Cloud Search API and skill system.
   - These are not part of the OSS retrieval runtime.
   - They may be useful as benchmark/control-arm or exploratory fallback research.
   - They are not a substitute for Keystone's governed retrieval/evidence contracts.

Net judgment from this pass:
- Browser Use OSS is not secretly a full anti-bot acquisition solution.
- Browser Use Cloud may be strategically relevant for Keystone difficult-site acquisition.
- The repo's hidden value is less "we missed a magical open-source stealth stack" and more "the product surface is much broader than the Python package alone, and the difficult-site advantages mostly live in the commercial cloud layer."

## 6. Concrete File Refs

Core cloud wrapper:
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/cloud/cloud.py`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/cloud/views.py`

Cloud-backed sandbox:
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/sandbox/sandbox.py`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/sandbox/views.py`

Browser profile, proxy, extensions, light anti-fingerprint behavior:
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/profile.py`

Captcha and storage-state auth/session persistence:
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/watchdogs/captcha_watchdog.py`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/watchdogs/storage_state_watchdog.py`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/session.py`

Cloud auth and profile sync:
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/sync/auth.py`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/skill_cli/profile_use.py`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/skill_cli/README.md`

Local 2FA / secrets / Gmail:
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/tools/registry/service.py`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/integrations/gmail/service.py`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/integrations/gmail/actions.py`

Open-source docs that blur into cloud:
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/README.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/skills/open-source/references/browser.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/skills/open-source/references/quickstart.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/skills/open-source/references/integrations.md`

Embedded cloud docs/examples that reveal the broader product:
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/skills/cloud/references/api-v2.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/skills/cloud/references/features.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/skills/cloud/references/sessions.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/examples/cloud/README.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/examples/cloud/04_proxy_usage.py`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/examples/cloud/05_search_api.py`


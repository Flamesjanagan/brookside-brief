# The Brookside Brief — Morning Publishing Playbook

How the daily update works now that the site lives on Vercel (v0 build).

---

## Your public link

Share **this** address (not the one with the random hash):

> **https://v0-vercel-deployment-ten.vercel.app**

The link you were given earlier — the one containing `...g8snakr5g...` — is a *deployment-specific* URL and Vercel keeps those behind a login on purpose. The address above is the production link and is the one to send people.

**If the production link still asks people to sign in:** open the project in Vercel → **Settings → Deployment Protection → Vercel Authentication → Disabled → Save.** Then anyone can open it.

---

## The daily loop (about 2 minutes)

1. **You:** finish the morning `.docx` as usual and send it to me here (drag the file into the chat).
2. **Me:** I convert it and send back two things:
   - the brief formatted as clean **paste-ready content**, and
   - a short **v0 instruction** to drop in.
3. **You:** open your project on **v0.app**, paste the instruction + content into the chat, and let v0 update the page. v0 redeploys automatically.
4. **Verify:** refresh **https://v0-vercel-deployment-ten.vercel.app** — the new brief is live for everyone.

That's it. No code, no terminal.

---

## The v0 instruction template

Each morning I'll fill this in for you, but here's the shape so you know what's coming:

> Update the **Morning Brief** section to today's edition, dated **[DATE]**. Replace the current brief body with the content below, keeping the existing masthead, navigation, Macro Terminal, Stock Picks, and styling exactly as they are. Also update the dateline in the top bar to **[DATE]**.
>
> [FULL BRIEF CONTENT — I provide this]

---

## Notes & options

- **Why uploads-through-the-site don't publish for everyone:** a browser upload only saves to *that person's* browser. Having one upload appear for all visitors needs server-side storage. If you ever want a true in-site "Upload" button that publishes for everyone, I can build that with Vercel Blob and a password — just ask; it's a one-time setup.
- **The live v0 build is currently trimmed** (shorter brief, and the Macro Terminal / Stock Picks tabs are visual only). Pasting my full content restores the complete brief. If you want the interactive Macro Terminal and Stock Picks builder back too, tell me and I'll give v0 the exact pieces to rebuild them.
- **The badger logo** is already on your live site at `/images/badger-logo.png` — it carried into v0 fine.
- **Archive of past briefs:** I keep every `.docx` you send in this folder, so we always have the full back catalogue to republish if needed.

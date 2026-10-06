---
name: design-md-library
description: Library of 74 ready-made DESIGN.md design systems inspired by real brands (Vercel, Stripe, Linear, Apple, Notion, Airbnb, Spotify, Tesla, Supabase, Figma, etc.). Use when the user wants a page, site, or component "in the style of" / "like" a known brand, asks for a DESIGN.md, or wants a ready design system (colors, typography, spacing, components) to build consistent UI.
---

# DESIGN.md Library

Source: [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) (MIT). Each file in `designs/` is a DESIGN.md (Google Stitch format): YAML front matter with color, typography, spacing and radius tokens, followed by prose rules for layout, components, imagery and do/don't guidance.

Available designs (file `designs/<name>.md`):
airbnb, airtable, apple, binance, bmw-m, bmw, bugatti, cal, claude, clay, clickhouse, cohere, coinbase, composio, cursor, dell-1996, elevenlabs, expo, ferrari, figma, framer, hashicorp, hp, ibm, intercom, kraken, lamborghini, linear.app, lovable, mastercard, meta, minimax, mintlify, miro, mistral.ai, mongodb, nike, nintendo-2001, notion, nvidia, ollama, opencode.ai, pinterest, playstation, posthog, raycast, renault, replicate, resend, revolut, runwayml, sanity, sentry, shopify, slack, spacex, spotify, starbucks, stripe, supabase, superhuman, tesla, theverge, together.ai, uber, vercel, vodafone, voltagent, warp, webflow, wired, wise, x.ai, zapier

## How to use

1. Map the user's request to one design name above (e.g. "like Linear" → `linear.app`, "Claude style" → `claude`). If several fit or none is named, propose 2–3 candidates and let the user pick.
2. Read `designs/<name>.md` in full before writing UI. The files are long (~40 KB); read the whole file rather than skimming the tokens only.
3. Apply it:
   - **To build UI now:** translate the tokens into the project's styling system (Tailwind theme / CSS variables), then follow the component and layout rules when writing pages.
   - **If the user wants the design system in the project:** copy the file to the project root as `DESIGN.md` so every later agent turn uses it.
4. These are *inspired interpretations*, not official brand assets. Do not reproduce logos, trademarks, or proprietary fonts the project is not licensed for; use the suggested fallbacks, and don't present the result as the brand's own site.

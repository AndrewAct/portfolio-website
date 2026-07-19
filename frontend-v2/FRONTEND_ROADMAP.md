# Frontend Roadmap

Check this file at the start of every session. Mark items done as you go.

---

## Completed

- [x] GitHub social icon added (bottom-left, HomeView.vue)
- [x] Projects page at `/projects` — TickSense glass card with full feature list → ticksense.ai
- [x] WrightSOP / 图匠 project card — bilingual name, Hanyu Pinyin plus English-IPA guide, original/modern dictionary definition, Supabase-backed architecture stack, and tujiang.build CTA
- [x] Projects page navigation — accessible previous/next controls with looping project count
- [x] Projects data source — typed `src/data/projects.ts` catalog keeps content out of the view component
- [x] Utilities page — full glassmorphism redesign over homepage background image
- [x] Horoscope result card — redesigned as premium cream "oracle card" with Cormorant Garamond title, gold accent bar, hidden duplicate h2/h3 via CSS
- [x] Font: switched from Syne (too flat/wide) to Cormorant Garamond italic 700 for all display titles
- [x] Consistent glass design system: `rgba(255,255,255,0.09)` + `blur(32px) saturate(190%)` + inner highlight inset shadow

---

## Projects Page

- [x] Carousel navigation: left/right arrow buttons to scroll through multiple projects
- [ ] Auto-refresh every 60 seconds (when project list becomes API-driven)
- [x] Data source: move project content to a typed catalog — adding a project no longer requires component changes
- [ ] Consider glassmorphism card grid for multiple projects (reference: `lvyovo-wiki.tech/projects`)

---

## Utilities

- [ ] Update `horoscope-styles.scss` download button to use an SVG icon instead of the emoji `⬇`
- [ ] Restore the History button (currently commented out in HomeView.vue — line 14)
- [ ] `/horoscope` route exists but has no real implementation (HoroscopeView.vue is a placeholder)

---

## General / Future

- [x] Add WrightSOP / 图匠 to the Projects page
- [ ] Add more projects to the Projects page as they ship
- [ ] Consider a shared `GlassPage.vue` layout component to DRY up the background + overlay + back-button pattern used by both `/projects` and `/utilities`

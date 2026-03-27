# BadenHackt Frontend

Vue 3, TypeScript, Vite. **Kein** mitgelieferter Tailwind-Plus-/Vendor-Block im Repository – nur die tatsächlich genutzten Komponenten.

## Struktur (Kurz)

| Pfad | Inhalt |
|------|--------|
| `src/styles/tokens.css` | Farben, Radii, Schatten, Layout-Breiten (`--color-*`, `--layout-*`) |
| `src/styles/base.css` | Import von `tokens.css`, Reset, `body` |
| `src/constants/copy.ts` | Deutsche UI-Strings |
| `src/components/ui/` | `UiButton`, `UiModal` |
| `src/components/layout/` | `AppTopBar` |
| `src/components/dashboard/` | `RoomCard`, `DashboardPageTitle`, `WhitelistModal` |

Build: `npm run build` · Dev: `npm run dev`

Siehe Root-`project.md` für Gesamtprojekt und Changelog.

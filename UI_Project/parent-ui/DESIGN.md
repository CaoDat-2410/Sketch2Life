# Sketch2Life · Parent Android UI

## Visual direction

An illustrated storybook that starts with a child's drawing and opens into a living world. The three supplied farm-app videos informed the full-height scenic illustration, layered paper surface, soft spatial depth, and tap-driven scene change. All artwork in this preview is original SVG for Sketch2Life; farm data, weather controls, and reward mechanics are not used.

The first screen has one promise and one primary action. The scene is playful for children; the paper sheet, clear typography, and restrained controls are for parents. Interior screens keep the same forest green, cream paper, sky blue, and warm sun palette while giving form tasks a calmer setting.

The two later supplied farm clips were reviewed across their timelines. Their interaction pattern is a scenic hero above a rounded information sheet, with selectable locations, a focused detail state, and smooth environmental transitions. The Parent home now adapts that pattern into three illustrated story worlds: Khu vườn, Dòng suối, and Bầu trời. Scene buttons update the artwork, concise heading, and a contextual card. The first two cards open existing stories; the sky card opens an existing family lesson. The scenes are original Sketch2Life illustrations, with a flying butterfly, rocking paper boat, drifting clouds, and floating paper plane. Farm maps, weather data, and agriculture features are deliberately absent because they have no place in the Parent workflow. Interior pages use shorter entrance and press transitions so reading and forms remain calm.

## Tokens and components

- Ink `#24433e`; primary forest `#245f4d`; sky `#a9d9eb`; paper `#fffbf1`; sun `#f5cf76`.
- Baloo 2 for short display headings, Be Vietnam Pro for actions and body copy.
- 8px spacing rhythm; 18–30px rounded surfaces; soft elevation only where layers overlap.
- Full-width primary action for the next required step. Secondary actions stay text or light surfaces.
- Home scene has a reversible “nét vẽ / sống dậy” preview; it does not create or mutate a story run.
- The home page is one vertical scroll surface. Android bottom navigation stays visible; the story flow has its own scrollable content and a stable action footer.

## Motion and accessibility

- The cloud, butterfly, boat, and paper plane loop only in their respective scenes. Scene switching uses opacity/transform; no scroll hijacking or forced autoplay.
- `prefers-reduced-motion: reduce` removes looping motion and transitions.
- Primary controls are at least 44px tall, with visible keyboard focus. Icon-only controls have names; SVG scene art has a text alternative.
- Copy is intentionally short on the home screen. Legal/privacy and consent copy remains available where a parent must make an informed decision.

## Login preview

The supplied login clip was reviewed at half-second intervals. Its sequence is a layered scenic reveal, an illustrated hero that contracts behind a rounded white form, a muted-to-active login button, and a brief loading transition into the main screen. The Parent preview follows that sequence with original Sketch2Life storybook artwork and Vietnamese copy. The scene enters over roughly one second so the form remains usable without a prolonged splash delay.

Open `?preview=login` on the local preview URL to review the login directly. This is a UI prototype: email/password validation, password visibility, remember-toggle visuals, and transition states work locally; the action enters the demo and explicitly says no account was authenticated. No credentials are saved or sent to a server.

The `Tạo tài khoản` action opens `?preview=signup`'s matching Parent registration screen. It validates email, password presence and password confirmation locally, with errors beside each input. A valid form reports that no account was created because Firebase Authentication is not integrated in this preview. Child profile setup remains a separate later step. The redundant child switcher was removed from the Home header; profile selection remains available in the bottom navigation's Hồ sơ screen and the story setup flow.

## Workflow boundary

The Parent mainflow still follows `PARENT_FLOW_AUDIT.md`: one child and optional lesson → artwork → idea/audio and transcript confirmation if needed → subject confirmation → minimal context → script/storyboard review → asynchronous video and safety gate → activities only after a playable video with a pinned lesson. The visual toggle and animations never bypass these gates. This remains a React/Vite UI preview with local fixtures, not verified native Android or live backend integration.

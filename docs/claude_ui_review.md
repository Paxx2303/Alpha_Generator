# Claude UI Review Pack

Updated: 2026-05-18
Scope: Sprint 1 review for frontend changes

## Files changed

- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/src/types.ts`
- `frontend/src/index.css`

## What to review

### TASK-02 Credential masking

- Settings credentials now use password inputs by default through `CredentialInput`.
- Reveal/hide toggle changes button label and `aria-label` between `eye` and `eye-off`.
- WorldQuant credential row includes `Test connection` button.
- Save flow now submits only dirty fields instead of the whole form.

Review points:

- In `SettingsPage`, confirm `buildDirtyPayload()` excludes unchanged fields.
- Confirm secret fields reset to blank after save.
- Confirm password and API key fields stay masked unless revealed.

### TASK-03 Warning badge in Alphas UI

- Alphas table shows extra `Warning` badge when `needs_review` is true.
- Alpha detail header also shows the warning badge.
- Alpha detail page displays `gate_failure_reason` when present.

Review points:

- `AlphaRow` typing includes `needs_review` and `gate_failure_reason`.
- Status cell renders both primary status and warning badge without layout breakage.
- Warning styling is visible and consistent in `index.css`.

## Build check

```bash
cd frontend
npm run build
```

## Manual smoke paths

- Open `/settings` and verify credential fields are masked by default.
- Click reveal toggle and confirm the field value becomes visible.
- Click `Test connection` and confirm inline toast message updates.
- Open `/alphas` and verify warning badge appears for borderline rows when backend data provides `needs_review=true`.
- Open `/alphas/<id>` and verify failure reason banner appears when `gate_failure_reason` exists.

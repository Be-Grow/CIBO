# Remotion on Windows

The `mg` folder is the CIBO Remotion engine. Run its commands from this directory so Remotion resolves `public/` correctly:

```powershell
cd S:\Edição BEGrow\CIBO\skills\reel-motion\mg
npm.cmd ci
npx.cmd remotion compositions .\src\index.ts
```

If Node.js cannot validate the Windows certificate chain while downloading packages or Chromium, use the Windows certificate store for that command:

```powershell
$env:NODE_OPTIONS = '--use-system-ca'
```

`public/audio.wav` is the local audio sample used by the default `Audiogram` composition. Recreate it with `node .\scripts\create-test-audio.mjs`. It is synthetic test audio, not source music for client delivery.

The repository previously tracked a `node_modules` file containing a macOS absolute path. It is removed from the Windows workflow; dependencies belong in the ignored local `node_modules` directory and are restored with `npm ci`.

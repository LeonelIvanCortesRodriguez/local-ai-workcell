# Third-party notices

The runtime and package scripts use only the Python standard library. The SVG and PNG fixtures, status-page source, diagram, mark, README images, and demo recordings were created for this repository and are included under its MIT License. No third-party source, OCR model, document, or production log is redistributed.

## Bundled fonts

The status page self-hosts two font files. Nothing is fetched from a font service at runtime.

| File | Family | License | Source |
| --- | --- | --- | --- |
| `assets/fonts/Archivo.woff2` | Archivo, Copyright 2020 The Archivo Project Authors | SIL Open Font License 1.1, [`assets/fonts/Archivo-OFL.txt`](assets/fonts/Archivo-OFL.txt) | Google Fonts Latin subset `archivo/v25`, from the upstream [Omnibus-Type/Archivo](https://github.com/Omnibus-Type/Archivo) project |
| `assets/fonts/MartianMono.woff2` | Martian Mono, Copyright 2021 The Martian Mono Project Authors | SIL Open Font License 1.1, [`assets/fonts/MartianMono-OFL.txt`](assets/fonts/MartianMono-OFL.txt) | Google Fonts Latin subset `martianmono/v6`, from the upstream [evilmartians/mono](https://github.com/evilmartians/mono) project |

Neither license declares a Reserved Font Name, so the unmodified Latin subsets may be redistributed under their original names. The files are bundled as published and not modified.

## Development tools

README images, the social preview, and the replay GIF and MP4 are rendered with a local Chrome browser driven by Playwright Core (Apache-2.0) and encoded with FFmpeg. These tools are optional, are not bundled, and are not required to run the workflow. Tesseract is an optional local dependency of the v0.2 experiment and is not bundled.

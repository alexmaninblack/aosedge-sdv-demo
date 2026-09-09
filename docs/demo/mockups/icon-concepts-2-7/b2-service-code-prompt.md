<!-- SPDX-FileCopyrightText: 2026 maninblack -->
<!-- SPDX-License-Identifier: MIT -->

# B2 Service code-symbol edit prompt

Exact image-generation input, retained as design provenance.

```json
{
  "method": "Built-in image generation; localized image edit",
  "source": "b2-automotive-miniatures.png",
  "output": "b2-service-code.png",
  "prompt": "Use case: precise-object-edit.\nEdit the supplied \"B2 — Automotive miniatures\" image. Make exactly ONE localized change: on the blue top face of the Service icon (upper specimen grid, second row, far right), remove the four white square/window panes and replace them with the white code symbol \"</>\".\nThe code glyph must clearly be a left angle bracket, forward slash, and right angle bracket; centered on the top face, following the same perspective, bold enough to read when small, with balanced spacing. It should look like an inlaid or printed white marking on the existing blue surface. No Windows-like four-pane motif anywhere on Service.\nPreserve the Service object's blue rounded top slab, dark base, geometry, materials, perspective, shadows and position.\nKeep ALL other parts of the image unchanged: the Component layers immediately to its left are explicitly approved and must NOT change; all Vehicle, Platform, Brake, Tire, Cloud and Gateway illustrations; every heading, English label, background, arrangement and the complete IN CONTEXT lower panel. Do not redesign any other icon, alter any label, add another code symbol elsewhere, crop or reframe the board, or change the B2 heading.\nOutput a sibling image of the same complete board, with only that single Service marking replaced."
}
```

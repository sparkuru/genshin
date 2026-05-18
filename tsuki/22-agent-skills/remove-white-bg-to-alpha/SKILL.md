---
name: remove-white-bg-to-alpha
description: Extracts the main character from a single image with a solid or near-solid light background by converting only edge-connected background regions to transparent alpha. Use when the user provides one illustration, avatar, sticker, or character render and expects a transparent PNG saved under /tmp with the output directory reported back.
---

# Remove White Background To Alpha

## Purpose

Use this skill when the user gives one image with a pure or near-pure light background and wants the character extracted as a transparent PNG.

The goal is practical delivery:

- process one input image
- write the result under `/tmp`
- return the output directory path

## Input And Output Contract

Input:

- one JPG or PNG image

Output:

- one transparent PNG, usually `result.png`
- one optional checkerboard preview, usually `preview.png`
- one output directory under `/tmp`, such as `/tmp/remove-white-bg-to-alpha-<timestamp>/`

Never write generated files into the workspace unless the user explicitly asks for that location.

## When To Use

Use this skill when all of the following are mostly true:

- the background is solid or near-solid
- the background is white, off-white, or light gray
- the background touches the image border
- the main requirement is "extract the character" rather than "do semantic segmentation"

Do not use this as the first choice for:

- complex backgrounds
- strong shadows or gradients across the whole background
- cases where the subject contains large white areas merged into the outer background
- images that clearly need a model-based matting workflow

## Execution Workflow

1. Inspect the image and confirm that the background is close to a solid light color.
2. Create a temporary output directory under `/tmp`.
3. Save the main result as PNG in that directory.
4. Save a preview image in the same directory when edge quality needs visual confirmation.
5. Reply with the output directory and the generated file paths.

## Extraction Rule

Do not remove all white pixels.

Only remove pixels that satisfy both conditions:

- they are close to the estimated background color
- they are connected to the outer border

This protects bright details inside the subject, such as highlights, white clothing trim, or reflective accents.

## Recommended Method

Use this sequence:

1. Convert the image to RGBA.
2. Sample the four borders to estimate the background color.
3. Compute color distance from each pixel to the estimated background.
4. Mark near-background pixels as candidates.
5. Flood fill from the image border to keep only edge-connected candidates as transparent background.
6. Feather the immediate edge slightly to reduce halos and hard cut lines.
7. Export as PNG.

## Default Parameters

Use these defaults first:

- `quant_step=16`
- `bg_threshold=36`
- `feather_start=28`
- `feather_end=46`

Tune only when needed:

- if the subject edge is being removed, lower `bg_threshold`
- if white background remains, raise `bg_threshold` slightly
- if the cut edge looks too soft, lower `feather_end`

## Verification

Before finishing, verify:

- the background is transparent
- interior highlights are still preserved
- no large white fringe remains around the character
- the output file is PNG

## Response Format

After processing, report the result in a compact form:

```text
输出目录: /tmp/remove-white-bg-to-alpha-1234567890
主文件: /tmp/remove-white-bg-to-alpha-1234567890/result.png
预览图: /tmp/remove-white-bg-to-alpha-1234567890/preview.png
```

If extraction quality is limited by the image itself, state the reason briefly and still report the directory.
const sharp = require('sharp');

async function processCoverPhoto(inputPath, outputPath) {
  const W = 1920, H = 1080;  // fixed output size

  const overlay = Buffer.alloc(W * H * 4);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4;
      const t = Math.max(0, (y / H - 0.3) / 0.7);
      overlay[i] = 8; overlay[i+1] = 18; overlay[i+2] = 42;
      overlay[i+3] = Math.round(Math.pow(t, 1.4) * 210);
    }
  }

  await sharp(inputPath)
    .resize(W, H, { fit: 'cover', position: 'center' })
    .composite([{ input: overlay, raw: { width: W, height: H, channels: 4 } }])
    .jpeg({ quality: 97 })
    .toFile(outputPath);

  console.log('Cover processed at 1920x1080');
}

processCoverPhoto('./cover_photo_raw.jpg', './cover.jpg').catch(console.error);

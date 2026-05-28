const sharp = require('sharp');

async function main() {
  const W = 1920, H = 1080;

  // Gradient overlay SVG: dark navy ramp from 35% height to bottom + left vignette
  const gradient = `<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="bottomGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="35%" stop-color="#0D1F3C" stop-opacity="0"/>
        <stop offset="100%" stop-color="#0D1F3C" stop-opacity="0.82"/>
      </linearGradient>
      <linearGradient id="leftVig" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#0D1F3C" stop-opacity="0.20"/>
        <stop offset="35%" stop-color="#0D1F3C" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <rect width="${W}" height="${H}" fill="url(#bottomGrad)"/>
    <rect width="${W}" height="${H}" fill="url(#leftVig)"/>
  </svg>`;

  const gradBuffer = Buffer.from(gradient);

  await sharp('cover_photo_raw.jpg')
    .resize(W, H, { fit: 'cover', position: 'centre' })
    .composite([{ input: gradBuffer, blend: 'over' }])
    .jpeg({ quality: 92 })
    .toFile('cover_photo.jpg');

  console.log('Cover photo processed');
}
main().catch(console.error);

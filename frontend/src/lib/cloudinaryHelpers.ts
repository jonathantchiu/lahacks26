import { cld } from './cloudinary';
import { fill } from '@cloudinary/url-gen/actions/resize';
import { format, quality } from '@cloudinary/url-gen/actions/delivery';
import { auto as autoFormat } from '@cloudinary/url-gen/qualifiers/format';
import { auto as autoQuality } from '@cloudinary/url-gen/qualifiers/quality';
import type { CloudinaryImage } from '@cloudinary/url-gen';

const CLOUDINARY_REGEX = /\/upload\/(?:v\d+\/)?(.+?)(?:\.\w+)?$/;

export function extractPublicId(url: string): string | null {
  const match = url.match(CLOUDINARY_REGEX);
  return match ? match[1] : null;
}

export function isCloudinaryUrl(url: string): boolean {
  return url.includes('res.cloudinary.com');
}

export function getEventImage(url: string, width: number = 400): CloudinaryImage | null {
  if (!isCloudinaryUrl(url)) return null;
  const publicId = extractPublicId(url);
  if (!publicId) return null;

  return cld
    .image(publicId)
    .resize(fill().width(width))
    .delivery(format(autoFormat()))
    .delivery(quality(autoQuality()));
}

export function getThumbnail(url: string): CloudinaryImage | null {
  return getEventImage(url, 200);
}

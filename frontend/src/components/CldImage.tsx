import { AdvancedImage } from '@cloudinary/react';
import { getEventImage, getThumbnail, isCloudinaryUrl } from '../lib/cloudinaryHelpers';

interface CldImageProps {
  src: string;
  alt: string;
  className?: string;
  thumbnail?: boolean;
  width?: number;
}

export default function CldImage({ src, alt, className, thumbnail, width }: CldImageProps) {
  if (!isCloudinaryUrl(src)) {
    return <img src={src} alt={alt} className={className} />;
  }

  const cldImg = thumbnail ? getThumbnail(src) : getEventImage(src, width);
  if (!cldImg) {
    return <img src={src} alt={alt} className={className} />;
  }

  return <AdvancedImage cldImg={cldImg} alt={alt} className={className} />;
}

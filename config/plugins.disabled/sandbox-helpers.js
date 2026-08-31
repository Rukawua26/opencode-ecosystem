const DEFAULT_IMAGE = 'alpine:latest';
const IMAGE_PATTERN = /^[a-z0-9][a-z0-9._/:@-]{0,127}$/i;

export { DEFAULT_IMAGE, IMAGE_PATTERN };

export function validateImage(image) {
  if (typeof image !== 'string' || !image.trim()) return DEFAULT_IMAGE;
  if (/[;&|`$(){}\n\r]/.test(image)) throw new Error('Image contains shell metacharacters');
  if (!IMAGE_PATTERN.test(image)) throw new Error('Image has an invalid format');
  return image;
}

export function buildDockerArgs(command, image) {
  const safeImage = validateImage(image);
  return ['run', '--rm', '-i', '--network', 'none', '--read-only', '--memory', '512m', '--cpus', '1', safeImage, 'sh', '-c', command];
}

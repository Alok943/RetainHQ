// Resolves a lesson image `asset` key to a servable URL.
// Lesson JSON stores only a stable key (e.g. "ai-engineering/<slug>/overlap.png");
// the actual binary lives in the Supabase public bucket `lesson-images`. Absolute URLs
// and root-relative paths (used for local/dev placeholders) pass through untouched.
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const BUCKET = 'lesson-images';

export function lessonImageUrl(asset) {
  if (!asset || typeof asset !== 'string') return null;
  if (/^https?:\/\//.test(asset) || asset.startsWith('/')) return asset;
  if (!SUPABASE_URL) return null;
  return `${SUPABASE_URL}/storage/v1/object/public/${BUCKET}/${asset}`;
}

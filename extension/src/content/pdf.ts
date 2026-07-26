import { startActivityTracking } from './activity_tracker'

function getTitle(): string {
  // Browser PDF viewer usually sets the document title to the filename
  let title = document.title
  if (title.endsWith('.pdf')) {
    title = title.replace(/\.pdf$/i, '')
  }
  
  // URL fallback if title is empty or generic
  if (!title || title.length < 3) {
    const parts = window.location.pathname.split('/')
    const filePart = parts[parts.length - 1]
    if (filePart) {
      title = decodeURIComponent(filePart).replace(/\.pdf$/i, '')
    }
  }
  
  return title
}

startActivityTracking({
  surface: 'pdf',
  url_domain: window.location.hostname, // Capture domain for context
  getTitle
})

import { startActivityTracking } from './activity_tracker'

function getTitle(): string {
  // Coursera titles often in a specific h1 or breadcrumbs
  const titleEl = document.querySelector('h1[data-e2e="page-header-title"]') || 
                  document.querySelector('.breadcrumb-title')
  
  if (titleEl && titleEl.textContent) {
    return titleEl.textContent.trim()
  }
  
  return document.title.replace(' | Coursera', '')
}

startActivityTracking({
  surface: 'coursera',
  url_domain: 'coursera.org',
  getTitle
})

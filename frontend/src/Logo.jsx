import React from 'react';
import logoDark from './assets/logo-mark-dark.png';
import logoLight from './assets/logo-mark-light.png';

/**
 * RetainHQ logo mark.
 * variant="dark"  -> navy mark (#0F172A) for LIGHT surfaces
 * variant="light" -> white mark for DARK surfaces (e.g. #131b2e)
 */
function Logo({ variant = 'dark', className = '' }) {
  const src = variant === 'light' ? logoLight : logoDark;
  return (
    <img
      src={src}
      alt="RetainHQ"
      draggable={false}
      className={className}
    />
  );
}

export default Logo;

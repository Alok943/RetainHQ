import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';

export default function GlossaryTerm({ term, definition, example, children }) {
  const [open, setOpen] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0, align: 'top' });
  const buttonRef = useRef(null);
  const popoverRef = useRef(null);

  const updatePosition = () => {
    if (!open || !buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    
    let align = 'top';
    let top = rect.top + window.scrollY - 8; // 8px gap above
    
    // If it's too close to the top of the viewport, flip it below
    if (rect.top < 160) {
      align = 'bottom';
      top = rect.bottom + window.scrollY + 8; // 8px gap below
    }
    
    // Center it horizontally relative to the trigger
    let left = rect.left + window.scrollX + (rect.width / 2);
    setCoords({ top, left, align });
  };

  useEffect(() => {
    updatePosition();
    // Use capture phase for scroll to catch inner scrolling containers
    window.addEventListener('scroll', updatePosition, true);
    window.addEventListener('resize', updatePosition);
    return () => {
      window.removeEventListener('scroll', updatePosition, true);
      window.removeEventListener('resize', updatePosition);
    };
  }, [open]);

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && open) setOpen(false);
    };
    const handleClickOutside = (e) => {
      if (open && buttonRef.current && !buttonRef.current.contains(e.target) && 
          popoverRef.current && !popoverRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('keydown', handleEsc);
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);
    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [open]);

  const toggle = (e) => {
    e.preventDefault();
    setOpen((o) => !o);
  };

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        aria-expanded={open}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={toggle}
        className="inline border-b border-dotted border-[#0891B2] text-inherit bg-[#0891B2]/[0.05] hover:bg-[#0891B2]/[0.12] transition-colors focus:outline-none focus:ring-2 focus:ring-[#0891B2]/40 rounded-[2px] cursor-help px-[1px]"
      >
        {children}
      </button>

      {open && createPortal(
        <div
          ref={popoverRef}
          role="tooltip"
          className="absolute z-[100] p-4 shadow-[0_10px_38px_-10px_rgba(15,23,42,0.15)] rounded-xl animate-in fade-in zoom-in-95 duration-150 border border-[rgba(15,23,42,0.08)] bg-white pointer-events-auto"
          style={{
            maxWidth: '320px',
            width: 'max-content',
            top: coords.align === 'top' ? 'auto' : `${coords.top}px`,
            bottom: coords.align === 'top' ? `${document.documentElement.scrollHeight - coords.top}px` : 'auto',
            left: `${coords.left}px`,
            transform: 'translateX(-50%)',
          }}
        >
          <div className="font-sans text-[13px] text-[#0F172A] leading-relaxed">
            {definition}
          </div>
          {example && (
            <div className="mt-3 pt-2 border-t border-[rgba(15,23,42,0.06)]">
              <span className="block font-sans text-[10px] font-bold uppercase tracking-wider text-[#0891B2] mb-1">Example</span>
              <span className="block font-sans text-[13px] text-[#475569] leading-relaxed">
                {example}
              </span>
            </div>
          )}
        </div>,
        document.body
      )}
    </>
  );
}

"use client"

import { useEffect } from 'react'
import { usePathname } from 'next/navigation'

export function SidebarRemover() {
  const pathname = usePathname()
  
  useEffect(() => {
    // Create a mutation observer to catch any dynamically added sidebar
    const observer = new MutationObserver((mutations) => {
      // Check the entire DOM periodically
      removeSidebars();
    });
    
    // Start observing the document body for changes
    observer.observe(document.body, { 
      childList: true,
      subtree: true 
    });
    
    // Initial check
    removeSidebars();
    
    // Cleanup
    return () => observer.disconnect();
    
    function removeSidebars() {
      // Try multiple selector approaches
      
      // Approach 1: Look for divs with specific content
      document.querySelectorAll('div, nav').forEach(el => {
        const text = el.textContent || '';
        if (
          text.includes('Dashboard') && 
          text.includes('Analysis') && 
          text.includes('Portfolio') &&
          text.trim().split(/\s+/).length < 10 // Likely just a menu with few items
        ) {
          console.log('Removing sidebar by content:', el);
          el.remove();
        }
      });
      
      // Approach 2: Look for elements positioned like a sidebar
      document.querySelectorAll('*').forEach(el => {
        if (el instanceof HTMLElement) {
          const style = window.getComputedStyle(el);
          const rect = el.getBoundingClientRect();
          
          // Sidebars are typically fixed/absolute, on the left, and tall
          if (
            (style.position === 'fixed' || style.position === 'absolute') &&
            rect.left < 100 &&
            rect.height > 200 &&
            rect.width < 300
          ) {
            console.log('Removing potential sidebar by position:', el);
            el.style.display = 'none';
          }
        }
      });
      
      // Approach 3: Target by class names that might indicate a sidebar
      ['sidebar', 'side-nav', 'sidenav', 'nav-sidebar', 'navigation'].forEach(className => {
        document.querySelectorAll(`[class*=${className}]`).forEach(el => {
          console.log(`Removing element with class containing "${className}":`, el);
          el.remove();
        });
      });
    }
  }, [pathname]);
  
  return null;
} 
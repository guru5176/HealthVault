import { useEffect, useRef, useState } from 'react';

export default function ParallaxSection({ children, speed = 0.5, bgImage, minHeight = '500px', overlayColor = 'rgba(10,10,12,0.8)' }) {
  const [offset, setOffset] = useState(0);
  const sectionRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => {
      if (sectionRef.current) {
        const rect = sectionRef.current.getBoundingClientRect();
        // Only calculate parallax if the section is somewhat in the viewport
        if (rect.top <= window.innerHeight && rect.bottom >= 0) {
           const scrolled = window.scrollY - sectionRef.current.offsetTop;
           setOffset(scrolled * speed);
        }
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [speed]);

  return (
    <div 
      ref={sectionRef}
      style={{
        position: 'relative',
        minHeight,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        borderRadius: '24px',
        margin: '40px 0',
        border: '1px solid var(--border-color)',
      }}
    >
      {/* Background layer */}
      <div 
        style={{
          position: 'absolute',
          top: '-20%',
          left: 0,
          right: 0,
          bottom: '-20%',
          backgroundImage: bgImage ? `url(${bgImage})` : 'none',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          transform: `translateY(${offset}px)`,
          transition: 'transform 0.1s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
          willChange: 'transform',
          zIndex: 0,
        }}
      />
      
      {/* Overlay */}
      <div style={{
        position: 'absolute',
        inset: 0,
        background: overlayColor,
        zIndex: 1,
      }} />

      {/* Content layer */}
      <div style={{
        position: 'relative',
        zIndex: 2,
        width: '100%',
        padding: '40px',
      }}>
        {children}
      </div>
    </div>
  );
}

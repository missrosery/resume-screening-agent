"use client";

import { AnimatePresence, motion, type Variants } from "framer-motion";
import { usePathname } from "next/navigation";
import { HTMLAttributes, PropsWithChildren, useEffect, useRef, useState } from "react";

const pageVariants: Variants = {
  initial: { opacity: 0, y: 16 },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.35,
      ease: [0.16, 1, 0.3, 1],
      staggerChildren: 0.06,
    },
  },
  exit: {
    opacity: 0,
    y: 10,
    transition: { duration: 0.2, ease: [0.7, 0, 0.84, 0] },
  },
};

const cardVariants: Variants = {
  initial: { opacity: 0, y: 14, scale: 0.98 },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] },
  },
};

const staggerContainerVariants: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.05,
    },
  },
};

const staggerItemVariants: Variants = {
  initial: { opacity: 0, y: 12 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] },
  },
};

const fadeInVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.3 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

export function PageTransition({ children }: PropsWithChildren) {
  const pathname = usePathname();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={pathname}
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

export function MotionPage({ className, children }: HTMLAttributes<HTMLElement>) {
  return (
    <motion.main className={className} variants={pageVariants} initial="initial" animate="animate">
      {children}
    </motion.main>
  );
}

export function MotionCard({ className, children }: HTMLAttributes<HTMLDivElement>) {
  return (
    <motion.div className={className} variants={cardVariants}>
      {children}
    </motion.div>
  );
}

export function StaggerContainer({ className, children }: HTMLAttributes<HTMLDivElement>) {
  return (
    <motion.div
      className={className}
      variants={staggerContainerVariants}
      initial="initial"
      animate="animate"
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({ className, children }: HTMLAttributes<HTMLDivElement>) {
  return (
    <motion.div className={className} variants={staggerItemVariants}>
      {children}
    </motion.div>
  );
}

export function FadeIn({ className, children }: HTMLAttributes<HTMLDivElement>) {
  return (
    <motion.div
      className={className}
      variants={fadeInVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {children}
    </motion.div>
  );
}

export function TypewriterText({ text, className }: { text: string; className?: string }) {
  const [visibleLength, setVisibleLength] = useState(0);
  const previousText = useRef(text);

  useEffect(() => {
    if (!text.startsWith(previousText.current)) {
      setVisibleLength(0);
    }
    previousText.current = text;
  }, [text]);

  useEffect(() => {
    if (visibleLength >= text.length) return;
    const timeout = window.setTimeout(() => {
      setVisibleLength((current) => Math.min(current + 1, text.length));
    }, 12);
    return () => window.clearTimeout(timeout);
  }, [text, visibleLength]);

  return <p className={className}>{text.slice(0, visibleLength)}</p>;
}

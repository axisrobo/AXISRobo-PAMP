'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Languages, Menu, X } from 'lucide-react';
import clsx from 'clsx';
import { useState, useRef, useEffect } from 'react';
import { useLocale, useT } from '@/shared/lib/locale';
import { AuthButton } from '@/shared/components/ui/AuthButton';
import { useAuth } from '@/shared/lib/auth-context';
import { isAdminPath, isRequesterPath, isReviewerPath } from '@/shared/lib/navigation';
import { appConfig } from '@/shared/lib/app-config';

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const pathname = usePathname();
  const isHome = isRequesterPath(pathname ?? '');
  const isReviewer = isReviewerPath(pathname ?? '');
  const isAdmin = isAdminPath(pathname ?? '');
  const { hasRole } = useAuth();
  const canReview = hasRole('ea_admin', 'ea_reviewer');
  const canAdmin = hasRole('ea_admin');
  const { locale, toggleLocale } = useLocale();
  const t = useT();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!dropdownOpen) return;
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) setDropdownOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [dropdownOpen]);

  useEffect(() => { setDropdownOpen(false); }, [pathname]);

  return (
    <header className="h-14 bg-mdb-teal-deep border-b border-mdb-teal flex items-center justify-between px-4 sticky top-0 z-50">
      <div className="flex items-center gap-4">
        <button onClick={() => onMenuClick ? onMenuClick() : setDropdownOpen(v => !v)} className="lg:hidden p-1.5 -ml-1 hover:bg-mdb-teal rounded transition-colors cursor-pointer" aria-label="Toggle menu">
          {dropdownOpen && !onMenuClick ? <X className="w-5 h-5 text-white" /> : <Menu className="w-5 h-5 text-white" />}
        </button>
        <Link href="/" className="flex items-center">
          <img src={appConfig.logoSrc} alt={appConfig.logoAlt} className="h-14 w-auto block object-contain" />
        </Link>
        <div className="hidden sm:block leading-tight">
          <div className="text-white font-semibold text-sm md:text-base">{appConfig.appTitle}</div>
          <div className="text-mdb-stone text-[11px] md:text-xs">{appConfig.appSubtitle}</div>
        </div>
      </div>

      <div className="hidden lg:flex items-center gap-1">
        <Link href="/" className={clsx('px-4 py-2 text-sm font-medium rounded-pill transition-colors', isHome && !isReviewer && !isAdmin ? 'bg-mdb-green text-mdb-teal-deep' : 'text-white hover:bg-mdb-teal')}>{t("I'm Requester")}</Link>
        {canReview && <Link href="/reviewer" className={clsx('px-4 py-2 text-sm font-medium rounded-pill transition-colors', isReviewer ? 'bg-mdb-green text-mdb-teal-deep' : 'text-white hover:bg-mdb-teal')}>{t("I'm Reviewer")}</Link>}
        {canAdmin && <Link href="/admin" className={clsx('px-4 py-2 text-sm font-medium rounded-pill transition-colors', isAdmin ? 'bg-mdb-green text-mdb-teal-deep' : 'text-white hover:bg-mdb-teal')}>{t("I'm Admin")}</Link>}
        <button onClick={toggleLocale} className="p-2 hover:bg-mdb-teal rounded-pill transition-colors ml-2 flex items-center gap-1 cursor-pointer" title={t('Switch Language')}>
          <Languages className="w-5 h-5 text-mdb-stone" />
          <span className="text-xs text-mdb-stone font-medium">{locale === 'en' ? 'EN' : 'ZH'}</span>
        </button>
        <div className="ml-2"><AuthButton /></div>
      </div>

      {dropdownOpen && !onMenuClick && (
        <div ref={dropdownRef} className="lg:hidden absolute top-14 left-0 right-0 bg-mdb-teal-deep border-b border-mdb-teal shadow-md z-40 px-4 py-3 space-y-2">
          <Link href="/" className={clsx('block px-3 py-2 text-sm font-medium rounded-pill transition-colors', isHome && !isReviewer && !isAdmin ? 'bg-mdb-green text-mdb-teal-deep' : 'text-white hover:bg-mdb-teal')}>{t("I'm Requester")}</Link>
          {canReview && <Link href="/reviewer" className={clsx('block px-3 py-2 text-sm font-medium rounded-pill transition-colors', isReviewer ? 'bg-mdb-green text-mdb-teal-deep' : 'text-white hover:bg-mdb-teal')}>{t("I'm Reviewer")}</Link>}
          {canAdmin && <Link href="/admin" className={clsx('block px-3 py-2 text-sm font-medium rounded-pill transition-colors', isAdmin ? 'bg-mdb-green text-mdb-teal-deep' : 'text-white hover:bg-mdb-teal')}>{t("I'm Admin")}</Link>}
          <div className="border-t border-mdb-teal my-2" />
          <div className="flex items-center justify-between px-3 py-1">
            <button onClick={toggleLocale} className="flex items-center gap-1 text-sm text-mdb-stone hover:text-white cursor-pointer"><Languages className="w-4 h-4" /><span>{locale === 'en' ? 'EN' : 'ZH'}</span></button>
            <AuthButton />
          </div>
        </div>
      )}
    </header>
  );
}

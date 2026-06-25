import Link from 'next/link';
import type { SVGProps } from 'react';
import { appConfig } from '@/shared/lib/app-config';

function PhoneIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.08 4.18 2 2 0 0 1 4.06 2h3a2 2 0 0 1 2 1.72c.12.86.3 1.7.54 2.51a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.57-1.06a2 2 0 0 1 2.11-.45c.81.24 1.65.42 2.51.54A2 2 0 0 1 22 16.92z" />
    </svg>
  );
}

function MailIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" />
      <path d="m22 6-10 7L2 6" />
    </svg>
  );
}

export function Footer() {
  const contactText = appConfig.supportContacts.join(', ');

  return (
    <footer className="bg-text-primary text-white">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex flex-col gap-6">
          <div>
            <h3 className="text-sm font-medium">Contact Us</h3>
            <ul className="mt-3 space-y-2 text-sm text-white/70">
              <li className="flex items-center gap-2">
                <PhoneIcon className="h-4 w-4 text-white/50" />
                <span>Contact Person: {contactText}</span>
              </li>
              <li className="flex items-center gap-2">
                <MailIcon className="h-4 w-4 text-white/50" />
                <a href={`mailto:${appConfig.supportEmail}`} className="hover:text-white transition-colors">
                  {appConfig.supportEmail}
                </a>
              </li>
            </ul>
          </div>

          <Link href="/" className="inline-flex items-center gap-2 text-sm text-white/80 hover:text-white transition-colors">
            <span className="bg-brand-primary text-white font-semibold px-2 py-1 rounded">{appConfig.brandName}.</span>
            <span>{appConfig.appTitle}</span>
          </Link>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 text-xs text-white/50 text-center">
          &copy; {new Date().getFullYear()} {appConfig.brandName}. All rights reserved.
        </div>
      </div>
    </footer>
  );
}

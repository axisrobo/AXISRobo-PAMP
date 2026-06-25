import type { NextPage } from 'next';

const Custom500: NextPage = () => {
  return (
    <main
      style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        padding: '2rem',
        fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, sans-serif',
      }}
    >
      <div style={{ textAlign: 'center', maxWidth: 560 }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>500</h1>
        <p style={{ color: '#555', lineHeight: 1.6 }}>
          Internal server error. Please retry in a few seconds.
        </p>
      </div>
    </main>
  );
};

export default Custom500;

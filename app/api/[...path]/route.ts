import { NextRequest, NextResponse } from 'next/server';
import { randomUUID } from 'node:crypto';

export const runtime = 'nodejs';
const allowed = new Set(['health', 'status', 'stations', 'places', 'chat', 'search', 'options', 'prereservations', 'dossiers']);

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!allowed.has(path[0]) || path.some(p => !/^[a-zA-Z0-9-]+$/.test(p))) return NextResponse.json({ detail: 'Route inconnue.' }, { status: 404 });
  const incoming = request.headers.get('origin');
  if (request.method !== 'GET' && incoming) {
    try {
      const origin = new URL(incoming);
      if (origin.host !== request.headers.get('host') || !['http:', 'https:'].includes(origin.protocol)) return NextResponse.json({ detail: 'Origine invalide.' }, { status: 403 });
    } catch { return NextResponse.json({ detail: 'Origine invalide.' }, { status: 403 }); }
  }
  const cookie = request.cookies.get('echappee-session')?.value;
  const session = cookie && /^[0-9a-f-]{36}$/.test(cookie) ? cookie : randomUUID();
  try {
    const response = await fetch(`${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/${path.join('/')}${request.nextUrl.search}`, {
      method: request.method, headers: { 'Content-Type': 'application/json', 'X-Session': session },
      body: request.method === 'GET' ? undefined : await request.text(), cache: 'no-store', signal: AbortSignal.timeout(['chat','search'].includes(path[0])?195000:100000),
    });
    const result = new NextResponse(await response.text(), { status: response.status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
    if (!cookie && !['health','status','stations','places'].includes(path[0])) result.cookies.set('echappee-session', session, { httpOnly: true, sameSite: 'lax', secure: request.nextUrl.protocol === 'https:', path: '/', maxAge: 60 * 60 * 24 * 7 });
    return result;
  } catch {
    return NextResponse.json({ detail: 'Le moteur de voyage est indisponible. Lancez le backend Python sur le port 8000.' }, { status: 503 });
  }
}
export const GET = proxy;
export const POST = proxy;

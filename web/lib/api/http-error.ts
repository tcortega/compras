import { NextResponse } from 'next/server'
import { ApiError, ApiNotFoundError } from '@/lib/types'

export function jsonError(err: unknown): NextResponse {
  if (err instanceof ApiNotFoundError) {
    return NextResponse.json({ error: err.message }, { status: 404 })
  }
  if (err instanceof ApiError) {
    return NextResponse.json({ error: err.message }, { status: err.status })
  }
  return NextResponse.json({ error: 'Falha interna' }, { status: 500 })
}

export function stagingOff(): NextResponse {
  return NextResponse.json({ error: 'Triagem interna desligada' }, { status: 404 })
}

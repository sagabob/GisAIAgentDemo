import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { RuntimeConfigService } from '../config/runtime-config.service';
import { ChatResponse } from '../models/chat.model';

@Injectable({ providedIn: 'root' })
export class AgentService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(RuntimeConfigService);

  ask(message: string, sessionId?: string | null): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.config.agentApiUrl}/chat`, {      message,
      session_id: sessionId ?? null,
    });
  }

  reset(sessionId: string): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.config.agentApiUrl}/chat/reset`, {
      session_id: sessionId,
    });
  }
}

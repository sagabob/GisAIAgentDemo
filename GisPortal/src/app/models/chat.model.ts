import { Place } from './place.model';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  places?: Place[];
  total?: number | null;
}

export interface ChatResponse {
  answer: string;
  places: Place[];
  total?: number | null;
  session_id: string;
}

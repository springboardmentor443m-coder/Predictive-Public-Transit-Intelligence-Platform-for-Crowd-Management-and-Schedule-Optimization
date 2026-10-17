export type DataState = 'LIVE' | 'HISTORICAL' | 'PREDICTED' | 'UNAVAILABLE' | 'DEV_INFRASTRUCTURE_TEST';

export interface WebSocketEvent {
  event: string;
  data_state: DataState;
  timestamp: string;
  payload?: any;
  message?: string;
  echo?: string;
}

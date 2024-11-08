export interface URLBase {
  url: string;
}

export interface URLResponse {
  original_url: string;
  shortened_url: string;
  created_at: string;
}

export interface DeleteURLRequest {
  url: string;
}

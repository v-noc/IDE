/** Mirrors backend `ChatCompletionParams` / REST `generation` object. */

export interface ChatCompletionParams {
  provider?: string | null;
  model?: string | null;
  temperature?: number | null;
  max_tokens?: number | null;
  top_p?: number | null;
  frequency_penalty?: number | null;
  presence_penalty?: number | null;
  stop?: string[] | null;
}

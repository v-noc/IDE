import { Hono } from "hono";
import { jsonRpcPost } from "./jsonrpc";

function parseArgs(argv: string[]) {
  let host = "127.0.0.1";
  let port = 9001;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--host" && argv[i + 1]) {
      host = argv[++i];
    } else if (a === "--port" && argv[i + 1]) {
      port = Number(argv[++i]) || 0;
    }
  }
  return { host, port };
}

const { host, port: preferredPort } = parseArgs(process.argv.slice(2));

const app = new Hono();
app.post("/rpc", jsonRpcPost);

const server = Bun.serve({
  hostname: host,
  port: preferredPort,
  fetch: app.fetch,
});

console.log(`READY port=${server.port}`);

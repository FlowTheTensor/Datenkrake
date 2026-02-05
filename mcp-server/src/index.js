import express from "express";
import mysql from "mysql2/promise";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema
} from "@modelcontextprotocol/sdk/types.js";

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3001;
const DB_HOST = process.env.DB_HOST || "db";
const DB_USER = process.env.DB_USER || "mcp_read";
const DB_PASSWORD = process.env.DB_PASSWORD || "changeMeMcp";
const DB_NAME = process.env.DB_NAME || "telemetry";

const server = new Server(
  {
    name: "mcp-mariadb",
    version: "0.1.0"
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "sql_query",
        description: "Run a read-only SELECT query against the telemetry database.",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string" }
          },
          required: ["query"]
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name !== "sql_query") {
    return {
      content: [{ type: "text", text: "Unknown tool." }],
      isError: true
    };
  }

  const query = request.params.arguments?.query || "";
  if (!/^\s*select\b/i.test(query)) {
    return {
      content: [{ type: "text", text: "Only SELECT queries are allowed." }],
      isError: true
    };
  }

  try {
    const connection = await mysql.createConnection({
      host: DB_HOST,
      user: DB_USER,
      password: DB_PASSWORD,
      database: DB_NAME
    });

    const [rows] = await connection.query(query);
    await connection.end();

    return {
      content: [{ type: "text", text: JSON.stringify(rows, null, 2) }]
    };
  } catch (error) {
    return {
      content: [{ type: "text", text: `Query failed: ${error.message}` }],
      isError: true
    };
  }
});

const transports = new Map();

app.get("/sse", async (req, res) => {
  const transport = new SSEServerTransport("/messages", res);
  transports.set(transport.sessionId, transport);

  res.on("close", () => {
    transports.delete(transport.sessionId);
  });

  await server.connect(transport);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId;
  const transport = transports.get(sessionId);

  if (!transport) {
    res.status(404).json({ error: "Unknown session" });
    return;
  }

  await transport.handlePostMessage(req, res);
});

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`MCP server listening on port ${PORT}`);
});

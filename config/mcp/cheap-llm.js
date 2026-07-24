#!/usr/bin/env node
// MCP server: modelo económico para tareas auxiliares (resumir, extraer, clasificar)
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { stdin, stdout } from 'node:process';

const HOME = process.env.HOME || '/tmp';
const ENV_FILE = join(HOME, '.config/opencode/.env');
if (existsSync(ENV_FILE)) {
  for (const line of readFileSync(ENV_FILE, 'utf-8').split('\n')) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const idx = trimmed.indexOf('=');
      if (idx > 0) process.env[trimmed.slice(0, idx)] = trimmed.slice(idx + 1);
    }
  }
}

let buffer = '';
stdin.setEncoding('utf-8');
stdin.on('data', (chunk) => {
  buffer += chunk;
  const lines = buffer.split('\n');
  buffer = lines.pop();
  for (const line of lines) {
    if (line.trim()) handle(JSON.parse(line));
  }
});

function send(msg) {
  stdout.write(JSON.stringify(msg) + '\n');
}

function handle(msg) {
  const { id, method, params } = msg;

  if (method === 'initialize') {
    return send({ id, result: {
      protocolVersion: '2024-11-05',
      capabilities: { tools: {} },
      serverInfo: { name: 'cheap-llm', version: '1.0.0' },
    }});
  }

  if (method === 'notifications/initialized') return;

  if (method === 'tools/list') {
    return send({ id, result: {
      tools: [
        {
          name: 'summarize',
          description: 'Resumir texto usando un modelo económico. Útil para reducir textos largos a lo esencial.',
          inputSchema: {
            type: 'object',
            properties: {
              text: { type: 'string', description: 'Texto a resumir' },
              maxWords: { type: 'number', description: 'Máximo de palabras en el resumen', default: 100 },
            },
            required: ['text'],
          },
        },
      ],
    }});
  }

  if (method === 'tools/call') {
    const { name, arguments: args } = params;
    if (name === 'summarize') {
      const text = (args.text || '').slice(0, 10000);
      const prompt = `Resume el siguiente texto en máximo ${args.maxWords || 100} palabras. Sé conciso y captura los puntos principales:\n\n${text}`;
      return callCheapLLM(prompt, id);
    }
    return send({ id, error: { code: -32601, message: `Tool not found: ${name}` } });
  }
}

async function callCheapLLM(prompt, id) {
  const apiKey = process.env.GOOGLE_API_KEY || process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return send({ id, error: { code: -32000, message: 'GOOGLE_API_KEY no configurada' } });
  }

  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=${apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.3, maxOutputTokens: 500 },
        }),
      }
    );
    const data = await res.json();
    const text = data?.candidates?.[0]?.content?.parts?.[0]?.text || '(sin respuesta)';
    send({ id, result: { content: [{ type: 'text', text }] } });
  } catch (err) {
    send({ id, error: { code: -32000, message: err.message } });
  }
}

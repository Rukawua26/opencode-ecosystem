const WARN_CONSECUTIVE = 5;
const WARN_TOTAL = 20;
const WARN_FAILURES = 3;

const sessionState = new Map();

function getState(sessionID) {
  const sid = sessionID || 'default';
  if (!sessionState.has(sid)) {
    sessionState.set(sid, {
      lastTool: null,
      consecutive: 0,
      total: 0,
      failures: 0,
      lastFailTool: null,
    });
  }
  return sessionState.get(sid);
}

function resetState(sessionID) {
  const sid = sessionID || 'default';
  sessionState.delete(sid);
}

export const guardrailsPlugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      const st = getState(input.sessionID);
      st.total++;

      if (input.tool === st.lastTool) {
        st.consecutive++;
      } else {
        st.consecutive = 1;
        st.lastTool = input.tool;
      }

      if (st.consecutive >= WARN_CONSECUTIVE) {
        output.args = {
          ...output.args,
          _guardrail_warning: `[GUARDRAIL: Llamaste a "${input.tool}" ${st.consecutive} veces seguidas. Si no está funcionando, considera cambiar de enfoque o herramienta.]`,
        };
      }
    },

    "tool.execute.after": async (input, output) => {
      const st = getState(input.sessionID);

      if (st.total >= WARN_TOTAL && Math.random() < 0.3) {
        output.output = `[⚠️ ${st.total} tools usadas en esta sesión. Considera si puedes simplificar.]\n\n${output.output}`;
        output.metadata = { ...output.metadata, guardrail_triggered: "total_calls" };
      }

      const outText = output?.output || '';
      if (!outText || outText.trim().length < 5) {
        if (input.tool === st.lastFailTool) {
          st.failures++;
        } else {
          st.failures = 1;
          st.lastFailTool = input.tool;
        }

        if (st.failures >= WARN_FAILURES) {
          output.output = `[GUARDRAIL: "${input.tool}" devolvió resultado vacío ${st.failures} veces. Prueba otra estrategia.]\n\n${output.output}`;
          st.failures = 0;
        }
      } else {
        st.failures = 0;
      }
    },

    "session.compacted": async (input, _output) => {
      resetState(input.sessionID);
    },
  };
};

export default guardrailsPlugin;

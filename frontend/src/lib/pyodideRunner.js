// Client-side Python execution tracer, powered by Pyodide (CPython -> WASM).
// Loaded LAZILY from CDN on first use — never bundled, so it costs nothing until
// a learner actually clicks "Visualize execution". Given a snippet, it runs a
// sys.settrace harness inside Pyodide and returns a list of execution steps
// ({line, locals, stdout}) that the <CodeTrace> scrubber animates. Zero server
// compute — the whole point (server-side execution is what bankrupted early IDEs).

const PYODIDE_VERSION = '0.26.4';
const CDN_BASE = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

// The tracer. Verified in CPython; sys.settrace is supported in Pyodide.
const TRACER_SRC = `
import sys, json, io, contextlib

class _StepLimit(Exception):
    pass

def trace(source, max_steps=300):
    steps = []
    out = io.StringIO()
    try:
        code = compile(source, "<lesson>", "exec")
    except SyntaxError as e:
        return json.dumps({"steps": [], "error": "SyntaxError: " + str(e), "truncated": False})

    def safe_repr(v):
        try:
            r = repr(v)
        except Exception:
            r = "<unrepr>"
        return r if len(r) <= 120 else r[:117] + "..."

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != "<lesson>":
            return None
        if event == "line":
            if len(steps) >= max_steps:
                raise _StepLimit()
            local_vars = {k: safe_repr(v) for k, v in frame.f_locals.items() if not k.startswith("__")}
            steps.append({"line": frame.f_lineno, "locals": local_vars, "stdout": out.getvalue()})
        return tracer

    err = None
    truncated = False
    sys.settrace(tracer)
    try:
        with contextlib.redirect_stdout(out):
            exec(code, {"__name__": "__main__"})
    except _StepLimit:
        truncated = True
    except Exception as e:
        err = type(e).__name__ + ": " + str(e)
    finally:
        sys.settrace(None)
    steps.append({"line": None, "locals": {}, "stdout": out.getvalue(), "error": err})
    return json.dumps({"steps": steps, "error": err, "truncated": truncated})
`;

let _pyodidePromise = null;

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = () => reject(new Error('Failed to load Pyodide'));
    document.head.appendChild(s);
  });
}

// Singleton: load Pyodide + define the tracer exactly once, reuse across snippets.
function getPyodide() {
  if (!_pyodidePromise) {
    _pyodidePromise = (async () => {
      if (!window.loadPyodide) {
        await loadScript(`${CDN_BASE}pyodide.js`);
      }
      const pyodide = await window.loadPyodide({ indexURL: CDN_BASE });
      await pyodide.runPythonAsync(TRACER_SRC);
      return pyodide;
    })().catch((e) => {
      _pyodidePromise = null; // allow retry on failure
      throw e;
    });
  }
  return _pyodidePromise;
}

/**
 * Trace a Python snippet's execution.
 * @returns {Promise<{steps: Array<{line:number|null, locals:Object, stdout:string, error?:string}>, error:?string, truncated:boolean}>}
 */
export async function tracePython(code, maxSteps = 300) {
  const pyodide = await getPyodide();
  pyodide.globals.set('__lesson_src', code);
  const json = await pyodide.runPythonAsync(`trace(__lesson_src, ${maxSteps})`);
  return JSON.parse(json);
}

export default tracePython;

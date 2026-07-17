// frontend/src/maths/evaluator.js
// A tiny safe mathematical evaluator.
// Supports: numbers, x, + - * / ^, parentheses, |x| (or abs(x)), sin(), cos().
// No eval, no new Function.

export function evaluate(expr, xValue) {
  const tokens = [];
  let i = 0;
  while (i < expr.length) {
    let char = expr[i];
    if (/\s/.test(char)) {
      i++;
      continue;
    }
    if (/[a-z]/i.test(char)) {
      let word = "";
      while (i < expr.length && /[a-z]/i.test(expr[i])) {
        word += expr[i];
        i++;
      }
      tokens.push({ type: "word", value: word.toLowerCase() });
    } else if (/[0-9.]/.test(char)) {
      let numStr = "";
      while (i < expr.length && /[0-9.]/.test(expr[i])) {
        numStr += expr[i];
        i++;
      }
      tokens.push({ type: "num", value: parseFloat(numStr) });
    } else if ("+-*/^()|".includes(char)) {
      tokens.push({ type: "op", value: char });
      i++;
    } else {
      throw new Error("Unknown character: " + char);
    }
  }

  let pos = 0;

  function parseExpression() {
    let left = parseTerm();
    while (pos < tokens.length && tokens[pos].type === "op" && (tokens[pos].value === "+" || tokens[pos].value === "-")) {
      let op = tokens[pos].value;
      pos++;
      let right = parseTerm();
      if (op === "+") left += right;
      else left -= right;
    }
    return left;
  }

  function parseTerm() {
    let left = parseFactor();
    while (pos < tokens.length && tokens[pos].type === "op" && (tokens[pos].value === "*" || tokens[pos].value === "/")) {
      let op = tokens[pos].value;
      pos++;
      let right = parseFactor();
      if (op === "*") {
        left *= right;
      } else {
        left /= right;
      }
    }
    return left;
  }

  function parseFactor() {
    let left = parseBase();
    if (pos < tokens.length && tokens[pos].type === "op" && tokens[pos].value === "^") {
      pos++;
      let right = parseFactor(); // right-associative
      left = Math.pow(left, right);
    }
    return left;
  }

  function parseBase() {
    if (pos >= tokens.length) throw new Error("Unexpected end of expression");
    let token = tokens[pos];

    // Unary minus/plus bind LOOSER than ^, so -x^2 = -(x^2), not (-x)^2.
    // Negate a full factor (which consumes the exponent) rather than a bare base.
    if (token.type === "op" && token.value === "-") {
      pos++;
      return -parseFactor();
    }
    if (token.type === "op" && token.value === "+") {
      pos++;
      return parseFactor();
    }

    if (token.type === "op" && token.value === "(") {
      pos++;
      let val = parseExpression();
      if (pos >= tokens.length || tokens[pos].value !== ")") throw new Error("Missing closing parenthesis");
      pos++;
      return val;
    }

    if (token.type === "op" && token.value === "|") {
      pos++;
      let val = parseExpression();
      if (pos >= tokens.length || tokens[pos].value !== "|") throw new Error("Missing closing pipe");
      pos++;
      return Math.abs(val);
    }

    if (token.type === "num") {
      pos++;
      return token.value;
    }

    if (token.type === "word") {
      if (token.value === "x") {
        pos++;
        return xValue;
      }
      if (token.value === "abs") {
        pos++;
        if (pos >= tokens.length || tokens[pos].value !== "(") throw new Error("Expected ( after abs");
        pos++;
        let val = parseExpression();
        if (pos >= tokens.length || tokens[pos].value !== ")") throw new Error("Missing closing parenthesis");
        pos++;
        return Math.abs(val);
      }
      if (token.value === "sin") {
        pos++;
        if (pos >= tokens.length || tokens[pos].value !== "(") throw new Error("Expected ( after sin");
        pos++;
        let val = parseExpression();
        if (pos >= tokens.length || tokens[pos].value !== ")") throw new Error("Missing closing parenthesis");
        pos++;
        return Math.sin(val);
      }
      if (token.value === "cos") {
        pos++;
        if (pos >= tokens.length || tokens[pos].value !== "(") throw new Error("Expected ( after cos");
        pos++;
        let val = parseExpression();
        if (pos >= tokens.length || tokens[pos].value !== ")") throw new Error("Missing closing parenthesis");
        pos++;
        return Math.cos(val);
      }
      throw new Error("Unknown function or variable: " + token.value);
    }

    throw new Error("Unexpected token: " + token.value);
  }

  const result = parseExpression();
  if (pos < tokens.length) {
    throw new Error("Unexpected tokens at end of expression");
  }
  return result;
}

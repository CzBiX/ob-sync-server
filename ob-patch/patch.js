const swc = require('@swc/core');

class Walker {
  constructor(tree, onVisitNode) {
    this.tree = tree;
    this.onVisitNode = onVisitNode;
    this.end = false;
  }

  run() {
    this.visitNodes(this.tree, 'body')
    return this.tree; 
  }

  visitNodes(parent, prop) {
    const arr = parent[prop] ?? [];
    const tmp = [...arr];
    tmp.forEach((node, index) => {
      this.visitNode(node, parent, prop, index);
    });
  }

  visitArgs(parent, prop) {
    const arr = parent[prop] ?? [];
    arr.forEach((node, index) => {
      this.visitNode(node.expression, parent, prop, index);
    });
  }

  visitNode(node, parent, prop, index) {
    if (this.end || !node) return;

    if (this.onVisitNode?.(node, parent, prop, index)) {
      this.end = true;
      return;
    }

    switch (node.type) {
      case 'ArrayExpression':
        this.visitArgs(node, 'elements');
        break;
      case 'AssignmentExpression':
        this.visitNode(node.left, node, 'left', null);
        this.visitNode(node.right, node, 'right', null);
        break;
      case 'BlockStatement':
        this.visitNodes(node, 'stmts');
        break;
      case 'CallExpression':
      case 'NewExpression':
        this.visitNode(node.callee, node, 'callee', null)
        this.visitArgs(node, 'arguments');
        break;
      case 'IfStatement':
      case 'ConditionalExpression':
        this.visitNode(node.test, node, 'test', null);
        this.visitNode(node.consequent, node, 'consequent', null);
        this.visitNode(node.alternate, node, 'alternate', null);
        break;
      case 'ArrowFunctionExpression':
      case 'FunctionDeclaration':
      case 'FunctionExpression':
        this.visitNode(node.body, node, 'body', null);
        break;
      case 'ExpressionStatement':
      case 'ParenthesisExpression':
        this.visitNode(node.expression, node, 'expression', null);
        break;
      case 'ReturnStatement':
        this.visitNode(node.argument, node, 'argument', null);
        break;
      case 'SequenceExpression':
        this.visitNodes(node, 'expressions');
      case 'VariableDeclaration':
        this.visitNodes(node, 'declarations');
        break;
      case 'VariableDeclarator':
        this.visitNode(node.init, node, 'init', null);
        break;
    }
  }
}

function objectMatch(obj, pattern) {
  return Object.keys(pattern).every((key) => {
    const value = obj[key];
    if (value === null) return pattern[key] === null;

    if (typeof pattern[key] === 'object') {
      return objectMatch(value, pattern[key]);
    }

    if (typeof pattern[key] === 'array') {
      if (valut.length !== pattern[key].length) return false;

      return pattern[key].every((item, index) => {
        return objectMatch(value[index], item);
      })
    }

    return value === pattern[key];
  });
}

function printStmt(stmt) {
  return swc.printSync({
    type: 'Script',
    span: { start: 0, end: 0, ctxt: 0 },
    body: [stmt]
  }, {
    minify: true,
  })
}

const PATTERN_API_BASE = {
  type: 'VariableDeclaration',
  declarations: [{
    type: 'VariableDeclarator',
    id: {
      type: 'Identifier',
    },
    init: {
      type: 'BinaryExpression',
      operator: '+',
      left: {
        type: 'StringLiteral',
        value: 'https://',
      },
      right: {
        type: 'CallExpression',
        callee: {
          type: 'MemberExpression',
          object: {
            type: 'ArrayExpression',
          },
          property: {
            type: 'Identifier',
            value: 'join',
          }
        },
      },
    },
  }]
}

const PATTERN_WEBSOCKET_URL = {
  type: 'IfStatement',
  test: {
    type: 'BinaryExpression',
    operator: '&&',
    left: {
      type: 'UnaryExpression',
      operator: '!',
      argument: {
        type: 'CallExpression',
        callee: {
          type: 'MemberExpression',
          object: {
            type: 'Identifier',
          },
          property: {
            type: 'Identifier',
            value: 'call',
          },
        },
        arguments: [{
          expression: {
            type: 'Identifier',
          }
        }, {
          expression: {
            type: 'StringLiteral',
            value: '.obsidian.md',
          }
        }],
      },
    },
    right: {
      type: 'BinaryExpression',
      operator: '!==',
    },
  },
  consequent: {
    type: 'ReturnStatement',
  }
}

async function patch(source) {
  const ast = await swc.parse(source, {
    script: true,
    target: 'esnext',
    isModule: false,
  })

  const visitor = (() => {
    let label = 0

    return (node, parent, prop, index) => {
      switch (label) {
        case 0:
          if (objectMatch(node, PATTERN_API_BASE)) {
            console.log('found API base:', printStmt(node).code)

            const id = node.declarations[0].id.value
            const ast = swc.parseSync(`window.__apiBaseHandler = {};var ${id} = new Proxy(new String("http://dummy.obsidian.md"), window.__apiBaseHandler);`)
            parent[prop].splice(index, 1, ...ast.body)

            label++
          }
          break
        case 1:
          if (objectMatch(node, PATTERN_WEBSOCKET_URL)) {
            console.log('found websocket url:', printStmt(node).code)

            parent[prop].splice(index, 1)

            label++
          }
          break
        default:
          return true
      }
    }
  })()

  const walker = new Walker(ast, visitor)
  const result = walker.run()

  const code = await swc.print(result, {
    isModule: false,
    minify: true,
  })

  return code
}

const source = `
var mn = "https://" + [String.fromCharCode(97, 112, 105), "obsidian", "md"].join(".");
dummy(function() {
if (!HJ.call(u, ".obsidian.md") && "127.0.0.1" !== u)
  return s(new Error("Unable to connect to server."));
});`;

async function main() {
  const code = await patch(source)
  console.log('patched:', code.code) 
}

module.exports = {
  patch,
}

if (require.main === module) {
  main()
}